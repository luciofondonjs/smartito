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
        try:
            # Use a new connection for each query
            conn = self.get_connection()
            
            # Execute query and get results
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Convert to DataFrame
            result = cursor.fetch_dataframe()
            
            # Close the cursor and connection
            cursor.close()
            conn.close()
            
            return result
        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")
    
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
