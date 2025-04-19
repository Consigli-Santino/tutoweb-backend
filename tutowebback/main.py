import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from fastapi.staticfiles import StaticFiles
from tutowebback.models import models
from tutowebback.config import database
from tutowebback.urls import urlsUser, urlsCarrera, urlsRole, urlsMaterias

# Crear directorios para imágenes si no existen
os.makedirs("uploads/profile_images", exist_ok=True)

models.Base.metadata.create_all(bind=database.engine)

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
]
app = FastAPI(
    title="TUTOWEB API",
    description="API para la gestión de perfiles, autenticacion, clases, reservas, pagos del sistema TutoWeb",
    middleware=middleware
)

# Montar directorio para servir archivos estáticos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Incluir todas las rutas definidas
app.include_router(urlsUser.router)
app.include_router(urlsCarrera.router)
app.include_router(urlsRole.router)
app.include_router(urlsMaterias.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=7000, reload=True)