import os
import sys
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.config import database
from tutowebback.schemas import schemas
from tutowebback.auth import auth

router = APIRouter(tags=["MateriasXCarreraXUsuario"])

@router.post("/materias-carrera-usuario/create", response_model=None)
async def create_materia_carrera_usuario(
    materia_carrera_usuario: schemas.MateriasXCarreraXUsuarioCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "alumno&tutor"])),
):
    from tutowebback.controllers import materiasXCarreraXUsuarioController
    return await materiasXCarreraXUsuarioController.create_materia_carrera_usuario(materia_carrera_usuario, db, current_user)

@router.get("/materias-carrera-usuario/all", response_model=None)
async def get_all_materias_carrera_usuario(
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.controllers import materiasXCarreraXUsuarioController
    return await materiasXCarreraXUsuarioController.get_all_materias_carrera_usuario(db, current_user)

@router.get("/materias-carrera-usuario/{id}", response_model=None)
async def get_materia_carrera_usuario(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "alumno&tutor", "estudiante"])),
):
    from tutowebback.controllers import materiasXCarreraXUsuarioController
    return await materiasXCarreraXUsuarioController.get_materia_carrera_usuario(id, db, current_user)

@router.get("/materias-carrera-usuario/usuario/{usuario_id}/carrera/{carrera_id}", response_model=None)
async def get_materias_by_usuario_and_carrera(
    usuario_id: int,
    carrera_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor", "estudiante"])),
):
    from tutowebback.controllers import materiasXCarreraXUsuarioController
    return await materiasXCarreraXUsuarioController.get_materias_by_usuario_and_carrera(usuario_id, carrera_id, db, current_user)

@router.get("/materias-carrera-usuario/materia/{materia_id}/carrera/{carrera_id}", response_model=None)
async def get_usuarios_by_materia_and_carrera(
    materia_id: int,
    carrera_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor"])),
):
    from tutowebback.controllers import materiasXCarreraXUsuarioController
    return await materiasXCarreraXUsuarioController.get_usuarios_by_materia_and_carrera(materia_id, carrera_id, db, current_user)

@router.put("/materias-carrera-usuario/{id}", response_model=None)
async def edit_materia_carrera_usuario(
    id: int,
    materia_carrera_usuario: schemas.MateriasXCarreraXUsuarioUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor"])),
):
    from tutowebback.controllers import materiasXCarreraXUsuarioController
    return await materiasXCarreraXUsuarioController.edit_materia_carrera_usuario(id, materia_carrera_usuario, db, current_user)

@router.delete("/materias-carrera-usuario/{id}", response_model=None)
async def delete_materia_carrera_usuario(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"]))
):
    from tutowebback.controllers import materiasXCarreraXUsuarioController
    return await materiasXCarreraXUsuarioController.delete_materia_carrera_usuario(id, db, current_user)