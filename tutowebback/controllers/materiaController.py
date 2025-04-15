import os
import sys
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from starlette import status

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.services import materiaService

async def create_materia(materia: schemas.MateriaCreate, db: Session = Depends(database.get_db), current_user: schemas.Usuario = None):
    try:
        db_materia = materiaService.MateriaService().create_materia(db, materia)
        materia_response = db_materia.to_dict_materia()
        return {
            "success": True,
            "data": materia_response,
            "message": "Materia created successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error creating materia: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error creating materia: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_materia(id: int, db: Session, current_user: schemas.Usuario = None):
    try:
        db_materia = materiaService.MateriaService().get_materia(db, id)
        materia_response = db_materia.to_dict_materia()
        return {
            "success": True,
            "data": materia_response,
            "message": "Get materia successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving materia: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving materia: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_all_materias(db: Session, current_user: schemas.Usuario = None):
    try:
        db_materias = materiaService.MateriaService().get_all_materias(db)
        materia_responses = [materia.to_dict_materia() for materia in db_materias]
        return {
            "success": True,
            "data": materia_responses,
            "message": "Get materias successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving materias: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving materias: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_materias_by_carrera(carrera_id: int, db: Session, current_user: schemas.Usuario = None):
    try:
        db_materias = materiaService.MateriaService().get_materias_by_carrera(db, carrera_id)
        materia_responses = [materia.to_dict_materia() for materia in db_materias]
        return {
            "success": True,
            "data": materia_responses,
            "message": "Get materias by carrera successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving materias by carrera: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving materias by carrera: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def edit_materia(id: int, materia: schemas.MateriaUpdate, db: Session, current_user: schemas.Usuario = None):
    try:
        db_materia = materiaService.MateriaService().edit_materia(db, id, materia)
        materia_response = db_materia.to_dict_materia()
        return {
            "success": True,
            "data": materia_response,
            "message": "Materia edited successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error updating materia: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error updating materia: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def delete_materia(id: int, db: Session = Depends(database.get_db), current_user: schemas.Usuario = None):
    try:
        materiaService.MateriaService().delete_materia(db, id)
        return {
            "success": True,
            "message": "Materia deleted successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error deleting materia: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error deleting materia: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")