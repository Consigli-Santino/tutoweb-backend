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
# Agregar estas funciones al archivo notificacionService.py existente

def obtener_todas_las_notificaciones(db: Session, fecha_desde: str = None, fecha_hasta: str = None):
    """
    Obtiene todas las notificaciones del sistema con filtros de fecha (solo para admins)
    
    Args:
        db: Sesión de base de datos
        fecha_desde: Fecha desde en formato YYYY-MM-DD (opcional)
        fecha_hasta: Fecha hasta en formato YYYY-MM-DD (opcional)
    
    Returns:
        Lista de notificaciones con información del usuario
    """
    try:
        # Construir la consulta base con información del usuario
        query = db.query(models.Notificacion).join(
            models.Usuario, 
            models.Notificacion.usuario_id == models.Usuario.id
        )
        
        # Aplicar filtros de fecha si se proporcionan
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(models.Notificacion.fecha_creacion >= fecha_desde_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_desde incorrecto. Use YYYY-MM-DD")
        
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                # Incluir todo el día hasta
                fecha_hasta_obj = datetime.combine(fecha_hasta_obj, datetime.max.time())
                query = query.filter(models.Notificacion.fecha_creacion <= fecha_hasta_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_hasta incorrecto. Use YYYY-MM-DD")
        
        # Obtener las notificaciones ordenadas por fecha (más recientes primero)
        notificaciones = query.order_by(models.Notificacion.fecha_creacion.desc()).all()
        
        # Convertir a formato de respuesta con información del usuario
        notificaciones_response = []
        for notif in notificaciones:
            notif_dict = notif.to_dict_notificacion()
            
            # Agregar información del usuario
            if hasattr(notif, 'usuario') and notif.usuario:
                notif_dict["usuario"] = notif.usuario.to_dict_usuario()
            else:
                # Fallback: obtener usuario manualmente si no está cargado
                usuario = db.query(models.Usuario).filter(models.Usuario.id == notif.usuario_id).first()
                if usuario:
                    notif_dict["usuario"] = usuario.to_dict_usuario()
            
            # Agregar información de la reserva si existe
            if notif.reserva_id:
                reserva = db.query(models.Reserva).filter(models.Reserva.id == notif.reserva_id).first()
                if reserva:
                    notif_dict["reserva"] = reserva.to_dict_reserva()
            
            notificaciones_response.append(notif_dict)
        
        return notificaciones_response
        
    except Exception as e:
        logging.error(f"Error obteniendo todas las notificaciones: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def eliminar_notificacion(db: Session, notificacion_id: int, usuario_id: int):
    """
    Elimina una notificación (solo el propietario o admins)
    
    Args:
        db: Sesión de base de datos
        notificacion_id: ID de la notificación
        usuario_id: ID del usuario (para verificar permisos)
    
    Returns:
        True si se eliminó correctamente
    """
    try:
        # Obtener la notificación
        notificacion = db.query(models.Notificacion).filter(models.Notificacion.id == notificacion_id).first()
        if not notificacion:
            raise HTTPException(status_code=404, detail="Notificación not found")
        
        # Verificar que la notificación pertenezca al usuario
        if notificacion.usuario_id != usuario_id:
            # Verificar si es admin (esto se puede hacer en el controller también)
            usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
            if not usuario or not hasattr(usuario, 'rol') or usuario.rol.nombre not in ["superAdmin", "admin"]:
                raise HTTPException(status_code=403, detail="No puedes eliminar una notificación que no es tuya")
        
        # Eliminar la notificación
        db.delete(notificacion)
        db.commit()
        
        return True
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logging.error(f"Error eliminando notificación: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def obtener_notificaciones_por_tipo(db: Session, usuario_id: int, tipo: str):
    """
    Obtiene notificaciones de un usuario filtradas por tipo
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario
        tipo: Tipo de notificación ("reserva", "pago", "recordatorio", "sistema")
    
    Returns:
        Lista de notificaciones del tipo especificado
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
        
        # Obtener notificaciones por tipo
        notificaciones = db.query(models.Notificacion).filter(
            models.Notificacion.usuario_id == usuario_id,
            models.Notificacion.tipo == tipo
        ).order_by(models.Notificacion.fecha_creacion.desc()).all()
        
        return notificaciones
        
    except Exception as e:
        logging.error(f"Error obteniendo notificaciones por tipo: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def obtener_estadisticas_notificaciones(db: Session, fecha_desde: str = None, fecha_hasta: str = None):
    """
    Obtiene estadísticas de notificaciones para el dashboard de administración
    
    Args:
        db: Sesión de base de datos
        fecha_desde: Fecha desde en formato YYYY-MM-DD (opcional)
        fecha_hasta: Fecha hasta en formato YYYY-MM-DD (opcional)
    
    Returns:
        Diccionario con estadísticas de notificaciones
    """
    try:
        # Construir la consulta base
        query = db.query(models.Notificacion)
        
        # Aplicar filtros de fecha si se proporcionan
        if fecha_desde:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            query = query.filter(models.Notificacion.fecha_creacion >= fecha_desde_obj)
        
        if fecha_hasta:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            fecha_hasta_obj = datetime.combine(fecha_hasta_obj, datetime.max.time())
            query = query.filter(models.Notificacion.fecha_creacion <= fecha_hasta_obj)
        
        # Obtener todas las notificaciones del período
        notificaciones = query.all()
        
        # Calcular estadísticas
        total = len(notificaciones)
        leidas = len([n for n in notificaciones if n.leida])
        no_leidas = total - leidas
        
        # Estadísticas por tipo
        por_tipo = {}
        for tipo in ["reserva", "pago", "recordatorio", "sistema"]:
            por_tipo[tipo] = len([n for n in notificaciones if n.tipo == tipo])
        
        # Estadísticas por usuario (top 10 usuarios con más notificaciones)
        usuarios_count = {}
        for notif in notificaciones:
            usuarios_count[notif.usuario_id] = usuarios_count.get(notif.usuario_id, 0) + 1
        
        # Obtener información de los usuarios con más notificaciones
        top_usuarios = []
        for usuario_id, count in sorted(usuarios_count.items(), key=lambda x: x[1], reverse=True)[:10]:
            usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
            if usuario:
                top_usuarios.append({
                    "usuario_id": usuario_id,
                    "nombre": f"{usuario.nombre} {usuario.apellido}",
                    "email": usuario.email,
                    "count": count
                })
        
        return {
            "total": total,
            "leidas": leidas,
            "no_leidas": no_leidas,
            "porcentaje_leidas": round((leidas / total * 100) if total > 0 else 0, 2),
            "por_tipo": por_tipo,
            "top_usuarios": top_usuarios
        }
        
    except Exception as e:
        logging.error(f"Error obteniendo estadísticas de notificaciones: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")