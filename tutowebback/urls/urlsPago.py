import os
import sys
from fastapi import APIRouter, Depends, BackgroundTasks, Body, Query, Request
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.config import database
from tutowebback.schemas import schemas
from tutowebback.auth import auth

router = APIRouter(tags=["Pagos"])

@router.post("/pago/create", response_model=None)
async def create_pago(
    pago: schemas.PagoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import pagoController
    return await pagoController.create_pago(pago, db, current_user, background_tasks)

@router.get("/pago/callback", response_model=None)
async def callback_handler(
    request: Request,
    db: Session = Depends(database.get_db)
):
    from tutowebback.controllers import pagoController
    return await pagoController.payment_callback(request, db)
@router.put("/pago/{pago_id}/estado/{estado}", response_model=None)
async def update_pago_estado(
    pago_id: int,
    estado: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import pagoController
    return await pagoController.update_pago_estado(pago_id, estado, db, current_user, background_tasks)

@router.get("/pago/reserva/{reserva_id}", response_model=None)
async def get_pago_by_reserva(
    reserva_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import pagoController
    return await pagoController.get_pago_by_reserva(reserva_id, db, current_user)

@router.get("/mercadopago/public-key", response_model=None)
async def get_mercadopago_public_key(
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import pagoController
    return await pagoController.get_mercadopago_public_key(current_user)

@router.post("/webhook/mercadopago", response_model=None)
async def webhook_mercadopago(
    payment_data: dict = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(database.get_db),
):
    from tutowebback.controllers import pagoController
    return await pagoController.webhook_mercadopago(payment_data, db, background_tasks)
@router.get("/pagos/estudiante", response_model=None)
async def get_pagos_by_estudiante(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import pagoController
    return await pagoController.get_pagos_by_estudiante(db, current_user)
@router.get("/pagos/tutor", response_model=None)
async def get_pagos_by_tutor(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.get_current_user),
):
    from tutowebback.controllers import pagoController
    return await pagoController.get_pagos_by_tutor(db, current_user)
