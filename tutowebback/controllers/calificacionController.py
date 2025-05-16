import os
import sys
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.services import calificacionService
from tutowebback.auth import auth


async def create_calificacion(calificacion: schemas.CalificacionCreate, db: Session, current_user: schemas.Usuario):
    try:
        # Verificar que el calificador_id coincida con el usuario actual
        if calificacion.calificador_id != current_user["id"] and current_user["user_rol"] not in ["superAdmin", "admin"]:
            raise HTTPException(status_code=403, detail="Solo puedes crear calificaciones para ti mismo")
            
        # Pasar la calificación tal como está, ya incluye calificador_id
        db_calificacion = calificacionService.CalificacionService().create_calificacion(
            db, calificacion, current_user["id"]
        )
        
        calificacion_response = db_calificacion.to_dict_calificacion()
        
        return {
            "success": True,
            "data": calificacion_response,
            "message": "Calificación created successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error creating calificacion: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error creating calificacion: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_calificacion_by_reserva(reserva_id: int, db: Session, current_user: schemas.Usuario):
    try:
        db_calificacion = calificacionService.CalificacionService().get_calificacion_by_reserva(db, reserva_id)
        
        if not db_calificacion:
            return {
                "success": False,
                "data": None,
                "message": "No calificación found for this reserva"
            }
        
        calificacion_response = db_calificacion.to_dict_calificacion()
        
        return {
            "success": True,
            "data": calificacion_response,
            "message": "Get calificacion successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving calificacion: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving calificacion: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_calificaciones_by_tutor(tutor_id: int, db: Session, current_user: schemas.Usuario):
    try:
        db_calificaciones = calificacionService.CalificacionService().get_calificaciones_by_tutor(db, tutor_id)
        
        calificacion_responses = []
        for calificacion in db_calificaciones:
            calificacion_dict = calificacion.to_dict_calificacion()
            
            # Añadir información del estudiante calificador
            if hasattr(calificacion, 'calificador') and calificacion.calificador:
                calificacion_dict["calificador"] = calificacion.calificador.to_dict_usuario()
            
            # Añadir información básica de la reserva
            if hasattr(calificacion, 'reserva') and calificacion.reserva:
                calificacion_dict["reserva"] = calificacion.reserva.to_dict_reserva()
            
            calificacion_responses.append(calificacion_dict)
        
        return {
            "success": True,
            "data": calificacion_responses,
            "message": "Get calificaciones by tutor successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving calificaciones: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving calificaciones: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_calificaciones_by_estudiante(db: Session, current_user: schemas.Usuario):
    try:
        db_calificaciones = calificacionService.CalificacionService().get_calificaciones_by_estudiante(
            db, current_user["id"]
        )
        
        calificacion_responses = []
        for calificacion in db_calificaciones:
            calificacion_dict = calificacion.to_dict_calificacion()
            
            # Añadir información del tutor calificado
            if hasattr(calificacion, 'calificado') and calificacion.calificado:
                calificacion_dict["calificado"] = calificacion.calificado.to_dict_usuario()
            
            # Añadir información básica de la reserva
            if hasattr(calificacion, 'reserva') and calificacion.reserva:
                calificacion_dict["reserva"] = calificacion.reserva.to_dict_reserva()
            
            calificacion_responses.append(calificacion_dict)
        
        return {
            "success": True,
            "data": calificacion_responses,
            "message": "Get calificaciones by estudiante successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving calificaciones: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving calificaciones: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_calificaciones_for_estudiante_reservas(db: Session, current_user: schemas.Usuario):
    try:
        # Obtener todas las calificaciones para las reservas del estudiante actual
        calificaciones_dict = calificacionService.CalificacionService().get_calificaciones_for_estudiante_reservas(
            db, current_user["id"]
        )
        
        # Convertir a un formato adecuado para la respuesta
        calificaciones_response = {}
        for reserva_id, calificacion in calificaciones_dict.items():
            calificaciones_response[reserva_id] = calificacion.to_dict_calificacion()
        
        return {
            "success": True,
            "data": calificaciones_response,
            "message": "Get calificaciones for estudiante reservas successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving calificaciones: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving calificaciones: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")