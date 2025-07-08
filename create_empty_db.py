#!/usr/bin/env python3
"""
Script to create an empty finance.db file with proper schema.
This ensures fresh installations have a working database file.
"""

import sqlite3
import os
from pathlib import Path

def create_empty_database():
    """Create an empty database file with schema applied."""
    db_path = "finance.db"
    schema_path = Path("schema.sql")
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create new database connection
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Apply schema if it exists
    if schema_path.exists():
        with schema_path.open() as f:
            schema_sql = f.read()
        
        conn.executescript(schema_sql)
        conn.commit()
        print(f"Created empty database with schema: {db_path}")
    else:
        print(f"Warning: schema.sql not found, created empty database: {db_path}")
    
    conn.close()

if __name__ == "__main__":
    create_empty_database()