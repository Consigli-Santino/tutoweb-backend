import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.models import models
from tutowebback.schemas import schemas


class DisponibilidadService:

    def create_disponibilidad(self, db: Session, disponibilidad: schemas.DisponibilidadCreate):
        try:
            # Verificar si existe el tutor
            existing_tutor = db.query(models.Usuario).filter(models.Usuario.id == disponibilidad.tutor_id).first()
            if not existing_tutor:
                raise HTTPException(status_code=404, detail="Tutor not found")
            # Verificar si ya existe una disponibilidad similar (mismo día y horarios superpuestos)
            existing_disponibilidad = db.query(models.Disponibilidad).filter(
                models.Disponibilidad.tutor_id == disponibilidad.tutor_id,
                models.Disponibilidad.dia_semana == disponibilidad.dia_semana,
                ((models.Disponibilidad.hora_inicio <= disponibilidad.hora_inicio) &
                 (models.Disponibilidad.hora_fin > disponibilidad.hora_inicio)) |
                ((models.Disponibilidad.hora_inicio < disponibilidad.hora_fin) &
                 (models.Disponibilidad.hora_fin >= disponibilidad.hora_fin)) |
                ((models.Disponibilidad.hora_inicio >= disponibilidad.hora_inicio) &
                 (models.Disponibilidad.hora_fin <= disponibilidad.hora_fin))
            ).first()

            if existing_disponibilidad:
                raise HTTPException(status_code=400, detail="Overlapping availability already exists")

            # Crear la nueva disponibilidad
            db_disponibilidad = models.Disponibilidad(
                tutor_id=disponibilidad.tutor_id,
                dia_semana=disponibilidad.dia_semana,
                hora_inicio=disponibilidad.hora_inicio,
                hora_fin=disponibilidad.hora_fin
            )

            db.add(db_disponibilidad)
            db.commit()
            db.refresh(db_disponibilidad)
            return db_disponibilidad
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error creating disponibilidad")
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating disponibilidad: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def get_disponibilidad(self, db: Session, id: int):
        db_disponibilidad = db.query(models.Disponibilidad).filter(models.Disponibilidad.id == id).first()
        if db_disponibilidad is None:
            raise HTTPException(status_code=404, detail="Disponibilidad not found")
        return db_disponibilidad

    def get_disponibilidades_by_tutor(self, db: Session, tutor_id: int):
        # Verificar si existe el tutor
        existing_tutor = db.query(models.Usuario).filter(models.Usuario.id == tutor_id).first()
        if not existing_tutor:
            raise HTTPException(status_code=404, detail="Tutor not found")

        return db.query(models.Disponibilidad).filter(models.Disponibilidad.tutor_id == tutor_id).all()

    def edit_disponibilidad(self, db: Session, id: int, disponibilidad: schemas.DisponibilidadUpdate, current_user_id: int):
        try:
            db_disponibilidad = db.query(models.Disponibilidad).filter(models.Disponibilidad.id == id).first()
            if db_disponibilidad is None:
                raise HTTPException(status_code=404, detail="Disponibilidad not found")

            # Verificar si el usuario actual es el dueño de esta disponibilidad
            if db_disponibilidad.tutor_id != current_user_id:
                # Verifica si el usuario tiene rol de administrador (puedes ajustar según tus roles)
                current_user = db.query(models.Usuario).filter(models.Usuario.id == current_user_id).first()
                if current_user.id_rol not in [1, 2]:  # Asumiendo que 1 es superAdmin y 2 es admin
                    raise HTTPException(status_code=403, detail="Not authorized to modify this availability")

            # Verificar si la actualización genera superposición con otras disponibilidades
            if disponibilidad.dia_semana is not None or disponibilidad.hora_inicio is not None or disponibilidad.hora_fin is not None:
                new_dia = disponibilidad.dia_semana if disponibilidad.dia_semana is not None else db_disponibilidad.dia_semana
                new_hora_inicio = disponibilidad.hora_inicio if disponibilidad.hora_inicio is not None else db_disponibilidad.hora_inicio
                new_hora_fin = disponibilidad.hora_fin if disponibilidad.hora_fin is not None else db_disponibilidad.hora_fin

                existing_disponibilidad = db.query(models.Disponibilidad).filter(
                    models.Disponibilidad.tutor_id == db_disponibilidad.tutor_id,
                    models.Disponibilidad.dia_semana == new_dia,
                    models.Disponibilidad.id != id,
                    ((models.Disponibilidad.hora_inicio <= new_hora_inicio) &
                     (models.Disponibilidad.hora_fin > new_hora_inicio)) |
                    ((models.Disponibilidad.hora_inicio < new_hora_fin) &
                     (models.Disponibilidad.hora_fin >= new_hora_fin)) |
                    ((models.Disponibilidad.hora_inicio >= new_hora_inicio) &
                     (models.Disponibilidad.hora_fin <= new_hora_fin))
                ).first()

                if existing_disponibilidad:
                    raise HTTPException(status_code=400, detail="Overlapping availability already exists")

            # Actualizar campos
            if disponibilidad.dia_semana is not None:
                db_disponibilidad.dia_semana = disponibilidad.dia_semana
            if disponibilidad.hora_inicio is not None:
                db_disponibilidad.hora_inicio = disponibilidad.hora_inicio
            if disponibilidad.hora_fin is not None:
                db_disponibilidad.hora_fin = disponibilidad.hora_fin

            db.commit()
            db.refresh(db_disponibilidad)
            return db_disponibilidad
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error updating disponibilidad")
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating disponibilidad: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def delete_disponibilidad(self, db: Session, id: int, current_user_id: int):
        try:
            db_disponibilidad = db.query(models.Disponibilidad).filter(models.Disponibilidad.id == id).first()
            if db_disponibilidad is None:
                raise HTTPException(status_code=404, detail="Disponibilidad not found")

            # Verificar si el usuario actual es el dueño de esta disponibilidad
            if db_disponibilidad.tutor_id != current_user_id:
                # Verifica si el usuario tiene rol de administrador
                current_user = db.query(models.Usuario).filter(models.Usuario.id == current_user_id).first()
                if current_user.id_rol not in [1, 2]:  # Asumiendo que 1 es superAdmin y 2 es admin
                    raise HTTPException(status_code=403, detail="Not authorized to delete this availability")

            # Verificar si hay reservas asociadas a esta disponibilidad
            # Esto requeriría añadir un campo a tu modelo de Reserva para relacionarlo con Disponibilidad
            # O puedes chequear por día y horario

            db.delete(db_disponibilidad)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting disponibilidad: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")