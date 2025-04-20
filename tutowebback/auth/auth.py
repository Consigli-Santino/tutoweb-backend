import os
import sys

from cryptography.hazmat.backends.openssl import backend
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi import Depends, status, HTTPException
from config.database import get_db

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tutowebback.config import database
from tutowebback.models import models
from tutowebback.schemas import schemas

environment = os.getenv('ENVIRONMENT', 'development')
env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'environments', f".env-{environment}")
load_dotenv(env_file)

# Configuración de JWT
SECRET_KEY = os.getenv("API_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1000000

# Configuración de passlib para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer Token
bearer_scheme = HTTPBearer()


def login_for_access_token(db: Session, email: str, password: str):
    user = verify_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Obtener el rol del usuario
    rol = None
    if user.id_rol:
        rol = db.query(models.Rol).filter(models.Rol.id == user.id_rol).first()

    # Obtener las carreras del usuario
    carreras = []
    user_carreras = db.query(models.CarreraUsuario).filter(models.CarreraUsuario.usuario_id == user.id).all()
    for user_carrera in user_carreras:
        carrera = db.query(models.Carrera).filter(models.Carrera.id == user_carrera.carrera_id).first()
        if carrera:
            carreras.append({
                "id": carrera.id,
                "nombre": carrera.nombre
            })

    # Crear un token JWT con los datos del usuario
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_data": {
                "nombre": user.nombre,
                "apellido": user.apellido,
                "email": user.email,
            },
            "user_rol": rol.nombre if rol else None,
            "user_carreras": carreras
        },
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_user(db: Session, email: str, password: str):
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None


# Generar token de acceso
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Validar rol para cada endpoint
def role_required(allowed_roles: list):
    async def check_roles(
            current_user: schemas.Usuario = Depends(get_current_user)
    ):
        if allowed_roles:
            user_rol = current_user.get("user_rol")
            if user_rol not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Operation not permitted: missing required role",
                )
        return current_user

    return check_roles


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(database.get_db)
):
    token = credentials.credentials
    try:
        # Decodificar el token JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_data = payload.get("user_data")  # Obtener los datos del usuario
        user_rol = payload.get("user_rol")  # Obtener el rol del usuario
        user_carreras = payload.get("user_carreras")  # Obtener las carreras del usuario

        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user data",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Devolver los datos del usuario desde el token
        return {
            **user_data,  # Incluir todos los datos del usuario
            "user_rol": user_rol,  # Incluir el rol del usuario
            "user_carreras": user_carreras  # Incluir las carreras del usuario
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )