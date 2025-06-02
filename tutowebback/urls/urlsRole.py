import os
import sys

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.auth import auth

router = APIRouter(tags=["Roles"])

@router.post("/create", response_model=None)
async def create(
    role: schemas.RolCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "eDefuncionAdmin", "eNacimientoAdmin"])),
):
    from tutowebback.controllers import roleController
    return await roleController.create_rol(role, db, current_user)
@router.get("/roles/all", response_model=None)
async def get_all_roles(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "alumno&tutor"])),
):
    from tutowebback.controllers import roleController
    return await roleController.get_all_roles(db, current_user)
@router.get("/roles/all/register", response_model=None)
async def get_all_roles_by_register(
    db: Session = Depends(database.get_db),
):
    from tutowebback.controllers import roleController
    return await roleController.get_all_roles_by_register(db)
@router.get("/roles/{id}", response_model=None)
async def get_role(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "eDefuncionAdmin", "eNacimientoAdmin"])),
):
    from tutowebback.controllers import roleController
    return await roleController.get_role(id,db, current_user)
@router.put("/role/{id}", response_model=None)
async def edit_role(
    id: int,
    role: schemas.RolUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "eDefuncionAdmin", "eNacimientoAdmin"])),
):
    from tutowebback.controllers import roleController
    return await roleController.edit_role(id, role, db, current_user)
@router.delete("/roleDelete/{id}", response_model=None)
async def delete_role(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "eDefuncionAdmin", "eNacimientoAdmin"])),
):
    from tutowebback.controllers import roleController
    return await roleController.delete_role(id, db, current_user)