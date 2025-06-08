import os
import sys

from services.mercadoPagoService import MercadoPagoService

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from fastapi.staticfiles import StaticFiles
from models import models
from config import database
from urls import urlsUser, urlsCarrera, urlsRole, urlsMaterias, urlsMateriasCarreraUsuario, \
    urlsDisponibilidad, urlsReserva, urlsServicioTutoria,urlsNotificacion,urlsPago,urlsCalificacion

# Crear directorios para imágenes si no existen
os.makedirs("uploads/profile_images", exist_ok=True)

models.Base.metadata.create_all(bind=database.engine)

middleware = [
    Middleware(CORSMiddleware,   allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
]
app = FastAPI(
    title="TUTOWEB API",
    description="API para la gestión de perfiles, autenticacion, clases, reservas, pagos del sistema TutoWeb",
    middleware=middleware
)
app.mount("/uploads", StaticFiles(directory="tutowebback/uploads"), name="uploads")

# Incluir todas las rutas definidas
app.include_router(urlsUser.router)
app.include_router(urlsNotificacion.router)
app.include_router(urlsServicioTutoria.router)
app.include_router(urlsReserva.router)
app.include_router(urlsDisponibilidad.router)
app.include_router(urlsPago.router)
app.include_router(urlsMateriasCarreraUsuario.router)
app.include_router(urlsCarrera.router)
app.include_router(urlsRole.router)
app.include_router(urlsMaterias.router)
app.include_router(urlsCalificacion.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=7000, reload=True)