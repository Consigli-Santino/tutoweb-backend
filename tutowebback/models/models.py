from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, DateTime, Text, Date, Time, CheckConstraint, \
    UniqueConstraint, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date, time

Base = declarative_base()


class Rol(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)

    # Relationships
    usuarios = relationship("Usuario", back_populates="rol")

    def to_dict_rol(self):
        return {
            "id": self.id,
            "nombre": self.nombre
        }


class Carrera(Base):
    __tablename__ = 'carreras'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    facultad = Column(String(100), default='Universidad Tecnológica Nacional')

    # Relationships
    materias = relationship("Materia", back_populates="carrera")
    usuarios = relationship("CarreraUsuario", back_populates="carrera")

    def to_dict_carrera(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "facultad": self.facultad
        }


class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
    puntuacion_promedio = Column(Numeric(3, 2), default=0)
    cantidad_reseñas = Column(Integer, default=0)
    foto_perfil = Column(String(255), nullable=True)
    # Campo para relación con rol (manteniéndolo como ya lo generamos)
    id_rol = Column(Integer, ForeignKey('roles.id'), nullable=True)

    # Relationships
    rol = relationship("Rol", back_populates="usuarios")
    carreras = relationship("CarreraUsuario", back_populates="usuario")
    servicios_tutoria = relationship("ServicioTutoria", back_populates="tutor")
    disponibilidad = relationship("Disponibilidad", back_populates="tutor")
    reservas_estudiante = relationship("Reserva", foreign_keys="Reserva.estudiante_id", back_populates="estudiante")
    calificaciones_dadas = relationship("Calificacion", foreign_keys="Calificacion.calificador_id",
                                        back_populates="calificador")
    calificaciones_recibidas = relationship("Calificacion", foreign_keys="Calificacion.calificado_id",
                                            back_populates="calificado")
    notificaciones = relationship("Notificacion", back_populates="usuario")
    dispositivos = relationship("DispositivoUsuario", back_populates="usuario")

    def to_dict_usuario(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "puntuacion_promedio": float(self.puntuacion_promedio) if self.puntuacion_promedio else 0,
            "cantidad_reseñas": self.cantidad_reseñas,
            "foto_perfil": self.foto_perfil,
            "rol": {
                "id": self.rol.id,
                "nombre": self.rol.nombre
            },
            "carreras": [
                {
                    "id": carrera_usuario.carrera.id,
                    "nombre": carrera_usuario.carrera.nombre
                }
                for carrera_usuario in self.carreras
            ] if self.carreras else []
        }


class CarreraUsuario(Base):
    __tablename__ = 'carrera_usuario'

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    carrera_id = Column(Integer, ForeignKey('carreras.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    usuario = relationship("Usuario", back_populates="carreras")
    carrera = relationship("Carrera", back_populates="usuarios")

    def to_dict_carrera_usuario(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "carrera_id": self.carrera_id
        }


class Materia(Base):
    __tablename__ = 'materias'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    carrera_id = Column(Integer, ForeignKey('carreras.id', ondelete='CASCADE'), nullable=False)
    descripcion = Column(Text, nullable=True)
    año_plan = Column(Integer, nullable=True)

    # Relationships
    carrera = relationship("Carrera", back_populates="materias")
    servicios_tutoria = relationship("ServicioTutoria", back_populates="materia")

    def to_dict_materia(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "carrera_id": self.carrera_id,
            "descripcion": self.descripcion
        }


class ServicioTutoria(Base):
    __tablename__ = 'servicios_tutoria'

    id = Column(Integer, primary_key=True)
    tutor_id = Column(Integer, ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    materia_id = Column(Integer, ForeignKey('materias.id', ondelete='CASCADE'), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    descripcion = Column(Text, nullable=True)
    modalidad = Column(String(50))
    activo = Column(Boolean, default=True)

    # Check constraint for modalidad
    __table_args__ = (
        CheckConstraint("modalidad IN ('presencial', 'virtual', 'ambas')"),
        UniqueConstraint('tutor_id', 'materia_id', name='UQ_tutor_materia'),
    )

    # Relationships
    tutor = relationship("Usuario", back_populates="servicios_tutoria")
    materia = relationship("Materia", back_populates="servicios_tutoria")
    reservas = relationship("Reserva", back_populates="servicio")

    def to_dict_servicio_tutoria(self):
        return {
            "id": self.id,
            "tutor_id": self.tutor_id,
            "materia_id": self.materia_id,
            "precio": float(self.precio) if self.precio else 0,
            "descripcion": self.descripcion,
            "modalidad": self.modalidad,
            "activo": self.activo
        }


class Disponibilidad(Base):
    __tablename__ = 'disponibilidad'

    id = Column(Integer, primary_key=True)
    tutor_id = Column(Integer, ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    dia_semana = Column(Integer)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)

    # Check constraints
    __table_args__ = (
        CheckConstraint("dia_semana BETWEEN 1 AND 7"),
        CheckConstraint("hora_inicio < hora_fin"),
    )

    # Relationships
    tutor = relationship("Usuario", back_populates="disponibilidad")

    def to_dict_disponibilidad(self):
        return {
            "id": self.id,
            "tutor_id": self.tutor_id,
            "dia_semana": self.dia_semana,
            "hora_inicio": self.hora_inicio.isoformat() if self.hora_inicio else None,
            "hora_fin": self.hora_fin.isoformat() if self.hora_fin else None
        }


class Reserva(Base):
    __tablename__ = 'reservas'

    id = Column(Integer, primary_key=True)
    estudiante_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    servicio_id = Column(Integer, ForeignKey('servicios_tutoria.id'), nullable=False)
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    estado = Column(String(20))
    notas = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Check constraints
    __table_args__ = (
        CheckConstraint("estado IN ('pendiente', 'confirmada', 'completada', 'cancelada')"),
        CheckConstraint("hora_inicio < hora_fin"),
    )

    # Relationships
    estudiante = relationship("Usuario", foreign_keys=[estudiante_id], back_populates="reservas_estudiante")
    servicio = relationship("ServicioTutoria", back_populates="reservas")
    pagos = relationship("Pago", back_populates="reserva")
    calificaciones = relationship("Calificacion", back_populates="reserva")
    notificaciones = relationship("Notificacion", back_populates="reserva")

    def to_dict_reserva(self):
        return {
            "id": self.id,
            "estudiante_id": self.estudiante_id,
            "servicio_id": self.servicio_id,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "hora_inicio": self.hora_inicio.isoformat() if self.hora_inicio else None,
            "hora_fin": self.hora_fin.isoformat() if self.hora_fin else None,
            "estado": self.estado,
            "notas": self.notas,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }


class Pago(Base):
    __tablename__ = 'pagos'

    id = Column(Integer, primary_key=True)
    reserva_id = Column(Integer, ForeignKey('reservas.id', ondelete='CASCADE'), nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    metodo_pago = Column(String(50))
    estado = Column(String(50))
    referencia_externa = Column(String(100), nullable=True)
    fecha_pago = Column(DateTime, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Check constraints
    __table_args__ = (
        CheckConstraint("metodo_pago IN ('mercado_pago', 'efectivo')"),
        CheckConstraint("estado IN ('pendiente', 'completado', 'cancelado', 'reembolsado')"),
    )

    # Relationships
    reserva = relationship("Reserva", back_populates="pagos")

    def to_dict_pago(self):
        return {
            "id": self.id,
            "reserva_id": self.reserva_id,
            "monto": float(self.monto) if self.monto else 0,
            "metodo_pago": self.metodo_pago,
            "estado": self.estado,
            "referencia_externa": self.referencia_externa,
            "fecha_pago": self.fecha_pago.isoformat() if self.fecha_pago else None,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }


class Calificacion(Base):
    __tablename__ = 'calificaciones'

    id = Column(Integer, primary_key=True)
    reserva_id = Column(Integer, ForeignKey('reservas.id', ondelete='CASCADE'), nullable=False)
    calificador_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    calificado_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    puntuacion = Column(Integer)
    comentario = Column(Text, nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)

    # Check constraints
    __table_args__ = (
        CheckConstraint("puntuacion BETWEEN 1 AND 5"),
    )

    # Relationships
    reserva = relationship("Reserva", back_populates="calificaciones")
    calificador = relationship("Usuario", foreign_keys=[calificador_id], back_populates="calificaciones_dadas")
    calificado = relationship("Usuario", foreign_keys=[calificado_id], back_populates="calificaciones_recibidas")

    def to_dict_calificacion(self):
        return {
            "id": self.id,
            "reserva_id": self.reserva_id,
            "calificador_id": self.calificador_id,
            "calificado_id": self.calificado_id,
            "puntuacion": self.puntuacion,
            "comentario": self.comentario,
            "fecha": self.fecha.isoformat() if self.fecha else None
        }


class Notificacion(Base):
    __tablename__ = 'notificaciones'

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    titulo = Column(String(100), nullable=False)
    mensaje = Column(Text, nullable=False)
    tipo = Column(String(50))
    leida = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_programada = Column(DateTime, nullable=True)
    reserva_id = Column(Integer, ForeignKey('reservas.id', ondelete='SET NULL'), nullable=True)

    # Check constraints
    __table_args__ = (
        CheckConstraint("tipo IN ('reserva', 'pago', 'recordatorio', 'sistema')"),
    )

    # Relationships
    usuario = relationship("Usuario", back_populates="notificaciones")
    reserva = relationship("Reserva", back_populates="notificaciones")

    def to_dict_notificacion(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "titulo": self.titulo,
            "mensaje": self.mensaje,
            "tipo": self.tipo,
            "leida": self.leida,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_programada": self.fecha_programada.isoformat() if self.fecha_programada else None,
            "reserva_id": self.reserva_id
        }


class DispositivoUsuario(Base):
    __tablename__ = 'dispositivos_usuario'

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    token_dispositivo = Column(String(255), nullable=False)
    plataforma = Column(String(20))
    ultimo_acceso = Column(DateTime, default=datetime.utcnow)

    # Check constraints and unique constraint
    __table_args__ = (
        CheckConstraint("plataforma IN ('web', 'android', 'ios')"),
        UniqueConstraint('usuario_id', 'token_dispositivo', name='UQ_usuario_token'),
    )

    # Relationships
    usuario = relationship("Usuario", back_populates="dispositivos")

    def to_dict_dispositivo_usuario(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "token_dispositivo": self.token_dispositivo,
            "plataforma": self.plataforma,
            "ultimo_acceso": self.ultimo_acceso.isoformat() if self.ultimo_acceso else None
        }