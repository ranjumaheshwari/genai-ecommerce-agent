import sqlite3
import os
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path
from app.config import get_settings

logger = logging.getLogger(__name__)

class DatabaseHandler:
    def __init__(self, db_path: str = None):
        """
        Initialize database handler with enhanced security and error handling

        Args:
            db_path: Path to the SQLite database file
        """
        settings = get_settings()

        # Use configured database path or default
        if db_path is None:
            if os.path.isabs(settings.database_path):
                db_path = settings.database_path
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                db_path = os.path.join(base_dir, settings.database_path)

        self.db_path = db_path
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish database connection with enhanced error handling"""
        try:
            # Ensure the data directory exists
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logger.info(f"Created database directory: {db_dir}")

            # Check if database file exists
            if not os.path.exists(self.db_path):
                logger.warning(f"Database file does not exist: {self.db_path}")
                raise FileNotFoundError(f"Database file not found: {self.db_path}")

            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # Allow multi-threading
                timeout=30.0  # 30 second timeout
            )
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access

            # Enable foreign key constraints
            self.connection.execute("PRAGMA foreign_keys = ON")

            logger.info(f"Connected to database: {self.db_path}")

            # Validate database structure
            self._validate_database_structure()

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _validate_database_structure(self):
        """Validate that required tables exist"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            required_tables = ['sales', 'total_sales', 'eligibility']
            missing_tables = [table for table in required_tables if table not in tables]

            if missing_tables:
                logger.warning(f"Missing required tables: {missing_tables}")
            else:
                logger.info("All required tables found in database")

        except Exception as e:
            logger.warning(f"Could not validate database structure: {e}")
    
    def execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query with enhanced security and error handling

        Args:
            sql_query: SQL query to execute (must be a SELECT statement)

        Returns:
            List of dictionaries representing the query results

        Raises:
            ValueError: If query is not a SELECT statement
            Exception: If query execution fails
        """
        if not self.connection:
            raise Exception("Database connection not established")

        # Additional security check
        sql_upper = sql_query.upper().strip()
        if not sql_upper.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")

        try:
            logger.debug(f"Executing SQL query: {sql_query}")
            cursor = self.connection.cursor()

            # Set query timeout and row limit for safety
            cursor.execute("PRAGMA query_timeout = 30000")  # 30 seconds
            cursor.execute(sql_query)

            # Fetch results with a reasonable limit
            rows = cursor.fetchmany(10000)  # Limit to 10k rows max

            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append(dict(row))

            logger.info(f"Query returned {len(results)} rows")
            return results

        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            logger.error(f"SQL was: {sql_query}")
            raise Exception(f"Database query failed: {str(e)}")
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"SQL was: {sql_query}")
            raise Exception(f"Query execution failed: {str(e)}")
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get database schema information
        
        Returns:
            Dictionary containing table schemas
        """
        try:
            cursor = self.connection.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        "name": row[1],
                        "type": row[2],
                        "not_null": bool(row[3]),
                        "primary_key": bool(row[5])
                    })
                schema[table] = columns
            
            return schema
            
        except Exception as e:
            print(f"Failed to get schema: {e}")
            return {}
    
    def get_sample_data(self, table_name: str = None, limit: int = 5) -> Dict[str, Any]:
        """
        Get sample data from the database
        
        Args:
            table_name: Specific table to query (optional)
            limit: Number of records to return
            
        Returns:
            Dictionary containing sample data
        """
        try:
            cursor = self.connection.cursor()
            
            if table_name:
                # Get sample data from specific table
                cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                rows = cursor.fetchall()
                return {table_name: [dict(row) for row in rows]}
            else:
                # Get sample data from all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                sample_data = {}
                for table in tables:
                    cursor.execute(f"SELECT * FROM {table} LIMIT {limit}")
                    rows = cursor.fetchall()
                    sample_data[table] = [dict(row) for row in rows]
                
                return sample_data
                
        except Exception as e:
            print(f"Failed to get sample data: {e}")
            return {}
    
    def is_connected(self) -> bool:
        """Check if database connection is active"""
        try:
            if self.connection:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                return True
            return False
        except:
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __del__(self):
        """Destructor to ensure connection is closed"""
        self.close() 