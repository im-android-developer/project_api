import os

def get_connection():
    """PostgreSQL connection — set DATABASE_URL env var."""
    # TODO: implement after DATABASE_URL is provided
    raise NotImplementedError("DATABASE_URL not configured yet")

def execute_query(query, params=None, fetch=False):
    """
    Execute a query and optionally return results.
    - fetch=False : INSERT / UPDATE / DELETE  → returns lastrowid
    - fetch=True  : SELECT                    → returns list of dicts
    """
    # TODO: implement after DATABASE_URL is provided
    raise NotImplementedError("DATABASE_URL not configured yet")
