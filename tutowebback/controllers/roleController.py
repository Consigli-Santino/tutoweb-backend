import os
import sys
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tutowebback.schemas import schemas
from tutowebback.config import database
from tutowebback.services import roleService
from tutowebback.auth.auth import get_current_user

async def create_rol(rol: schemas.RolCreate, db: Session = Depends(database.get_db), current_user: schemas.Usuario=None):
    try:
        db_rol = roleService.RoleService().create_rol(db, rol)
        rol_response = db_rol.to_dict_rol()
        return {
            "success": True,
            "data": rol_response,
            "message": "Role created successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error creating role: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error creating role: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_all_roles(db: Session = Depends(database.get_db),  current_user: schemas.Usuario=None):
    try:
        db_rol = roleService.RoleService().get_all_roles(db)
        rol_response = [rol.to_dict_rol() for rol in db_rol]
        return {
            "success": True,
            "data": rol_response,
            "message": "Roles retrieved successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving role: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving role: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_role(id: int, db: Session = Depends(database.get_db),  current_user: schemas.Usuario=None):
    try:
        db_rol = roleService.RoleService().get_role(db, id)
        rol_response = db_rol.to_dict_rol()
        return {
            "success": True,
            "data": rol_response,
            "message": "Role retrieved successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error retrieving role: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error retrieving role: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def edit_rol(id: int, rol: schemas.RolUpdate, db: Session = Depends(database.get_db),  current_user: schemas.Usuario=None):
    try:
        db_rol = roleService.RoleService().edit_rol(db, id, rol)
        rol_response = db_rol.to_dict_rol()
        return {
            "success": True,
            "data": rol_response,
            "message": "Role updated successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error updating role: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error updating role: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

## Todo delete logic role
async def delete_role(id: int, db: Session = Depends(database.get_db),  current_user: schemas.Usuario=None):
    try:
        roleService.RoleService().delete_role(db, id)
        return {
            "success": True,
            "message": "Role deleted successfully"
        }
    except HTTPException as he:
        logging.error(f"HTTP error deleting role: {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"Error deleting role: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")