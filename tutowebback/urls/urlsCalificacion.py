import os
import sys
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.config import database
from tutowebback.schemas import schemas
from tutowebback.auth import auth

router = APIRouter(tags=["Calificaciones"])

@router.post("/calificacion/create", response_model=None)
async def create_calificacion(
    calificacion: schemas.CalificacionCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import calificacionController
    return await calificacionController.create_calificacion(calificacion, db, current_user)

@router.get("/calificacion/reserva/{reserva_id}", response_model=None)
async def get_calificacion_by_reserva(
    reserva_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import calificacionController
    return await calificacionController.get_calificacion_by_reserva(reserva_id, db, current_user)

@router.get("/calificaciones/tutor/{tutor_id}", response_model=None)
async def get_calificaciones_by_tutor(
    tutor_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import calificacionController
    return await calificacionController.get_calificaciones_by_tutor(tutor_id, db, current_user)

@router.get("/calificaciones/estudiante", response_model=None)
async def get_calificaciones_by_estudiante(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import calificacionController
    return await calificacionController.get_calificaciones_by_estudiante(db, current_user)