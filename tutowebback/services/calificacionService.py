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
 
    def get_calificaciones_by_date_range(
        self,
        db: Session,
        fecha_desde: datetime.date = None,
        fecha_hasta: datetime.date = None,
        usuario_id: int = None
    ):
        """
        Obtiene calificaciones filtradas por rango de fechas y opcionalmente por usuario.
        Solo incluye calificaciones de reservas completadas.
        """
        try:
            from datetime import datetime, timedelta, time

            # Consulta base con joins para obtener toda la información necesaria
            query = db.query(models.Calificacion).options(
                joinedload(models.Calificacion.calificador),
                joinedload(models.Calificacion.calificado),
                joinedload(models.Calificacion.reserva).joinedload(models.Reserva.servicio).joinedload(models.ServicioTutoria.materia),
                joinedload(models.Calificacion.reserva).joinedload(models.Reserva.estudiante),
            ).join(
                models.Reserva, models.Calificacion.reserva_id == models.Reserva.id
            ).filter(
                models.Reserva.estado == "completada"
            )

            # Aplicar filtro de fechas si se proporcionan
            if fecha_desde:
                query = query.filter(models.Calificacion.fecha >= fecha_desde)
            else:
                # Por defecto, últimos 60 días
                fecha_desde_default = datetime.utcnow() - timedelta(days=60)
                query = query.filter(models.Calificacion.fecha >= fecha_desde_default)

            if fecha_hasta:
                # Incluir todo el día hasta las 23:59:59
                fecha_hasta_end = datetime.combine(fecha_hasta, time(23, 59, 59))
                query = query.filter(models.Calificacion.fecha <= fecha_hasta_end)

            # Filtro opcional por usuario (puede ser calificador o calificado)
            if usuario_id:
                query = query.filter(
                    (models.Calificacion.calificador_id == usuario_id) |
                    (models.Calificacion.calificado_id == usuario_id)
                )

            # Ordenar por fecha descendente (más recientes primero)
            calificaciones = query.order_by(models.Calificacion.fecha.desc()).all()

            return calificaciones

        except Exception as e:
            logging.error(f"Error getting calificaciones by date range: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")        
    def get_calificaciones_by_date_range_formatted(
        self,
        db: Session,
        fecha_desde_str: str = None,
        fecha_hasta_str: str = None,
        usuario_id: int = None
    ):
        """
        Obtiene calificaciones filtradas y formateadas para la respuesta.
        Maneja conversión de fechas y validaciones.
        """
        try:
            from datetime import datetime

            # Convertir strings a objetos date si se proporcionan
            fecha_desde_obj = None
            fecha_hasta_obj = None

            if fecha_desde_str:
                try:
                    fecha_desde_obj = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date()
                except ValueError:
                    raise HTTPException(status_code=400, detail="Formato de fecha_desde incorrecto. Use YYYY-MM-DD")

            if fecha_hasta_str:
                try:
                    fecha_hasta_obj = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date()
                except ValueError:
                    raise HTTPException(status_code=400, detail="Formato de fecha_hasta incorrecto. Use YYYY-MM-DD")

            # Validar que fecha_desde sea anterior a fecha_hasta
            if fecha_desde_obj and fecha_hasta_obj and fecha_desde_obj > fecha_hasta_obj:
                raise HTTPException(status_code=400, detail="La fecha_desde debe ser anterior a fecha_hasta")

            # Obtener calificaciones usando el método base
            db_calificaciones = self.get_calificaciones_by_date_range(db, fecha_desde_obj, fecha_hasta_obj, usuario_id)

            # Formatear respuesta con información detallada
            calificaciones_response = []
            for calificacion in db_calificaciones:
                calificacion_dict = {
                    "id": calificacion.id,
                    "puntuacion": calificacion.puntuacion,
                    "comentario": calificacion.comentario,
                    "fecha": calificacion.fecha.isoformat() if calificacion.fecha else None,
                    "reserva_id": calificacion.reserva_id,

                    # Información del calificador (estudiante)
                    "calificador": {
                        "id": calificacion.calificador.id,
                        "nombre": calificacion.calificador.nombre,
                        "apellido": calificacion.calificador.apellido,
                        "email": calificacion.calificador.email
                    } if calificacion.calificador else None,

                    # Información del calificado (tutor)
                    "calificado": {
                        "id": calificacion.calificado.id,
                        "nombre": calificacion.calificado.nombre,
                        "apellido": calificacion.calificado.apellido,
                        "email": calificacion.calificado.email,
                        "puntuacion_promedio": float(calificacion.calificado.puntuacion_promedio) if calificacion.calificado.puntuacion_promedio else 0,
                        "cantidad_reseñas": calificacion.calificado.cantidad_reseñas
                    } if calificacion.calificado else None,

                    # Información de la reserva y materia
                    "reserva": {
                        "fecha": calificacion.reserva.fecha.isoformat() if calificacion.reserva and calificacion.reserva.fecha else None,
                        "hora_inicio": calificacion.reserva.hora_inicio.isoformat() if calificacion.reserva and calificacion.reserva.hora_inicio else None,
                        "hora_fin": calificacion.reserva.hora_fin.isoformat() if calificacion.reserva and calificacion.reserva.hora_fin else None,
                        "materia": {
                            "id": calificacion.reserva.servicio.materia.id,
                            "nombre": calificacion.reserva.servicio.materia.nombre,
                            "carrera_id": calificacion.reserva.servicio.materia.carrera_id
                        } if (calificacion.reserva and calificacion.reserva.servicio and calificacion.reserva.servicio.materia) else None
                    } if calificacion.reserva else None
                }

                calificaciones_response.append(calificacion_dict)

            return calificaciones_response

        except Exception as e:
            logging.error(f"Error getting formatted calificaciones by date range: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")