import os
import sys
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.config import database
from tutowebback.schemas import schemas
from tutowebback.auth import auth

router = APIRouter(tags=["Materias"])

@router.post("/materia/create", response_model=None)
async def create_materia(
    materia: schemas.MateriaCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.controllers import materiaController
    return await materiaController.create_materia(materia, db, current_user)

@router.get("/materias/all", response_model=None)
async def get_all_materias(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor", "estudiante"])),
):
    from tutowebback.controllers import materiaController
    return await materiaController.get_all_materias(db, current_user)

@router.get("/materias/carrera/{carrera_id}", response_model=None)
async def get_materias_by_carrera(
    carrera_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor", "estudiante"])),
):
    from tutowebback.controllers import materiaController
    return await materiaController.get_materias_by_carrera(carrera_id, db, current_user)

@router.get("/materia/{id}", response_model=None)
async def get_materia(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor", "estudiante"])),
):
    from tutowebback.controllers import materiaController
    return await materiaController.get_materia(id, db, current_user)

@router.put("/materia/{id}", response_model=None)
async def edit_materia(
    id: int,
    materia: schemas.MateriaUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.controllers import materiaController
    return await materiaController.edit_materia(id, materia, db, current_user)

@router.delete("/materia/{id}", response_model=None)
async def delete_materia(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"]))
):
    from tutowebback.controllers import materiaController
    return await materiaController.delete_materia(id, db, current_user)