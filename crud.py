from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from models import UpdateTableRequest, CreateTableAdmin

def test_query(db: Session):
    query = text("SELECT * from pg_statistic")
    result = db.execute(query).mappings().all()
    return result

def create_roles(db: Session):
    """Create the three roles in the database"""
    try:
        # Create roles
        for role in ["role1", "role2", "role3"]:
            query = text(f"CREATE ROLE {role} WITH LOGIN;")
            try:
                db.execute(query)
            except Exception:
                pass  # Role might already exist
        
        db.commit()
        return "Roles created successfully"
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating roles: {str(e)}")

def create_user(user: CreateTableAdmin, db: Session):
    """Create a user with a role"""
    try:
        # Create user
        query = text(f"CREATE USER {user.username} WITH LOGIN;")
        try:
            db.execute(query)
        except Exception:
            pass  # User might already exist

        # Grant role
        query = text(f"GRANT {user.role} TO {user.username};")
        db.execute(query)
        
        db.commit()
        return f"User {user.username} created and granted role {user.role}"
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

def get_user_role(db: Session, username: str):
    """Get the role of a user"""
    query = text("""
        SELECT rolname 
        FROM pg_roles 
        WHERE rolname = :username;
    """)
    result = db.execute(query, {"username": username}).fetchone()
    return result[0] if result else None

def check_role1_permission(db: Session, username: str):
    if username != "role1":
        raise HTTPException(status_code=403, detail="Permission denied: Only role1 can create tables and insert data")

def check_role2_permission(db: Session, username: str):
    if username != "role2":
        raise HTTPException(status_code=403, detail="Permission denied: Only role2 can view and delete tables")

def check_role3_permission(db: Session, username: str):
    if username != "role3":
        raise HTTPException(status_code=403, detail="Permission denied: Only role3 can update tables")

def create_table(db: Session, table_name: str, username: str):
    """Create a new table (role1 only)"""
    check_role1_permission(db, username)

    # Validate table name
    if not table_name or len(table_name) < 1 or len(table_name) > 63:
        raise HTTPException(status_code=400, detail="Table name must be between 1 and 63 characters")
    
    # Check if table already exists
    check_query = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        );
    """)
    exists = db.execute(check_query, {"table_name": table_name}).scalar()
    
    if exists:
        raise HTTPException(status_code=400, detail=f"Table '{table_name}' already exists!")

    try:
        # Use proper SQL quoting for table name
        query = text(f"""
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                age INT NOT NULL
            );
        """)
        db.execute(query)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating table: {str(e)}")

def insert_data(db: Session, table_name: str, name: str, age: int, username: str):
    """Insert data into a table (role1 only)"""
    check_role1_permission(db, username)

    # Check if table exists first
    check_query = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        );
    """)
    exists = db.execute(check_query, {"table_name": table_name}).scalar()
    
    if not exists:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' does not exist. Please create the table first.")

    # Get the current column names
    columns = get_table_columns(db, table_name)
    column_names = [col["column_name"] for col in columns]
    
    # Find the string column (name) and integer column (age)
    string_columns = [col for col in columns if col["data_type"] in ["character varying", "text"]]
    int_columns = [col for col in columns if col["data_type"] == "integer"]
    
    if not string_columns or not int_columns:
        raise HTTPException(status_code=400, detail=f"Table '{table_name}' must have one string column and one integer column")
    
    name_column = string_columns[0]["column_name"]
    age_column = int_columns[0]["column_name"]

    try:
        # First check the actual column names in the table
        query_columns = text(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = :table_name;
        """)
        actual_columns = db.execute(query_columns, {"table_name": table_name}).fetchall()
        actual_column_names = [col[0] for col in actual_columns]
        
        # Get the integer column that's not the id column
        non_id_int_columns = [col for col in actual_columns 
                             if col[1] == "integer" and col[0].lower() != "id"]
        
        if not non_id_int_columns:
            raise HTTPException(status_code=400, detail=f"Table '{table_name}' must have an integer column other than 'id'")
            
        # Use the actual column names from the table
        query = text(f"""
            INSERT INTO "{table_name}" ("{name_column}", "{non_id_int_columns[0][0]}") 
            VALUES (:{name_column}, :{non_id_int_columns[0][0]});
        """)
        
        # Create a dictionary with the correct parameter names
        params = {
            name_column: name,
            non_id_int_columns[0][0]: age
        }
        
        db.execute(query, params)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inserting data into table '{table_name}': {str(e)}")

def get_all_tables_info(db: Session, username: str):
    """Get list of all tables (role2 only)"""
    check_role2_permission(db, username)
    query = text("""
        SELECT table_name, table_schema, table_type
        FROM information_schema.tables
        WHERE table_schema = 'public';
    """)
    result = db.execute(query).fetchall()
    return [{"table_name": row[0], "table_schema": row[1], "table_type": row[2]} for row in result]

def get_info_table(db: Session, table_name: str, username: str):
    """Get table contents (role2 only)"""
    check_role2_permission(db, username)
    
    # Check if table exists
    query_check = text("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_name = :table_name
        );
    """)
    table_exists = db.execute(query_check, {"table_name": table_name}).scalar()
    
    if not table_exists:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' does not exist")
    
    # Use proper SQL quoting for the table name
    query = text(f"""
        SELECT * FROM "{table_name}";
    """)
    result = db.execute(query).fetchall()
    return [dict(row._mapping) for row in result]

def delete_table_endpoint(db: Session, table_name: str, username: str):
    """Delete a table (role2 only)"""
    check_role2_permission(db, username)
    
    # Check if table exists first
    check_query = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        );
    """)
    exists = db.execute(check_query, {"table_name": table_name}).scalar()
    
    if not exists:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' does not exist")
    
    try:
        query = text(f"""DROP TABLE IF EXISTS "{table_name}";""")
        db.execute(query)
        db.commit()
        return f"Table '{table_name}' deleted successfully"
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting table: {str(e)}")

def get_table_columns(db: Session, table_name: str):
    """Get all columns in a table"""
    query = text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = :table_name;
    """)
    result = db.execute(query, {"table_name": table_name}).all()
    return [{"column_name": row[0], "data_type": row[1]} for row in result]

def update_table_info(db: Session, update_table_request: UpdateTableRequest, username: str):
    """Update table structure (role3 only)"""
    check_role3_permission(db, username)
    table_name = update_table_request.table_name
    new_table_name = update_table_request.new_table_name
    new_name = update_table_request.new_name
    new_age = update_table_request.new_age

    # Validate column names
    if new_name and not new_name.isidentifier():
        raise HTTPException(status_code=400, detail="Invalid column name. Column names must be valid SQL identifiers.")

    # Check if new table name exists
    if new_table_name:
        query_check = text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :new_table_name);")
        exists = db.execute(query_check, {"new_table_name": new_table_name}).scalar()
        
        if exists:
            raise HTTPException(status_code=400, detail="Table with the new name already exists")

    # Check if source table exists
    query_check_source = text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name);")
    source_exists = db.execute(query_check_source, {"table_name": table_name}).scalar()
    if not source_exists:
        raise HTTPException(status_code=404, detail=f"Source table '{table_name}' does not exist")

    try:
        changes = []
        
        # Rename table if requested
        if new_table_name:
            query = text(f"""
                ALTER TABLE "{table_name}" RENAME TO "{new_table_name}";
            """)
            db.execute(query)
            changes.append(f"Table '{table_name}' renamed to '{new_table_name}'")
            # Update table_name for subsequent operations
            table_name = new_table_name
        
        # Get current columns
        columns = get_table_columns(db, table_name)
        column_names = [col["column_name"] for col in columns]
        
        # Update name column if requested
        if new_name:
            # Check if we have any string columns that could be the name column
            string_columns = [col["column_name"] for col in columns if col["data_type"] in ["character varying", "text"]]
            
            if not string_columns:
                raise HTTPException(status_code=404, detail=f"No string columns found in table '{table_name}' to rename")
            
            # Check if the new name already exists as a column
            if new_name in column_names:
                raise HTTPException(status_code=400, detail=f"Column '{new_name}' already exists in table '{table_name}'")
            
            # If we don't find the exact 'name' column, try to rename the first string column
            if "name" not in column_names:
                old_name = string_columns[0]
                query_name = text(f"""
                    ALTER TABLE "{table_name}" RENAME COLUMN "{old_name}" TO "{new_name}";
                """)
                db.execute(query_name)
                changes.append(f"Column '{old_name}' renamed to '{new_name}'")
            else:
                query_name = text(f"""
                    ALTER TABLE "{table_name}" RENAME COLUMN name TO "{new_name}";
                """)
                db.execute(query_name)
                changes.append(f"Column 'name' renamed to '{new_name}'")

        # Update age values if requested (not renaming the column)
        if new_age is not None:
            # Check if the age column exists
            query_check_age = text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND column_name = 'age'
                );
            """)
            age_exists = db.execute(query_check_age, {"table_name": table_name}).scalar()
            
            if not age_exists:
                raise HTTPException(status_code=404, detail=f"Column 'age' does not exist in table '{table_name}'")

            query_age = text(f"""
                UPDATE "{table_name}" SET age = :new_age;
            """)
            db.execute(query_age, {"new_age": new_age})
            changes.append(f"Updated all ages to {new_age}")

        db.commit()
        return {
            "message": "Changes applied successfully!",
            "changes": changes
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
