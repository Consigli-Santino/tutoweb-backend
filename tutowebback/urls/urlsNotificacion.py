# urlsNotificacion.py - Versión completa

import os
import sys
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.config import database
from tutowebback.schemas import schemas
from tutowebback.auth import auth

router = APIRouter(tags=["Notificaciones"])


@router.post("/notificaciones/create", response_model=None)
async def create_notificacion(
    notificacion: schemas.NotificacionCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.controllers import notificacionController
    return await notificacionController.create_notificacion(notificacion, db, current_user)


@router.get("/notificaciones", response_model=None)
async def get_notificaciones(
    solo_no_leidas: bool = Query(False, description="Si es True, solo devuelve notificaciones no leídas"),
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import notificacionController
    return await notificacionController.get_notificaciones_by_user(db, current_user, solo_no_leidas)


@router.get("/notificaciones/all", response_model=None)
async def get_all_notificaciones(
    fecha_desde: str = Query(None, description="Fecha desde en formato YYYY-MM-DD"),
    fecha_hasta: str = Query(None, description="Fecha hasta en formato YYYY-MM-DD"),
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.controllers import notificacionController
    return await notificacionController.get_all_notificaciones(db, current_user, fecha_desde, fecha_hasta)


@router.get("/notificaciones/tipo/{tipo}", response_model=None)
async def get_notificaciones_by_tipo(
    tipo: str,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.services import notificacionService
    notificaciones = notificacionService.obtener_notificaciones_por_tipo(
        db, current_user["id"], tipo
    )
    
    notificaciones_response = [notif.to_dict_notificacion() for notif in notificaciones]
    
    return {
        "success": True,
        "data": notificaciones_response,
        "message": f"Get notificaciones by tipo {tipo} successfully"
    }


@router.get("/notificaciones/estadisticas", response_model=None)
async def get_estadisticas_notificaciones(
    fecha_desde: str = Query(None, description="Fecha desde en formato YYYY-MM-DD"),
    fecha_hasta: str = Query(None, description="Fecha hasta en formato YYYY-MM-DD"),
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.services import notificacionService
    estadisticas = notificacionService.obtener_estadisticas_notificaciones(
        db, fecha_desde, fecha_hasta
    )
    
    return {
        "success": True,
        "data": estadisticas,
        "message": "Get estadísticas notificaciones successfully"
    }


@router.put("/notificaciones/{notificacion_id}/leer", response_model=None)
async def marcar_notificacion_como_leida(
    notificacion_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import notificacionController
    return await notificacionController.mark_notificacion_as_read(notificacion_id, db, current_user)


@router.put("/notificaciones/leer-todas", response_model=None)
async def marcar_todas_como_leidas(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import notificacionController
    return await notificacionController.mark_all_as_read(db, current_user)


@router.delete("/notificaciones/{notificacion_id}", response_model=None)
async def delete_notificacion(
    notificacion_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import notificacionController
    return await notificacionController.delete_notificacion(notificacion_id, db, current_user)