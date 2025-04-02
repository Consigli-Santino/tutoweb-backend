import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.models import models
from tutowebback.schemas import schemas

class RoleService:
    def create_rol(self, db: Session, rol: schemas.RolCreate):
        try:
            db_rol = models.Rol(nombre=rol.nombre)
            db.add(db_rol)
            db.commit()
            db.refresh(db_rol)
            return db_rol
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Role name already exists")
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating role: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def get_role(self, db: Session, rol_id: int):
        db_rol = db.query(models.Rol).filter(models.Rol.id == rol_id).first()
        if db_rol is None:
            raise HTTPException(status_code=404, detail="Role not found")
        return db_rol
    def get_all_roles(self, db: Session):
        db_rol = db.query(models.Rol).all()
        if db_rol is None:
            raise HTTPException(status_code=404, detail="Roles not found")
        return db_rol
    def edit_rol(self, db: Session, rol_id: int, rol: schemas.RolUpdate):
        db_rol = self.get_role(db, rol_id)

        try:
            if rol.nombre is not None:
                db_rol.nombre = rol.nombre

            db.commit()
            db.refresh(db_rol)
            return db_rol
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Role name already exists")
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating role: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def delete_role(self, db: Session, rol_id: int):
        db_rol = self.get_role(db, rol_id)
        try:
            db_rol.estado = False
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting role: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")