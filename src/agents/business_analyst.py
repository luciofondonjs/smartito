"""
Business Analyst Agent for interpreting business questions and contextualizing results.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel


class BusinessAnalystAgent:
    """
    Business Analyst Agent that specializes in:
    - Understanding business context and requirements
    - Translating user questions into technical requirements
    - Interpreting technical results for business stakeholders
    - Providing actionable business insights
    """
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model=model,
            temperature=0.3,  # Slightly higher for more creative business interpretations
        )
        
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the Business Analyst agent."""
        return """
You are a **Business Analyst Agent** specializing in airline industry metrics and digital analytics.

## Your Role
You serve as the bridge between business stakeholders and technical data analysis. You:
1. **Interpret user questions** and understand business context
2. **Translate business needs** into technical requirements for the Data Analyst
3. **Analyze technical results** and extract business insights
4. **Communicate findings** in business-friendly language
5. **Provide actionable recommendations** based on data

## Business Context

### Airline Website Funnel
You work with data from an airline website that tracks user behavior through a conversion funnel:
- **Traffic**: Users visiting the website
- **Flight Pages**: Users viewing flight information
- **Payment Confirmation**: Users completing bookings

### Key Business Metrics
- **Conversion Rate**: (Payment Confirmations / Traffic) × 100
- **Funnel Drop-off**: Where users exit the booking process
- **Market Performance**: How different countries/cultures perform
- **Device Performance**: Desktop vs mobile experience
- **Traffic Source Performance**: Organic vs paid vs promoted traffic

### Business Dimensions
- **Culture/Market**: BR (Brazil), CL (Chile), PE (Peru), PY (Paraguay), US (United States), CO (Colombia), AR (Argentina), EC (Ecuador), UY (Uruguay)
- **Device Types**: Desktop, Mobile
- **Traffic Sources**: 
  - Organico (Organic): Direct and SEO traffic
  - Pagado (Paid): Paid advertising traffic  
  - Promoted (Promoted): Social media and promotional traffic

## Response Guidelines

### 1. User Question Analysis
When receiving a user question:
- Identify the key business metric being asked about
- Determine the time period of interest
- Identify relevant dimensions (market, device, traffic source)
- Clarify any ambiguous requirements

### 2. Technical Requirements Translation
For the Data Analyst, provide:
- Clear business question definition
- Specific metrics needed
- Required time periods and filters
- Segmentation requirements
- Context about business importance

### 3. Results Interpretation
When receiving technical analysis:
- FIRST verify if actual data exists - be honest when no data is available for a time period
- NEVER invent or fabricate data that doesn't exist in the technical results
- Translate technical findings into business language only if data exists
- Identify trends, patterns, and anomalies from real data only
- Highlight business implications based only on actual data

### 4. Communication Style
- Use clear, business-friendly language
- Be concise and direct by default - focus on answering the question precisely
- Only provide detailed analysis, recommendations or context when explicitly requested
- Avoid technical jargon when speaking to users
- Provide minimal context for metrics - just enough to make them understandable

## Business Intelligence Framework

### Performance Categories
- **Excellent**: Conversion rate >5%, high traffic engagement
- **Good**: Conversion rate 3-5%, steady performance
- **Needs Improvement**: Conversion rate 1-3%, optimization opportunities
- **Poor**: Conversion rate <1%, requires immediate attention

### Key Questions to Consider
- Is performance improving or declining over time?
- Which markets/devices are performing best/worst?
- Are there seasonal patterns or anomalies?
- What factors might be driving performance changes?
- Where should the business focus optimization efforts?

## Your Approach
1. **Listen carefully** to understand the true business need
2. **Ask clarifying questions** if requirements are unclear
3. **Coordinate with Data Analyst** for technical analysis
4. **Interpret results** in business context
5. **Provide clear, actionable recommendations**

Remember: You are the business expert who makes data meaningful and actionable for decision-makers.
"""
    
    def interpret_user_question(self, user_question: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Interpret a user's business question and prepare it for technical analysis.
        
        Args:
            user_question: Raw question from the user
            conversation_history: Previous conversation context
            
        Returns:
            Dictionary with interpreted requirements
        """
        interpretation_prompt = f"""
A user has asked the following question about airline website performance:

"{user_question}"

Please analyze this question and provide:

1. **Business Context**: What business metric or performance area is the user interested in?

2. **Technical Requirements**: What specific data analysis is needed to answer this question?
   - Time period (if not specified, assume current year)
   - Metrics to calculate
   - Segmentation needed (by culture, device, traffic type)
   - Any comparisons required

3. **Clarifications Needed**: If the question is ambiguous, what clarifications should we ask?

4. **Business Importance**: Why is this question important from a business perspective?

Format your response as a structured analysis that I can use to coordinate with the Data Analyst.
"""
        
        try:
            # Start with system prompt
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add conversation history if available
            if conversation_history and len(conversation_history) > 0:
                # Add a context header
                messages.append(SystemMessage(content="Previous conversation context:"))
                
                # Limit to the most recent exchanges
                relevant_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
                
                # Add each message from history
                for entry in relevant_history:
                    role = entry.get("role", "user")
                    content = entry.get("content", "")
                    
                    if role == "user":
                        messages.append(HumanMessage(content=f"User asked: {content}"))
                    elif role == "assistant":
                        # Summarize long responses
                        if len(content) > 200:
                            content = content[:200] + "..."
                        messages.append(SystemMessage(content=f"You responded: {content}"))
                
                # Add a separator
                messages.append(SystemMessage(content="\nNow consider the current question in light of this context:"))
            
            # Add the current question
            messages.append(HumanMessage(content=interpretation_prompt))
            
            # Invoke the LLM
            response = self.llm.invoke(messages)
            
            return {
                "success": True,
                "interpretation": response.content,
                "original_question": user_question
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to interpret user question: {str(e)}",
                "original_question": user_question
            }
    
    def synthesize_results(self, user_question: str, technical_analysis: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Synthesize technical analysis results into business-friendly response.
        
        Args:
            user_question: Original user question
            technical_analysis: Results from Data Analyst
            conversation_history: Previous conversation context
            
        Returns:
            Dictionary with business synthesis
        """
        # Check if user has requested for detailed analysis
        user_wants_details = False
        if conversation_history:
            for entry in conversation_history:
                if isinstance(entry, dict) and entry.get("role") == "user":
                    content = entry.get("content", "").lower()
                    if any(phrase in content for phrase in ["más detalles", "más información", "explica", "explícame", 
                                                           "recomendaciones", "insights", "explain", "more details", 
                                                           "more information", "recommendations", "elaborate", "analyze"]):
                        user_wants_details = True
                        break
                elif isinstance(entry, tuple) and len(entry) == 2 and entry[0] == "user":
                    content = entry[1].lower()
                    if any(phrase in content for phrase in ["más detalles", "más información", "explica", "explícame", 
                                                           "recomendaciones", "insights", "explain", "more details", 
                                                           "more information", "recommendations", "elaborate", "analyze"]):
                        user_wants_details = True
                        break
        
        # The current question might also have details request
        current_q_lower = user_question.lower()
        if any(phrase in current_q_lower for phrase in ["más detalles", "más información", "explica", "explícame", 
                                                        "recomendaciones", "insights", "explain", "more details", 
                                                        "more information", "recommendations", "elaborate", "analyze"]):
            user_wants_details = True
        
        # Choose the appropriate prompt based on user preference
        if user_wants_details:
            synthesis_prompt = f"""
**Original User Question**: {user_question}

**Technical Analysis Results**: 
{technical_analysis}

As a Business Analyst, provide a detailed analysis of these results:

1. **Data Availability Check**:
   - First, verify if actual data is available in the technical results
   - If there's no data or empty results, clearly state "No data available for [time period/criteria]"
   - DO NOT invent or fabricate metrics if they're not in the technical analysis

2. If data IS available, provide:

   a. **Answer**: Start with a clear, direct answer to the user's question

   b. **Key Findings**: 
      - Main metrics and performance indicators from the data
      - Important trends or patterns observed
      - Notable insights or anomalies

   c. **Business Context**:
      - What these numbers mean for the business
      - How performance compares to expectations

   d. **Actionable Recommendations**:
      - Specific actions the business should consider
      - Areas for optimization or improvement

Use clear, business-friendly language and focus only on insights derived from the actual data available.

IMPORTANT: Review the technical analysis carefully. If SQL queries returned empty/null results or if it mentions no data was found, DO NOT fabricate data in your response.
"""
        else:
            synthesis_prompt = f"""
**Original User Question**: {user_question}

**Technical Analysis Results**: 
{technical_analysis}

As a Business Analyst, provide a concise response:

1. Check if the data is actually available from the database query. 
   - If there's no real data available, clearly state "No data available for [time period/criteria]" 
   - DO NOT make up or invent numbers - be honest about data availability

2. If data is available:
   - Answer the user's question directly and briefly (1-2 sentences)
   - Mention only the most critical numbers/metrics that directly answer the question
   - Keep your entire response under 4 sentences

Be direct, precise, and to the point. The user can always ask for more details if needed.

IMPORTANT: Review the technical analysis carefully. If it mentions no data was found, or if SQL queries returned empty/null results, DO NOT fabricate data in your response.
"""
        
        try:
            # Start with system prompt
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add conversation history if available
            if conversation_history and len(conversation_history) > 0:
                # Add a context header
                messages.append(SystemMessage(content="Previous conversation context:"))
                
                # Limit to the most recent exchanges
                relevant_history = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
                
                # Add each message from history
                for entry in relevant_history:
                    role = entry.get("role", "user")
                    content = entry.get("content", "")
                    
                    if role == "user":
                        messages.append(HumanMessage(content=f"User asked: {content}"))
                    elif role == "assistant":
                        # Only include short snippets from previous responses
                        if len(content) > 100:
                            content = content[:100] + "..."
                        messages.append(SystemMessage(content=f"You responded: {content}"))
                
                # Add a separator
                messages.append(SystemMessage(content="\nNow synthesize the technical analysis in the context of the conversation:"))
            
            # Add the synthesis request
            messages.append(HumanMessage(content=synthesis_prompt))
            
            # Invoke the LLM
            response = self.llm.invoke(messages)
            
            return {
                "success": True,
                "business_response": response.content,
                "original_question": user_question
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to synthesize results: {str(e)}",
                "business_response": "I apologize, but I encountered an error while analyzing the results. Please try your question again."
            }
    
    def ask_clarifying_questions(self, user_question: str, conversation_history: List[Dict[str, str]] = None) -> List[str]:
        """
        Generate clarifying questions if the user's request is ambiguous.
        
        Args:
            user_question: User's original question
            conversation_history: Previous conversation context
            
        Returns:
            List of clarifying questions
        """
        # Primero verificar si el usuario está rechazando explícitamente la necesidad de clarificaciones
        # o si la pregunta ya tiene suficiente información para proporcionar una respuesta
        rejection_phrases = [
            "no quiero más clarificaciones", 
            "no quiero más preguntas", 
            "no quiero clarificación",
            "sin clarificaciones", 
            "sin preguntas", 
            "dame una respuesta directa",
            "responde directamente",
            "ya te expliqué",
            "ya lo dije",
            "por favor responde",
            "no más preguntas",
            "no i want",  # En inglés
            "don't ask",   # En inglés
            "general",
            "datos",
            "métricas",
            "resultados",
            "información"
        ]
        
        # Convierte todo a minúsculas para la comparación
        user_question_lower = user_question.lower()
        
        # Si el usuario está rechazando clarificaciones, no realizar ninguna
        for phrase in rejection_phrases:
            if phrase in user_question_lower:
                return []  # No hacer más preguntas de clarificación
        
        # Verificar también en el contexto reciente si ya se respondieron clarificaciones
        if conversation_history and len(conversation_history) >= 3:
            # Analiza las últimas 3 interacciones por patrones de rechazo o frustración
            recent_exchanges = conversation_history[-3:]
            clarification_count = 0
            
            for entry in recent_exchanges:
                content = entry.get("content", "").lower()
                role = entry.get("role", "")
                
                # Si la asistente ya ha hecho clarificaciones múltiples veces, no hacer más
                if role == "assistant" and ("clarification" in content or "clarificación" in content):
                    clarification_count += 1
                
                # Si el usuario ha respondido pero siguen viniendo clarificaciones, no hacer más
                if role == "user" and any(word in content for word in ["todo", "all", "ambos", "both"]):
                    return []
            
            # Si ya se han hecho demasiadas clarificaciones, parar
            if clarification_count >= 2:
                return []
        
        clarification_prompt = f"""
A user asked: "{user_question}"

IMPORTANT: By default, assume you should answer WITHOUT asking clarifying questions!

Only ask for clarification if the question is SEVERELY ambiguous and meets ALL of the following criteria:
1) There's absolutely NO way to make a reasonable assumption about what the user wants
2) The question is completely unclear about ESSENTIAL information (not just preferences or details)
3) Making an assumption would very likely lead to a completely wrong or misleading answer

Standard assumptions you should make WITHOUT clarification:
- If no specific time period is mentioned, use the most recent complete month or year
- If no specific device is mentioned, analyze ALL devices (desktop + mobile)
- If no traffic source is mentioned, include ALL traffic sources combined
- If no comparison is mentioned, simply provide the requested metric without comparisons
- If no specific country/region is mentioned but context suggests one, use that country

If possible, DO NOT ASK clarifying questions. The vast majority of questions can be answered directly.
For example, "what's the conversion rate for Chile in August?" means GENERAL conversion across all devices and traffic sources.

In 95% of cases, you should respond with "No clarification needed."

If you absolutely must ask for clarification (which should be extremely rare), provide AT MOST 1 essential question.
Format: "1. - Question text"
"""
        
        try:
            # Start with system prompt
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add conversation history if available
            if conversation_history and len(conversation_history) > 0:
                # Add a context header
                messages.append(SystemMessage(content="Previous conversation context:"))
                
                # Limit to the most recent exchanges
                relevant_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
                
                # Add each message from history
                for entry in relevant_history:
                    role = entry.get("role", "user")
                    content = entry.get("content", "")
                    
                    if role == "user":
                        messages.append(HumanMessage(content=f"User asked: {content}"))
                    elif role == "assistant":
                        # Summarize long responses
                        if len(content) > 100:
                            content = content[:100] + "..."
                        messages.append(SystemMessage(content=f"You responded: {content}"))
                
                # Add a separator
                messages.append(SystemMessage(content="\nConsider the context above when determining if this question needs clarification:"))
            
            # Add the current request
            messages.append(HumanMessage(content=clarification_prompt))
            
            # Invoke the LLM
            response = self.llm.invoke(messages)
            
            if "no clarification needed" in response.content.lower():
                return []
            
            # Split response into individual questions
            questions = [q.strip() for q in response.content.split('\n') if q.strip() and q.strip() != '']
            return questions[:3]  # Limit to max 3 questions
            
        except Exception as e:
            return []  # Return empty list if there's an error
