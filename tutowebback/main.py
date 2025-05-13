import os
import sys

from tutowebback.services.mercadoPagoService import MercadoPagoService

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from fastapi.staticfiles import StaticFiles
from tutowebback.models import models
from tutowebback.config import database
from tutowebback.urls import urlsUser, urlsCarrera, urlsRole, urlsMaterias, urlsMateriasCarreraUsuario, \
    urlsDisponibilidad, urlsReserva, urlsServicioTutoria,urlsNotificacion,urlsPago

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
app.include_router(urlsNotificacion.router)
app.include_router(urlsServicioTutoria.router)
app.include_router(urlsReserva.router)
app.include_router(urlsDisponibilidad.router)
app.include_router(urlsPago.router)
app.include_router(urlsMateriasCarreraUsuario.router)
app.include_router(urlsCarrera.router)
app.include_router(urlsRole.router)
app.include_router(urlsMaterias.router)

# Endpoint para crear usuario vendedor de prueba (solo ejecutar una vez)
@app.get("/crear-usuario-vendedor")
def endpoint_crear_vendedor():
    mp_service = MercadoPagoService()
    vendedor = mp_service.crear_usuario_vendedor()
    if vendedor:
        return {
            "message": "Usuario vendedor de prueba creado exitosamente",
            "vendedor": vendedor
        }
    else:
        return {
            "message": "Error al crear usuario vendedor de prueba"
        }


# Endpoint para probar la creación de preferencia
@app.get("/crear-preferencia-prueba")
def endpoint_crear_preferencia():
    mp_service = MercadoPagoService()
    preferencia = mp_service.crear_preferencia(
        titulo="Producto de prueba",
        precio=100,
        cantidad=1,
        reserva_id=1,
        pago_id=1,
        notas="Prueba de integración"
    )

    return {
        "message": "Preferencia creada exitosamente",
        "checkout_url": preferencia["init_point"],
        "id": preferencia["id"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=7000, reload=True)