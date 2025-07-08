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
        
        This method performs the following operations:
        1. Establishes connection to SQLite database file (creates if doesn't exist)
        2. Reads schema.sql file containing table definitions and indexes
        3. Executes the schema to create all required tables and relationships
        4. Commits the transaction to persist the schema
        
        The schema includes:
        - transactions: Core financial transaction data
        - categories: Hierarchical category structure for transaction classification
        - bank_accounts: Bank account details and balances
        - auto_categorisation_rules: Rules for automatic transaction categorisation
        - analysis_views: Saved filter configurations for financial analysis
        
        Note: If schema.sql doesn't exist, database will still be created but empty.
        This allows for dynamic schema setup in testing environments.
        """
        schema_path = Path("schema.sql")
        # Always establish connection, even if schema file doesn't exist
        self.conn = sqlite3.connect(self.db_path)
        # Enable foreign key constraints for referential integrity
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        if schema_path.exists():
            with schema_path.open() as f:
                schema_sql = f.read()
            
            self.conn.executescript(schema_sql)
            self.conn.commit()
    
    def execute(self, query: str, parameters: Optional[List[Any]] = None):
        """
        Execute a database query with optional parameters.
        
        This method provides a safe interface for executing SQL queries with
        parameterized inputs to prevent SQL injection attacks. All database
        operations throughout the application should use this method.
        
        Args:
            query: SQL query string to execute (use ? placeholders for parameters)
            parameters: Optional list of parameters to substitute into query placeholders
            
        Returns:
            Database cursor with query results. Use cursor.fetchone(), cursor.fetchall(),
            or cursor.fetchmany() to retrieve results.
            
        Example:
            # Safe parameterized query
            cursor = db.execute("SELECT * FROM transactions WHERE amount > ?", [100.0])
            transactions = cursor.fetchall()
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