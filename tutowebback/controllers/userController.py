import os
import sys
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from starlette import status

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.services import usersService

async def create_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(database.get_db), current_user: schemas.Usuario = None):
    try:
        db_usuario = usersService.UsuarioService().create_usuario(db, usuario)
        usuario_response = db_usuario.to_dict_usuario()
        return {
            "success": True,
            "data": usuario_response,
            "message": "Usuario created successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error creating usuario: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error creating usuario: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_usuario(id: int, db: Session, current_user: schemas.Usuario = None):
    try:
        db_usuario = usersService.UsuarioService().get_usuario(db, id)
        usuario_response = db_usuario.to_dict_usuario()
        return {
            "success": True,
            "data": usuario_response,
            "message": "Get usuario successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving usuario: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving usuario: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_all_usuarios(db: Session, current_user: schemas.Usuario = None):
    try:
        db_usuarios = usersService.UsuarioService().get_all_usuarios(db)
        usuario_responses = [usuario.to_dict_usuario() for usuario in db_usuarios]
        return {
            "success": True,
            "data": usuario_responses,
            "message": "Get usuarios successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving usuarios: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving usuarios: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_tutores(db: Session, current_user: schemas.Usuario = None):
    try:
        db_tutores = usersService.UsuarioService().get_tutores(db)
        tutor_responses = [tutor.to_dict_usuario() for tutor in db_tutores]
        return {
            "success": True,
            "data": tutor_responses,
            "message": "Get tutores successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving tutores: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving tutores: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def edit_usuario(id: int, usuario: schemas.UsuarioUpdate, db: Session, current_user: schemas.Usuario = None):
    try:
        db_usuario = usersService.UsuarioService().edit_usuario(db, id, usuario)
        usuario_response = db_usuario.to_dict_usuario()
        return {
            "success": True,
            "data": usuario_response,
            "message": "Usuario edited successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error updating usuario: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error updating usuario: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def delete_usuario(id: int, db: Session = Depends(database.get_db), current_user: schemas.Usuario = None):
    try:
        usersService.UsuarioService().delete_usuario(db, id)
        return {
            "success": True,
            "message": "Usuario deleted successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error deleting usuario: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error deleting usuario: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")