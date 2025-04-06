from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db
from crud import (
    test_query, create_table, insert_data, get_all_tables_info, 
    get_info_table, delete_table_endpoint, update_table_info,
    create_user, create_roles
)
from sqlalchemy import text
from models import InsertDataRequest, UpdateTableRequest, CreateTableAdmin, CreateTableRequest
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Query

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/test")
def test_query_run(db: Session = Depends(get_db)):
    result = test_query(db)
    return {"result": result}

# Initialize everything
@app.post("/init-system")
def initialize_system(db: Session = Depends(get_db)):
    """Initialize roles and create default users"""
    try:
        # First create roles
        create_roles(db)
        
        # Create a user for each role
        users = [
            CreateTableAdmin(username="role1", role="role1"),
            CreateTableAdmin(username="role2", role="role2"),
            CreateTableAdmin(username="role3", role="role3")
        ]
        
        results = []
        for user in users:
            try:
                result = create_user(user, db)
                results.append(result)
            except HTTPException as e:
                if "User already exists" not in str(e.detail):
                    raise e
                results.append(f"User {user.username} already exists")
        
        return {"message": "System initialized", "details": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize roles
@app.post("/init-roles")
def initialize_roles(db: Session = Depends(get_db)):
    """Initialize the three roles in the database"""
    try:
        result = create_roles(db)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create user with role
@app.post("/create-user")
def create_user_endpoint(request: CreateTableAdmin, db: Session = Depends(get_db)):
    try:
        result = create_user(request, db)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_table")
def create_table_endpoint(request: CreateTableRequest, db: Session = Depends(get_db)):
    try:
        create_table(db, request.table_name, request.username)
        return {"message": f"Table '{request.table_name}' created successfully!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/insert_data")
def insert_data_endpoint(request: InsertDataRequest, db: Session = Depends(get_db)):
    try:
        insert_data(db, request.table_name, request.name, request.age, request.username)
        return {"message": f"Data inserted into table '{request.table_name}' successfully!"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/get_all_tables")
def get_tables(username: str, db: Session = Depends(get_db)):
    try:
        tables_info = get_all_tables_info(db, username)
        return {"tables": tables_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_info_table")
def get_info_table_endpoint(username: str, db: Session = Depends(get_db), table_name: str = Query(...)):
    try:
        table_info = get_info_table(db, table_name, username)
        return {"table_info": table_info}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete_table/{table_name}")
def delete_table(table_name: str, username: str, db: Session = Depends(get_db)):
    try:
        message = delete_table_endpoint(db, table_name, username)
        return {"message": message}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/update_table")
def update_table(request: UpdateTableRequest, db: Session = Depends(get_db)):
    try:
        result = update_table_info(db, request, request.username)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
