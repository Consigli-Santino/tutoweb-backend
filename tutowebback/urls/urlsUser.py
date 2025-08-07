import os
import sys

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.responses import FileResponse
from fastapi import Request
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import database
from tutowebback.schemas import schemas
from tutowebback.auth import auth

router = APIRouter(tags=["Usuarios"])

@router.post("/usuario/create", response_model=None)
async def create(
        usuario: schemas.UsuarioCreate,
        db: Session = Depends(database.get_db),
        current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.controllers import userController
    return await userController.create_usuario(usuario, db, current_user)


# Endpoint para registro con imagen
@router.post("/usuario/register-user", response_model=None)
async def register_form(
        nombre: str = Form(...),
        apellido: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        id_carrera: List[int] = Form(...),
        profile_image: Optional[UploadFile] = File(None),
        id_rol: Optional[int] = Form(None),
        db: Session = Depends(database.get_db),
):
    # Crear objeto UsuarioCreate
    usuario = schemas.UsuarioCreate(
        nombre=nombre,
        apellido=apellido,
        email=email,
        password=password,
        foto_perfil=None,  # Se actualizará después
        id_rol=id_rol,
        id_carrera=id_carrera
    )

    # Llamar al controlador con la imagen
    from tutowebback.controllers import userController
    return await userController.create_usuario(usuario, db, profile_image)


# Endpoint original para edición sin imagen
@router.put("/usuario/{id}", response_model=None)
async def edit_usuario(
        id: int,
        usuario: schemas.UsuarioUpdate,
        db: Session = Depends(database.get_db),
        current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin"])),
):
    from tutowebback.controllers import userController
    return await userController.edit_usuario(id, usuario, db, current_user)

@router.get("/tutores/by/carrera/{carrera_id}/with-materias", response_model=None)
async def get_tutores_by_carrera_with_materias(
    carrera_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor","alumno","alumno&tutor"])),
):
    from tutowebback.controllers import userController
    return await userController.get_tutores_by_carrera_with_materias(db, current_user, carrera_id)
@router.put("/usuario/{emailParam}/form", response_model=None)
async def edit_usuario_form(
        emailParam: str,
        id: Optional[int] = Form(None),
        nombre: Optional[str] = Form(None),
        apellido: Optional[str] = Form(None),
        email: Optional[str] = Form(None),
        password: Optional[str] = Form(None),
        id_carrera: Optional[List[int]] = Form(None),
        profile_image: Optional[UploadFile] = File(None),
        id_rol: Optional[int] = Form(None),
        db: Session = Depends(database.get_db),
        current_user: schemas.Usuario = Depends(auth.role_required(["alumno&tutor", "alumno","superAdmin"])),
):
    usuario = schemas.UsuarioUpdate(
        nombre=nombre,
        apellido=apellido,
        email=email,
        password=password,
        foto_perfil=None, 
        id_rol=id_rol,
        id_carrera=id_carrera
    )

    from tutowebback.controllers import userController
    return await userController.edit_usuario(emailParam,id, usuario, db, current_user, profile_image)


@router.get("/uploads/{path:path}")
async def get_upload(path: str):
    try:
        full_path = os.path.join(os.getcwd(), "uploads", path)
        
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        return FileResponse(
            full_path,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*",
                "ngrok-skip-browser-warning": "true",  
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        print(f"Error sirviendo archivo: {e}")
        raise HTTPException(status_code=500, detail=f"Error al servir archivo: {str(e)}")


# Resto de endpoints sin cambios
@router.get("/usuarios/all", response_model=None)
async def get_all_usuarios(
        db: Session = Depends(database.get_db),
        current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor","alumno"])),
):
    from tutowebback.controllers import userController
    return await userController.get_all_usuarios(db, current_user)
@router.get("/tutores/by/carrera/{id}", response_model=None)
async def get_tutores_by_carrera(
        id: int,
        db: Session = Depends(database.get_db),
        current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor","alumno","alumno&tutor"])),
):
    from tutowebback.controllers import userController
    return await userController.get_tutores_by_carrera(db, current_user,id)
@router.get("/usuarios/tutores", response_model=None)
async def get_tutores(
        db: Session = Depends(database.get_db)
      ,
):
    from tutowebback.controllers import userController
    return await userController.get_tutores(db)


@router.get("/usuario/{id}", response_model=None)
async def get_usuario(
        id: int,
        db: Session = Depends(database.get_db),
        current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "admin", "tutor", "estudiante"])),
):
    from tutowebback.controllers import userController
    return await userController.get_usuario(id, db, current_user)
@router.get("/usuario/by-email/{email}", response_model=None)
async def get_usuario(
        email: str,
        db: Session = Depends(database.get_db),
        current_user: schemas.Usuario = Depends(auth.role_required(["superAdmin", "alumno","alumno&tutor"])),
):
    from tutowebback.controllers import userController
    return await userController.get_usuario_by_email(email, db, current_user)


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