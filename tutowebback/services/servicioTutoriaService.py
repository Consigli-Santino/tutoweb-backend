# servicioTutoriaService.py

import os
import sys
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.models import models
from tutowebback.schemas import schemas


class ServicioTutoriaService:

    def create_servicio(self, db: Session, servicio: schemas.ServicioTutoriaCreate):
        try:
            # Verificar si existe el tutor
            tutor = db.query(models.Usuario).filter(models.Usuario.id == servicio.tutor_id).first()
            if not tutor:
                raise HTTPException(status_code=404, detail="Tutor not found")

            # Verificar si existe la materia
            materia = db.query(models.Materia).filter(models.Materia.id == servicio.materia_id).first()
            if not materia:
                raise HTTPException(status_code=404, detail="Materia not found")

            # Verificar si el tutor tiene asignada esta materia en MateriasXCarreraXUsuario
            relacion = db.query(models.MateriasXCarreraXUsuario).filter(
                models.MateriasXCarreraXUsuario.usuario_id == servicio.tutor_id,
                models.MateriasXCarreraXUsuario.materia_id == servicio.materia_id,
                models.MateriasXCarreraXUsuario.estado == True
            ).first()

            if not relacion:
                raise HTTPException(
                    status_code=400,
                    detail="El tutor no tiene asignada esta materia. Debe asignarla primero."
                )

            # Verificar si ya existe un servicio para este tutor y materia
            servicio_existente = db.query(models.ServicioTutoria).filter(
                models.ServicioTutoria.tutor_id == servicio.tutor_id,
                models.ServicioTutoria.materia_id == servicio.materia_id
            ).first()

            if servicio_existente and servicio_existente.activo:
                raise HTTPException(
                    status_code=400,
                    detail="Ya existe un servicio para esta materia"
                )

            # Crear el nuevo servicio
            db_servicio = models.ServicioTutoria(
                tutor_id=servicio.tutor_id,
                materia_id=servicio.materia_id,
                precio=servicio.precio,
                descripcion=servicio.descripcion,
                modalidad=servicio.modalidad,
                activo=servicio.activo
            )

            db.add(db_servicio)
            db.commit()
            db.refresh(db_servicio)
            return db_servicio
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error creating servicio")
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating servicio: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def get_servicio(self, db: Session, id: int):
        db_servicio = db.query(models.ServicioTutoria).options(
            joinedload(models.ServicioTutoria.tutor),
            joinedload(models.ServicioTutoria.materia)
        ).filter(models.ServicioTutoria.id == id).first()

        if db_servicio is None:
            raise HTTPException(status_code=404, detail="Servicio not found")
        return db_servicio

    def get_servicios_by_tutor(self, db: Session, email: str):
        return db.query(models.ServicioTutoria).join(models.Usuario).options(
            joinedload(models.ServicioTutoria.materia)
        ).filter(
            models.Usuario.email == email,
            models.ServicioTutoria.activo == True
        ).all()

    def get_servicios_by_materia(self, db: Session, materia_id: int):
        return db.query(models.ServicioTutoria).options(
            joinedload(models.ServicioTutoria.tutor)
        ).filter(
            models.ServicioTutoria.materia_id == materia_id,
            models.ServicioTutoria.activo == True
        ).all()

    def edit_servicio(self, db: Session, id: int, servicio: schemas.ServicioTutoriaUpdate):
        try:
            db_servicio = db.query(models.ServicioTutoria).filter(models.ServicioTutoria.id == id).first()
            if db_servicio is None:
                raise HTTPException(status_code=404, detail="Servicio not found")

            # Si se cambia la materia, verificar que el tutor tenga asignada esta materia
            if servicio.materia_id is not None:
                relacion = db.query(models.MateriasXCarreraXUsuario).filter(
                    models.MateriasXCarreraXUsuario.usuario_id == db_servicio.tutor_id,
                    models.MateriasXCarreraXUsuario.materia_id == servicio.materia_id,
                    models.MateriasXCarreraXUsuario.estado == True
                ).first()

                if not relacion:
                    raise HTTPException(
                        status_code=400,
                        detail="El tutor no tiene asignada esta materia. Debe asignarla primero."
                    )

                # Verificar que no exista otro servicio para esta nueva materia
                servicio_existente = db.query(models.ServicioTutoria).filter(
                    models.ServicioTutoria.tutor_id == db_servicio.tutor_id,
                    models.ServicioTutoria.materia_id == servicio.materia_id,
                    models.ServicioTutoria.id != id
                ).first()

                if servicio_existente:
                    raise HTTPException(
                        status_code=400,
                        detail="Ya existe un servicio para esta materia"
                    )

            # Actualizar campos
            if servicio.materia_id is not None:
                db_servicio.materia_id = servicio.materia_id
            if servicio.precio is not None:
                db_servicio.precio = servicio.precio
            if servicio.descripcion is not None:
                db_servicio.descripcion = servicio.descripcion
            if servicio.modalidad is not None:
                db_servicio.modalidad = servicio.modalidad
            if servicio.activo is not None:
                db_servicio.activo = servicio.activo

            db.commit()
            db.refresh(db_servicio)
            return db_servicio
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error updating servicio")
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating servicio: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def delete_servicio(self, db: Session, id: int):
        try:
            db_servicio = db.query(models.ServicioTutoria).filter(models.ServicioTutoria.id == id).first()
            if db_servicio is None:
                raise HTTPException(status_code=404, detail="Servicio not found")

            # Verificar si hay reservas asociadas a este servicio
            reservas = db.query(models.Reserva).filter(
                models.Reserva.servicio_id == id,
                models.Reserva.estado.in_(["pendiente", "confirmada"])
            ).first()

            if reservas:
                raise HTTPException(
                    status_code=400,
                    detail="No se puede eliminar el servicio porque tiene reservas pendientes o confirmadas"
                )

            # Hacer borrado lógico en lugar de físico (cambiar activo a False)
            db_servicio.activo = False
            db.commit()
            db.refresh(db_servicio)
            return True
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting servicio: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")