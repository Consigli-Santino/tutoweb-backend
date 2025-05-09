# reservaController.py
import os
import sys
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging
from datetime import datetime, date

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

        # Delegar toda la lógica al servicio
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


async def check_reservas(tutor_id: int, fecha_str: str, db: Session):
    try:
        # Convertir string a objeto date
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha incorrecto. Use YYYY-MM-DD")

        # Delegar la lógica al servicio
        reservas = reservaService.ReservaService().check_reservas_by_fecha_tutor(db, tutor_id, fecha)

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
        # Obtener la reserva del servicio
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


async def get_reserva_detallada(id: int, db: Session, current_user: schemas.Usuario):
    try:
        # Obtener la reserva detallada
        service = reservaService.ReservaService()
        db_reserva = service.get_reserva(db, id)

        # Verificar que el usuario pueda ver esta reserva
        if (db_reserva.estudiante_id != current_user["id"] and
                db_reserva.tutor_id != current_user["id"] and
                current_user["user_rol"] not in ["superAdmin", "admin"]):
            raise HTTPException(status_code=403, detail="No estás autorizado para ver esta reserva")

        # Obtener detalles completos
        reserva_response = service.get_reserva_detallada(db, id)

        return {
            "success": True,
            "data": reserva_response,
            "message": "Get reserva detallada successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving reserva detallada: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving reserva detallada: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_reservas_by_estudiante(db: Session, current_user: schemas.Usuario):
    try:
        # Delegar la lógica al servicio
        db_reservas = reservaService.ReservaService().get_reservas_by_estudiante(db, current_user["id"])

        # Transformar las reservas en formato de respuesta
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


async def get_reservas_by_estudiante_detalladas(db: Session, current_user: schemas.Usuario):
    try:
        # Delegar la lógica al servicio
        reserva_responses = reservaService.ReservaService().get_reservas_by_estudiante_detalladas(db,
                                                                                                  current_user["id"])

        return {
            "success": True,
            "data": reserva_responses,
            "message": "Get reservas detalladas by estudiante successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving detailed reservas: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving detailed reservas: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_reservas_by_tutor(db: Session, current_user: schemas.Usuario):
    try:
        # Delegar la lógica al servicio
        db_reservas = reservaService.ReservaService().get_reservas_by_tutor(db, current_user["id"])

        # Transformar a formato de respuesta
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


async def get_reservas_by_tutor_detalladas(db: Session, current_user: schemas.Usuario):
    try:
        # Delegar la lógica al servicio
        reserva_responses = reservaService.ReservaService().get_reservas_by_tutor_detalladas(db, current_user["id"])

        return {
            "success": True,
            "data": reserva_responses,
            "message": "Get reservas detalladas by tutor successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving detailed reservas for tutor: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving detailed reservas for tutor: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def edit_reserva(id: int, reserva: schemas.ReservaUpdate, db: Session, current_user: schemas.Usuario):
    try:
        # Comprobar si el usuario es admin
        is_admin = current_user["user_rol"] in ["superAdmin", "admin"]

        # Delegar toda la lógica al servicio
        db_reserva = reservaService.ReservaService().edit_reserva(
            db,
            id,
            reserva,
            current_user["id"],
            is_admin
        )

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
        # Obtener la reserva
        service = reservaService.ReservaService()
        db_reserva = service.get_reserva(db, id)

        # Solo el admin o el estudiante pueden eliminar una reserva
        if (db_reserva.estudiante_id != current_user["id"] and
                current_user["user_rol"] not in ["superAdmin", "admin"]):
            raise HTTPException(status_code=403,
                                detail="No estás autorizado para eliminar esta reserva")

        # Delegar la eliminación al servicio
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

        # Delegar la lógica al servicio
        disponibilidades = reservaService.ReservaService().get_disponibilidades_disponibles(db, tutor_id, fecha)

        # Convertir a formato de respuesta
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


async def get_horarios_disponibles(servicio_id: int, fecha_str: str, db: Session):
    try:
        # Convertir string a objeto date
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha incorrecto. Use YYYY-MM-DD")

        # Delegar la lógica al servicio
        slots = reservaService.ReservaService().get_horarios_disponibles(db, servicio_id, fecha)

        return {
            "success": True,
            "data": slots,
            "message": "Get horarios disponibles successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving horarios disponibles: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving horarios disponibles: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")