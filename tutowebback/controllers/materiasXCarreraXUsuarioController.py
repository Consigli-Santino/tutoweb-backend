import os
import sys
import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.services import materiasXCarreraXUsuarioService
from tutowebback.schemas import schemas


async def create_materia_carrera_usuario(materia_carrera_usuario: schemas.MateriasXCarreraXUsuarioCreate, db: Session,
                                         current_user: Optional[schemas.Usuario] = None):
    try:
        db_relation = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().create_materia_carrera_usuario(
            db, materia_carrera_usuario)

        relation_dict = db_relation.to_dict_materia_usuario()
        # Añadir la información completa de la materia
        if hasattr(db_relation, 'materia') and db_relation.materia:
            relation_dict["materia"] = db_relation.materia.to_dict_materia()
        else:
            relation_dict["materia"] = None

        return {
            "success": True,
            "data": relation_dict,
            "message": "Materia-carrera-usuario relation created successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error creating materia-carrera-usuario relation: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error creating materia-carrera-usuario relation: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_materia_carrera_usuario(id: int, db: Session, current_user: Optional[schemas.Usuario] = None):
    try:
        db_relations = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().get_materia_carrera_usuario(db,
                                                                                                                     id)

        relation_responses = []
        for relation in db_relations:
            relation_dict = relation.to_dict_materia_usuario()
            # Añadir la información completa de la materia
            if hasattr(relation, 'materia') and relation.materia:
                relation_dict["materia"] = relation.materia.to_dict_materia()
            else:
                relation_dict["materia"] = None
            relation_responses.append(relation_dict)

        return {
            "success": True,
            "data": relation_responses,
            "message": "Get materia-carrera-usuario relation successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving materia-carrera-usuario relation: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving materia-carrera-usuario relation: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_all_materias_carrera_usuario(db: Session, current_user: Optional[schemas.Usuario] = None):
    try:
        db_relations = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().get_all_materias_carrera_usuario(
            db)

        relation_responses = []
        for relation in db_relations:
            relation_dict = relation.to_dict_materia_usuario()
            # Añadir la información completa de la materia
            if hasattr(relation, 'materia') and relation.materia:
                relation_dict["materia"] = relation.materia.to_dict_materia()
            else:
                relation_dict["materia"] = None
            relation_responses.append(relation_dict)

        return {
            "success": True,
            "data": relation_responses,
            "message": "Get all materias-carrera-usuario relations successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving all materias-carrera-usuario relations: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving all materias-carrera-usuario relations: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_materias_by_usuario_and_carrera(usuario_id: int, carrera_id: int, db: Session,
                                              current_user: Optional[schemas.Usuario] = None):
    try:
        db_relations = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().get_materias_by_usuario_and_carrera(
            db, usuario_id, carrera_id)

        relation_responses = []
        for relation in db_relations:
            relation_dict = relation.to_dict_materia_usuario()
            # Añadir la información completa de la materia
            if hasattr(relation, 'materia') and relation.materia:
                relation_dict["materia"] = relation.materia.to_dict_materia()
            else:
                relation_dict["materia"] = None
            relation_responses.append(relation_dict)

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


async def get_usuarios_by_materia_and_carrera(materia_id: int, carrera_id: int, db: Session,
                                              current_user: Optional[schemas.Usuario] = None):
    try:
        db_relations = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().get_usuarios_by_materia_and_carrera(
            db, materia_id, carrera_id)

        relation_responses = []
        for relation in db_relations:
            relation_dict = relation.to_dict_materia_usuario()
            # Añadir la información completa de la materia y usuario
            if hasattr(relation, 'materia') and relation.materia:
                relation_dict["materia"] = relation.materia.to_dict_materia()
            else:
                relation_dict["materia"] = None

            if hasattr(relation, 'usuario') and relation.usuario:
                relation_dict["usuario"] = relation.usuario.to_dict_usuario()
            else:
                relation_dict["usuario"] = None

            relation_responses.append(relation_dict)

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


async def edit_materia_carrera_usuario(id: int, materia_carrera_usuario: schemas.MateriasXCarreraXUsuarioUpdate,
                                       db: Session, current_user: Optional[schemas.Usuario] = None):
    try:
        db_relation = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().edit_materia_carrera_usuario(db,
                                                                                                                     id,
                                                                                                                     materia_carrera_usuario)

        relation_dict = db_relation.to_dict_materia_usuario()
        # Añadir la información completa de la materia
        if hasattr(db_relation, 'materia') and db_relation.materia:
            relation_dict["materia"] = db_relation.materia.to_dict_materia()
        else:
            relation_dict["materia"] = None

        return {
            "success": True,
            "data": relation_dict,
            "message": "Materia-carrera-usuario relation updated successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error updating materia-carrera-usuario relation: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error updating materia-carrera-usuario relation: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def delete_materia_carrera_usuario(id: int, db: Session, current_user: Optional[schemas.Usuario] = None):
    try:
        result = materiasXCarreraXUsuarioService.MateriasXCarreraXUsuarioService().delete_materia_carrera_usuario(db,
                                                                                                                  id)

        return {
            "success": result,
            "message": "Materia-carrera-usuario relation deleted successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error deleting materia-carrera-usuario relation: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error deleting materia-carrera-usuario relation: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")