import os
import sys
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.services import disponibilidadService


async def create_disponibilidad(disponibilidad: schemas.DisponibilidadCreate, db: Session,
                                current_user: schemas.Usuario):
    try:
        # Asegúrate de que el tutor_id coincida con el usuario actual, excepto para administradores
        if disponibilidad.tutor_id != current_user["id"] and current_user["user_rol"] not in ["superAdmin", "admin"]:
            raise HTTPException(status_code=403, detail="You can only create availability for yourself")

        db_disponibilidad = disponibilidadService.DisponibilidadService().create_disponibilidad(db, disponibilidad)
        disponibilidad_response = db_disponibilidad.to_dict_disponibilidad()
        return {
            "success": True,
            "data": disponibilidad_response,
            "message": "Disponibilidad created successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error creating disponibilidad: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error creating disponibilidad: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_disponibilidad(id: int, db: Session, current_user: schemas.Usuario):
    try:
        db_disponibilidad = disponibilidadService.DisponibilidadService().get_disponibilidad(db, id)

        # Verificar si el usuario actual puede ver esta disponibilidad
        if db_disponibilidad.tutor_id != current_user["id"] and current_user["user_rol"] not in ["superAdmin", "admin"]:
            # En este caso, permitimos que cualquier usuario vea la disponibilidad (puedes ajustar esta política)
            pass

        disponibilidad_response = db_disponibilidad.to_dict_disponibilidad()
        return {
            "success": True,
            "data": disponibilidad_response,
            "message": "Get disponibilidad successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving disponibilidad: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving disponibilidad: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_disponibilidades_by_tutor(tutor_id: int, db: Session, current_user: schemas.Usuario):
    try:
        db_disponibilidades = disponibilidadService.DisponibilidadService().get_disponibilidades_by_tutor(db, tutor_id)
        disponibilidad_responses = [disponibilidad.to_dict_disponibilidad() for disponibilidad in db_disponibilidades]
        return {
            "success": True,
            "data": disponibilidad_responses,
            "message": "Get disponibilidades by tutor successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving disponibilidades by tutor: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving disponibilidades by tutor: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def edit_disponibilidad(id: int, disponibilidad: schemas.DisponibilidadUpdate, db: Session,
                              current_user: schemas.Usuario):
    try:
        service = disponibilidadService.DisponibilidadService()

        # Verificar que la disponibilidad pertenezca al usuario actual, excepto para administradores
        db_disponibilidad = service.get_disponibilidad(db, id)

        if db_disponibilidad.tutor_id != current_user["id"] and current_user["user_rol"] not in ["superAdmin", "admin"]:
            raise HTTPException(status_code=403, detail="You can only edit your own availability")

        # Pasar el ID del usuario actual para verificación adicional en el servicio
        db_disponibilidad = service.edit_disponibilidad(db, id, disponibilidad, current_user["id"])
        disponibilidad_response = db_disponibilidad.to_dict_disponibilidad()
        return {
            "success": True,
            "data": disponibilidad_response,
            "message": "Disponibilidad edited successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error updating disponibilidad: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error updating disponibilidad: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def delete_disponibilidad(id: int, db: Session, current_user: schemas.Usuario):
    try:
        service = disponibilidadService.DisponibilidadService()

        # Verificar que la disponibilidad pertenezca al usuario actual, excepto para administradores
        db_disponibilidad = service.get_disponibilidad(db, id)

        if db_disponibilidad.tutor_id != current_user["id"] and current_user["user_rol"] not in ["superAdmin", "admin"]:
            raise HTTPException(status_code=403, detail="You can only delete your own availability")

        result = service.delete_disponibilidad(db, id, current_user["id"])
        return {
            "success": result,
            "message": "Disponibilidad deleted successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error deleting disponibilidad: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error deleting disponibilidad: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")