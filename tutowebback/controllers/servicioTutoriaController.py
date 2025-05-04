# servicioTutoriaController.py

import os
import sys
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.services import servicioTutoriaService


async def create_servicio(servicio: schemas.ServicioTutoriaCreate, db: Session, current_user: schemas.Usuario):
    try:
        # Verificar que el tutor_id sea el del usuario actual (a menos que sea admin)
        if servicio.tutor_id != current_user["id"] and current_user["user_rol"] not in ["superAdmin", "admin"]:
            raise HTTPException(status_code=403, detail="Solo puedes crear servicios para ti mismo")

        db_servicio = servicioTutoriaService.ServicioTutoriaService().create_servicio(db, servicio)
        servicio_response = db_servicio.to_dict_servicio_tutoria()

        return {
            "success": True,
            "data": servicio_response,
            "message": "Servicio created successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error creating servicio: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error creating servicio: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_servicio(id: int, db: Session, current_user: schemas.Usuario):
    try:
        db_servicio = servicioTutoriaService.ServicioTutoriaService().get_servicio(db, id)
        servicio_response = db_servicio.to_dict_servicio_tutoria()

        return {
            "success": True,
            "data": servicio_response,
            "message": "Get servicio successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving servicio: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving servicio: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_servicios_by_tutor(email: str, db: Session, current_user: schemas.Usuario):
    try:
        db_servicios = servicioTutoriaService.ServicioTutoriaService().get_servicios_by_tutor(db, email)
        servicios_response = [servicio.to_dict_servicio_tutoria() for servicio in db_servicios]

        return {
            "success": True,
            "data": servicios_response,
            "message": "Get servicios by tutor successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving servicios: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving servicios: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_servicios_by_materia(materia_id: int, db: Session, current_user: schemas.Usuario):
    try:
        db_servicios = servicioTutoriaService.ServicioTutoriaService().get_servicios_by_materia(db, materia_id)
        servicios_response = [servicio.to_dict_servicio_tutoria() for servicio in db_servicios]

        return {
            "success": True,
            "data": servicios_response,
            "message": "Get servicios by materia successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving servicios: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving servicios: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def edit_servicio(id: int, servicio: schemas.ServicioTutoriaUpdate, db: Session, current_user: schemas.Usuario):
    try:
        # Verificar que el usuario tenga permisos para editar este servicio
        db_servicio = servicioTutoriaService.ServicioTutoriaService().get_servicio(db, id)

        if db_servicio.tutor_id != current_user["id"] and current_user["user_rol"] not in ["superAdmin", "admin"]:
            raise HTTPException(status_code=403, detail="Solo puedes editar tus propios servicios")

        db_servicio = servicioTutoriaService.ServicioTutoriaService().edit_servicio(db, id, servicio)
        servicio_response = db_servicio.to_dict_servicio_tutoria()

        return {
            "success": True,
            "data": servicio_response,
            "message": "Servicio updated successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error updating servicio: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error updating servicio: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def delete_servicio(id: int, db: Session, current_user: schemas.Usuario):
    try:
        # Verificar que el usuario tenga permisos para eliminar este servicio
        db_servicio = servicioTutoriaService.ServicioTutoriaService().get_servicio(db, id)

        if db_servicio.tutor_id != current_user["id"] and current_user["user_rol"] not in ["superAdmin", "admin"]:
            raise HTTPException(status_code=403, detail="Solo puedes eliminar tus propios servicios")

        result = servicioTutoriaService.ServicioTutoriaService().delete_servicio(db, id)

        return {
            "success": result,
            "message": "Servicio deleted successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error deleting servicio: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error deleting servicio: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")