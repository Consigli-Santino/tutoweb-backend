import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.models import models
from tutowebback.schemas import schemas


class CarreraService:

    def create_carrera(self, db: Session, carrera: schemas.CarreraCreate):
        try:
            # Verificar si ya existe una carrera con el mismo nombre
            existing_carrera = db.query(models.Carrera).filter(models.Carrera.nombre == carrera.nombre).first()
            if existing_carrera:
                raise HTTPException(status_code=400, detail="Carrera name already exists")

            # Crear la nueva carrera
            db_carrera = models.Carrera(
                nombre=carrera.nombre,
                descripcion=carrera.descripcion,
                facultad=carrera.facultad
            )

            db.add(db_carrera)
            db.commit()
            db.refresh(db_carrera)
            return db_carrera
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Carrera name already exists")
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating carrera: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def get_carrera(self, db: Session, id: int):
        db_carrera = db.query(models.Carrera).filter(models.Carrera.id == id).first()
        if db_carrera is None:
            raise HTTPException(status_code=404, detail="Carrera not found")
        return db_carrera

    def get_all_carreras(self, db: Session):
        return db.query(models.Carrera).all()

    def edit_carrera(self, db: Session, id: int, carrera: schemas.CarreraUpdate):
        try:
            db_carrera = db.query(models.Carrera).filter(models.Carrera.id == id).first()
            if db_carrera is None:
                raise HTTPException(status_code=404, detail="Carrera not found")

            # Verificar si el nuevo nombre ya existe en otra carrera
            if carrera.nombre:
                existing_carrera = db.query(models.Carrera).filter(
                    models.Carrera.nombre == carrera.nombre,
                    models.Carrera.id != id
                ).first()
                if existing_carrera:
                    raise HTTPException(status_code=400, detail="Carrera name already exists")

            # Actualizar campos
            if carrera.nombre is not None:
                db_carrera.nombre = carrera.nombre
            if carrera.descripcion is not None:
                db_carrera.descripcion = carrera.descripcion
            if carrera.facultad is not None:
                db_carrera.facultad = carrera.facultad

            db.commit()
            db.refresh(db_carrera)
            return db_carrera
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Carrera name already exists")
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating carrera: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def delete_carrera(self, db: Session, id: int):
        try:
            db_carrera = db.query(models.Carrera).filter(models.Carrera.id == id).first()
            if db_carrera is None:
                raise HTTPException(status_code=404, detail="Carrera not found")

            # Verificar si hay relaciones con usuarios o materias
            user_associations = db.query(models.CarreraUsuario).filter(
                models.CarreraUsuario.carrera_id == id
            ).first()

            if user_associations:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete carrera because it has associated users"
                )

            materias = db.query(models.Materia).filter(
                models.Materia.carrera_id == id
            ).first()

            if materias:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete carrera because it has associated materias"
                )

            db.delete(db_carrera)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting carrera: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")