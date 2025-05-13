import os
import sys
from fastapi import Depends, HTTPException, BackgroundTasks, Body
from sqlalchemy.orm import Session
import logging
from datetime import datetime
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.services import pagoService, notificacionService, mercadoPagoService
from tutowebback.models import models


async def create_pago(pago: schemas.PagoCreate, db: Session, current_user: schemas.Usuario,
                      background_tasks: BackgroundTasks):
    try:
        # Crear el pago
        db_pago, preference = pagoService.PagoService().create_pago(db, pago, current_user["id"])

        # Preparar la respuesta
        pago_response = db_pago.to_dict_pago()

        # Si hay preferencia de MercadoPago, añadir a la respuesta
        if preference:
            pago_response["payment_url"] = preference["init_point"]
            pago_response["preference_id"] = preference["id"]

        # Enviar notificación en segundo plano
        background_tasks.add_task(
            notificar_pago,
            db=db,
            pago_id=db_pago.id,
            reserva_id=pago.reserva_id,
            metodo_pago=pago.metodo_pago,
            es_confirmacion=db_pago.estado == "completado"
        )

        return {
            "success": True,
            "data": pago_response,
            "message": "Pago iniciado correctamente"
        }
    except HTTPException as he:
        logging.error(f"HTTP error creating pago: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error creating pago: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def update_pago_estado(pago_id: int, estado: str, db: Session, current_user: schemas.Usuario,
                             background_tasks: BackgroundTasks):
    try:
        # Actualizar el estado del pago
        db_pago = pagoService.PagoService().update_pago_estado(db, pago_id, estado, current_user["id"])

        # Enviar notificación en segundo plano
        if estado == "completado":
            background_tasks.add_task(
                notificar_pago,
                db=db,
                pago_id=db_pago.id,
                reserva_id=db_pago.reserva_id,
                metodo_pago=db_pago.metodo_pago,
                es_confirmacion=True
            )

        return {
            "success": True,
            "data": db_pago.to_dict_pago(),
            "message": f"Estado del pago actualizado a {estado}"
        }
    except HTTPException as he:
        logging.error(f"HTTP error updating pago: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error updating pago: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_pago_by_reserva(reserva_id: int, db: Session, current_user: schemas.Usuario):
    try:
        # Verificar que la reserva exista
        reserva = db.query(models.Reserva).filter(models.Reserva.id == reserva_id).first()
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva not found")

        # Verificar permisos
        is_estudiante = reserva.estudiante_id == current_user["id"]

        # Obtener el servicio para verificar si es el tutor
        servicio = db.query(models.ServicioTutoria).filter(models.ServicioTutoria.id == reserva.servicio_id).first()
        is_tutor = servicio and servicio.tutor_id == current_user["id"]

        # Verificar si es admin
        is_admin = current_user["user_rol"] in ["superAdmin", "admin"]

        if not (is_estudiante or is_tutor or is_admin):
            raise HTTPException(status_code=403, detail="No tienes permiso para ver este pago")

        # Obtener el pago
        db_pago = pagoService.PagoService().get_pago_by_reserva(db, reserva_id)

        if not db_pago:
            return {
                "success": True,
                "data": None,
                "message": "No hay pagos para esta reserva"
            }

        return {
            "success": True,
            "data": db_pago.to_dict_pago(),
            "message": "Pago obtenido correctamente"
        }
    except HTTPException as he:
        logging.error(f"HTTP error getting pago: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error getting pago: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_mercadopago_public_key(current_user: schemas.Usuario):
    try:
        # Obtener la public key
        mp_service = mercadoPagoService.MercadoPagoService()
        public_key = mp_service.get_public_key()

        return {
            "success": True,
            "data": {
                "public_key": public_key
            },
            "message": "Public key obtenida correctamente"
        }
    except Exception as e:
        logging.error(f"Error getting MercadoPago public key: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def webhook_mercadopago(payment_data: dict, db: Session, background_tasks: BackgroundTasks):
    try:
        logging.info(f"Received webhook: {payment_data}")

        # Verificar que sea una notificación de tipo payment
        if payment_data.get("type") != "payment":
            return {"success": True, "message": "Notificación recibida pero no procesada"}

        # Obtener el ID de pago
        payment_id = payment_data.get("data", {}).get("id")
        if not payment_id:
            raise HTTPException(status_code=400, detail="ID de pago no proporcionado")

        # Procesar la notificación
        result = pagoService.PagoService().process_webhook_notification(db, payment_id)

        if result:
            # Enviar notificación en segundo plano
            background_tasks.add_task(
                notificar_pago_webhook,
                db=db,
                payment_id=payment_id
            )

            return {"success": True, "message": "Pago procesado correctamente"}
        else:
            return {"success": False, "message": "Error procesando el pago"}

    except Exception as e:
        logging.error(f"Error en webhook: {e}")
        return {"success": False, "message": f"Error en webhook: {str(e)}"}


# Función para enviar notificaciones en segundo plano
def notificar_pago(db: Session, pago_id: int, reserva_id: int, metodo_pago: str, es_confirmacion: bool):
    try:
        # Obtener la reserva
        reserva = db.query(models.Reserva).filter(models.Reserva.id == reserva_id).first()
        if not reserva:
            logging.error(f"Reserva {reserva_id} no encontrada para notificación de pago")
            return

        # Obtener el servicio y materia
        servicio = db.query(models.ServicioTutoria).filter(models.ServicioTutoria.id == reserva.servicio_id).first()
        if not servicio:
            logging.error(f"Servicio para reserva {reserva_id} no encontrado")
            return

        materia = db.query(models.Materia).filter(models.Materia.id == servicio.materia_id).first()
        materia_nombre = materia.nombre if materia else "materia"

        # Determinar destinatarios y mensajes según sea confirmación o inicio de pago
        if es_confirmacion:
            # Notificar al estudiante
            notificacionService.crear_notificacion(
                db=db,
                usuario_id=reserva.estudiante_id,
                titulo="Pago confirmado",
                mensaje=f"Tu pago por la tutoría de {materia_nombre} ha sido confirmado.",
                tipo="pago",
                reserva_id=reserva.id
            )

            # Notificar al tutor
            notificacionService.crear_notificacion(
                db=db,
                usuario_id=servicio.tutor_id,
                titulo="Pago recibido",
                mensaje=f"Has recibido un pago por la tutoría de {materia_nombre}.",
                tipo="pago",
                reserva_id=reserva.id
            )
        else:
            # Es inicio de pago
            metodo_texto = "efectivo" if metodo_pago == "efectivo" else "Mercado Pago"

            # Notificar al tutor
            notificacionService.crear_notificacion(
                db=db,
                usuario_id=servicio.tutor_id,
                titulo="Pago iniciado",
                mensaje=f"Un estudiante ha iniciado un pago en {metodo_texto} por la tutoría de {materia_nombre}.",
                tipo="pago",
                reserva_id=reserva.id
            )
    except Exception as e:
        logging.error(f"Error enviando notificación de pago: {e}")


def notificar_pago_webhook(db: Session, payment_id: str):
    try:
        # Consultar el pago en MercadoPago
        mp_service = mercadoPagoService.MercadoPagoService()
        payment_info = mp_service.consultar_pago(payment_id)

        # Obtener la external_reference
        external_reference = payment_info.get("external_reference", "")
        if not external_reference or "_pago_" not in external_reference:
            logging.warning(f"External reference inválida: {external_reference}")
            return

        # Extraer IDs de reserva y pago
        parts = external_reference.split("_")
        if len(parts) < 4:
            logging.warning(f"Formato de external reference incorrecto: {external_reference}")
            return

        reserva_id = int(parts[1])
        pago_id = int(parts[3])

        # Obtener el pago en la base de datos
        pago_service = pagoService.PagoService()
        db_pago = pago_service.get_pago_by_id(db, pago_id)
        if not db_pago:
            logging.warning(f"Pago con ID {pago_id} no encontrado")
            return

        # Si el pago está confirmado, enviar notificación
        if db_pago.estado == "completado":
            notificar_pago(
                db=db,
                pago_id=pago_id,
                reserva_id=reserva_id,
                metodo_pago="mercado_pago",
                es_confirmacion=True
            )
    except Exception as e:
        logging.error(f"Error en notificar_pago_webhook: {e}")