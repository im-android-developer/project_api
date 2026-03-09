import os
import mysql.connector
from mysql.connector import Error

def get_connection():
    """Create and return a new MySQL database connection."""
    return mysql.connector.connect(
        host     = os.environ.get("DB_HOST", "localhost"),
        user     = os.environ.get("DB_USER", "root"),
        password = os.environ.get("DB_PASSWORD", ""),
        database = os.environ.get("DB_NAME", "StockMarketDB")
    )

def execute_query(query, params=None, fetch=False):
    """
    Execute a query and optionally return results.
    - fetch=False : INSERT / UPDATE / DELETE  → returns lastrowid
    - fetch=True  : SELECT                    → returns list of dicts
    """
    conn   = None
    cursor = None
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if fetch:
            return cursor.fetchall()
        else:
            conn.commit()
            return cursor.lastrowid
    except Error as e:
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
