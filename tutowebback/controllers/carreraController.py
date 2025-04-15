import os
import sys
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from starlette import status

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.services import carreraService

async def create_carrera(carrera: schemas.CarreraCreate, db: Session = Depends(database.get_db), current_user: schemas.Usuario = None):
    try:
        db_carrera = carreraService.CarreraService().create_carrera(db, carrera)
        carrera_response = db_carrera.to_dict_carrera()
        return {
            "success": True,
            "data": carrera_response,
            "message": "Carrera created successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error creating carrera: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error creating carrera: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_carrera(id: int, db: Session, current_user: schemas.Usuario = None):
    try:
        db_carrera = carreraService.CarreraService().get_carrera(db, id)
        carrera_response = db_carrera.to_dict_carrera()
        return {
            "success": True,
            "data": carrera_response,
            "message": "Get carrera successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving carrera: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving carrera: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_all_carreras(db: Session, current_user: schemas.Usuario = None):
    try:
        db_carreras = carreraService.CarreraService().get_all_carreras(db)
        carrera_responses = [carrera.to_dict_carrera() for carrera in db_carreras]
        return {
            "success": True,
            "data": carrera_responses,
            "message": "Get carreras successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving carreras: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving carreras: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def edit_carrera(id: int, carrera: schemas.CarreraUpdate, db: Session, current_user: schemas.Usuario = None):
    try:
        db_carrera = carreraService.CarreraService().edit_carrera(db, id, carrera)
        carrera_response = db_carrera.to_dict_carrera()
        return {
            "success": True,
            "data": carrera_response,
            "message": "Carrera edited successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error updating carrera: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error updating carrera: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def delete_carrera(id: int, db: Session = Depends(database.get_db), current_user: schemas.Usuario = None):
    try:
        carreraService.CarreraService().delete_carrera(db, id)
        return {
            "success": True,
            "message": "Carrera deleted successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error deleting carrera: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error deleting carrera: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")