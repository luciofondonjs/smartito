"""
Data Analyst Agent for technical data analysis and SQL query generation.
"""

from datetime import datetime
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from ..tools.database_tools import DATABASE_TOOLS


class DataAnalystAgent:
    """
    Data Analyst Agent that specializes in:
    - Converting business questions into SQL queries
    - Executing database queries
    - Performing statistical analysis
    - Providing technical insights
    """
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model=model,
            temperature=0.1,  # Low temperature for more consistent technical analysis
        )
        self.tools = DATABASE_TOOLS
        
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the Data Analyst agent."""
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        return f"""
You are a **Data Analyst Agent** with expertise in SQL, data analysis, and working with Redshift databases.

## Your Role
You are responsible for the technical analysis of business questions. You:
1. **Convert business requirements into precise SQL queries**
2. **Execute queries against the database**
3. **Perform statistical analysis on results**
4. **Provide technical insights and data-driven answers**

## Database Context
You have access to a Redshift database with the table `amplitude.funnels_resumido`.

### Table: `funnels_resumido`
- **Purpose**: Daily aggregated funnel data for airline website
- **Granularity**: One row per day, culture (country), device, and traffic type
- **Current Date**: {current_date}

### Columns:
- `date` (datetime): Date of data (YYYY-MM-DD 00:00:00.000)
- `culture` (text): Market/country (BR, CL, PE, PY, US, CO, AR, EC, UY)
- `device` (text): Device type (desktop, mobile)  
- `traffic_type` (text): Traffic source (Organico, Pagado, Promoted)
- `traffic` (numeric): Website traffic count
- `flight_dom_loaded_flight` (numeric): Domestic flight page loads
- `payment_confirmation_loaded` (numeric): Payment confirmation page views
- `median_time_seconds` (numeric): Median completion time (seconds)
- `median_time_minutes` (numeric): Median completion time (minutes)

## Analysis Guidelines

### 1. Query Construction
- Always use `amplitude.funnels_resumido` as the table name
- Apply proper date filters (current year if not specified)
- Use appropriate aggregations (SUM, AVG, COUNT)
- Include relevant GROUP BY clauses for segmentation
- Order results logically (usually by date or metric values)

### 2. Data Analysis
- Calculate conversion rates: `payment_confirmation_loaded / traffic * 100`
- Analyze trends over time periods
- Compare performance across cultures, devices, traffic types
- Identify top/bottom performers
- Calculate growth rates and percentage changes

### 3. Dealing with Ambiguity
- When information is ambiguous or missing, make reasonable assumptions and state them
- For conversion metrics, include ALL devices (mobile + desktop) if not specified
- For market analysis, include specific countries mentioned or focus on ALL markets if none specified
- For time periods, default to the current year or most recent month if not specified
- If traffic type is unspecified, analyze ALL traffic types combined
- NEVER refuse to analyze due to missing details - make reasonable assumptions instead

### 3. Technical Best Practices
- Validate query results before analysis
- Handle null values appropriately
- Use CASE statements for conditional logic
- Apply date functions (DATE_TRUNC, EXTRACT) for time analysis
- Limit result sets when appropriate

### 4. Response Format
Always structure your responses as:
1. **SQL Query**: The exact query executed
2. **Results Summary**: Key metrics and findings
3. **Technical Analysis**: Statistical insights and calculations
4. **Recommendations**: Data-driven suggestions for the business analyst

## Available Tools
You have access to these tools:
- `sql_query`: Execute SQL queries against the database
- `data_analysis`: Perform statistical analysis on query results  
- `get_schema_info`: Get detailed table schema information

## Important Notes
- Only use SELECT statements (no DDL/DML operations)
- If no year is specified, assume current year ({datetime.now().year})
- Always explain your technical approach
- Provide context for numbers and percentages
- Highlight significant trends or anomalies

Remember: You are the technical expert. Focus on data accuracy, statistical significance, and clear technical explanations.
"""
    
    def analyze_request(self, business_question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a business question and provide technical data analysis.
        
        Args:
            business_question: The business question from the Business Analyst
            context: Additional context or parameters
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Create the analysis message
            analysis_prompt = f"""
Business Question to Analyze: {business_question}

Additional Context: {context or 'None provided'}

Please follow these steps:
1. First, get the database schema information to understand the data structure
2. Analyze the business question and determine what SQL query is needed
3. Execute the appropriate SQL query
4. Perform statistical analysis on the results
5. Provide a comprehensive technical response

Focus on providing accurate data analysis that the Business Analyst can interpret for the end user.
"""
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=analysis_prompt)
            ]
            
            # Create a function calling agent
            llm_with_tools = self.llm.bind_tools(self.tools)
            
            # Get initial response
            response = llm_with_tools.invoke(messages)
            
            # Handle tool calls
            messages.append(response)
            
            # Execute tools if requested
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    # Find and execute the tool
                    tool = next((t for t in self.tools if t.name == tool_name), None)
                    if tool:
                        try:
                            tool_result = tool.invoke(tool_args)
                            
                            # Add tool result to messages
                            messages.append({
                                "role": "tool",
                                "content": tool_result,
                                "tool_call_id": tool_call["id"]
                            })
                        except Exception as e:
                            messages.append({
                                "role": "tool", 
                                "content": f"Tool execution failed: {str(e)}",
                                "tool_call_id": tool_call["id"]
                            })
                
                # Get final response after tool execution
                final_response = llm_with_tools.invoke(messages)
                
                return {
                    "success": True,
                    "analysis": final_response.content,
                    "technical_details": {
                        "tools_used": [tc["name"] for tc in response.tool_calls],
                        "query_executed": True
                    }
                }
            else:
                return {
                    "success": True,
                    "analysis": response.content,
                    "technical_details": {
                        "tools_used": [],
                        "query_executed": False
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Data analysis failed: {str(e)}",
                "analysis": "Technical analysis could not be completed due to an error."
            }
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate a SQL query before execution.
        
        Args:
            query: SQL query string
            
        Returns:
            Validation result dictionary
        """
        query_lower = query.lower().strip()
        
        # Check for dangerous operations
        dangerous_ops = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']
        found_dangerous = [op for op in dangerous_ops if op in query_lower]
        
        if found_dangerous:
            return {
                "valid": False,
                "error": f"Query contains dangerous operations: {', '.join(found_dangerous)}",
                "suggestions": "Only SELECT queries are allowed for data analysis."
            }
        
        # Check for required table reference
        if 'funnels_resumido' not in query_lower:
            return {
                "valid": False,
                "error": "Query must reference the funnels_resumido table",
                "suggestions": "Use 'amplitude.funnels_resumido' as the table name."
            }
        
        return {
            "valid": True,
            "message": "Query validation passed"
        }
