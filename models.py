from pydantic import BaseModel, Field
from sqlalchemy import text
from fastapi import Query
from typing import Optional, List

class InsertDataRequest(BaseModel):
    table_name: str
    name: str
    age: int
    username: str

# Pydantic модель для тела запроса
class CreateTableRequest(BaseModel):
    table_name: str
    username: str

class UpdateTableRequest(BaseModel):  
    table_name: str
    new_table_name: Optional[str] = None
    new_name: Optional[str] = None
    new_age: Optional[int] = None
    username: str

class CreateTableAdmin(BaseModel):
    username: str
    role: str

class CreateRoleRequest(BaseModel):
    role_name: str
    username: str
    permissions: Optional[List[str]] = None

class ModifyRolePermissionsRequest(BaseModel):
    role_name: str
    username: str
    permission: str
    action: str = "grant"  # "grant" or "revoke"
