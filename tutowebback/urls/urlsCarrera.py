import os
import sys
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.config import database
from tutowebback.schemas import schemas
from tutowebback.auth import auth

router = APIRouter(tags=["Carreras"])

@router.post("/carrera/create", response_model=None)
async def create_carrera(
    carrera: schemas.CarreraCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.controllers import carreraController
    return await carreraController.create_carrera(carrera, db, current_user)

@router.get("/carreras/all", response_model=None)
async def get_all_carreras(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor", "estudiante"])),
):
    from tutowebback.controllers import carreraController
    return await carreraController.get_all_carreras(db, current_user)

@router.get("/carrera/{id}", response_model=None)
async def get_carrera(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor", "estudiante"])),
):
    from tutowebback.controllers import carreraController
    return await carreraController.get_carrera(id, db, current_user)

@router.put("/carrera/{id}", response_model=None)
async def edit_carrera(
    id: int,
    carrera: schemas.CarreraUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.controllers import carreraController
    return await carreraController.edit_carrera(id, carrera, db, current_user)

@router.delete("/carrera/{id}", response_model=None)
async def delete_carrera(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"]))
):
    from tutowebback.controllers import carreraController
    return await carreraController.delete_carrera(id, db, current_user)