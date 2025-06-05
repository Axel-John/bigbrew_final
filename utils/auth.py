import re
from config.database import get_db_connection
from utils.password import hash_password

def generate_employee_id():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get the last employee ID
        cursor.execute("SELECT employee_id FROM employees ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            last_id = result[0]
            # Extract the number and increment
            num = int(last_id[3:]) + 1
        else:
            # If no employees exist, start with 1
            num = 1
            
        # Format the new ID
        new_id = f"EMP{num:04d}"
        return new_id
        
    except Exception as e:
        print(f"Error generating employee ID: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def validate_password(password):
    """Validate password requirements:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    - Contains at least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
        
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
        
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
        
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
        
    return True, "Password is valid" 