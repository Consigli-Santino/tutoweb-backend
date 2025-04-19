import os
import sys
from fastapi import Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import logging
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.services import usersService
from tutowebback.services.imageService import ImageService

# Inicializar el servicio de imágenes
image_service = ImageService()


async def create_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(database.get_db),
                        profile_image: Optional[UploadFile] = None):
    """
    Crea un usuario y opcionalmente maneja una imagen de perfil
    """
    try:
        # Si hay imagen, procesarla (esto ocurre cuando se recibe de un endpoint modificado)
        if profile_image:
            # Primero crear el usuario sin imagen para obtener el ID
            temp_usuario = schemas.UsuarioCreate(
                nombre=usuario.nombre,
                apellido=usuario.apellido,
                email=usuario.email,
                password=usuario.password,
                es_tutor=usuario.es_tutor,
                foto_perfil=None,
                id_rol=usuario.id_rol,
                id_carrera=usuario.id_carrera
            )

            db_usuario = usersService.UsuarioService().create_usuario(db, temp_usuario)

            # Guardar imagen y actualizar usuario
            foto_path = await image_service.save_profile_image(
                user_id=db_usuario.id,
                file=profile_image
            )

            if foto_path:
                # Actualizar con la ruta de la imagen
                db_usuario.foto_perfil = foto_path
                db.commit()
                db.refresh(db_usuario)

            usuario_response = db_usuario.to_dict_usuario()

        else:
            # Flujo normal sin imagen
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


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


async def edit_usuario(id: int, usuario: schemas.UsuarioUpdate, db: Session, current_user: schemas.Usuario = None,
                       profile_image: Optional[UploadFile] = None):
    """
    Edita un usuario y opcionalmente maneja una imagen de perfil
    """
    try:
        # Obtener usuario actual para tener info de imagen antigua
        service = usersService.UsuarioService()
        db_usuario = service.get_usuario(db, id)
        old_image_path = db_usuario.foto_perfil

        # Si hay nueva imagen, procesarla
        if profile_image:
            # Guardar nueva imagen
            new_image_path = await image_service.save_profile_image(
                user_id=id,
                file=profile_image
            )

            if new_image_path:
                # Actualizar el objeto de actualización con la nueva ruta
                usuario.foto_perfil = new_image_path

                # Eliminar imagen anterior si existe
                if old_image_path:
                    image_service.delete_profile_image(old_image_path)

        # Continuar con la actualización normal
        db_usuario = service.edit_usuario(db, id, usuario)
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


async def delete_usuario(id: int, db: Session = Depends(database.get_db), current_user: schemas.Usuario = None):
    try:
        # Obtener usuario para verificar si tiene imagen
        usuario_service = usersService.UsuarioService()
        db_usuario = usuario_service.get_usuario(db, id)

        # Si el usuario tenía imagen, intentar eliminarla
        if db_usuario.foto_perfil:
            image_service.delete_profile_image(db_usuario.foto_perfil)

        # Eliminar usuario (baja lógica en tu caso)
        usuario_service.delete_usuario(db, id)

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