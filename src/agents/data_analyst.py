"""
Data Analyst Agent for technical data analysis and SQL query generation.
"""

from datetime import datetime
import json
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
        self.conversation_memory = {}  # Stores parameters from previous queries
        
        self.system_prompt = self._create_system_prompt()
    
    def _extract_query_params_from_context(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract relevant query parameters from conversation context.
        
        Args:
            context: Conversation context from the Business Analyst
            
        Returns:
            Dictionary with extracted parameters
        """
        # Default parameters
        query_params = {
            "dates": [],
            "cultures": [],
            "devices": [],
            "traffic_types": [],
            "last_executed_queries": [],
            "metrics_of_interest": []
        }
        
        # If no context provided, return empty parameters
        if not context:
            return query_params
            
        try:
            # Extract SQL queries from previous technical details
            if "question_interpretation" in context and "technical_details" in context.get("question_interpretation", {}):
                tech_details = context["question_interpretation"]["technical_details"]
                if "debug_info" in tech_details:
                    debug_info = tech_details["debug_info"]
                    # Extract SQL queries
                    if "tool_results" in debug_info:
                        for tool_result in debug_info["tool_results"]:
                            if tool_result.get("tool") == "sql_query" and "args" in tool_result:
                                query = tool_result["args"].get("query", "")
                                if query:
                                    query_params["last_executed_queries"].append(query)
            
            # Extract parameters from previous queries
            for query in query_params["last_executed_queries"]:
                # Extract dates
                date_patterns = [
                    r"date\s*>=\s*['\"](\d{4}-\d{2}-\d{2})['\"]",
                    r"date\s*<=\s*['\"](\d{4}-\d{2}-\d{2})['\"]",
                    r"date\s*=\s*['\"](\d{4}-\d{2}-\d{2})['\"]",
                    r"date\s*BETWEEN\s*['\"](\d{4}-\d{2}-\d{2})['\"]",
                    r"TO_DATE\(['\"](\d{4}-\d{2}-\d{2})['\"]"
                ]
                
                for pattern in date_patterns:
                    import re
                    matches = re.findall(pattern, query)
                    if matches:
                        for match in matches:
                            if match not in query_params["dates"]:
                                query_params["dates"].append(match)
                
                # Extract cultures/countries
                if "culture" in query:
                    culture_matches = re.findall(r"culture\s*=\s*['\"]([A-Z]{2})['\"]", query)
                    for match in culture_matches:
                        if match not in query_params["cultures"]:
                            query_params["cultures"].append(match)
                
                # Extract devices
                if "device" in query:
                    device_matches = re.findall(r"device\s*=\s*['\"](\w+)['\"]", query)
                    for match in device_matches:
                        if match not in query_params["devices"]:
                            query_params["devices"].append(match)
                
                # Extract traffic types
                if "traffic_type" in query:
                    traffic_matches = re.findall(r"traffic_type\s*=\s*['\"](\w+)['\"]", query)
                    for match in traffic_matches:
                        if match not in query_params["traffic_types"]:
                            query_params["traffic_types"].append(match)
                
                # Extract metrics of interest
                metrics_of_interest = ["conversion_rate", "traffic", "payment_confirmation_loaded"]
                for metric in metrics_of_interest:
                    if metric in query.lower() and metric not in query_params["metrics_of_interest"]:
                        query_params["metrics_of_interest"].append(metric)
            
            # Also try to extract parameters from the original business question
            original_question = context.get("original_question", "")
            if original_question:
                # Check for countries/cultures
                countries_mapping = {
                    "chile": "CL", "brasil": "BR", "peru": "PE", "paraguay": "PY", 
                    "argentina": "AR", "colombia": "CO", "ecuador": "EC", "uruguay": "UY",
                    "estados unidos": "US"
                }
                
                for country, code in countries_mapping.items():
                    if country.lower() in original_question.lower() and code not in query_params["cultures"]:
                        query_params["cultures"].append(code)
                
                # Check for devices
                devices = ["desktop", "mobile", "móvil"]
                for device in devices:
                    if device.lower() in original_question.lower():
                        normalized_device = "mobile" if device == "móvil" else device
                        if normalized_device not in query_params["devices"]:
                            query_params["devices"].append(normalized_device)
                
                # Check for dates and time periods
                months = {
                    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04", 
                    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
                    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
                    "january": "01", "february": "02", "march": "03", "april": "04",
                    "may": "05", "june": "06", "july": "07", "august": "08",
                    "september": "09", "october": "10", "november": "11", "december": "12"
                }
                
                for month, month_num in months.items():
                    # Look for patterns like "agosto de 2025", "august 2025", etc.
                    year_patterns = [
                        f"{month}\\s+(?:de\\s+)?(\\d{{4}})",
                        f"{month}\\s+(\\d{{4}})",
                    ]
                    
                    for pattern in year_patterns:
                        import re
                        year_matches = re.findall(pattern, original_question.lower())
                        if year_matches:
                            year = year_matches[0]
                            # Add date range for the entire month
                            start_date = f"{year}-{month_num}-01"
                            end_date = f"{year}-{month_num}-31"  # Simplified
                            
                            if start_date not in query_params["dates"]:
                                query_params["dates"].append(start_date)
                            if end_date not in query_params["dates"]:
                                query_params["dates"].append(end_date)
            
            # Format the parameters for better prompt inclusion
            formatted_params = {}
            for key, values in query_params.items():
                if values:
                    formatted_params[key] = values
            
            return formatted_params
            
        except Exception as e:
            print(f"Error extracting query parameters: {str(e)}")
            return {}
    
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
- Calculate conversion rates: `(payment_confirmation_loaded * 100.0) / NULLIF(traffic, 0)`
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
- If your SQL query returns NO DATA for the requested time period, BE EXPLICIT about this fact and DO NOT INVENT DATA

### 3.1 Handling Future Dates
- When users ask about FUTURE dates (e.g., any date after the current date):
  1. ALWAYS construct and execute a specific SQL query for that date range
  2. Example for future date query: 
     ```sql
     SELECT 
         date, 
         culture, 
         traffic, 
         payment_confirmation_loaded,
         -- IMPORTANT: Use CAST or multiply by 100.0 to ensure floating point division
         (payment_confirmation_loaded * 100.0 / NULLIF(traffic, 0)) AS conversion_rate
     FROM amplitude.funnels_resumido
     WHERE culture = 'CL' AND date >= '2025-08-01' AND date <= '2025-08-31'
     ```
  3. When the query returns no rows (as expected), state: "No data is available for [specific time period]"
  4. DO NOT invent or fabricate metrics when no data is available

### 3. Technical Best Practices
- Validate query results before analysis
- Handle null values appropriately
- Use CASE statements for conditional logic
- Apply date functions (DATE_TRUNC, EXTRACT) for time analysis
- Limit result sets when appropriate

### 4. Response Format
Always structure your responses as:
1. **SQL Query**: The exact query executed
2. **Data Availability**: Explicitly state if the query returned data or not
   - If NO DATA: "No data available for the requested [time period/criteria]"
   - If data exists: "Query returned X rows of data"
3. **Results Summary**: Key metrics and findings (ONLY if data exists)
4. **Technical Analysis**: Statistical insights and calculations (ONLY if data exists)
5. **Recommendations**: Data-driven suggestions (ONLY if data exists)

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
        # Extract previous query parameters from conversation history
        last_query_params = self._extract_query_params_from_context(context)
        try:
            # Create the analysis message with previous query parameters if available
            context_with_params = f"{context or 'None provided'}\n\nPrevious Query Parameters: {last_query_params}"
            
            analysis_prompt = f"""
Business Question to Analyze: {business_question}

Additional Context: {context_with_params}

VERY IMPORTANT: You MUST ALWAYS use the sql_query tool to execute a query against the amplitude.funnels_resumido table. Using only get_schema_info is NOT sufficient to answer questions.

Please follow these steps:
1. CRITICAL: Analyze the conversation history first
   - Look at "Previous Query Parameters" section in the additional context
   - For follow-up questions, REUSE these parameters (dates, cultures, etc.)
   - MOST IMPORTANT: If this is a follow-up about previous results, ALWAYS use the SAME date range and culture

2. REQUIRED: Execute an SQL query against amplitude.funnels_resumido table
   - Use sql_query tool - NOT just get_schema_info
   - MANDATORY FORMAT: "SELECT column1, column2... FROM amplitude.funnels_resumido WHERE..."
   - For follow-up questions about results, use SAME date and filter parameters as previous query

3. For your SQL query:
   - Always use schema prefix 'amplitude.' for table names
   - For dates, use: WHERE date >= '2025-08-01' AND date <= '2025-08-31'
   - When calculating conversion rate: (payment_confirmation_loaded * 100.0) / NULLIF(traffic, 0)
   - If previous query used specific parameters (e.g., "Chile", "August 2025"), REUSE THEM
   
4. Check the query results:
   - If the query returns no rows, state "No data exists for [time period]"
   - DO NOT invent data if none is returned

5. IMPORTANT - DATA PRESENTATION FORMAT:
   - When user asks for data tables, ALWAYS present results as formatted markdown tables
   - Example markdown table format:
     ```
     | Fecha | Dispositivo | Tráfico | Conversión |
     |-------|------------|---------|------------|
     | 01-08 | Mobile     | 1500    | 3.2%       |
     | 02-08 | Desktop    | 2300    | 4.5%       |
     ```
   - Make sure table columns are properly aligned
   - Include headers with clear column names
   - For large datasets, limit to top 10-15 rows unless asked for more

6. Provide your response including:
   - The exact SQL query you executed
   - Whether data was found or not
   - Analysis of any data found
   - PROPERLY FORMATTED DATA TABLES when the user asks for tables or detailed data

EXAMPLE: If a previous question was about "conversion rates in Chile for August 2025" and the next question asks for "the complete table", use the SAME date range and country filter.

IMPORTANT: If the user asks about metrics for a specific time period like "August 2025", you MUST execute an SQL query for that specific period, even though it's a future date, to demonstrate there's no data.
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
            
            print("\n==== DATA ANALYST DEBUG ====")
            print(f"Question: {business_question}")
            print(f"Initial tool calls: {[tc['name'] for tc in response.tool_calls] if response.tool_calls else 'None'}")
            
            # Store all tool results for debug output
            debug_tool_results = []
            
            # Execute tools if requested
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    print(f"\nExecuting tool: {tool_name}")
                    print(f"Tool args: {tool_args}")
                    
                    # Find and execute the tool
                    tool = next((t for t in self.tools if t.name == tool_name), None)
                    if tool:
                        try:
                            tool_result = tool.invoke(tool_args)
                            
                            # Store for debug
                            debug_tool_results.append({
                                "tool": tool_name,
                                "args": tool_args,
                                "result": tool_result[:500] + "..." if len(tool_result) > 500 else tool_result
                            })
                            
                            print(f"Tool result (truncated): {tool_result[:200]}...")
                            
                            # Add tool result to messages
                            messages.append({
                                "role": "tool",
                                "content": tool_result,
                                "tool_call_id": tool_call["id"]
                            })
                        except Exception as e:
                            error_msg = f"Tool execution failed: {str(e)}"
                            debug_tool_results.append({
                                "tool": tool_name, 
                                "args": tool_args,
                                "error": error_msg
                            })
                            print(f"Tool error: {error_msg}")
                            
                            messages.append({
                                "role": "tool", 
                                "content": error_msg,
                                "tool_call_id": tool_call["id"]
                            })
                
                # Verify if an SQL query was executed
                sql_query_executed = False
                executed_sql = ""
                for result in debug_tool_results:
                    if result["tool"] == "sql_query":
                        sql_query_executed = True
                        try:
                            # Try to extract the executed SQL query
                            if "args" in result and "query" in result["args"]:
                                executed_sql = result["args"]["query"]
                            elif "query_executed" in json.loads(result["result"]):
                                executed_sql = json.loads(result["result"])["query_executed"]
                        except:
                            executed_sql = "Unable to extract SQL query"
                        break
                
                # If no SQL query was executed, force one to be executed
                if not sql_query_executed:
                    print("\n⚠️ WARNING: No SQL query was executed. Forcing a query execution...")
                    
                    # Create a default query to the table
                    default_query = """
                    SELECT 
                        date, 
                        culture, 
                        device, 
                        traffic_type,
                        traffic,
                        payment_confirmation_loaded,
                        (CAST(payment_confirmation_loaded AS DECIMAL(18,2)) * 100.0 / NULLIF(traffic, 0)) as conversion_rate
                    FROM 
                        amplitude.funnels_resumido
                    WHERE 
                        date BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE
                    LIMIT 5
                    """
                    
                    # Execute the query
                    try:
                        print(f"Executing default SQL query: {default_query}")
                        
                        # Find the SQL tool
                        sql_tool = next((t for t in self.tools if t.name == "sql_query"), None)
                        if sql_tool:
                            # Execute the tool
                            tool_result = sql_tool.invoke({"query": default_query})
                            
                            # Add result to debug info
                            debug_tool_results.append({
                                "tool": "sql_query",
                                "args": {"query": default_query},
                                "result": tool_result[:500] + "..." if len(tool_result) > 500 else tool_result,
                                "forced": True
                            })
                            
                            # Add to messages
                            messages.append({
                                "role": "tool",
                                "content": f"I've executed a SQL query for you: {default_query}\n\nResult: {tool_result}",
                                "tool_call_id": "forced_query"
                            })
                            
                            executed_sql = default_query
                            print("Default query executed successfully")
                        else:
                            print("ERROR: sql_query tool not found")
                    except Exception as e:
                        print(f"ERROR executing default query: {str(e)}")
                
                # Get final response after tool execution
                final_response = llm_with_tools.invoke(messages)
                
                print("\nFinal response from Data Analyst:")
                print(f"{final_response.content[:300]}...")
                print(f"SQL query executed: {sql_query_executed or 'Forced query'}")
                print(f"SQL query: {executed_sql}")
                print("==== END DEBUG ====\n")
                
                response_content = final_response.content
                
                # If SQL query was forced, append information about it
                if not sql_query_executed and executed_sql:
                    response_content += "\n\nNOTE: I've executed a query against the amplitude.funnels_resumido table to verify data availability."
                
                # Extract and store parameters from this query for future reference
                extracted_params = {}
                for result in debug_tool_results:
                    if result["tool"] == "sql_query" and "args" in result and "query" in result["args"]:
                        query = result["args"]["query"]
                        # Update conversation memory
                        try:
                            # Extract culture/country
                            import re
                            culture_matches = re.findall(r"culture\s*=\s*['\"]([A-Z]{2})['\"]", query)
                            if culture_matches:
                                extracted_params["culture"] = culture_matches[0]
                            
                            # Extract date ranges
                            date_patterns = [
                                r"date\s*>=\s*['\"](\d{4}-\d{2}-\d{2})['\"]",
                                r"date\s*<=\s*['\"](\d{4}-\d{2}-\d{2})['\"]"
                            ]
                            dates = []
                            for pattern in date_patterns:
                                matches = re.findall(pattern, query)
                                dates.extend(matches)
                            
                            if dates:
                                extracted_params["dates"] = dates
                                
                            # Extract device
                            device_matches = re.findall(r"device\s*=\s*['\"](\w+)['\"]", query)
                            if device_matches:
                                extracted_params["device"] = device_matches[0]
                        except Exception as e:
                            print(f"Error extracting parameters: {str(e)}")
                
                # Store in conversation memory
                if extracted_params:
                    self.conversation_memory.update(extracted_params)
                    print(f"Updated conversation memory: {self.conversation_memory}")
                
                return {
                    "success": True,
                    "analysis": response_content,
                    "technical_details": {
                        "tools_used": [tc["name"] for tc in response.tool_calls] + ([] if sql_query_executed else ["sql_query"]),
                        "query_executed": True,
                        "executed_sql": executed_sql,
                        "query_parameters": extracted_params,
                        "debug_info": {
                            "question": business_question,
                            "tool_results": debug_tool_results,
                            "conversation_memory": self.conversation_memory
                        }
                    }
                }
            else:
                print("\n⚠️ WARNING: No tool calls made by Data Analyst. Forcing a SQL query...")
                
                # Create a default query related to the question
                default_query = """
                SELECT 
                    date, 
                    culture, 
                    device, 
                    traffic_type,
                    traffic,
                    payment_confirmation_loaded,
                    (payment_confirmation_loaded * 100.0 / NULLIF(traffic, 0)) as conversion_rate
                FROM 
                    amplitude.funnels_resumido
                WHERE 
                    date BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE
                LIMIT 5
                """
                
                # Try to extract keywords from the question to make query more relevant
                query_lower = business_question.lower()
                
                # Check for country/culture
                countries = {"chile": "CL", "brasil": "BR", "peru": "PE", 
                            "paraguay": "PY", "argentina": "AR", "colombia": "CO",
                            "ecuador": "EC", "uruguay": "UY", "estados unidos": "US"}
                
                for country, code in countries.items():
                    if country in query_lower:
                        default_query = default_query.replace("WHERE", f"WHERE culture = '{code}' AND")
                        break
                
                # Check for device type
                if "mobile" in query_lower or "móvil" in query_lower:
                    default_query = default_query.replace("WHERE", "WHERE device = 'mobile' AND")
                elif "desktop" in query_lower or "escritorio" in query_lower:
                    default_query = default_query.replace("WHERE", "WHERE device = 'desktop' AND")
                
                # Execute the query
                try:
                    print(f"Executing forced SQL query: {default_query}")
                    
                    # Find the SQL tool
                    sql_tool = next((t for t in self.tools if t.name == "sql_query"), None)
                    if sql_tool:
                        # Execute the tool
                        tool_result = sql_tool.invoke({"query": default_query})
                        
                        # Create debug info
                        debug_tool_results = [{
                            "tool": "sql_query",
                            "args": {"query": default_query},
                            "result": tool_result[:500] + "..." if len(tool_result) > 500 else tool_result,
                            "forced": True
                        }]
                        
                        # Add to messages
                        messages.append({
                            "role": "tool",
                            "content": f"I've executed a SQL query for you: {default_query}\n\nResult: {tool_result}",
                            "tool_call_id": "forced_query"
                        })
                        
                        print(f"Forced SQL query result: {tool_result[:200]}...")
                        
                        # Get final response after adding SQL results
                        final_response = llm_with_tools.invoke(messages)
                        
                        print("\nFinal response after forced SQL query:")
                        print(f"{final_response.content[:300]}...")
                        print("==== END DEBUG ====\n")
                        
                        response_content = final_response.content
                        if "no data" not in response_content.lower():
                            response_content += "\n\nNOTE: I've executed a query against the amplitude.funnels_resumido table to provide this analysis."
                        
                        return {
                            "success": True,
                            "analysis": response_content,
                            "technical_details": {
                                "tools_used": ["sql_query"],
                                "query_executed": True,
                                "executed_sql": default_query,
                                "debug_info": {
                                    "question": business_question,
                                    "tool_results": debug_tool_results,
                                    "original_response": response.content
                                }
                            }
                        }
                    else:
                        print("ERROR: sql_query tool not found")
                        # If SQL tool not found, return the original response without modification
                except Exception as e:
                    print(f"ERROR executing forced query: {str(e)}")
                
                # If we failed to execute the forced query, return the original response
                print("==== END DEBUG ====\n")
                return {
                    "success": True,
                    "analysis": response.content + "\n\nNote: I attempted to query the database but encountered an error.",
                    "technical_details": {
                        "tools_used": [],
                        "query_executed": False,
                        "debug_info": {
                            "question": business_question,
                            "response": response.content,
                            "error": "Failed to execute forced query"
                        }
                    }
                }
                
        except Exception as e:
            print(f"\nERROR in Data Analyst: {str(e)}")
            print("==== END DEBUG ====\n")
            
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
