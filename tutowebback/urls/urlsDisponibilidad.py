import os
import sys
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.config import database
from tutowebback.schemas import schemas
from tutowebback.auth import auth

router = APIRouter(tags=["Disponibilidad"])

@router.post("/disponibilidad/create", response_model=None)
async def create_disponibilidad(
    disponibilidad: schemas.DisponibilidadCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["alumno&tutor", "tutor"])),
):
    from tutowebback.controllers import disponibilidadController
    return await disponibilidadController.create_disponibilidad(disponibilidad, db, current_user)
@router.get("/disponibilidades/disponibles/{tutor_id}/{fecha}", response_model=None)
async def get_disponibilidades_disponibles(
    tutor_id: int,
    fecha: str ,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin","alumno", "alumno&tutor", "tutor", "estudiante"])),
):
    from tutowebback.controllers import disponibilidadController
    return await disponibilidadController.get_disponibilidades_disponibles(tutor_id, fecha, db, current_user)
@router.get("/disponibilidades/tutor/{tutor_id}", response_model=None)
async def get_disponibilidades_by_tutor(
    tutor_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin","alumno", "alumno&tutor", "tutor", "estudiante"])),
):
    from tutowebback.controllers import disponibilidadController
    return await disponibilidadController.get_disponibilidades_by_tutor(tutor_id, db, current_user)

@router.get("/disponibilidad/{id}", response_model=None)
async def get_disponibilidad(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "alumno&tutor", "tutor"])),
):
    from tutowebback.controllers import disponibilidadController
    return await disponibilidadController.get_disponibilidad(id, db, current_user)

@router.put("/disponibilidad/{id}", response_model=None)
async def edit_disponibilidad(
    id: int,
    disponibilidad: schemas.DisponibilidadUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["alumno&tutor", "tutor"])),
):
    from tutowebback.controllers import disponibilidadController
    return await disponibilidadController.edit_disponibilidad(id, disponibilidad, db, current_user)

@router.delete("/disponibilidad/{id}", response_model=None)
async def delete_disponibilidad(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["alumno&tutor", "tutor"]))
):
    from tutowebback.controllers import disponibilidadController
    return await disponibilidadController.delete_disponibilidad(id, db, current_user)