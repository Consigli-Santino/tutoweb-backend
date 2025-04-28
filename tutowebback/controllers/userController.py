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
    Implementa transaccionalidad para asegurar que todas las operaciones
    se completen correctamente o se revierta todo.
    """
    # Iniciar una transacción explícita
    transaction = db.begin_nested()

    try:
        temp_path = None
        foto_path = None

        # Si hay imagen, guardarla temporalmente
        if profile_image:
            # Guardar imagen pero no comprometer la DB aún
            temp_path = await image_service.save_profile_image(
                emailUser=usuario.email,
                file=profile_image
            )

            # Si tenemos la ruta de la imagen, incluirla en el objeto usuario
            if temp_path:
                # Crear copia del usuario con la imagen
                usuario_con_imagen = schemas.UsuarioCreate(
                    nombre=usuario.nombre,
                    apellido=usuario.apellido,
                    email=usuario.email,
                    password=usuario.password,
                    foto_perfil=temp_path,  # Incluir la ruta de la imagen
                    id_rol=usuario.id_rol,
                    id_carrera=usuario.id_carrera
                )

                # Crear usuario con imagen
                db_usuario = usersService.UsuarioService().create_usuario(db, usuario_con_imagen)
                foto_path = temp_path
            else:
                # Si falló el guardado de imagen, crear sin imagen
                temp_usuario = schemas.UsuarioCreate(
                    nombre=usuario.nombre,
                    apellido=usuario.apellido,
                    email=usuario.email,
                    password=usuario.password,
                    foto_perfil=None,
                    id_rol=usuario.id_rol,
                    id_carrera=usuario.id_carrera
                )
                db_usuario = usersService.UsuarioService().create_usuario(db, temp_usuario)
        else:
            # Flujo normal sin imagen
            db_usuario = usersService.UsuarioService().create_usuario(db, usuario)

        # Si llegamos aquí sin errores, confirmar la transacción
        transaction.commit()
        db.commit()

        # Preparar respuesta
        usuario_response = db_usuario.to_dict_usuario()

        return {
            "success": True,
            "data": usuario_response,
            "message": "Usuario created successfully"
        }

    except HTTPException as he:
        # Revertir la transacción
        transaction.rollback()

        # Si hubo un error pero ya se guardó la imagen, eliminarla
        if temp_path:
            image_service.delete_profile_image(temp_path)

        logging.error(f"HTTP error creating usuario: {he.detail}")
        raise he

    except Exception as e:
        # Revertir la transacción
        transaction.rollback()

        # Si hubo un error pero ya se guardó la imagen, eliminarla
        if temp_path:
            image_service.delete_profile_image(temp_path)

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


async def edit_usuario(emailParam: str, usuario: schemas.UsuarioUpdate, db: Session,
                       current_user: schemas.Usuario = None,
                       profile_image: Optional[UploadFile] = None):
    """
    Edita un usuario y opcionalmente maneja una imagen de perfil
    Implementa transaccionalidad para asegurar que todas las operaciones
    se completen correctamente o se revierta todo.
    """
    # Iniciar una transacción explícita
    transaction = db.begin_nested()

    try:
        # Obtener usuario actual para tener info de imagen antigua
        service = usersService.UsuarioService()
        db_usuario = service.get_usuario_by_email(db, emailParam)
        old_image_path = db_usuario.foto_perfil

        new_image_path = None

        # Si hay nueva imagen, procesarla
        if profile_image:
            # Guardar nueva imagen
            new_image_path = await image_service.save_profile_image(
                emailUser=emailParam,
                file=profile_image
            )

            # Actualizar el objeto de actualización con la nueva ruta
            if new_image_path:
                usuario.foto_perfil = new_image_path

        # Continuar con la actualización normal
        db_usuario = service.edit_usuario(db, emailParam, usuario)

        # Si llegamos aquí sin errores, confirmar la transacción
        transaction.commit()
        db.commit()

        # Eliminar imagen anterior si existe y se subió una nueva exitosamente
        if old_image_path and new_image_path:
            image_service.delete_profile_image(old_image_path)

        # Preparar respuesta
        usuario_response = db_usuario.to_dict_usuario()

        return {
            "success": True,
            "data": usuario_response,
            "message": "Usuario edited successfully"
        }

    except HTTPException as he:
        # Revertir la transacción
        transaction.rollback()

        # Si hubo un error pero ya se guardó la imagen nueva, eliminarla
        if new_image_path:
            image_service.delete_profile_image(new_image_path)

        logging.error(f"HTTP error updating usuario: {he.detail}")
        raise he

    except Exception as e:
        # Revertir la transacción
        transaction.rollback()

        # Si hubo un error pero ya se guardó la imagen nueva, eliminarla
        if new_image_path:
            image_service.delete_profile_image(new_image_path)

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


async def get_usuario_by_email(email, db, current_user):
    try:
        if current_user['email'] != email:
            if current_user.id_rol != "superAdmin":
                raise HTTPException(status_code=403, detail="No tienes permiso para acceder a este recurso")
        db_usuario = usersService.UsuarioService().get_usuario_by_email(db, email)
        usuario_response = db_usuario.to_dict_usuario()
        return {
            "success": True,
            "data": usuario_response,
            "message": "Get usuario by email successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving usuario by email: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving usuario by email: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_tutores_by_carrera(db, current_user, id):
    try:
        db_tutores = usersService.UsuarioService().get_tutores_by_carrera(db, id)
        tutor_responses = [tutor.to_dict_usuario() for tutor in db_tutores]
        return {
            "success": True,
            "data": tutor_responses,
            "message": "Get tutores by carrera successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving tutores by carrera: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving tutores by carrera: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")