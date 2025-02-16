# File: models/database_manager.py

import sqlite3
from pathlib import Path

class DatabaseManager:
    """Manages database connections and schema initialisation"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._initialise_database()
    
    def _initialise_database(self):
        """Initialise the database with schema if it doesn't exist"""
        schema_path = Path("schema.sql")
        if schema_path.exists():
            with schema_path.open() as f:
                schema_sql = f.read()
            
            self.conn = sqlite3.connect(self.db_path)
            self.conn.executescript(schema_sql)
            self.conn.commit()
    
    def execute(self, query: str, parameters=None):
        """Execute a database query with optional parameters"""
        if parameters is None:
            parameters = []
        cursor = self.conn.cursor()
        cursor.execute(query, parameters)
        return cursor
    
    def commit(self):
        """Commit pending transactions"""
        self.conn.commit()