import mysql.connector
from mysql.connector import Error
from utils.password import hash_password

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="bigbrew_db"
        )
        if connection.is_connected():
            print("Successfully connected to MariaDB")
            return connection
    except Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return None
    return None

def init_db():
    conn = get_db_connection()
    if conn and conn.is_connected():
        cursor = conn.cursor()
        
        # Create products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                type VARCHAR(50) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                availability ENUM('Available', 'Limited', 'Out of Stock') NOT NULL,  # Use ENUM for valid values
                image_path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create admin table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create employees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id VARCHAR(20) UNIQUE NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,  # Ensure the role column exists
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Alter the table if the role column is missing
        cursor.execute("""
            ALTER TABLE employees
            ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL
        """)

        # Create default admin employee account if not exists
        from utils.auth import hash_password
        employee_id = "EMP0001"
        first_name = "Admin"
        last_name = "Emp"
        email = "admin.emp@gmail.com"
        password = hash_password("admin123")
        role = "admin"
        cursor.execute("SELECT * FROM employees WHERE employee_id = %s", (employee_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO employees (employee_id, first_name, last_name, email, password, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (employee_id, first_name, last_name, email, password, role))
            conn.commit()
            print("Default admin employee account created!")
        else:
            print("Default admin employee account already exists.")

        # Create admin account if not exists
        cursor.execute("SELECT * FROM admin WHERE username = 'BBADMIN'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO admin (username, full_name, password)
                VALUES (%s, %s, %s)
            """, ('BBADMIN', 'Big Brew Admin', hash_password('admin123')))

        # Create orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INT AUTO_INCREMENT PRIMARY KEY,
                product_name VARCHAR(100) NOT NULL,
                size VARCHAR(20) NOT NULL,
                add_ons VARCHAR(255),
                quantity INT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add transaction_id column to orders if not exists
        cursor.execute('''
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS transaction_id INT
        ''')

        # Create transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                order_number INT NOT NULL,
                order_code VARCHAR(20) NOT NULL,
                payment_method VARCHAR(50) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'Normal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Alter transactions table to add order_number and order_code columns if they don't exist
        cursor.execute("""
            ALTER TABLE transactions
            ADD COLUMN IF NOT EXISTS order_number INT NOT NULL,
            ADD COLUMN IF NOT EXISTS order_code VARCHAR(20) NOT NULL
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully!")
    else:
        print("Failed to connect to database!")

def create_employee_admin():
    from utils.auth import hash_password
    conn = get_db_connection()
    if conn and conn.is_connected():
        cursor = conn.cursor()
        employee_id = "EMP001"
        first_name = "Admin"
        last_name = "Emp"
        email = "admin.emp@gmail.com"
        password = hash_password("admin123")  # Change password as needed
        role = "admin"
        # Check if employee already exists
        cursor.execute("SELECT * FROM employees WHERE employee_id = %s", (employee_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO employees (employee_id, first_name, last_name, email, password, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (employee_id, first_name, last_name, email, password, role))
            conn.commit()
            print("Employee admin account created!")
        else:
            print("Employee admin account already exists.")
        cursor.close()
        conn.close()

def create_default_accounts():
    from utils.auth import hash_password
    conn = get_db_connection()
    if conn and conn.is_connected():
        cursor = conn.cursor()
        # Create default admin employee account if not exists
        employee_id = "EMP0001"
        first_name = "Admin"
        last_name = "Emp"
        email = "admin.emp@gmail.com"
        password = hash_password("admin123")
        role = "admin"
        cursor.execute("SELECT * FROM employees WHERE employee_id = %s", (employee_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO employees (employee_id, first_name, last_name, email, password, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (employee_id, first_name, last_name, email, password, role))
            conn.commit()
            print("Default admin employee account created!")
        else:
            print("Default admin employee account already exists.")
        # Create admin account if not exists
        cursor.execute("SELECT * FROM admin WHERE username = 'BBADMIN'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO admin (username, full_name, password)
                VALUES (%s, %s, %s)
            """, ('BBADMIN', 'Big Brew Admin', hash_password('admin123')))
            conn.commit()
            print("Default admin account created!")
        else:
            print("Default admin account already exists.")
        cursor.close()
        conn.close()

# --- ORDER FUNCTIONS ---
def insert_order(product_name, size, add_ons, quantity, price):
    conn = get_db_connection()
    if conn and conn.is_connected():
        cursor = conn.cursor()
        try:
            # Insert into orders table only
            cursor.execute(
                """
                INSERT INTO orders (product_name, size, add_ons, quantity, price, status)
                VALUES (%s, %s, %s, %s, %s, 'Pending')
                """,
                (product_name, size, add_ons, quantity, price)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting order: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def fetch_pending_orders():
    conn = get_db_connection()
    if conn and conn.is_connected():
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.order_id, o.product_name, o.size, o.add_ons, o.quantity, o.price, o.status, o.created_at, p.image_path, p.type 
            FROM orders o 
            LEFT JOIN products p ON o.product_name = p.name 
            WHERE o.status = 'Pending' 
            ORDER BY o.created_at DESC
        """)
        orders = cursor.fetchall()
        cursor.close()
        conn.close()
        return orders
    return []

def get_next_transaction_code():
    conn = get_db_connection()
    cursor = None
    try:
        if conn and conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transactions")
            count = cursor.fetchone()[0]
            next_id = count + 1
            return f"BBT{next_id:04d}"
        return "BBT0001"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def clear_pending_orders():
    conn = get_db_connection()
    if conn and conn.is_connected():
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM orders WHERE status = 'Pending'")
            conn.commit()
            return True
        except Exception as e:
            print(f"Error clearing pending orders: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def get_employee_first_name(user_id):
    conn = get_db_connection()
    if conn and conn.is_connected():
        cursor = conn.cursor()
        cursor.execute("SELECT first_name FROM employees WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return row[0]
    return user_id

def get_employee_full_name(user_id):
    conn = get_db_connection()
    if conn and conn.is_connected():
        cursor = conn.cursor()
        # Try employees table first
        cursor.execute("SELECT first_name, last_name FROM employees WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        if row:
            cursor.close()
            conn.close()
            return f"{row[0]} {row[1]}"
        # If not found, always return the first admin's full_name
        cursor.execute("SELECT full_name FROM admin LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return row[0]
    return "Big Brew Admin"

init_db()
create_default_accounts()