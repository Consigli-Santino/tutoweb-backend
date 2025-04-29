import os
import sys
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.services import materiasXCarreraXUsuarioService

async def create_materia_carrera_usuario(materia_carrera_usuario: schemas.MateriasXCarreraXUsuarioCreate, db: Session, current_user: schemas.Usuario = None):
    try:
        if current_user['user_rol']== "alumno&tutor":
            if current_user['user_data']['id'] != materia_carrera_usuario.usuario_id:
                raise HTTPException(status_code=403, detail="You are not allowed to create this relation")
        db_relation = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().create_materia_carrera_usuario(db, materia_carrera_usuario)
        relation_response = db_relation.to_dict_materia_usuario()
        return {
            "success": True,
            "data": relation_response,
            "message": "Relation created successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error creating relation: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error creating relation: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_materia_carrera_usuario(id: int, db: Session, current_user: schemas.Usuario = None):
    try:
        db_relation = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().get_materia_carrera_usuario(db, id)
        relation_response = db_relation.to_dict_materia_usuario()
        return {
            "success": True,
            "data": relation_response,
            "message": "Get relation successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving relation: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving relation: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_all_materias_carrera_usuario(db: Session, current_user: schemas.Usuario = None):
    try:
        db_relations = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().get_all_materias_carrera_usuario(db)
        relation_responses = [relation.to_dict_materia_usuario() for relation in db_relations]
        return {
            "success": True,
            "data": relation_responses,
            "message": "Get all relations successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving relations: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving relations: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_materias_by_usuario_and_carrera(usuario_id: int, carrera_id: int, db: Session, current_user: schemas.Usuario = None):
    try:
        db_relations = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().get_materias_by_usuario_and_carrera(db, usuario_id, carrera_id)
        relation_responses = [relation.to_dict_materia_usuario() for relation in db_relations]
        return {
            "success": True,
            "data": relation_responses,
            "message": "Get materias by usuario and carrera successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving materias by usuario and carrera: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving materias by usuario and carrera: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_usuarios_by_materia_and_carrera(materia_id: int, carrera_id: int, db: Session, current_user: schemas.Usuario = None):
    try:
        db_relations = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().get_usuarios_by_materia_and_carrera(db, materia_id, carrera_id)
        relation_responses = [relation.to_dict_materia_usuario() for relation in db_relations]
        return {
            "success": True,
            "data": relation_responses,
            "message": "Get usuarios by materia and carrera successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving usuarios by materia and carrera: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving usuarios by materia and carrera: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def edit_materia_carrera_usuario(id: int, materia_carrera_usuario: schemas.MateriasXCarreraXUsuarioUpdate, db: Session, current_user: schemas.Usuario = None):
    try:
        db_relation = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().edit_materia_carrera_usuario(db, id, materia_carrera_usuario)
        relation_response = db_relation.to_dict_materia_usuario()
        return {
            "success": True,
            "data": relation_response,
            "message": "Relation edited successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error updating relation: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error updating relation: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def delete_materia_carrera_usuario(id: int, db: Session, current_user: schemas.Usuario = None):
    try:
        materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().delete_materia_carrera_usuario(db, id)
        return {
            "success": True,
            "message": "Relation deleted successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error deleting relation: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error deleting relation: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")