import mysql.connector
from mysql.connector import Error

# Database Configuration Constants
DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = "Ngminh@1409"
DB_PORT = 3307
DB_NAME = "hospital_management_db" # Update this to your actual database name

def get_connection():
    """
    Creates and returns a connection to the MySQL database.
    Returns:
        mysql.connector.connection_cext.CMySQLConnection: Connection object or None if failed.
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            database=DB_NAME
        )
        if connection.is_connected():
            return connection
            
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

def close_connection(connection, cursor=None):
    """
    Safely closes the database connection and cursor.
    """
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()