"""
Database Manager Module

This module provides database connection management and schema initialisation 
for the BNB Financial Manager application.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Any, List


class DatabaseManager:
    """
    Manages database connections and schema initialisation.
    
    This class handles SQLite database connections, schema setup, and provides
    a unified interface for database operations throughout the application.
    """
    
    def __init__(self, db_path: str):
        """
        Initialise the database manager with a database file path.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._initialise_database()
    
    def _initialise_database(self):
        """
        Initialise the database with schema if it doesn't exist.
        
        Reads the schema.sql file and executes it to set up the database
        structure if the schema file exists.
        """
        schema_path = Path("schema.sql")
        if schema_path.exists():
            with schema_path.open() as f:
                schema_sql = f.read()
            
            self.conn = sqlite3.connect(self.db_path)
            self.conn.executescript(schema_sql)
            self.conn.commit()
    
    def execute(self, query: str, parameters: Optional[List[Any]] = None):
        """
        Execute a database query with optional parameters.
        
        Args:
            query: SQL query string to execute
            parameters: Optional list of parameters for the query
            
        Returns:
            Database cursor with query results
        """
        if parameters is None:
            parameters = []
        cursor = self.conn.cursor()
        cursor.execute(query, parameters)
        return cursor
    
    def cursor(self):
        """
        Get a database cursor for manual query execution.
        
        Returns:
            SQLite cursor object
        """
        return self.conn.cursor()
    
    def commit(self):
        """Commit pending transactions."""
        self.conn.commit()

    def rollback(self):
        """Rollback (undo) pending transactions in case of error."""
        self.conn.rollback()
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None