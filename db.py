import os
from urllib.parse import urlparse
import mysql.connector
from mysql.connector import Error

def get_connection():
    """Create and return a MySQL connection.
    Priority: DATABASE_URL → individual MYSQL* vars → local DB_* vars.
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        p = urlparse(url)
        return mysql.connector.connect(
            host     = p.hostname,
            port     = p.port or 3306,
            user     = p.username,
            password = p.password,
            database = p.path.lstrip("/")
        )

    return mysql.connector.connect(
        host     = os.environ.get("MYSQLHOST")     or os.environ.get("DB_HOST", "localhost"),
        port     = int(os.environ.get("MYSQLPORT") or os.environ.get("DB_PORT", 3306)),
        user     = os.environ.get("MYSQLUSER")     or os.environ.get("DB_USER", "root"),
        password = os.environ.get("MYSQLPASSWORD") or os.environ.get("DB_PASSWORD", ""),
        database = os.environ.get("MYSQLDATABASE") or os.environ.get("DB_NAME", "StockMarketDB")
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
