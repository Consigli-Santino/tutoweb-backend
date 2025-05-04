# reservaController.py
import os
import sys
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging
from datetime import datetime, date

from tutowebback.models import models

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.services import reservaService
from tutowebback.auth import auth

async def create_reserva(reserva: schemas.ReservaCreate, db: Session, current_user: schemas.Usuario):
    try:
        # Verificar que el estudiante_id sea el del usuario actual (a menos que sea admin)
        if reserva.estudiante_id != current_user["id"] and current_user["user_rol"] not in ["superAdmin", "admin"]:
            raise HTTPException(status_code=403, detail="Solo puedes crear reservas para ti mismo")

        db_reserva = reservaService.ReservaService().create_reserva(db, reserva)
        reserva_response = db_reserva.to_dict_reserva()

        return {
            "success": True,
            "data": reserva_response,
            "message": "Reserva created successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error creating reserva: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error creating reserva: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# En reservaController.py
async def check_reservas(tutor_id: int, fecha_str: str, db: Session):
    try:
        # Convertir string a objeto date
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha incorrecto. Use YYYY-MM-DD")

        # Obtener servicios del tutor
        servicios = db.query(models.ServicioTutoria).filter(
            models.ServicioTutoria.tutor_id == tutor_id,
            models.ServicioTutoria.activo == True
        ).all()

        if not servicios:
            return {
                "success": True,
                "data": [],
                "message": "No hay servicios para este tutor"
            }

        # Obtener IDs de servicios
        servicio_ids = [servicio.id for servicio in servicios]

        # Obtener todas las reservas para los servicios del tutor en la fecha dada
        reservas = db.query(models.Reserva).filter(
            models.Reserva.servicio_id.in_(servicio_ids),
            models.Reserva.fecha == fecha,
            models.Reserva.estado.in_(["pendiente", "confirmada"])
        ).all()

        # Convertir a formato de respuesta
        reservas_response = [reserva.to_dict_reserva() for reserva in reservas]

        return {
            "success": True,
            "data": reservas_response,
            "message": "Reservas obtenidas correctamente"
        }
    except HTTPException as he:
        logging.error(f"HTTP error checking reservas: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error checking reservas: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
async def get_reserva(id: int, db: Session, current_user: schemas.Usuario):
    try:
        db_reserva = reservaService.ReservaService().get_reserva(db, id)

        # Verificar que el usuario pueda ver esta reserva
        if (db_reserva.estudiante_id != current_user["id"] and
                db_reserva.tutor_id != current_user["id"] and
                current_user["user_rol"] not in ["superAdmin", "admin"]):
            raise HTTPException(status_code=403, detail="No estás autorizado para ver esta reserva")

        reserva_response = db_reserva.to_dict_reserva()

        return {
            "success": True,
            "data": reserva_response,
            "message": "Get reserva successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving reserva: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving reserva: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_reservas_by_estudiante(db: Session, current_user: schemas.Usuario):
    try:
        db_reservas = reservaService.ReservaService().get_reservas_by_estudiante(current_user["id"])
        reserva_responses = [reserva.to_dict_reserva() for reserva in db_reservas]

        return {
            "success": True,
            "data": reserva_responses,
            "message": "Get reservas by estudiante successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving reservas: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving reservas: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_reservas_by_tutor(db: Session, current_user: schemas.Usuario):
    try:
        db_reservas = reservaService.ReservaService().get_reservas_by_tutor(current_user["id"])
        reserva_responses = [reserva.to_dict_reserva() for reserva in db_reservas]

        return {
            "success": True,
            "data": reserva_responses,
            "message": "Get reservas by tutor successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving reservas: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving reservas: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def edit_reserva(id: int, reserva: schemas.ReservaUpdate, db: Session, current_user: schemas.Usuario):
    try:
        # Obtener la reserva para verificar permisos
        service = reservaService.ReservaService()
        db_reserva = service.get_reserva(db, id)

        # Verificar que el usuario pueda editar esta reserva
        is_estudiante = db_reserva.estudiante_id == current_user["id"]
        is_tutor = db_reserva.tutor_id == current_user["id"]
        is_admin = current_user["user_rol"] in ["superAdmin", "admin"]

        if not (is_estudiante or is_tutor or is_admin):
            raise HTTPException(status_code=403, detail="No estás autorizado para editar esta reserva")

        # Restricciones según tipo de usuario
        if is_estudiante and not is_admin:
            # Estudiantes solo pueden cancelar, no cambiar estado a confirmada o completada
            if reserva.estado and reserva.estado not in ["cancelada"]:
                raise HTTPException(status_code=403,
                                    detail="Como estudiante solo puedes cancelar la reserva")

        if is_tutor and not is_admin:
            # Tutores pueden confirmar, completar o cancelar, pero no cambiar fecha
            if reserva.fecha:
                raise HTTPException(status_code=403,
                                    detail="Como tutor no puedes cambiar la fecha de la reserva")

        db_reserva = service.edit_reserva(db, id, reserva)
        reserva_response = db_reserva.to_dict_reserva()

        return {
            "success": True,
            "data": reserva_response,
            "message": "Reserva edited successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error updating reserva: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error updating reserva: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def delete_reserva(id: int, db: Session, current_user: schemas.Usuario):
    try:
        # Obtener la reserva para verificar permisos
        service = reservaService.ReservaService()
        db_reserva = service.get_reserva(db, id)

        # Solo el admin o el estudiante pueden eliminar una reserva
        if (db_reserva.estudiante_id != current_user["id"] and
                current_user["user_rol"] not in ["superAdmin", "admin"]):
            raise HTTPException(status_code=403,
                                detail="No estás autorizado para eliminar esta reserva")

        result = service.delete_reserva(db, id)

        return {
            "success": result,
            "message": "Reserva deleted successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error deleting reserva: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error deleting reserva: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_disponibilidades_disponibles(tutor_id: int, fecha_str: str, db: Session):
    try:
        # Convertir string a objeto date
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha incorrecto. Use YYYY-MM-DD")

        disponibilidades = reservaService.ReservaService().get_disponibilidades_disponibles(db, tutor_id, fecha)
        disponibilidad_responses = [disp.to_dict_disponibilidad() for disp in disponibilidades]

        return {
            "success": True,
            "data": disponibilidad_responses,
            "message": "Get disponibilidades disponibles successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving disponibilidades: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving disponibilidades: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")