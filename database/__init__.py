"""
Database package for local SQLite persistence and history tracking.
"""
from database.db import (
    clear_history,
    delete_lookup,
    get_connection,
    get_db_path,
    get_lookup_history,
    init_db,
    save_lookup,
)
from database.models import LookupRecord

__all__ = [
    "LookupRecord",
    "get_db_path",
    "get_connection",
    "init_db",
    "save_lookup",
    "get_lookup_history",
    "delete_lookup",
    "clear_history",
]
