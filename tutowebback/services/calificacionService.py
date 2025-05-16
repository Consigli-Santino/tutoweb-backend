import os
import sys
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.models import models
from tutowebback.schemas import schemas
from tutowebback.services import notificacionService


class CalificacionService:
    def create_calificacion(self, db: Session, calificacion: schemas.CalificacionCreate, calificador_id: int):
        """
        Crea una nueva calificación y actualiza la puntuación promedio del tutor
        El calificador_id se pasa por separado para validación adicional
        """
        try:
            # Verificar si existe la reserva
            reserva = db.query(models.Reserva).filter(models.Reserva.id == calificacion.reserva_id).first()
            if not reserva:
                raise HTTPException(status_code=404, detail="Reserva not found")

            # Verificar que la reserva esté completada
            if reserva.estado != "completada":
                raise HTTPException(status_code=400, detail="La reserva debe estar completada para poder calificarla")

            # Verificar el pago
            pago = db.query(models.Pago).filter(
                models.Pago.reserva_id == calificacion.reserva_id,
                models.Pago.estado == "completado"
            ).first()
            
            if not pago:
                raise HTTPException(status_code=400, detail="Debe realizarse el pago antes de calificar")

            # Verificar que el usuario que califica sea el mismo que se especifica en calificador_id
            if calificacion.calificador_id != calificador_id:
                raise HTTPException(status_code=403, detail="No puedes crear calificaciones para otro usuario")

            # Verificar que el usuario que califica sea parte de la reserva
            if calificacion.calificador_id != reserva.estudiante_id:
                raise HTTPException(status_code=403, detail="Solo el estudiante puede calificar esta reserva")

            # Verificar que no exista ya una calificación para esta reserva
            existing_calificacion = db.query(models.Calificacion).filter(
                models.Calificacion.reserva_id == calificacion.reserva_id
            ).first()
            
            if existing_calificacion:
                raise HTTPException(status_code=400, detail="Esta reserva ya ha sido calificada")

            # Crear la calificación
            db_calificacion = models.Calificacion(
                reserva_id=calificacion.reserva_id,
                calificador_id=calificador_id,
                calificado_id=calificacion.calificado_id,
                puntuacion=calificacion.puntuacion,
                comentario=calificacion.comentario,
                fecha=datetime.utcnow()
            )

            db.add(db_calificacion)
            db.commit()
            db.refresh(db_calificacion)

            # Actualizar la puntuación promedio del tutor
            self._update_tutor_rating(db, calificacion.calificado_id)

            # Enviar notificación al tutor
            try:
                # Obtener información de la materia para la notificación
                servicio = db.query(models.ServicioTutoria).filter(
                    models.ServicioTutoria.id == reserva.servicio_id
                ).first()
                
                materia_nombre = "una materia"
                if servicio:
                    materia = db.query(models.Materia).filter(
                        models.Materia.id == servicio.materia_id
                    ).first()
                    if materia:
                        materia_nombre = materia.nombre

                # Crear notificación para el tutor
                notificacionService.crear_notificacion(
                    db=db,
                    usuario_id=calificacion.calificado_id,
                    titulo="Nueva calificación recibida",
                    mensaje=f"Has recibido una calificación de {calificacion.puntuacion} estrellas para tu tutoría de {materia_nombre}",
                    tipo="sistema",
                    reserva_id=reserva.id
                )
            except Exception as e:
                # No interrumpir el flujo si falla la notificación
                logging.error(f"Error creando notificación: {e}")

            return db_calificacion

        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error creating calificacion")
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating calificacion: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def _update_tutor_rating(self, db: Session, tutor_id: int):
        """
        Actualiza la puntuación promedio del tutor basado en todas sus calificaciones
        """
        try:
            # Obtener todas las calificaciones del tutor
            calificaciones = db.query(models.Calificacion).filter(
                models.Calificacion.calificado_id == tutor_id
            ).all()
            
            if not calificaciones:
                return

            # Calcular la puntuación promedio
            total_puntuacion = sum(c.puntuacion for c in calificaciones)
            cantidad_calificaciones = len(calificaciones)
            promedio = total_puntuacion / cantidad_calificaciones

            # Actualizar el usuario
            tutor = db.query(models.Usuario).filter(models.Usuario.id == tutor_id).first()
            if tutor:
                tutor.puntuacion_promedio = round(promedio, 2)
                tutor.cantidad_reseñas = cantidad_calificaciones
                db.commit()

        except Exception as e:
            logging.error(f"Error updating tutor rating: {e}")
            # No propagamos la excepción para no interrumpir el flujo principal

    def get_calificacion_by_reserva(self, db: Session, reserva_id: int):
        """
        Obtiene la calificación asociada a una reserva
        """
        return db.query(models.Calificacion).filter(
            models.Calificacion.reserva_id == reserva_id
        ).first()

    def get_calificaciones_by_tutor(self, db: Session, tutor_id: int):
        """
        Obtiene todas las calificaciones recibidas por un tutor
        """
        return db.query(models.Calificacion).options(
            joinedload(models.Calificacion.calificador),
            joinedload(models.Calificacion.reserva)
        ).filter(
            models.Calificacion.calificado_id == tutor_id
        ).all()

    def get_calificaciones_by_estudiante(self, db: Session, estudiante_id: int):
        """
        Obtiene todas las calificaciones realizadas por un estudiante
        """
        return db.query(models.Calificacion).options(
            joinedload(models.Calificacion.calificado),
            joinedload(models.Calificacion.reserva)
        ).filter(
            models.Calificacion.calificador_id == estudiante_id
        ).all()

    def get_calificaciones_for_estudiante_reservas(self, db: Session, estudiante_id: int):
        """
        Obtiene todas las calificaciones hechas por un estudiante, 
        organizadas por reserva_id para fácil acceso
        """
        try:
            # Primero obtenemos todas las reservas del estudiante
            reservas = db.query(models.Reserva).filter(
                models.Reserva.estudiante_id == estudiante_id
            ).all()
            
            if not reservas:
                return {}
                
            # Obtenemos los IDs de las reservas
            reserva_ids = [reserva.id for reserva in reservas]
            
            # Ahora obtenemos todas las calificaciones asociadas a esas reservas
            calificaciones = db.query(models.Calificacion).filter(
                models.Calificacion.reserva_id.in_(reserva_ids)
            ).all()
            
            # Organizamos las calificaciones por reserva_id para fácil acceso
            calificaciones_dict = {calificacion.reserva_id: calificacion for calificacion in calificaciones}
            
            return calificaciones_dict
            
        except Exception as e:
            logging.error(f"Error getting calificaciones for estudiante reservas: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
 
