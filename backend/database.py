import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables from the parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_db_connection():
    """
    Establish and return a connection to the MySQL database.
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "facetrack_attendance")
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

def init_db():
    """
    Initialize the database using the schema.sql file if needed.
    (This is usually run manually via phpMyAdmin or mysql CLI, but good to have)
    """
    pass
