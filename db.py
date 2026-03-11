import os
import psycopg2
import psycopg2.extras
from psycopg2 import OperationalError, DatabaseError

def get_connection():
    """Create and return a PostgreSQL connection via DATABASE_URL."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise OperationalError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(url)

def execute_query(query, params=None, fetch=False):
    """
    Execute a query and optionally return results.
    - fetch=False : INSERT / UPDATE / DELETE  → returns inserted row id (if RETURNING id used)
    - fetch=True  : SELECT                    → returns list of dicts
    """
    conn   = None
    cursor = None
    try:
        conn   = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, params or ())

        if fetch:
            return cursor.fetchall()
        else:
            conn.commit()
            if cursor.description:
                row = cursor.fetchone()
                return row[0] if row else None
            return None
    except (OperationalError, DatabaseError) as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
