import os
import sys

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.config import database
from tutowebback.schemas import schemas
from tutowebback.auth import auth

router = APIRouter(tags=["Usuarios"])

@router.post("/usuario/register", response_model=None)
async def register(
    usuario: schemas.UsuarioCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.controllers import userController
    return await userController.create_usuario(usuario, db, current_user)

@router.get("/usuarios/all", response_model=None)
async def get_all_usuarios(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor"])),
):
    from tutowebback.controllers import userController
    return await userController.get_all_usuarios(db, current_user)

@router.get("/usuarios/tutores", response_model=None)
async def get_tutores(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor", "estudiante"])),
):
    from tutowebback.controllers import usuarioController
    return await usuarioController.get_tutores(db, current_user)

@router.get("/usuario/{id}", response_model=None)
async def get_usuario(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor", "estudiante"])),
):
    from tutowebback.controllers import userController
    return await userController.get_usuario(id, db, current_user)

@router.put("/usuario/{id}", response_model=None)
async def edit_usuario(
    id: int,
    usuario: schemas.UsuarioUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.controllers import usuarioController
    return await usuarioController.edit_usuario(id, usuario, db, current_user)

@router.delete("/usuario/{id}", response_model=None)
async def delete_usuario(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"]))
):
    from tutowebback.controllers import userController
    return await userController.delete_usuario(id, db, current_user)

@router.post("/login", response_model=None)
async def login(
    email: str,
    password: str,
    db: Session = Depends(database.get_db),
):
    from tutowebback.auth import auth
    return auth.login_for_access_token(db, email, password)