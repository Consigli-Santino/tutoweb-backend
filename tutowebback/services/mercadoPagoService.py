import os
import mercadopago
import logging
from fastapi import HTTPException, FastAPI
from dotenv import load_dotenv

app = FastAPI()

# Cargar variables de entorno
environment = os.getenv('ENVIRONMENT', 'development')
env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'environments', f".env-{environment}")
load_dotenv(env_file)


class MercadoPagoService:
    def __init__(self):
        # Usar credenciales de prueba
        self.access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN",
                                      "TEST-2784401808757106-051013-668a9ab9589cc89b0e9406f10b8dcc63-1314524421")
        self.public_key = os.getenv("MERCADOPAGO_PUBLIC_KEY", "TEST-7fd540ed-5002-4b29-832b-c3a3ff6f83ad")

        self.sdk = mercadopago.SDK(self.access_token)

    def crear_preferencia(self, titulo, precio, cantidad, reserva_id, pago_id, notas=None):
        """
        Crea una preferencia de pago en Mercado Pago
        """
        try:
            # Obtener la URL base del frontend
            frontend_url = os.getenv('FRONTEND_URL', 'http://192.168.0.38:5173')

            # Configurar los items de la preferencia
            preference_data = {
                "items": [
                    {
                        "title": titulo,
                        "quantity": int(cantidad),
                        "unit_price": float(precio),
                        "currency_id": "ARS"
                    }
                ],
                "external_reference": f"reserva_{reserva_id}_pago_{pago_id}",
                "statement_descriptor": "TutoWeb - Pago de Tutoría",
                "back_urls": {
                    "success": f"{frontend_url}/payment-success",
                    "failure": f"{frontend_url}/payment-failure",
                    "pending": f"{frontend_url}/payment-pending"
                }
                # Omitir notification_url para pruebas locales
            }

            if notas:
                preference_data["items"][0]["description"] = notas

            # Crear la preferencia
            preference_response = self.sdk.preference().create(preference_data)

            if preference_response["status"] != 201 and preference_response["status"] != 200:
                logging.error(f"Error creando preferencia: {preference_response}")
                raise HTTPException(status_code=500, detail="Error al crear preferencia de pago")

            return preference_response["response"]

        except Exception as e:
            logging.error(f"Error en MercadoPagoService.crear_preferencia: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al crear preferencia de pago: {str(e)}")

    def consultar_pago(self, payment_id):
        """
        Consulta el estado de un pago por su ID
        """
        try:
            payment_response = self.sdk.payment().get(payment_id)

            if payment_response["status"] != 200:
                logging.error(f"Error consultando pago: {payment_response}")
                raise HTTPException(status_code=500, detail="Error al consultar el pago")

            return payment_response["response"]

        except Exception as e:
            logging.error(f"Error en MercadoPagoService.consultar_pago: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al consultar pago: {str(e)}")

    def get_public_key(self):
        """
        Retorna la public key para usar en el frontend
        """
        return self.public_key


# Endpoint para probar la creación de preferencia (solo para pruebas)
@app.get("/test-payment")
def test_payment():
    mp_service = MercadoPagoService()
    preferencia = mp_service.crear_preferencia(
        titulo="Tutoría de prueba",
        precio=100,
        cantidad=1,
        reserva_id=1,
        pago_id=1,
        notas="Prueba de integración"
    )

    return {
        "checkout_url": preferencia["init_point"],
        "sandbox_init_point": preferencia["sandbox_init_point"]
    }