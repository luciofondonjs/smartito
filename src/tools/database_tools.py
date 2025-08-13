"""
Database tools for LangChain agents to interact with Redshift.
"""

from typing import Dict, Any, List
import pandas as pd
import json
from datetime import datetime
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from ..config.database import get_database_connection


class SQLQueryInput(BaseModel):
    """Input schema for SQL query tool."""
    query: str = Field(..., description="SQL query to execute")


class SQLQueryTool(BaseTool):
    """Tool for executing SQL queries against Redshift."""
    
    name: str = "sql_query"
    description: str = """
    Execute SQL queries against the Redshift database.
    Use this tool to retrieve data from the funnels_resumido table.
    Always ensure your queries are safe and optimized.
    """
    args_schema: type[BaseModel] = SQLQueryInput
    
    def _run(
        self, 
        query: str,
        run_manager: CallbackManagerForToolRun = None
    ) -> str:
        """Execute SQL query and return results as JSON string."""
        try:
            db = get_database_connection()
            
            # Basic query validation
            query_lower = query.lower().strip()
            if any(dangerous in query_lower for dangerous in ['drop', 'delete', 'truncate', 'alter', 'create']):
                return json.dumps({
                    "error": "Query contains potentially dangerous operations. Only SELECT queries are allowed."
                })
            
            # Execute query
            result_df = db.execute_query(query)
            
            # Convert to JSON-serializable format
            result_dict = {
                "success": True,
                "rows_returned": len(result_df),
                "columns": list(result_df.columns),
                "data": result_df.to_dict('records')
            }
            
            return json.dumps(result_dict, default=str, indent=2)
            
        except Exception as e:
            error_dict = {
                "success": False,
                "error": str(e),
                "query": query
            }
            return json.dumps(error_dict, indent=2)


class DataAnalysisInput(BaseModel):
    """Input schema for data analysis tool."""
    data: str = Field(..., description="JSON data to analyze")
    analysis_type: str = Field(..., description="Type of analysis to perform")


class DataAnalysisTool(BaseTool):
    """Tool for performing data analysis on query results."""
    
    name: str = "data_analysis"
    description: str = """
    Perform statistical analysis on data retrieved from SQL queries.
    Can calculate metrics like totals, averages, growth rates, comparisons, etc.
    """
    args_schema: type[BaseModel] = DataAnalysisInput
    
    def _run(
        self, 
        data: str,
        analysis_type: str,
        run_manager: CallbackManagerForToolRun = None
    ) -> str:
        """Perform data analysis on the provided data."""
        try:
            # Parse JSON data
            data_dict = json.loads(data)
            
            if not data_dict.get("success", False):
                return json.dumps({
                    "error": "Cannot analyze failed query results",
                    "original_error": data_dict.get("error", "Unknown error")
                })
            
            df = pd.DataFrame(data_dict["data"])
            
            if df.empty:
                return json.dumps({
                    "success": True,
                    "message": "No data to analyze",
                    "analysis": {}
                })
            
            analysis_result = {}
            
            # Perform different types of analysis
            if analysis_type.lower() in ["summary", "basic"]:
                analysis_result = self._basic_summary(df)
            elif analysis_type.lower() in ["trends", "time_series"]:
                analysis_result = self._trend_analysis(df)
            elif analysis_type.lower() in ["comparison", "compare"]:
                analysis_result = self._comparison_analysis(df)
            else:
                analysis_result = self._basic_summary(df)
            
            result = {
                "success": True,
                "analysis_type": analysis_type,
                "rows_analyzed": len(df),
                "analysis": analysis_result
            }
            
            return json.dumps(result, default=str, indent=2)
            
        except Exception as e:
            error_dict = {
                "success": False,
                "error": f"Data analysis failed: {str(e)}",
                "analysis_type": analysis_type
            }
            return json.dumps(error_dict, indent=2)
    
    def _basic_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate basic statistical summary."""
        summary = {}
        
        # Numeric columns summary
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary["numeric_summary"] = {}
            for col in numeric_cols:
                summary["numeric_summary"][col] = {
                    "total": float(df[col].sum()),
                    "average": float(df[col].mean()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "count": int(df[col].count())
                }
        
        # Categorical columns summary
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            summary["categorical_summary"] = {}
            for col in categorical_cols:
                value_counts = df[col].value_counts().head(10)
                summary["categorical_summary"][col] = {
                    "unique_values": int(df[col].nunique()),
                    "top_values": value_counts.to_dict()
                }
        
        return summary
    
    def _trend_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends over time."""
        trends = {}
        
        # Look for date columns
        date_cols = []
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    pd.to_datetime(df[col])
                    date_cols.append(col)
                except:
                    continue
        
        if date_cols:
            date_col = date_cols[0]
            df_sorted = df.sort_values(date_col)
            
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                if len(df_sorted) > 1:
                    first_value = df_sorted[col].iloc[0]
                    last_value = df_sorted[col].iloc[-1]
                    
                    if first_value != 0:
                        growth_rate = ((last_value - first_value) / first_value) * 100
                    else:
                        growth_rate = 0
                    
                    trends[col] = {
                        "first_value": float(first_value),
                        "last_value": float(last_value),
                        "growth_rate_percent": float(growth_rate),
                        "trend": "increasing" if growth_rate > 0 else "decreasing" if growth_rate < 0 else "stable"
                    }
        
        return trends
    
    def _comparison_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compare values across different segments."""
        comparisons = {}
        
        # Find categorical columns for grouping
        categorical_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        for cat_col in categorical_cols:
            if len(df[cat_col].unique()) <= 10:  # Only for columns with few unique values
                comparisons[cat_col] = {}
                
                for num_col in numeric_cols:
                    group_stats = df.groupby(cat_col)[num_col].agg(['sum', 'mean', 'count']).to_dict('index')
                    comparisons[cat_col][num_col] = {
                        str(k): {
                            "total": float(v['sum']),
                            "average": float(v['mean']),
                            "count": int(v['count'])
                        } for k, v in group_stats.items()
                    }
        
        return comparisons


class SchemaInfoTool(BaseTool):
    """Tool for getting database schema information."""
    
    name: str = "get_schema_info"
    description: str = """
    Get information about the database schema and table structure.
    Use this to understand available tables and columns before writing queries.
    """
    
    def _run(self, run_manager: CallbackManagerForToolRun = None) -> str:
        """Get schema information for the funnels_resumido table."""
        try:
            db = get_database_connection()
            schema_info = db.get_table_schema("funnels_resumido")
            
            # Add additional context about the table
            table_description = {
                "table_info": {
                    "name": "funnels_resumido",
                    "schema": "amplitude",
                    "description": "Daily aggregated funnel data by culture, device, and traffic type",
                    "granularity": "One row per day, culture, device, and traffic type combination"
                },
                "column_descriptions": {
                    "date": "Date of the data (YYYY-MM-DD format)",
                    "culture": "Market/country code (BR, CL, PE, PY, US, CO, AR, EC, UY)",
                    "device": "Device type (desktop, mobile)",
                    "traffic_type": "Traffic source type (Organico, Pagado, Promoted)",
                    "traffic": "Website traffic count for the combination",
                    "flight_dom_loaded_flight": "Number of domestic flight page loads",
                    "payment_confirmation_loaded": "Number of payment confirmation page views",
                    "median_time_seconds": "Median completion time in seconds",
                    "median_time_minutes": "Median completion time in minutes"
                },
                "schema_details": schema_info,
                "current_date": datetime.now().strftime('%Y-%m-%d')
            }
            
            return json.dumps(table_description, default=str, indent=2)
            
        except Exception as e:
            error_dict = {
                "success": False,
                "error": f"Could not retrieve schema information: {str(e)}"
            }
            return json.dumps(error_dict, indent=2)


# List of all available tools
DATABASE_TOOLS = [
    SQLQueryTool(),
    DataAnalysisTool(),
    SchemaInfoTool(),
]
