# urlsNotificacion.py

import os
import sys
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.config import database
from tutowebback.schemas import schemas
from tutowebback.auth import auth

router = APIRouter(tags=["Notificaciones"])


@router.get("/notificaciones", response_model=None)
def get_notificaciones(
        solo_no_leidas: bool = Query(False, description="Si es True, solo devuelve notificaciones no leídas"),
        db: Session = Depends(database.get_db),
        current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.services import notificacionService
    notificaciones = notificacionService.obtener_notificaciones_usuario(
        db, current_user["id"], solo_no_leidas
    )

    # Convertir a formato de respuesta
    notificaciones_response = [notif.to_dict_notificacion() for notif in notificaciones]

    return {
        "success": True,
        "data": notificaciones_response,
        "message": "Get notificaciones successfully"
    }


@router.put("/notificaciones/{notificacion_id}/leer", response_model=None)
def marcar_notificacion_como_leida(
        notificacion_id: int,
        db: Session = Depends(database.get_db),
        current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.services import notificacionService
    notificacion = notificacionService.marcar_notificacion_como_leida(
        db, notificacion_id, current_user["id"]
    )

    return {
        "success": True,
        "data": notificacion.to_dict_notificacion(),
        "message": "Notificación marcada como leída"
    }


@router.put("/notificaciones/leer-todas", response_model=None)
def marcar_todas_como_leidas(
        db: Session = Depends(database.get_db),
        current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.services import notificacionService
    count = notificacionService.marcar_todas_como_leidas(db, current_user["id"])

    return {
        "success": True,
        "data": {"count": count},
        "message": f"Se marcaron {count} notificaciones como leídas"
    }