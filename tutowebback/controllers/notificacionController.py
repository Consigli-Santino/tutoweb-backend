import os
import sys
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.services import notificacionService
from tutowebback.models import models


async def create_notificacion(notificacion: schemas.NotificacionCreate, db: Session, current_user: schemas.Usuario):
    try:
        # Solo admins pueden crear notificaciones manualmente
        if current_user["user_rol"] not in ["superAdmin", "admin"]:
            raise HTTPException(status_code=403, detail="No tienes permisos para crear notificaciones")
            
        db_notificacion = notificacionService.crear_notificacion(
            db=db,
            usuario_id=notificacion.usuario_id,
            titulo=notificacion.titulo,
            mensaje=notificacion.mensaje,
            tipo=notificacion.tipo,
            fecha_programada=notificacion.fecha_programada,
            reserva_id=notificacion.reserva_id
        )
        
        notificacion_response = db_notificacion.to_dict_notificacion()
        
        return {
            "success": True,
            "data": notificacion_response,
            "message": "Notificación created successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error creating notificacion: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error creating notificacion: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_notificaciones_by_user(db: Session, current_user: schemas.Usuario, solo_no_leidas: bool = False):
    try:
        notificaciones = notificacionService.obtener_notificaciones_usuario(
            db, current_user["id"], solo_no_leidas
        )
        
        notificaciones_response = [notif.to_dict_notificacion() for notif in notificaciones]
        
        return {
            "success": True,
            "data": notificaciones_response,
            "message": "Get notificaciones successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving notificaciones: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving notificaciones: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_all_notificaciones(db: Session, current_user: schemas.Usuario, fecha_desde: str = None, fecha_hasta: str = None):
    """
    Obtiene todas las notificaciones del sistema (solo para admins)
    """
    try:
        # Solo admins pueden ver todas las notificaciones
        if current_user["user_rol"] not in ["superAdmin", "admin"]:
            raise HTTPException(status_code=403, detail="No tienes permisos para ver todas las notificaciones")
        
        notificaciones = notificacionService.obtener_todas_las_notificaciones(db, fecha_desde, fecha_hasta)
        
        return {
            "success": True,
            "data": notificaciones,
            "message": "Get all notificaciones successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving all notificaciones: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving all notificaciones: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def mark_notificacion_as_read(notificacion_id: int, db: Session, current_user: schemas.Usuario):
    try:
        notificacion = notificacionService.marcar_notificacion_como_leida(db, notificacion_id, current_user["id"])
        
        return {
            "success": True,
            "data": notificacion.to_dict_notificacion(),
            "message": "Notificación marked as read successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error marking notificacion as read: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error marking notificacion as read: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def mark_all_as_read(db: Session, current_user: schemas.Usuario):
    try:
        count = notificacionService.marcar_todas_como_leidas(db, current_user["id"])
        
        return {
            "success": True,
            "data": {"count": count},
            "message": f"Se marcaron {count} notificaciones como leídas"
        }
    except HTTPException as he:
        logging.error(f"HTTP error marking all notificaciones as read: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error marking all notificaciones as read: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def delete_notificacion(notificacion_id: int, db: Session, current_user: schemas.Usuario):
    try:
        result = notificacionService.eliminar_notificacion(db, notificacion_id, current_user["id"])
        
        return {
            "success": result,
            "message": "Notificación deleted successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error deleting notificacion: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error deleting notificacion: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")