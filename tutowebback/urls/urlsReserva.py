# urlsReserva.py

import os
import sys
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.config import database
from tutowebback.schemas import schemas
from tutowebback.auth import auth

router = APIRouter(tags=["Reservas"])

@router.post("/reserva/create", response_model=None)
async def create_reserva(
    reserva: schemas.ReservaCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import reservaController
    return await reservaController.create_reserva(reserva, db, current_user)

@router.get("/reserva/{id}", response_model=None)
async def get_reserva(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import reservaController
    return await reservaController.get_reserva(id, db, current_user)

@router.get("/reservas/estudiante", response_model=None)
async def get_reservas_by_estudiante(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import reservaController
    return await reservaController.get_reservas_by_estudiante(db, current_user)

# Nuevo endpoint para obtener reservas detalladas del estudiante
@router.get("/reservas/estudiante/detalladas", response_model=None)
async def get_reservas_by_estudiante_detalladas(
    fecha_desde: str = Query(None, description="Fecha desde en formato YYYY-MM-DD"),
    fecha_hasta: str = Query(None, description="Fecha hasta en formato YYYY-MM-DD"),
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import reservaController
    return await reservaController.get_reservas_by_estudiante_detalladas(
        db, current_user, fecha_desde, fecha_hasta
    )

@router.get("/reservas/admin/all", response_model=None)
async def get_all_reservas(
    fecha_desde: str = Query(None, description="Fecha desde en formato YYYY-MM-DD"),
    fecha_hasta: str = Query(None, description="Fecha hasta en formato YYYY-MM-DD"),
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.controllers import reservaController
    return await reservaController.get_all_reservas(db, current_user, fecha_desde, fecha_hasta)
# En urlsReserva.py
@router.get("/reservas/check", response_model=None)
async def check_reservas(
    tutor_id: int,
    fecha: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import reservaController
    return await reservaController.check_reservas(tutor_id, fecha, db)

@router.get("/reservas/tutor", response_model=None)
async def get_reservas_by_tutor(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import reservaController
    return await reservaController.get_reservas_by_tutor(db, current_user)

# Nuevo endpoint para obtener reservas detalladas del tutor
@router.get("/reservas/tutor/detalladas", response_model=None)
async def get_reservas_by_tutor_detalladas(
    fecha_desde: str = Query(None, description="Fecha desde en formato YYYY-MM-DD"),
    fecha_hasta: str = Query(None, description="Fecha hasta en formato YYYY-MM-DD"),
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import reservaController
    return await reservaController.get_reservas_by_tutor_detalladas(
        db, current_user, fecha_desde, fecha_hasta
    )

@router.put("/reserva/{id}", response_model=None)
async def edit_reserva(
    id: int,
    reserva: schemas.ReservaUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import reservaController
    return await reservaController.edit_reserva(id, reserva, db, current_user)

@router.delete("/reserva/{id}", response_model=None)
async def delete_reserva(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import reservaController
    return await reservaController.delete_reserva(id, db, current_user)

@router.get("/disponibilidades/disponibles/{tutor_id}", response_model=None)
async def get_disponibilidades_disponibles(
    tutor_id: int,
    fecha: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import reservaController
    return await reservaController.get_disponibilidades_disponibles(tutor_id, fecha, db)
@router.post("/reservas/actions", response_model=None)
async def get_reservas_actions(
    body: schemas.ReservasIdsRequest,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "alumno","alumno&tutor"])),
):
    from tutowebback.controllers import reservaController
    return await reservaController.get_reservas_actions(db,body,current_user)
@router.post("/reservas/estudiante/actions", response_model=None)
async def post_reserva_action(
    id_reserva: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "alumno","alumno&tutor"])),
):
    from tutowebback.controllers import reservaController
    return await reservaController.post_reserva_actions(id_reserva, db, current_user)

@router.get("/next/reserva/time", response_model=None)
async def get_next_reserva_time(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "alumno","alumno&tutor"])),
):
    from tutowebback.controllers import reservaController
    return await reservaController.get_next_reserva_time(db, current_user)