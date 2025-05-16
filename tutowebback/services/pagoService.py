import os
import sys
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.models import models
from tutowebback.schemas import schemas
from tutowebback.services import mercadoPagoService


class PagoService:
    def create_pago(self, db: Session, pago: schemas.PagoCreate, current_user_id: int):
        """
        Crea un pago para una reserva
        """
        try:
            # Verificar si existe la reserva
            reserva = db.query(models.Reserva).filter(models.Reserva.id == pago.reserva_id).first()
            if not reserva:
                raise HTTPException(status_code=404, detail="Reserva not found")

            # Verificar que la reserva corresponda al usuario actual o sea un administrador/tutor
            is_estudiante = reserva.estudiante_id == current_user_id

            # Obtener el servicio para verificar el tutor
            servicio = db.query(models.ServicioTutoria).filter(models.ServicioTutoria.id == reserva.servicio_id).first()
            if not servicio:
                raise HTTPException(status_code=404, detail="Servicio no encontrado")

            is_tutor = servicio.tutor_id == current_user_id

            # Verificar si es admin
            current_user = db.query(models.Usuario).filter(models.Usuario.id == current_user_id).first()
            is_admin = current_user and db.query(models.Rol).filter(
                models.Rol.id == current_user.id_rol).first().nombre in ["superAdmin", "admin"]

            if not (is_estudiante or is_tutor or is_admin):
                raise HTTPException(status_code=403, detail="No tienes permiso para crear un pago para esta reserva")

            # Verificar que la reserva esté en estado completada
            if reserva.estado != 'completada':
                raise HTTPException(status_code=400, detail="Solo se pueden pagar reservas completadas")

            # Verificar que no exista ya un pago completado para esta reserva
            existing_pago = db.query(models.Pago).filter(
                models.Pago.reserva_id == pago.reserva_id,
                models.Pago.estado == "completado"
            ).first()

            if existing_pago:
                raise HTTPException(status_code=400, detail="Esta reserva ya tiene un pago completado")

            # Verificar que el monto del pago coincida con el precio del servicio
            if float(pago.monto) != float(servicio.precio):
                raise HTTPException(status_code=400, detail=f"El monto del pago debe ser {servicio.precio}")

            # Crear el objeto de pago
            db_pago = models.Pago(
                reserva_id=pago.reserva_id,
                monto=pago.monto,
                metodo_pago=pago.metodo_pago,
                estado="pendiente",
                referencia_externa=None,
                fecha_pago=None,
                fecha_creacion=datetime.utcnow()
            )

            db.add(db_pago)
            db.flush()  # Para obtener el ID sin hacer commit

            # Si el método es efectivo y quien lo crea es el tutor, marcar como completado
            if pago.metodo_pago == "efectivo" and is_tutor:
                db_pago.estado = "completado"
                db_pago.fecha_pago = datetime.utcnow()
                db.commit()
                db.refresh(db_pago)
                return db_pago, None

            # Si el método es MercadoPago, crear preferencia
            elif pago.metodo_pago == "mercado_pago":
                # Obtener información de la materia para el título de pago
                materia = db.query(models.Materia).filter(models.Materia.id == servicio.materia_id).first()
                materia_nombre = materia.nombre if materia else "materia"

                mp_service = mercadoPagoService.MercadoPagoService()

                titulo = f"Tutoría de {materia_nombre}"
                notas = f"Reserva #{reserva.id} - {reserva.fecha} {reserva.hora_inicio}"

                try:
                    preference = mp_service.crear_preferencia(
                        titulo=titulo,
                        precio=float(pago.monto),
                        cantidad=1,
                        reserva_id=reserva.id,
                        pago_id=db_pago.id,
                        notas=notas
                    )

                    # Guardar referencia externa
                    db_pago.referencia_externa = preference["id"]
                    db.commit()
                    db.refresh(db_pago)

                    return db_pago, preference
                except Exception as e:
                    # Si falla la creación de la preferencia, eliminar el pago
                    db.delete(db_pago)
                    db.commit()
                    raise HTTPException(status_code=500, detail=f"Error al crear preferencia de pago: {str(e)}")

            # Otro método de pago (no debería llegar aquí)
            else:
                raise HTTPException(status_code=400, detail=f"Método de pago no válido: {pago.metodo_pago}")

        except HTTPException as he:
            db.rollback()
            raise he
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating pago: {e}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    def update_pago_estado(self, db: Session, pago_id: int, estado: str, current_user_id: int = None):
        """
        Actualiza el estado de un pago
        """
        try:
            # Obtener el pago
            db_pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
            if not db_pago:
                raise HTTPException(status_code=404, detail="Pago not found")

            # Verificar que el pago sea en efectivo si se actualiza manualmente
            if current_user_id and db_pago.metodo_pago != "efectivo":
                raise HTTPException(status_code=400, detail="Solo se pueden actualizar manualmente pagos en efectivo")

            # Verificar permisos si hay usuario actual
            if current_user_id:
                # Obtener la reserva y el servicio
                reserva = db.query(models.Reserva).filter(models.Reserva.id == db_pago.reserva_id).first()
                if not reserva:
                    raise HTTPException(status_code=404, detail="Reserva not found")

                servicio = db.query(models.ServicioTutoria).filter(
                    models.ServicioTutoria.id == reserva.servicio_id).first()
                if not servicio:
                    raise HTTPException(status_code=404, detail="Servicio not found")

                # Verificar si es el tutor o un admin
                current_user = db.query(models.Usuario).filter(models.Usuario.id == current_user_id).first()
                is_admin = current_user and db.query(models.Rol).filter(
                    models.Rol.id == current_user.id_rol).first().nombre in ["superAdmin", "admin"]

                if not is_admin and servicio.tutor_id != current_user_id:
                    raise HTTPException(status_code=403, detail="No tienes permiso para actualizar este pago")

            # Actualizar el estado
            if estado == "completado":
                db_pago.estado = estado
                db_pago.fecha_pago = datetime.utcnow()
            elif estado in ["pendiente", "cancelado"]:
                db_pago.estado = estado
            else:
                raise HTTPException(status_code=400, detail=f"Estado no válido: {estado}")

            db.commit()
            db.refresh(db_pago)
            return db_pago

        except HTTPException as he:
            db.rollback()
            raise he
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating pago: {e}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    def get_pago_by_reserva(self, db: Session, reserva_id: int):
        """
        Obtiene el pago más reciente de una reserva
        """
        return db.query(models.Pago).filter(
            models.Pago.reserva_id == reserva_id
        ).order_by(models.Pago.fecha_creacion.desc()).first()

    def get_pago_by_id(self, db: Session, pago_id: int):
        """
        Obtiene un pago por su ID
        """
        return db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    
    def process_webhook_notification(self, db: Session, payment_id: str):
        """
        Procesa una notificación de pago recibida desde MercadoPago
        """
        try:
            # Consultar el pago en MercadoPago
            mp_service = mercadoPagoService.MercadoPagoService()
            payment_info = mp_service.consultar_pago(payment_id)
            
            # Verificar el estado del pago
            status = payment_info.get("status", "")
            
            # Obtener la external_reference
            external_reference = payment_info.get("external_reference", "")
            if not external_reference or "_pago_" not in external_reference:
                logging.warning(f"External reference inválida: {external_reference}")
                return False, None
                
            # Extraer IDs de reserva y pago
            try:
                parts = external_reference.split("_")
                reserva_id = int(parts[1])
                pago_id = int(parts[3])
            except (IndexError, ValueError):
                logging.warning(f"Formato de external reference incorrecto: {external_reference}")
                return False, None
                
            # Obtener el pago en nuestra base de datos
            db_pago = self.get_pago_by_id(db, pago_id)
            if not db_pago:
                logging.warning(f"Pago con ID {pago_id} no encontrado")
                return False, None
                
            # Mapear los estados de MercadoPago a nuestros estados
            estado_mapping = {
                "approved": "completado",
                "pending": "pendiente",
                "rejected": "cancelado",
                "cancelled": "cancelado",
                "refunded": "reembolsado",
                "charged_back": "cancelado"
            }
            
            nuevo_estado = estado_mapping.get(status, db_pago.estado)
            
            # Si el estado ha cambiado, actualizarlo
            if nuevo_estado != db_pago.estado:
                db_pago.estado = nuevo_estado
                
                # Si el pago está aprobado, actualizar la fecha de pago
                if nuevo_estado == "completado" and not db_pago.fecha_pago:
                    db_pago.fecha_pago = datetime.now()
                    
                # Guardar la referencia externa
                db_pago.referencia_externa = payment_id
                
                db.commit()
                db.refresh(db_pago)
                
            return True, db_pago
                
        except Exception as e:
            logging.error(f"Error procesando notificación de webhook: {e}")
            db.rollback()
            return False, None
    def get_pagos_by_estudiante(self, db: Session, estudiante_id: int):
        """
        Obtiene todos los pagos asociados a las reservas de un estudiante
        """
        try:
            # Primero obtenemos todas las reservas del estudiante
            reservas = db.query(models.Reserva).filter(
                models.Reserva.estudiante_id == estudiante_id
            ).all()
            
            if not reservas:
                return []
                
            # Obtenemos los IDs de las reservas
            reserva_ids = [reserva.id for reserva in reservas]
            
            # Ahora obtenemos todos los pagos asociados a esas reservas
            pagos = db.query(models.Pago).filter(
                models.Pago.reserva_id.in_(reserva_ids)
            ).all()
            
            # Organizamos los pagos por reserva_id para fácil acceso
            pagos_dict = {pago.reserva_id: pago for pago in pagos}
            
            return pagos_dict
            
        except Exception as e:
            logging.error(f"Error getting pagos by estudiante: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")


