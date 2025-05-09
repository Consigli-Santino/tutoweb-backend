import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.models import models
from tutowebback.schemas import schemas


def crear_notificacion(db: Session, usuario_id: int, titulo: str, mensaje: str,
                       tipo: str = "sistema", fecha_programada: datetime = None,
                       reserva_id: int = None):
    """
    Crea una notificación para un usuario específico

    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario que recibirá la notificación
        titulo: Título de la notificación
        mensaje: Contenido de la notificación
        tipo: Tipo de notificación (reserva, pago, recordatorio, sistema)
        fecha_programada: Fecha y hora programada para mostrar la notificación (opcional)
        reserva_id: ID de la reserva relacionada (opcional)

    Returns:
        Objeto de notificación creado
    """
    try:
        # Verificar si existe el usuario
        usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario not found")

        # Verificar que el tipo sea válido
        tipos_validos = ["reserva", "pago", "recordatorio", "sistema"]
        if tipo not in tipos_validos:
            raise HTTPException(status_code=400,
                                detail=f"Tipo de notificación inválido. Debe ser uno de: {', '.join(tipos_validos)}")

        # Verificar reserva si se proporciona un ID
        if reserva_id:
            reserva = db.query(models.Reserva).filter(models.Reserva.id == reserva_id).first()
            if not reserva:
                raise HTTPException(status_code=404, detail="Reserva not found")

        # Crear la notificación
        nueva_notificacion = models.Notificacion(
            usuario_id=usuario_id,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            leida=False,
            fecha_creacion=datetime.utcnow(),
            fecha_programada=fecha_programada,
            reserva_id=reserva_id
        )

        db.add(nueva_notificacion)
        db.commit()
        db.refresh(nueva_notificacion)
        return nueva_notificacion

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error creando notificación")
    except Exception as e:
        db.rollback()
        logging.error(f"Error creando notificación: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def obtener_notificaciones_usuario(db: Session, usuario_id: int, solo_no_leidas: bool = False):
    """
    Obtiene las notificaciones de un usuario

    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario
        solo_no_leidas: Si es True, solo devuelve notificaciones no leídas

    Returns:
        Lista de notificaciones
    """
    try:
        # Verificar si existe el usuario
        usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario not found")

        # Construir la consulta
        query = db.query(models.Notificacion).filter(models.Notificacion.usuario_id == usuario_id)

        # Filtrar solo no leídas si se solicita
        if solo_no_leidas:
            query = query.filter(models.Notificacion.leida == False)

        # Obtener resultados ordenados por fecha (más recientes primero)
        notificaciones = query.order_by(models.Notificacion.fecha_creacion.desc()).all()

        return notificaciones

    except Exception as e:
        logging.error(f"Error obteniendo notificaciones: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def marcar_notificacion_como_leida(db: Session, notificacion_id: int, usuario_id: int):
    """
    Marca una notificación como leída

    Args:
        db: Sesión de base de datos
        notificacion_id: ID de la notificación
        usuario_id: ID del usuario (para verificar permisos)

    Returns:
        Notificación actualizada
    """
    try:
        # Obtener la notificación
        notificacion = db.query(models.Notificacion).filter(models.Notificacion.id == notificacion_id).first()
        if not notificacion:
            raise HTTPException(status_code=404, detail="Notificación not found")

        # Verificar que la notificación pertenezca al usuario
        if notificacion.usuario_id != usuario_id:
            raise HTTPException(status_code=403, detail="No puedes marcar como leída una notificación que no es tuya")

        # Actualizar estado
        notificacion.leida = True
        db.commit()
        db.refresh(notificacion)

        return notificacion

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logging.error(f"Error marcando notificación como leída: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def marcar_todas_como_leidas(db: Session, usuario_id: int):
    """
    Marca todas las notificaciones de un usuario como leídas

    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario

    Returns:
        Número de notificaciones actualizadas
    """
    try:
        # Verificar si existe el usuario
        usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario not found")

        # Actualizar todas las notificaciones no leídas
        result = db.query(models.Notificacion).filter(
            models.Notificacion.usuario_id == usuario_id,
            models.Notificacion.leida == False
        ).update({"leida": True})

        db.commit()

        return result

    except Exception as e:
        db.rollback()
        logging.error(f"Error marcando todas las notificaciones como leídas: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")