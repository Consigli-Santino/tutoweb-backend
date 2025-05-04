import os
import sys
from datetime import date

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

    def get_disponibilidades_disponibles(self, db: Session, tutor_id: int, fecha: date):
        """
        Obtiene las disponibilidades realmente disponibles, eliminando las que ya tienen reservas
        """
        try:
            # 1. Verificar si existe el tutor
            existing_tutor = db.query(models.Usuario).filter(models.Usuario.id == tutor_id).first()
            if not existing_tutor:
                raise HTTPException(status_code=404, detail="Tutor not found")

            # 2. Obtener el día de la semana de la fecha
            dia_semana = fecha.isoweekday()  # 1=lunes, 7=domingo

            # 3. Obtener todas las disponibilidades del tutor para ese día
            disponibilidades = db.query(models.Disponibilidad).filter(
                models.Disponibilidad.tutor_id == tutor_id,
                models.Disponibilidad.dia_semana == dia_semana
            ).all()

            if not disponibilidades:
                return []

            # 4. Obtener servicios del tutor (para buscar reservas)
            servicios = db.query(models.ServicioTutoria).filter(
                models.ServicioTutoria.tutor_id == tutor_id,
                models.ServicioTutoria.activo == True
            ).all()

            if not servicios:
                return disponibilidades  # Si no hay servicios, no puede haber reservas

            # 5. Obtener todas las reservas para ese tutor en esa fecha
            servicio_ids = [servicio.id for servicio in servicios]
            reservas = db.query(models.Reserva).filter(
                models.Reserva.servicio_id.in_(servicio_ids),
                models.Reserva.fecha == fecha,
                models.Reserva.estado.in_(["pendiente", "confirmada"])
            ).all()
            disponibilidades_disponibles = []

            for disp in disponibilidades:
                reserva_solapada = False
                for reserva in reservas:
                    if ((disp.hora_inicio <= reserva.hora_inicio and reserva.hora_inicio < disp.hora_fin) or
                            (disp.hora_inicio < reserva.hora_fin and reserva.hora_fin <= disp.hora_fin) or
                            (reserva.hora_inicio <= disp.hora_inicio and disp.hora_fin <= reserva.hora_fin)):
                        reserva_solapada = True
                        break
                if not reserva_solapada:
                    disponibilidades_disponibles.append(disp)

            return disponibilidades_disponibles
        except Exception as e:
            logging.error(f"Error getting disponibilidades disponibles: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
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