import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.models import models
from tutowebback.schemas import schemas
from tutowebback.auth import auth

class UsuarioService:

    def create_usuario(self, db: Session, usuario: schemas.UsuarioCreate):
        try:
            existing_user = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already exists")
            # Verificar si las carreras existen
            for carrera_id in usuario.id_carrera:
                existing_carrera = db.query(models.Carrera).filter(models.Carrera.id == carrera_id).first()
                if not existing_carrera:
                    raise HTTPException(status_code=404, detail=f"Carrera with id {carrera_id} not found")


            # Crear el nuevo usuario
            db_usuario = models.Usuario(
                nombre=usuario.nombre,
                apellido=usuario.apellido,
                email=usuario.email,
                password_hash=auth.get_password_hash(usuario.password),
                es_tutor=usuario.es_tutor,
                foto_perfil=usuario.foto_perfil,
                id_rol=usuario.id_rol,

            )
            db.add(db_usuario)
            db.flush()

            # Agregar carreras al usuario
            for carrera_id in usuario.id_carrera:
                db_carrera = db.query(models.Carrera).filter(models.Carrera.id == carrera_id).first()
                if not db_carrera:
                    raise HTTPException(status_code=404, detail=f"Carrera with id {carrera_id} not found")

                db_carrera_usuario = models.CarreraUsuario(
                    usuario_id=db_usuario.id,
                    carrera_id=db_carrera.id
                )
                db.add(db_carrera_usuario)
                db.flush()

            db.commit()
            db.refresh(db_usuario)
            return db_usuario
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Email already exists")
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating usuario: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def get_usuario(self, db: Session, usuario_id: int):
        db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
        if db_usuario is None:
            raise HTTPException(status_code=404, detail="Usuario not found")
        return db_usuario

    def get_all_usuarios(self, db: Session):
        db_usuarios = db.query(models.Usuario).filter(models.Usuario.activo == True).all()
        if db_usuarios is None:
            raise HTTPException(status_code=404, detail="Usuarios not found")
        return db_usuarios

    def get_tutores(self, db: Session):
        db_tutores = db.query(models.Usuario).filter(models.Usuario.es_tutor == True).all()
        if db_tutores is None:
            raise HTTPException(status_code=404, detail="Tutores not found")
        return db_tutores

    def edit_usuario(self, db: Session, usuario_id: int, usuario: schemas.UsuarioUpdate):
        db_usuario = self.get_usuario(db, usuario_id)
        try:
            # Actualizar campos básicos si se proporcionan
            if usuario.nombre is not None:
                db_usuario.nombre = usuario.nombre
            if usuario.apellido is not None:
                db_usuario.apellido = usuario.apellido
            if usuario.email is not None:
                db_usuario.email = usuario.email
            if usuario.password is not None:
                db_usuario.password_hash = auth.get_password_hash(usuario.password)
            if usuario.semestre is not None:
                db_usuario.semestre = usuario.semestre
            if usuario.id_rol is not None:
                db_usuario.id_rol = usuario.id_rol
            if usuario.es_tutor is not None:
                db_usuario.es_tutor = usuario.es_tutor
            if usuario.foto_perfil is not None:
                db_usuario.foto_perfil = usuario.foto_perfil
            if usuario.descripcion is not None:
                db_usuario.descripcion = usuario.descripcion
            if usuario.telefono is not None:
                db_usuario.telefono = usuario.telefono

            # Actualizar carreras si se proporcionan
            if usuario.id_carrera is not None:
                # Obtener las carreras actuales del usuario
                current_carreras = db.query(models.CarreraUsuario).filter(models.CarreraUsuario.usuario_id == db_usuario.id).all()
                current_carrera_ids = {carrera.carrera_id for carrera in current_carreras}

                # Convertir la lista de id_carrera a un set
                new_carrera_ids = set(usuario.id_carrera)

                # Identificar las carreras a agregar y eliminar
                carreras_to_add = new_carrera_ids - current_carrera_ids
                carreras_to_remove = current_carrera_ids - new_carrera_ids

                # Agregar nuevas relaciones
                for carrera_id in carreras_to_add:
                    db_carrera = db.query(models.Carrera).filter(models.Carrera.id == carrera_id).first()
                    if not db_carrera:
                        raise HTTPException(status_code=404, detail=f"Carrera with id {carrera_id} not found")
                    db_carrera_usuario = models.CarreraUsuario(
                        usuario_id=db_usuario.id,
                        carrera_id=db_carrera.id
                    )
                    db.add(db_carrera_usuario)

                # Eliminar relaciones que ya no están presentes
                for carrera_id in carreras_to_remove:
                    db.query(models.CarreraUsuario).filter(
                        models.CarreraUsuario.usuario_id == db_usuario.id,
                        models.CarreraUsuario.carrera_id == carrera_id
                    ).delete()

            db.commit()
            db.refresh(db_usuario)
            return db_usuario
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Email already exists")
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating usuario: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def delete_usuario(self, db: Session, usuario_id: int):
        db_usuario = self.get_usuario(db, usuario_id)
        try:
            db.query(models.CarreraUsuario).filter(models.CarreraUsuario.usuario_id == usuario_id).delete()
            db_usuario.activo = False
            db.commit()
            db.refresh(db_usuario)
            return {"message": "Usuario desactivado correctamente"}
        except Exception as e:
            db.rollback()
            logging.error(f"Error realizando la baja lógica del usuario: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

