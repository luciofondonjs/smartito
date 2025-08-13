"""
Database configuration and connection management for Redshift.
"""

import os
from typing import Dict, Any, Optional
import redshift_connector
import pandas as pd
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseConfig(BaseSettings):
    """Database configuration settings from environment variables."""
    
    # Database settings
    redshift_host: str = Field(..., env="REDSHIFT_HOST")
    redshift_port: int = Field(5439, env="REDSHIFT_PORT")
    redshift_database: str = Field(..., env="REDSHIFT_DATABASE")
    redshift_username: str = Field(..., env="REDSHIFT_USERNAME")
    redshift_password: str = Field(..., env="REDSHIFT_PASSWORD")
    redshift_schema: str = Field("amplitude", env="REDSHIFT_SCHEMA")
    
    # Additional application settings
    openai_api_key: str = Field(None, env="OPENAI_API_KEY")
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields


class RedshiftConnection:
    """Manages Redshift database connections and queries using redshift_connector."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._conn = None
        
    def get_connection(self):
        """Get a new connection to Redshift."""
        try:
            conn = redshift_connector.connect(
                host=self.config.redshift_host,
                port=self.config.redshift_port,
                database=self.config.redshift_database,
                user=self.config.redshift_username,
                password=self.config.redshift_password
            )
            conn.autocommit = True
            return conn
        except Exception as e:
            raise Exception(f"Error connecting to Redshift: {str(e)}")
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as pandas DataFrame.
        
        Args:
            query: SQL query string
            
        Returns:
            DataFrame with query results
            
        Raises:
            Exception: If query execution fails
        """
        conn = None
        cursor = None
        
        try:
            # Verify query is not empty
            if not query or not query.strip():
                raise ValueError("Query cannot be empty")
                
            # Check query starts with SELECT (security)
            if not query.lower().strip().startswith('select'):
                raise ValueError("Only SELECT queries are allowed")
            
            print(f"Connecting to Redshift using: host={self.config.redshift_host}, db={self.config.redshift_database}, user={self.config.redshift_username}")
            
            # Use a new connection for each query
            conn = self.get_connection()
            
            # Execute query and get results
            cursor = conn.cursor()
            
            print(f"Executing query: {query[:200]}...")
            
            # Try executing with timeout protection
            cursor.execute(query)
            
            # Convert to DataFrame
            print("Query executed successfully. Fetching results...")
            result = cursor.fetch_dataframe()
            
            row_count = len(result) if result is not None else 0
            print(f"Results fetched. Row count: {row_count}")
            
            # Return empty DataFrame if None
            if result is None:
                print("Warning: Query returned None. Converting to empty DataFrame")
                return pd.DataFrame()
                
            return result
            
        except Exception as e:
            # Provide detailed error message
            error_type = type(e).__name__
            error_msg = str(e)
            
            print(f"Database Error ({error_type}): {error_msg}")
            
            if "timeout" in error_msg.lower():
                error_details = "Query timed out. Please try a simpler query or add more filter conditions."
            elif "permission" in error_msg.lower() or "privileges" in error_msg.lower():
                error_details = "Insufficient permissions to execute query on this table/schema."
            elif "relation" in error_msg.lower() and "not exist" in error_msg.lower():
                error_details = f"Table not found in database. Make sure you're using the correct table name with schema prefix."
            elif "syntax error" in error_msg.lower():
                error_details = "SQL syntax error in query."
            else:
                error_details = f"Error executing query: {error_msg}"
                
            raise Exception(error_details)
            
        finally:
            # Ensure resources are always closed properly
            try:
                if cursor is not None:
                    cursor.close()
                    print("Database cursor closed")
            except Exception as cursor_err:
                print(f"Warning: Error closing cursor: {str(cursor_err)}")
                
            try:
                if conn is not None:
                    conn.close()
                    print("Database connection closed")
            except Exception as conn_err:
                print(f"Warning: Error closing connection: {str(conn_err)}")
    
    def get_table_schema(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """
        Get table schema information.
        
        Args:
            table_name: Name of the table
            schema: Schema name, defaults to configured schema
            
        Returns:
            Dictionary with table schema information
        """
        schema = schema or self.config.redshift_schema
        
        query = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_schema = '{schema}' 
        AND table_name = '{table_name}'
        ORDER BY ordinal_position;
        """
        
        try:
            schema_df = self.execute_query(query)
            return {
                "table_name": table_name,
                "schema": schema,
                "columns": schema_df.to_dict('records')
            }
        except Exception as e:
            raise Exception(f"Error getting table schema: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to establish a connection
            conn = self.get_connection()
            
            # Execute a simple test query
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            
            # Close connection
            cursor.close()
            conn.close()
            
            return result is not None and result[0] == 1
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False


# Global database instance
_db_config = None
_db_connection = None


def get_database_config() -> DatabaseConfig:
    """Get singleton database configuration."""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def get_database_connection() -> RedshiftConnection:
    """Get singleton database connection."""
    global _db_connection
    if _db_connection is None:
        config = get_database_config()
        _db_connection = RedshiftConnection(config)
    return _db_connection
