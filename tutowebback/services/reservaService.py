import os
import sys
from sqlalchemy.orm import Session, joinedload, aliased
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging
from datetime import datetime, date, time, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.models import models
from tutowebback.schemas import schemas
from tutowebback.services import notificacionService


class ReservaService:
    def create_reserva(self, db: Session, reserva: schemas.ReservaCreate):
        """
        Crea una nueva reserva y envía notificaciones
        """
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

            # Enviar notificación al tutor
            try:
                # Obtener información de la materia para la notificación
                materia_info = db.query(models.Materia).join(
                    models.ServicioTutoria, models.ServicioTutoria.materia_id == models.Materia.id
                ).filter(
                    models.ServicioTutoria.id == reserva.servicio_id
                ).first()

                materia_nombre = materia_info.nombre if materia_info else "una materia"

                # Crear notificación para el tutor
                notificacionService.crear_notificacion(
                    db=db,
                    usuario_id=servicio.tutor_id,
                    titulo="Nueva reserva de tutoría",
                    mensaje=f"Tienes una nueva reserva para {materia_nombre} el {reserva.fecha} a las {reserva.hora_inicio}",
                    tipo="reserva",
                    reserva_id=db_reserva.id
                )
            except Exception as e:
                # No interrumpir el flujo si falla la notificación
                logging.error(f"Error creando notificación: {e}")

            return db_reserva

        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error creating reserva")
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating reserva: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def get_reserva(self, db: Session, id: int):
        """
        Obtiene una reserva por su ID
        """
        db_reserva = db.query(models.Reserva).filter(models.Reserva.id == id).first()
        if db_reserva is None:
            raise HTTPException(status_code=404, detail="Reserva not found")
        return db_reserva

    def get_reserva_detallada(self, db: Session, id: int):
        """
        Obtiene una reserva con detalles completos (servicio, materia, tutor)
        """
        db_reserva = db.query(models.Reserva).filter(models.Reserva.id == id).first()
        if db_reserva is None:
            raise HTTPException(status_code=404, detail="Reserva not found")

        # Obtener información adicional
        reserva_dict = db_reserva.to_dict_reserva()

        # Obtener servicio asociado
        servicio = db.query(models.ServicioTutoria).filter(
            models.ServicioTutoria.id == db_reserva.servicio_id
        ).options(
            joinedload(models.ServicioTutoria.materia),
            joinedload(models.ServicioTutoria.tutor)
        ).first()

        # Añadir información del servicio
        if servicio:
            reserva_dict["servicio"] = servicio.to_dict_servicio_tutoria()

            # Añadir información del tutor
            if hasattr(servicio, 'tutor') and servicio.tutor:
                reserva_dict["tutor"] = servicio.tutor.to_dict_usuario()

            # Añadir información de la materia
            if hasattr(servicio, 'materia') and servicio.materia:
                reserva_dict["materia"] = servicio.materia.to_dict_materia()

        return reserva_dict

    def get_reservas_by_estudiante(self, db: Session, estudiante_id: int):
        """
        Obtiene todas las reservas de un estudiante
        """
        return db.query(models.Reserva).filter(models.Reserva.estudiante_id == estudiante_id).all()


    def get_reservas_by_estudiante_detalladas(
        self,
        db: Session,
        estudiante_id: int,
        fecha_desde: date = None,
        fecha_hasta: date = None
    ):
        """
        Obtiene todas las reservas de un estudiante con detalles completos y filtrado por fechas si se proveen.
        """
        query = db.query(models.Reserva).filter(models.Reserva.estudiante_id == estudiante_id)
        if fecha_desde:
            query = query.filter(models.Reserva.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.filter(models.Reserva.fecha <= fecha_hasta)

        db_reservas = query.all()
        reserva_responses = []

        for reserva in db_reservas:
            reserva_dict = reserva.to_dict_reserva()

            servicio = db.query(models.ServicioTutoria).filter(
                models.ServicioTutoria.id == reserva.servicio_id
            ).options(
                joinedload(models.ServicioTutoria.materia),
                joinedload(models.ServicioTutoria.tutor)
            ).first()

            if servicio:
                reserva_dict["servicio"] = servicio.to_dict_servicio_tutoria()
                if hasattr(servicio, 'tutor') and servicio.tutor:
                    reserva_dict["tutor"] = servicio.tutor.to_dict_usuario()
                if hasattr(servicio, 'materia') and servicio.materia:
                    reserva_dict["materia"] = servicio.materia.to_dict_materia()

            reserva_responses.append(reserva_dict)

        return reserva_responses

    def get_reservas_by_tutor(self, db: Session, tutor_id: int):
        """
        Obtiene todas las reservas que corresponden a un tutor
        """
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


    def get_reservas_by_tutor_detalladas(
        self,
        db: Session,
        tutor_id: int,
        fecha_desde: date = None,
        fecha_hasta: date = None
    ):
        """
        Obtiene todas las reservas de un tutor con detalles completos y filtrado por fechas si se proveen.
        """
        # Obtener los servicios del tutor
        servicios = db.query(models.ServicioTutoria).filter(models.ServicioTutoria.tutor_id == tutor_id).all()
        servicio_ids = [servicio.id for servicio in servicios]

        query = db.query(models.Reserva).filter(models.Reserva.servicio_id.in_(servicio_ids))
        if fecha_desde:
            query = query.filter(models.Reserva.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.filter(models.Reserva.fecha <= fecha_hasta)

        db_reservas = query.all()
        reserva_responses = []

        for reserva in db_reservas:
            reserva_dict = reserva.to_dict_reserva()

            servicio = db.query(models.ServicioTutoria).filter(
                models.ServicioTutoria.id == reserva.servicio_id
            ).options(
                joinedload(models.ServicioTutoria.materia),
                joinedload(models.ServicioTutoria.tutor)
            ).first()

            if servicio:
                reserva_dict["servicio"] = servicio.to_dict_servicio_tutoria()
                if hasattr(servicio, 'tutor') and servicio.tutor:
                    reserva_dict["tutor"] = servicio.tutor.to_dict_usuario()
                if hasattr(servicio, 'materia') and servicio.materia:
                    reserva_dict["materia"] = servicio.materia.to_dict_materia()

            reserva_responses.append(reserva_dict)

        return reserva_responses

    def check_reservas_by_fecha_tutor(self, db: Session, tutor_id: int, fecha: date):
        """
        Obtiene reservas de un tutor para una fecha específica
        """
        # Obtener servicios del tutor
        servicios = db.query(models.ServicioTutoria).filter(
            models.ServicioTutoria.tutor_id == tutor_id,
            models.ServicioTutoria.activo == True
        ).all()

        if not servicios:
            return []

        # Obtener IDs de servicios
        servicio_ids = [servicio.id for servicio in servicios]

        # Obtener todas las reservas para los servicios del tutor en la fecha dada
        reservas = db.query(models.Reserva).filter(
            models.Reserva.servicio_id.in_(servicio_ids),
            models.Reserva.fecha == fecha,
            models.Reserva.estado.in_(["pendiente", "confirmada"])
        ).all()

        return reservas

    def edit_reserva(self, db: Session, id: int, reserva_update: schemas.ReservaUpdate, current_user_id: int,
                     is_admin: bool = False):
        """
        Edita una reserva existente y gestiona notificaciones para cada cambio
        """
        try:
            db_reserva = self.get_reserva(db, id)

            # Obtener información inicial para comparar con los cambios
            old_estado = db_reserva.estado
            old_fecha = db_reserva.fecha
            old_hora_inicio = db_reserva.hora_inicio
            old_hora_fin = db_reserva.hora_fin

            # Obtener el servicio para saber el tutor asociado
            servicio = db.query(models.ServicioTutoria).filter(
                models.ServicioTutoria.id == db_reserva.servicio_id
            ).first()

            if not servicio:
                raise HTTPException(status_code=404, detail="Servicio de tutoría no encontrado")

            # Verificar permisos según usuario
            is_estudiante = db_reserva.estudiante_id == current_user_id
            is_tutor = servicio.tutor_id == current_user_id

            # Aplicar restricciones y validaciones según tipo de usuario
            self._apply_reserva_permissions(
                db_reserva,
                reserva_update,
                is_estudiante,
                is_tutor,
                is_admin
            )

            # Si se cambia la fecha u horario, verificar disponibilidad y conflictos
            if self._requires_availability_check(reserva_update, db_reserva):
                self._validate_update_availability(
                    db,
                    db_reserva,
                    reserva_update,
                    servicio.tutor_id
                )

            # Actualizar campos
            self._update_reserva_fields(db_reserva, reserva_update)

            # Si la reserva cambia a confirmada y es virtual, generar sala automáticamente
            if (reserva_update.estado == "confirmada" and old_estado != "confirmada" and
                    servicio.modalidad in ["virtual", "ambas"] and not db_reserva.sala_virtual):
                url_sala = self._generar_sala_jitsi(db_reserva, servicio)

                # Si se está estableciendo la URL manualmente, respetarla
                if reserva_update.sala_virtual and reserva_update.sala_virtual != db_reserva.sala_virtual:
                    db_reserva.sala_virtual = reserva_update.sala_virtual

            # Guardar cambios
            db.commit()
            db.refresh(db_reserva)

            # Gestionar notificaciones según los cambios realizados
            self._send_update_notifications(
                db,
                db_reserva,
                reserva_update,
                is_estudiante,
                is_tutor,
                old_estado
            )

            return db_reserva

        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Error updating reserva")
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating reserva: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
    def _apply_reserva_permissions(self, reserva, update, is_estudiante, is_tutor, is_admin):
        """
        Aplica las restricciones de permisos según el tipo de usuario
        """
        if not (is_estudiante or is_tutor or is_admin):
            raise HTTPException(
                status_code=403,
                detail="No estás autorizado para editar esta reserva"
            )

        # Si es estudiante y no es admin, aplicar restricciones
        if is_estudiante and not is_admin:
            # Comprobar que no esté cancelando muy cerca de la hora de la tutoría
            if update.estado and update.estado == "cancelada":
                # Verificar límite de tiempo (2 horas antes)
                reserva_datetime = datetime.combine(reserva.fecha, reserva.hora_inicio)
                now = datetime.now()
                limite_cancelacion = timedelta(hours=2)

                if now > (reserva_datetime - limite_cancelacion):
                    raise HTTPException(
                        status_code=403,
                        detail="No se puede cancelar con menos de 2 horas de anticipación"
                    )

            # Estudiantes solo pueden cancelar, no cambiar estado a confirmada o completada
            if update.estado and update.estado not in ["cancelada"]:
                raise HTTPException(
                    status_code=403,
                    detail="Como estudiante solo puedes cancelar la reserva"
                )

        # Si es tutor y no es admin, aplicar restricciones
        if is_tutor and not is_admin:
            # Tutores pueden confirmar, completar o cancelar, pero no cambiar fecha
            if update.fecha:
                raise HTTPException(
                    status_code=403,
                    detail="Como tutor no puedes cambiar la fecha de la reserva"
                )
    def _requires_availability_check(self, update, reserva):
        """
        Determina si es necesario verificar disponibilidad por los cambios
        """
        return (update.fecha is not None or
                update.hora_inicio is not None or
                update.hora_fin is not None)

    def _validate_update_availability(self, db, reserva, update, tutor_id):
        """
        Valida disponibilidad y conflictos para cambios de horario en la reserva
        """
        # Determinar la nueva fecha y horarios
        nueva_fecha = update.fecha if update.fecha is not None else reserva.fecha
        nueva_hora_inicio = update.hora_inicio if update.hora_inicio is not None else reserva.hora_inicio
        nueva_hora_fin = update.hora_fin if update.hora_fin is not None else reserva.hora_fin

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
            models.Disponibilidad.tutor_id == tutor_id,
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
            models.Reserva.servicio_id == reserva.servicio_id,
            models.Reserva.fecha == nueva_fecha,
            models.Reserva.id != reserva.id,  # Excluir la reserva actual
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

    def _update_reserva_fields(self, reserva, update):
        """
        Actualiza los campos de la reserva con los nuevos valores
        """
        if update.fecha is not None:
            reserva.fecha = update.fecha
        if update.hora_inicio is not None:
            reserva.hora_inicio = update.hora_inicio
        if update.hora_fin is not None:
            reserva.hora_fin = update.hora_fin
        if update.notas is not None:
            reserva.notas = update.notas
        if update.estado is not None:
            reserva.estado = update.estado

    def _send_update_notifications(self, db, reserva, update, is_estudiante, is_tutor, old_estado):
        """
        Envía notificaciones según el tipo de cambio en la reserva
        """
        try:
            # Obtener servicio y materia para las notificaciones
            servicio = db.query(models.ServicioTutoria).filter(
                models.ServicioTutoria.id == reserva.servicio_id
            ).options(
                joinedload(models.ServicioTutoria.materia)
            ).first()

            if not servicio or not hasattr(servicio, 'materia') or not servicio.materia:
                materia_nombre = "una materia"
            else:
                materia_nombre = servicio.materia.nombre

            # Construir mensaje base
            mensaje_base = f"Tutoría para {materia_nombre} el {reserva.fecha} a las {reserva.hora_inicio}"

            # Añadir información sobre la sala virtual si existe
            info_sala = ""
            if reserva.sala_virtual and servicio.modalidad in ["virtual", "ambas"]:
                info_sala = f"\n\nPara acceder a la sala virtual: {reserva.sala_virtual}"

            # Si se canceló la reserva y es un estudiante, notificar al tutor
            if is_estudiante and update.estado == "cancelada":
                notificacionService.crear_notificacion(
                    db=db,
                    usuario_id=servicio.tutor_id,
                    titulo="Reserva cancelada",
                    mensaje=f"Un estudiante ha cancelado su {mensaje_base}",
                    tipo="reserva",
                    reserva_id=reserva.id
                )

            # Si el tutor cambia el estado, notificar al estudiante
            elif is_tutor and update.estado and old_estado != update.estado:
                estado_texto = {
                    "confirmada": "confirmado",
                    "completada": "marcado como completada",
                    "cancelada": "cancelado"
                }.get(update.estado, update.estado)

                mensaje = f"Tu reserva para {mensaje_base} ha sido {estado_texto}"

                # Añadir información de la sala virtual si la reserva fue confirmada
                if update.estado == "confirmada" and reserva.sala_virtual and servicio.modalidad in ["virtual",
                                                                                                     "ambas"]:
                    mensaje += info_sala

                notificacionService.crear_notificacion(
                    db=db,
                    usuario_id=reserva.estudiante_id,
                    titulo=f"Reserva {estado_texto}",
                    mensaje=mensaje,
                    tipo="reserva",
                    reserva_id=reserva.id
                )

        except Exception as e:
            logging.error(f"Error creando notificación de cambio: {e}")

    def _generar_sala_jitsi(self, db_reserva, servicio):
        """
        Genera una sala de Jitsi Meet para una reserva virtual
        """
        try:
            if servicio.modalidad in ["virtual", "ambas"]:
                # Generar un nombre único para la sala usando ID de reserva y fecha
                nombre_sala = f"TutoWeb_{db_reserva.id}_{db_reserva.fecha.strftime('%Y%m%d')}"
                # Limpiar caracteres no permitidos
                nombre_sala = ''.join(c if c.isalnum() or c == '_' else '' for c in nombre_sala)

                # Crear URL de la sala
                url_sala = f"https://meet.jit.si/{nombre_sala}"

                # Actualizar la reserva con la URL
                db_reserva.sala_virtual = url_sala

                return url_sala
            return None
        except Exception as e:
            logging.error(f"Error generando sala Jitsi: {e}")
            return None

    def delete_reserva(self, db: Session, id: int):
        """
        Elimina una reserva (eliminación física)
        """
        try:
            db_reserva = self.get_reserva(db, id)
            db.delete(db_reserva)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting reserva: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
    def get_all_reservas_detalladas(
        self,
        db: Session,
        fecha_desde: date = None,
        fecha_hasta: date = None
    ):
        """
        Obtiene todas las reservas del sistema con información detallada (para admin)
        Incluye información del servicio, materia, tutor y estudiante
        """
        try:
            query = db.query(models.Reserva)
            if fecha_desde:
                query = query.filter(models.Reserva.fecha >= fecha_desde)
            if fecha_hasta:
                query = query.filter(models.Reserva.fecha <= fecha_hasta)
            reservas = query.all()

            sorted_reservas = sorted(reservas, key=lambda r: (
                0 if r.estado == "pendiente" else
                1 if r.estado == "confirmada" else
                2 if r.estado == "completada" else 3,
                r.fecha
            ))

            reserva_responses = []

            for reserva in sorted_reservas:
                # Datos básicos de la reserva
                reserva_dict = reserva.to_dict_reserva()

                # Obtener servicio asociado con materia y tutor
                servicio = db.query(models.ServicioTutoria).filter(
                    models.ServicioTutoria.id == reserva.servicio_id
                ).options(
                    joinedload(models.ServicioTutoria.materia),
                    joinedload(models.ServicioTutoria.tutor)
                ).first()

                # Añadir información del servicio
                if servicio:
                    reserva_dict["servicio"] = servicio.to_dict_servicio_tutoria()

                    # Añadir información del tutor
                    if hasattr(servicio, 'tutor') and servicio.tutor:
                        reserva_dict["tutor"] = servicio.tutor.to_dict_usuario()

                    # Añadir información de la materia
                    if hasattr(servicio, 'materia') and servicio.materia:
                        reserva_dict["materia"] = servicio.materia.to_dict_materia()

                # Obtener información del estudiante
                estudiante = db.query(models.Usuario).filter(
                    models.Usuario.id == reserva.estudiante_id
                ).first()

                if estudiante:
                    reserva_dict["estudiante"] = estudiante.to_dict_usuario()

                # Obtener información de pago (si existe)
                pago = db.query(models.Pago).filter(
                    models.Pago.reserva_id == reserva.id
                ).order_by(models.Pago.fecha_creacion.desc()).first()

                if pago:
                    reserva_dict["pago"] = pago.to_dict_pago()

                # Obtener calificación (si existe)
                calificacion = db.query(models.Calificacion).filter(
                    models.Calificacion.reserva_id == reserva.id
                ).first()

                if calificacion:
                    reserva_dict["calificacion"] = calificacion.to_dict_calificacion()

                reserva_responses.append(reserva_dict)

            return reserva_responses

        except Exception as e:
            logging.error(f"Error obteniendo todas las reservas detalladas: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")