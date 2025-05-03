# urlsServicioTutoria.py

import os
import sys
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.config import database
from tutowebback.schemas import schemas
from tutowebback.auth import auth

router = APIRouter(tags=["ServiciosTutoria"])

@router.post("/servicio/create", response_model=None)
async def create_servicio(
    servicio: schemas.ServicioTutoriaCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "alumno&tutor", "tutor"])),
):
    from tutowebback.controllers import servicioTutoriaController
    return await servicioTutoriaController.create_servicio(servicio, db, current_user)

@router.get("/servicio/{id}", response_model=None)
async def get_servicio(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "alumno&tutor", "tutor", "estudiante"])),
):
    from tutowebback.controllers import servicioTutoriaController
    return await servicioTutoriaController.get_servicio(id, db, current_user)

@router.get("/servicios/tutor/{tutor_id}", response_model=None)
async def get_servicios_by_tutor(
    tutor_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "alumno&tutor", "tutor", "estudiante"])),
):
    from tutowebback.controllers import servicioTutoriaController
    return await servicioTutoriaController.get_servicios_by_tutor(tutor_id, db, current_user)

@router.get("/servicios/materia/{materia_id}", response_model=None)
async def get_servicios_by_materia(
    materia_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "alumno&tutor", "tutor", "estudiante"])),
):
    from tutowebback.controllers import servicioTutoriaController
    return await servicioTutoriaController.get_servicios_by_materia(materia_id, db, current_user)

@router.put("/servicio/{id}", response_model=None)
async def edit_servicio(
    id: int,
    servicio: schemas.ServicioTutoriaUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "alumno&tutor", "tutor"])),
):
    from tutowebback.controllers import servicioTutoriaController
    return await servicioTutoriaController.edit_servicio(id, servicio, db, current_user)

@router.delete("/servicio/{id}", response_model=None)
async def delete_servicio(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "alumno&tutor", "tutor"])),
):
    from tutowebback.controllers import servicioTutoriaController
    return await servicioTutoriaController.delete_servicio(id, db, current_user)