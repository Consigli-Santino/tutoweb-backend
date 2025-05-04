import os
import shutil
from fastapi import UploadFile, HTTPException
from datetime import datetime
import logging
from pathlib import Path


class ImageService:
    """
    Servicio para gestionar el guardado y eliminación de imágenes de perfil
    """

    def __init__(self):
        # Configurar directorios para almacenamiento
        self.base_dir = Path("uploads")
        self.profile_dir = self.base_dir / "profile_images"

        # Crear directorios si no existen
        self.base_dir.mkdir(exist_ok=True)
        self.profile_dir.mkdir(exist_ok=True)

    async def save_profile_image(self, emailUser: str, file: UploadFile) -> str:
        """
        Guarda la imagen de perfil y devuelve la ruta para guardar en la BD

        Args:
            user_id: ID del usuario
            file: Archivo de imagen

        Returns:
            str: Ruta relativa para guardar en la BD
        """
        if not file or not file.filename:
            return None

        try:
            # Validar extensión
            file_extension = os.path.splitext(file.filename)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

            if file_extension not in valid_extensions:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de archivo no permitido. Use: jpg, jpeg, png, gif o webp"
                )

            # Crear nombre único: perfil_[ID]_[TIMESTAMP].[ext]
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"perfil_{emailUser}_{timestamp}{file_extension}"

            # Ruta completa
            file_path = self.profile_dir / filename

            # Guardar archivo
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Devolver ruta relativa
            return f"/uploads/profile_images/{filename}"

        except Exception as e:
            logging.error(f"Error al guardar imagen: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al procesar imagen: {str(e)}")

    def delete_profile_image(self, image_path: str) -> bool:
        """
        Elimina una imagen de perfil del sistema de archivos

        Args:
            image_path: Ruta relativa de la imagen

        Returns:
            bool: True si se eliminó, False si no
        """
        if not image_path:
            return False

        try:
            # Eliminar el slash inicial si existe
            if image_path.startswith('/'):
                image_path = image_path[1:]

            # Ruta absoluta
            file_path = Path(os.path.join(os.getcwd(), image_path))

            # Verificar y eliminar
            if file_path.exists():
                os.remove(file_path)
                return True

            return False

        except Exception as e:
            logging.error(f"Error al eliminar imagen: {str(e)}")
            return False