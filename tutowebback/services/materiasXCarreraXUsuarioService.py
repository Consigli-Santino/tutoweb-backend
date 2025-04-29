import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.models import models
from tutowebback.schemas import schemas


class MateriasXCarreraXUsuarioService:

    def create_materia_carrera_usuario(self, db: Session, materia_carrera_usuario: schemas.MateriasXCarreraXUsuarioCreate):
        try:
            # Verificar si existe el usuario
            existing_usuario = db.query(models.Usuario).filter(models.Usuario.id == materia_carrera_usuario.usuario_id).first()
            if not existing_usuario:
                raise HTTPException(status_code=404, detail="Usuario not found")

            # Verificar si existe la materia
            existing_materia = db.query(models.Materia).filter(models.Materia.id == materia_carrera_usuario.materia_id).first()
            if not existing_materia:
                raise HTTPException(status_code=404, detail="Materia not found")

            # Verificar si existe la carrera
            existing_carrera = db.query(models.Carrera).filter(models.Carrera.id == materia_carrera_usuario.carrera_id).first()
            if not existing_carrera:
                raise HTTPException(status_code=404, detail="Carrera not found")

            # Verificar si ya existe la relación
            existing_relation = db.query(models.MateriasXCarreraXUsuario).filter(
                models.MateriasXCarreraXUsuario.usuario_id == materia_carrera_usuario.usuario_id,
                models.MateriasXCarreraXUsuario.materia_id == materia_carrera_usuario.materia_id,
                models.MateriasXCarreraXUsuario.carrera_id == materia_carrera_usuario.carrera_id
            ).first()

            if existing_relation:
                raise HTTPException(status_code=400, detail="Relation already exists")

            # Crear la nueva relación
            db_materia_carrera_usuario = models.MateriasXCarreraXUsuario(
                estado=materia_carrera_usuario.estado,
                usuario_id=materia_carrera_usuario.usuario_id,
                materia_id=materia_carrera_usuario.materia_id,
                carrera_id=materia_carrera_usuario.carrera_id
            )

            db.add(db_materia_carrera_usuario)
            db.commit()
            db.refresh(db_materia_carrera_usuario)
            return db_materia_carrera_usuario
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error creating relation")
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating materia-carrera-usuario relation: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def get_materia_carrera_usuario(self, db: Session, id: int):
        db_materia_carrera_usuario = db.query(models.MateriasXCarreraXUsuario).filter(
            models.MateriasXCarreraXUsuario.usuario_id == id,
            models.MateriasXCarreraXUsuario.estado == True
        ).all()

        if not db_materia_carrera_usuario:
            raise HTTPException(status_code=404, detail="No found relations")

        return db_materia_carrera_usuario

    def get_all_materias_carrera_usuario(self, db: Session):
        return db.query(models.MateriasXCarreraXUsuario).all()

    def get_materias_by_usuario_and_carrera(self, db: Session, usuario_id: int, carrera_id: int):
        # Verificar si existe el usuario
        existing_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
        if not existing_usuario:
            raise HTTPException(status_code=404, detail="Usuario not found")

        # Verificar si existe la carrera
        existing_carrera = db.query(models.Carrera).filter(models.Carrera.id == carrera_id).first()
        if not existing_carrera:
            raise HTTPException(status_code=404, detail="Carrera not found")

        return db.query(models.MateriasXCarreraXUsuario).filter(
            models.MateriasXCarreraXUsuario.usuario_id == usuario_id,
            models.MateriasXCarreraXUsuario.carrera_id == carrera_id
        ).all()

    def get_usuarios_by_materia_and_carrera(self, db: Session, materia_id: int, carrera_id: int):
        # Verificar si existe la materia
        existing_materia = db.query(models.Materia).filter(models.Materia.id == materia_id).first()
        if not existing_materia:
            raise HTTPException(status_code=404, detail="Materia not found")

        # Verificar si existe la carrera
        existing_carrera = db.query(models.Carrera).filter(models.Carrera.id == carrera_id).first()
        if not existing_carrera:
            raise HTTPException(status_code=404, detail="Carrera not found")

        return db.query(models.MateriasXCarreraXUsuario).filter(
            models.MateriasXCarreraXUsuario.materia_id == materia_id,
            models.MateriasXCarreraXUsuario.carrera_id == carrera_id
        ).all()

    def edit_materia_carrera_usuario(self, db: Session, id: int, materia_carrera_usuario: schemas.MateriasXCarreraXUsuarioUpdate):
        try:
            db_materia_carrera_usuario = db.query(models.MateriasXCarreraXUsuario).filter(models.MateriasXCarreraXUsuario.id == id).first()
            if db_materia_carrera_usuario is None:
                raise HTTPException(status_code=404, detail="Relation not found")

            # Si se actualiza el usuario, verificar que exista
            if materia_carrera_usuario.usuario_id is not None:
                existing_usuario = db.query(models.Usuario).filter(models.Usuario.id == materia_carrera_usuario.usuario_id).first()
                if not existing_usuario:
                    raise HTTPException(status_code=404, detail="Usuario not found")

            # Si se actualiza la materia, verificar que exista
            if materia_carrera_usuario.materia_id is not None:
                existing_materia = db.query(models.Materia).filter(models.Materia.id == materia_carrera_usuario.materia_id).first()
                if not existing_materia:
                    raise HTTPException(status_code=404, detail="Materia not found")

            # Si se actualiza la carrera, verificar que exista
            if materia_carrera_usuario.carrera_id is not None:
                existing_carrera = db.query(models.Carrera).filter(models.Carrera.id == materia_carrera_usuario.carrera_id).first()
                if not existing_carrera:
                    raise HTTPException(status_code=404, detail="Carrera not found")

            # Verificar si la nueva combinación ya existe (evitar duplicados)
            if all(v is not None for v in [materia_carrera_usuario.usuario_id, materia_carrera_usuario.materia_id, materia_carrera_usuario.carrera_id]):
                usuario_id_to_check = materia_carrera_usuario.usuario_id
                materia_id_to_check = materia_carrera_usuario.materia_id
                carrera_id_to_check = materia_carrera_usuario.carrera_id

                existing_relation = db.query(models.MateriasXCarreraXUsuario).filter(
                    models.MateriasXCarreraXUsuario.usuario_id == usuario_id_to_check,
                    models.MateriasXCarreraXUsuario.materia_id == materia_id_to_check,
                    models.MateriasXCarreraXUsuario.carrera_id == carrera_id_to_check,
                    models.MateriasXCarreraXUsuario.id != id
                ).first()

                if existing_relation:
                    raise HTTPException(status_code=400, detail="Relation already exists")

            # Actualizar campos
            if materia_carrera_usuario.estado is not None:
                db_materia_carrera_usuario.estado = materia_carrera_usuario.estado
            if materia_carrera_usuario.usuario_id is not None:
                db_materia_carrera_usuario.usuario_id = materia_carrera_usuario.usuario_id
            if materia_carrera_usuario.materia_id is not None:
                db_materia_carrera_usuario.materia_id = materia_carrera_usuario.materia_id
            if materia_carrera_usuario.carrera_id is not None:
                db_materia_carrera_usuario.carrera_id = materia_carrera_usuario.carrera_id

            db.commit()
            db.refresh(db_materia_carrera_usuario)
            return db_materia_carrera_usuario
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error updating relation")
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating materia-carrera-usuario relation: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def delete_materia_carrera_usuario(self, db: Session, id: int):
        try:
            db_materia_carrera_usuario = db.query(models.MateriasXCarreraXUsuario).filter(models.MateriasXCarreraXUsuario.id == id).first()
            if db_materia_carrera_usuario is None:
                raise HTTPException(status_code=404, detail="Relation not found")

            db.delete(db_materia_carrera_usuario)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting materia-carrera-usuario relation: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")