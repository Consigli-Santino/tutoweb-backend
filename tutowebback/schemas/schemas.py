from pydantic import BaseModel, EmailStr, Field, validator, constr
from typing import List, Optional, Union
from datetime import datetime, date, time
from decimal import Decimal

# Esquemas para Rol (mantenemos lo que ya teníamos)
class RolBase(BaseModel):
    nombre: str

class RolCreate(RolBase):
    pass

class RolUpdate(BaseModel):
    nombre: Optional[str] = None

class Rol(RolBase):
    id: int

    class Config:
        from_attributes = True

class MateriasXCarreraXUsuarioBase(BaseModel):
    estado: bool
    usuario_id: int
    materia_id: int
    carrera_id: int


class MateriasXCarreraXUsuarioCreate(MateriasXCarreraXUsuarioBase):
    pass


class MateriasXCarreraXUsuarioUpdate(BaseModel):
    estado: Optional[bool] = None
    usuario_id: Optional[int] = None
    materia_id: Optional[int] = None
    carrera_id: Optional[int] = None


class MateriasXCarreraXUsuario(MateriasXCarreraXUsuarioBase):
    id: int

    class Config:
        orm_mode = True

# Esquemas para Carrera
class CarreraBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    facultad: Optional[str] = "Universidad Tecnológica Nacional"

class CarreraCreate(CarreraBase):
    pass

class CarreraUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    facultad: Optional[str] = None

class Carrera(CarreraBase):
    id: int

    class Config:
        from_attributes = True

# Esquemas para Usuario
class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    password: str
    foto_perfil: Optional[str] = None
    id_carrera: List[int]
    id_rol : int

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    foto_perfil: Optional[str] = None
    id_rol: Optional[int] = None
    id_carrera: Optional[List[int]] = None

class Usuario(UsuarioBase):
    id: int
    fecha_registro: Optional[datetime] = None
    puntuacion_promedio: float = 0
    cantidad_reseñas: int = 0
    foto_perfil: Optional[str] = None
    id_rol: Optional[int] = None
    carreras: List[Carrera] = []

    class Config:
        from_attributes = True

# Esquemas para CarreraUsuario
class CarreraUsuarioBase(BaseModel):
    usuario_id: int
    carrera_id: int

class CarreraUsuarioCreate(CarreraUsuarioBase):
    pass

class CarreraUsuarioUpdate(BaseModel):
    usuario_id: Optional[int] = None
    carrera_id: Optional[int] = None

class CarreraUsuario(CarreraUsuarioBase):
    id: int

    class Config:
        from_attributes = True

# Esquemas para Materia
class MateriaBase(BaseModel):
    nombre: str
    carrera_id: int
    descripcion: Optional[str] = None

class MateriaCreate(MateriaBase):
    pass

class MateriaUpdate(BaseModel):
    nombre: Optional[str] = None
    carrera_id: Optional[int] = None
    descripcion: Optional[str] = None

class Materia(MateriaBase):
    id: int
    carrera: Optional[Carrera] = None

    class Config:
        from_attributes = True

# Esquemas para ServicioTutoria
class ServicioTutoriaBase(BaseModel):
    tutor_id: int
    materia_id: int
    precio: float
    descripcion: Optional[str] = None
    modalidad: str = Field(..., pattern="^(presencial|virtual|ambas)$")
    activo: bool = True

    @validator('modalidad')
    def validate_modalidad(cls, v):
        if v not in ["presencial", "virtual", "ambas"]:
            raise ValueError('modalidad must be one of: presencial, virtual, ambas')
        return v

class ServicioTutoriaCreate(ServicioTutoriaBase):
    pass

class ServicioTutoriaUpdate(BaseModel):
    materia_id: Optional[int] = None
    precio: Optional[float] = None
    descripcion: Optional[str] = None
    modalidad: Optional[str] = None
    activo: Optional[bool] = None

    @validator('modalidad')
    def validate_modalidad(cls, v):
        if v is not None and v not in ["presencial", "virtual", "ambas"]:
            raise ValueError('modalidad must be one of: presencial, virtual, ambas')
        return v

class ServicioTutoria(ServicioTutoriaBase):
    id: int
    tutor: Optional[Usuario] = None
    materia: Optional[Materia] = None

    class Config:
        from_attributes = True

# Esquemas para Disponibilidad
class DisponibilidadBase(BaseModel):
    tutor_id: int
    dia_semana: int = Field(..., ge=1, le=7)
    hora_inicio: time
    hora_fin: time

    @validator('hora_fin')
    def validate_hora_fin(cls, v, values):
        if 'hora_inicio' in values and v <= values['hora_inicio']:
            raise ValueError('hora_fin must be after hora_inicio')
        return v

class DisponibilidadCreate(DisponibilidadBase):
    pass

class DisponibilidadUpdate(BaseModel):
    dia_semana: Optional[int] = Field(None, ge=1, le=7)
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None

    @validator('hora_fin')
    def validate_hora_fin(cls, v, values):
        if v is not None and 'hora_inicio' in values and values['hora_inicio'] is not None and v <= values['hora_inicio']:
            raise ValueError('hora_fin must be after hora_inicio')
        return v

class Disponibilidad(DisponibilidadBase):
    id: int
    tutor: Optional[Usuario] = None

    class Config:
        from_attributes = True

# Esquemas para Reserva
class ReservaBase(BaseModel):
    estudiante_id: int
    servicio_id: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    notas: Optional[str] = None
    estado: str = Field("pendiente", pattern="^(pendiente|confirmada|completada|cancelada)$")

    @validator('estado')
    def validate_estado(cls, v):
        if v not in ["pendiente", "confirmada", "completada", "cancelada"]:
            raise ValueError('estado must be one of: pendiente, confirmada, completada, cancelada')
        return v

    @validator('hora_fin')
    def validate_hora_fin(cls, v, values):
        if 'hora_inicio' in values and v <= values['hora_inicio']:
            raise ValueError('hora_fin must be after hora_inicio')
        return v

class ReservaCreate(ReservaBase):
    pass

class ReservaUpdate(BaseModel):
    fecha: Optional[date] = None
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    notas: Optional[str] = None
    estado: Optional[str] = None
    sala_virtual: Optional[str] = None

    @validator('estado')
    def validate_estado(cls, v):
        if v is not None and v not in ["pendiente", "confirmada", "completada", "cancelada"]:
            raise ValueError('estado must be one of: pendiente, confirmada, completada, cancelada')
        return v

    @validator('hora_fin')
    def validate_hora_fin(cls, v, values):
        if v is not None and 'hora_inicio' in values and values['hora_inicio'] is not None and v <= values['hora_inicio']:
            raise ValueError('hora_fin must be after hora_inicio')
        return v

class Reserva(ReservaBase):
    id: int
    fecha_creacion: datetime
    estudiante: Optional[Usuario] = None
    servicio: Optional[ServicioTutoria] = None

    class Config:
        from_attributes = True

# Esquemas para Pago
class PagoBase(BaseModel):
    reserva_id: int
    monto: float
    metodo_pago: str = Field(..., pattern="^(mercado_pago|efectivo)$")
    estado: str = Field("pendiente", pattern="^(pendiente|completado|cancelado|reembolsado)$")
    referencia_externa: Optional[str] = None
    fecha_pago: Optional[datetime] = None

    @validator('metodo_pago')
    def validate_metodo_pago(cls, v):
        if v not in ["mercado_pago", "efectivo"]:
            raise ValueError('metodo_pago must be one of: mercado_pago, efectivo')
        return v

    @validator('estado')
    def validate_estado(cls, v):
        if v not in ["pendiente", "completado", "cancelado", "reembolsado"]:
            raise ValueError('estado must be one of: pendiente, completado, cancelado, reembolsado')
        return v

class PagoCreate(PagoBase):
    pass

class PagoUpdate(BaseModel):
    monto: Optional[float] = None
    metodo_pago: Optional[str] = None
    estado: Optional[str] = None
    referencia_externa: Optional[str] = None
    fecha_pago: Optional[datetime] = None

    @validator('metodo_pago')
    def validate_metodo_pago(cls, v):
        if v is not None and v not in ["mercado_pago", "efectivo"]:
            raise ValueError('metodo_pago must be one of: mercado_pago, efectivo')
        return v

    @validator('estado')
    def validate_estado(cls, v):
        if v is not None and v not in ["pendiente", "completado", "cancelado"]:
            raise ValueError('estado must be one of: pendiente, completado, cancelado')
        return v

class Pago(PagoBase):
    id: int
    fecha_creacion: datetime
    reserva: Optional[Reserva] = None

    class Config:
        from_attributes = True

# Esquemas para Calificacion
class CalificacionBase(BaseModel):
    reserva_id: int
    calificador_id: int
    calificado_id: int
    puntuacion: int = Field(..., ge=1, le=5)
    comentario: Optional[str] = None

class CalificacionCreate(CalificacionBase):
    pass

class CalificacionUpdate(BaseModel):
    puntuacion: Optional[int] = Field(None, ge=1, le=5)
    comentario: Optional[str] = None

class Calificacion(CalificacionBase):
    id: int
    fecha: datetime
    reserva: Optional[Reserva] = None
    calificador: Optional[Usuario] = None
    calificado: Optional[Usuario] = None

    class Config:
        from_attributes = True

class ReservasIdsRequest(BaseModel):
    reserva_ids: List[int]
# Esquemas para Notificacion
class NotificacionBase(BaseModel):
    usuario_id: int
    titulo: str
    mensaje: str
    tipo: str = Field(..., pattern="^(reserva|pago|recordatorio|sistema)$")
    fecha_programada: Optional[datetime] = None
    reserva_id: Optional[int] = None

    @validator('tipo')
    def validate_tipo(cls, v):
        if v not in ["reserva", "pago", "recordatorio", "sistema"]:
            raise ValueError('tipo must be one of: reserva, pago, recordatorio, sistema')
        return v

class NotificacionCreate(NotificacionBase):
    pass

class NotificacionUpdate(BaseModel):
    titulo: Optional[str] = None
    mensaje: Optional[str] = None
    tipo: Optional[str] = None
    leida: Optional[bool] = None
    fecha_programada: Optional[datetime] = None

    @validator('tipo')
    def validate_tipo(cls, v):
        if v is not None and v not in ["reserva", "pago", "recordatorio", "sistema"]:
            raise ValueError('tipo must be one of: reserva, pago, recordatorio, sistema')
        return v

class Notificacion(NotificacionBase):
    id: int
    leida: bool = False
    fecha_creacion: datetime
    usuario: Optional[Usuario] = None
    reserva: Optional[Reserva] = None

    class Config:
        from_attributes = True

# Esquemas para DispositivoUsuario
class DispositivoUsuarioBase(BaseModel):
    usuario_id: int
    token_dispositivo: str
    plataforma: str = Field(..., pattern="^(web|android|ios)$")

    @validator('plataforma')
    def validate_plataforma(cls, v):
        if v not in ["web", "android", "ios"]:
            raise ValueError('plataforma must be one of: web, android, ios')
        return v

class DispositivoUsuarioCreate(DispositivoUsuarioBase):
    pass

class DispositivoUsuarioUpdate(BaseModel):
    token_dispositivo: Optional[str] = None
    plataforma: Optional[str] = None

    @validator('plataforma')
    def validate_plataforma(cls, v):
        if v is not None and v not in ["web", "android", "ios"]:
            raise ValueError('plataforma must be one of: web, android, ios')
        return v

class DispositivoUsuario(DispositivoUsuarioBase):
    id: int
    ultimo_acceso: datetime
    usuario: Optional[Usuario] = None

    class Config:
        from_attributes = True