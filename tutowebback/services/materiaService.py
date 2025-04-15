import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.models import models
from tutowebback.schemas import schemas


class MateriaService:

    def create_materia(self, db: Session, materia: schemas.MateriaCreate):
        try:
            # Verificar si existe la carrera
            existing_carrera = db.query(models.Carrera).filter(models.Carrera.id == materia.carrera_id).first()
            if not existing_carrera:
                raise HTTPException(status_code=404, detail="Carrera not found")

            # Verificar si ya existe una materia con el mismo nombre en la misma carrera
            existing_materia = db.query(models.Materia).filter(
                models.Materia.nombre == materia.nombre,
                models.Materia.carrera_id == materia.carrera_id
            ).first()

            if existing_materia:
                raise HTTPException(status_code=400, detail="Materia name already exists in this carrera")

            # Crear la nueva materia
            db_materia = models.Materia(
                nombre=materia.nombre,
                carrera_id=materia.carrera_id,
                descripcion=materia.descripcion
            )

            db.add(db_materia)
            db.commit()
            db.refresh(db_materia)
            return db_materia
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error creating materia")
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating materia: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def get_materia(self, db: Session, id: int):
        db_materia = db.query(models.Materia).filter(models.Materia.id == id).first()
        if db_materia is None:
            raise HTTPException(status_code=404, detail="Materia not found")
        return db_materia

    def get_all_materias(self, db: Session):
        return db.query(models.Materia).all()

    def get_materias_by_carrera(self, db: Session, carrera_id: int):
        # Verificar si existe la carrera
        existing_carrera = db.query(models.Carrera).filter(models.Carrera.id == carrera_id).first()
        if not existing_carrera:
            raise HTTPException(status_code=404, detail="Carrera not found")

        return db.query(models.Materia).filter(models.Materia.carrera_id == carrera_id).all()

    def edit_materia(self, db: Session, id: int, materia: schemas.MateriaUpdate):
        try:
            db_materia = db.query(models.Materia).filter(models.Materia.id == id).first()
            if db_materia is None:
                raise HTTPException(status_code=404, detail="Materia not found")

            # Si se actualiza la carrera, verificar que exista
            if materia.carrera_id is not None:
                existing_carrera = db.query(models.Carrera).filter(models.Carrera.id == materia.carrera_id).first()
                if not existing_carrera:
                    raise HTTPException(status_code=404, detail="Carrera not found")

            # Verificar si el nuevo nombre ya existe en la misma carrera (o en la nueva carrera si se está cambiando)
            if materia.nombre is not None:
                carrera_id_to_check = materia.carrera_id if materia.carrera_id is not None else db_materia.carrera_id
                existing_materia = db.query(models.Materia).filter(
                    models.Materia.nombre == materia.nombre,
                    models.Materia.carrera_id == carrera_id_to_check,
                    models.Materia.id != id
                ).first()

                if existing_materia:
                    raise HTTPException(status_code=400, detail="Materia name already exists in this carrera")

            # Actualizar campos
            if materia.nombre is not None:
                db_materia.nombre = materia.nombre
            if materia.carrera_id is not None:
                db_materia.carrera_id = materia.carrera_id
            if materia.descripcion is not None:
                db_materia.descripcion = materia.descripcion

            db.commit()
            db.refresh(db_materia)
            return db_materia
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error updating materia")
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating materia: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def delete_materia(self, db: Session, id: int):
        try:
            db_materia = db.query(models.Materia).filter(models.Materia.id == id).first()
            if db_materia is None:
                raise HTTPException(status_code=404, detail="Materia not found")

            # Verificar si hay servicios de tutoría asociados a esta materia
            servicios = db.query(models.ServicioTutoria).filter(
                models.ServicioTutoria.materia_id == id
            ).first()

            if servicios:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete materia because it has associated tutoring services"
                )

            db.delete(db_materia)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting materia: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")