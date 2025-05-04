import os
import sys
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging
from datetime import datetime, date, time, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.models import models
from tutowebback.schemas import schemas
class ReservaService:
    def create_reserva(self, db: Session, reserva: schemas.ReservaCreate):
        try:
            # Verificar si existe el estudiante
            estudiante = db.query(models.Usuario).filter(models.Usuario.id == reserva.estudiante_id).first()
            if not estudiante:
                raise HTTPException(status_code=404, detail="Estudiante not found")

            # Verificar si existe el servicio de tutoría
            servicio = db.query(models.ServicioTutoria).filter(models.ServicioTutoria.id == reserva.servicio_id).first()
            if not servicio:
                raise HTTPException(status_code=404, detail="Servicio de tutoría not found")

            # Verificar que el servicio esté activo
            if not servicio.activo:
                raise HTTPException(status_code=400, detail="El servicio de tutoría no está activo")

            # Obtener el día de la semana de la fecha seleccionada (1=lunes, 7=domingo)
            dia_semana = reserva.fecha.isoweekday()

            # Verificar que el tutor tenga disponibilidad para ese día y horario
            disponibilidad = db.query(models.Disponibilidad).filter(
                models.Disponibilidad.tutor_id == servicio.tutor_id,
                models.Disponibilidad.dia_semana == dia_semana,
                models.Disponibilidad.hora_inicio <= reserva.hora_inicio,
                models.Disponibilidad.hora_fin >= reserva.hora_fin
            ).first()

            if not disponibilidad:
                raise HTTPException(
                    status_code=400,
                    detail="El tutor no tiene disponibilidad para el día y horario seleccionados"
                )

            # Verificar que no exista ya una reserva para ese tutor, en esa fecha y con horario solapado
            reserva_existente = db.query(models.Reserva).filter(
                models.Reserva.servicio_id == reserva.servicio_id,
                models.Reserva.fecha == reserva.fecha,
                models.Reserva.estado.in_(["pendiente", "confirmada"]),
                # Verificar superposición de horarios
                ((models.Reserva.hora_inicio <= reserva.hora_inicio) &
                 (models.Reserva.hora_fin > reserva.hora_inicio)) |
                ((models.Reserva.hora_inicio < reserva.hora_fin) &
                 (models.Reserva.hora_fin >= reserva.hora_fin)) |
                ((models.Reserva.hora_inicio >= reserva.hora_inicio) &
                 (models.Reserva.hora_fin <= reserva.hora_fin))
            ).first()

            if reserva_existente:
                raise HTTPException(
                    status_code=400,
                    detail="Ya existe una reserva para este servicio en la fecha y horario seleccionados"
                )

            # Crear la reserva
            db_reserva = models.Reserva(
                estudiante_id=reserva.estudiante_id,
                servicio_id=reserva.servicio_id,
                fecha=reserva.fecha,
                hora_inicio=reserva.hora_inicio,
                hora_fin=reserva.hora_fin,
                notas=reserva.notas,
                estado=reserva.estado
            )

            db.add(db_reserva)
            db.commit()
            db.refresh(db_reserva)
            return db_reserva
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error creating reserva")
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating reserva: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def get_reserva(self, db: Session, id: int):
        db_reserva = db.query(models.Reserva).filter(models.Reserva.id == id).first()
        if db_reserva is None:
            raise HTTPException(status_code=404, detail="Reserva not found")
        return db_reserva

    def get_reservas_by_estudiante(self, db: Session, estudiante_id: int):
        return db.query(models.Reserva).filter(models.Reserva.estudiante_id == estudiante_id).all()

    def get_reservas_by_tutor(self, db: Session, tutor_id: int):
        # Obtener los servicios de tutoría del tutor
        servicios = db.query(models.ServicioTutoria).filter(
            models.ServicioTutoria.tutor_id == tutor_id
        ).all()

        if not servicios:
            return []

        # Obtener los IDs de los servicios
        servicio_ids = [servicio.id for servicio in servicios]

        # Obtener las reservas para esos servicios
        return db.query(models.Reserva).filter(
            models.Reserva.servicio_id.in_(servicio_ids)
        ).all()

    def edit_reserva(self, db: Session, id: int, reserva: schemas.ReservaUpdate):
        try:
            db_reserva = db.query(models.Reserva).filter(models.Reserva.id == id).first()
            if db_reserva is None:
                raise HTTPException(status_code=404, detail="Reserva not found")

            # Si se cambia la fecha u horario, verificar disponibilidad y conflictos
            if reserva.fecha is not None or reserva.hora_inicio is not None or reserva.hora_fin is not None:
                # Obtener el servicio para saber el tutor
                servicio = db.query(models.ServicioTutoria).filter(
                    models.ServicioTutoria.id == db_reserva.servicio_id
                ).first()

                # Determinar la nueva fecha y horarios
                nueva_fecha = reserva.fecha if reserva.fecha is not None else db_reserva.fecha
                nueva_hora_inicio = reserva.hora_inicio if reserva.hora_inicio is not None else db_reserva.hora_inicio
                nueva_hora_fin = reserva.hora_fin if reserva.hora_fin is not None else db_reserva.hora_fin

                # Verificar que la hora de inicio sea anterior a la hora de fin
                if nueva_hora_inicio >= nueva_hora_fin:
                    raise HTTPException(
                        status_code=400,
                        detail="La hora de inicio debe ser anterior a la hora de fin"
                    )

                # Obtener el día de la semana de la nueva fecha
                dia_semana = nueva_fecha.isoweekday()

                # Verificar disponibilidad del tutor
                disponibilidad = db.query(models.Disponibilidad).filter(
                    models.Disponibilidad.tutor_id == servicio.tutor_id,
                    models.Disponibilidad.dia_semana == dia_semana,
                    models.Disponibilidad.hora_inicio <= nueva_hora_inicio,
                    models.Disponibilidad.hora_fin >= nueva_hora_fin
                ).first()

                if not disponibilidad:
                    raise HTTPException(
                        status_code=400,
                        detail="El tutor no tiene disponibilidad para el día y horario seleccionados"
                    )

                # Verificar conflictos con otras reservas
                reserva_existente = db.query(models.Reserva).filter(
                    models.Reserva.servicio_id == db_reserva.servicio_id,
                    models.Reserva.fecha == nueva_fecha,
                    models.Reserva.id != id,  # Excluir la reserva actual
                    models.Reserva.estado.in_(["pendiente", "confirmada"]),
                    # Verificar superposición de horarios
                    ((models.Reserva.hora_inicio <= nueva_hora_inicio) &
                     (models.Reserva.hora_fin > nueva_hora_inicio)) |
                    ((models.Reserva.hora_inicio < nueva_hora_fin) &
                     (models.Reserva.hora_fin >= nueva_hora_fin)) |
                    ((models.Reserva.hora_inicio >= nueva_hora_inicio) &
                     (models.Reserva.hora_fin <= nueva_hora_fin))
                ).first()

                if reserva_existente:
                    raise HTTPException(
                        status_code=400,
                        detail="Ya existe una reserva para este servicio en la fecha y horario seleccionados"
                    )

            # Actualizar campos
            if reserva.fecha is not None:
                db_reserva.fecha = reserva.fecha
            if reserva.hora_inicio is not None:
                db_reserva.hora_inicio = reserva.hora_inicio
            if reserva.hora_fin is not None:
                db_reserva.hora_fin = reserva.hora_fin
            if reserva.notas is not None:
                db_reserva.notas = reserva.notas
            if reserva.estado is not None:
                db_reserva.estado = reserva.estado

            db.commit()
            db.refresh(db_reserva)
            return db_reserva
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error updating reserva")
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating reserva: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def delete_reserva(self, db: Session, id: int):
        try:
            db_reserva = db.query(models.Reserva).filter(models.Reserva.id == id).first()
            if db_reserva is None:
                raise HTTPException(status_code=404, detail="Reserva not found")

            db.delete(db_reserva)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting reserva: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def get_horarios_disponibles(self, db: Session, servicio_id: int, fecha: date):
        """
        Obtiene los horarios disponibles para un servicio y fecha específicos
        basándose en las disponibilidades del tutor y las reservas existentes
        """
        try:
            # Obtener el servicio y el tutor asociado
            servicio = db.query(models.ServicioTutoria).filter(
                models.ServicioTutoria.id == servicio_id
            ).first()

            if not servicio:
                raise HTTPException(status_code=404, detail="Servicio de tutoría not found")

            # Obtener el día de la semana de la fecha seleccionada
            dia_semana = fecha.isoweekday()

            # Obtener todas las disponibilidades del tutor para ese día
            disponibilidades = db.query(models.Disponibilidad).filter(
                models.Disponibilidad.tutor_id == servicio.tutor_id,
                models.Disponibilidad.dia_semana == dia_semana
            ).all()

            if not disponibilidades:
                return []  # No hay disponibilidades para ese día

            # Obtener todas las reservas para ese servicio en esa fecha
            reservas = db.query(models.Reserva).filter(
                models.Reserva.servicio_id == servicio_id,
                models.Reserva.fecha == fecha,
                models.Reserva.estado.in_(["pendiente", "confirmada"])
            ).all()

            # Generar slots de tiempo a partir de las disponibilidades
            slots_disponibles = []
            for disp in disponibilidades:
                # Generar slots de 1 hora
                hora_actual = disp.hora_inicio
                while hora_actual < disp.hora_fin:
                    # Calcular hora fin del slot (1 hora después o fin de disponibilidad)
                    hora_fin_slot = (datetime.combine(date.today(), hora_actual) + timedelta(hours=1)).time()
                    if hora_fin_slot > disp.hora_fin:
                        hora_fin_slot = disp.hora_fin

                    # Verificar si el slot está ocupado por alguna reserva
                    ocupado = False
                    for reserva in reservas:
                        # Verificar superposición
                        if (hora_actual < reserva.hora_fin and hora_fin_slot > reserva.hora_inicio):
                            ocupado = True
                            break

                    if not ocupado:
                        slots_disponibles.append({
                            "hora_inicio": hora_actual,
                            "hora_fin": hora_fin_slot
                        })

                    # Avanzar a la siguiente hora
                    hora_actual = hora_fin_slot

            return slots_disponibles
        except Exception as e:
            logging.error(f"Error getting horarios disponibles: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")