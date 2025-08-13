"""
Multi-agent workflow using LangGraph for orchestrating Business and Data Analyst agents.
"""

from typing import Dict, Any, List, Literal
from typing_extensions import TypedDict
import json
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

from ..agents.business_analyst import BusinessAnalystAgent
from ..agents.data_analyst import DataAnalystAgent


class WorkflowState(TypedDict):
    """State management for the multi-agent workflow."""
    
    # Input
    user_question: str
    conversation_history: List[Dict[str, str]]  # For context
    
    # Business Analyst outputs
    question_interpretation: Dict[str, Any]
    clarifying_questions: List[str]
    business_synthesis: Dict[str, Any]
    
    # Data Analyst outputs
    technical_analysis: Dict[str, Any]
    
    # Workflow control
    needs_clarification: bool
    analysis_complete: bool
    error_occurred: bool
    error_message: str
    
    # Final output
    final_response: str


class MultiAgentWorkflow:
    """
    LangGraph workflow that orchestrates Business and Data Analyst agents.
    
    Flow:
    1. User asks question
    2. Business Analyst interprets question
    3. Check if clarification needed
    4. Data Analyst performs technical analysis  
    5. Business Analyst synthesizes results
    6. Return business-friendly response
    """
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.business_analyst = BusinessAnalystAgent(openai_api_key)
        self.data_analyst = DataAnalystAgent(openai_api_key)
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
        
        # Add memory for conversation state
        memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=memory)
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        
        # Define the workflow graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (each represents a step in the process)
        workflow.add_node("interpret_question", self._interpret_question)
        workflow.add_node("check_clarification", self._check_clarification)
        workflow.add_node("perform_analysis", self._perform_technical_analysis)
        workflow.add_node("synthesize_results", self._synthesize_business_results)
        workflow.add_node("handle_error", self._handle_error)
        
        # Define the flow edges
        workflow.add_edge(START, "interpret_question")
        
        # After interpretation, check if clarification is needed
        workflow.add_conditional_edges(
            "interpret_question",
            self._should_ask_clarification,
            {
                "clarify": "check_clarification",
                "analyze": "perform_analysis",
                "error": "handle_error"
            }
        )
        
        # If clarification needed, end workflow to ask user
        workflow.add_edge("check_clarification", END)
        
        # After technical analysis, synthesize results
        workflow.add_conditional_edges(
            "perform_analysis", 
            self._check_analysis_success,
            {
                "synthesize": "synthesize_results",
                "error": "handle_error"
            }
        )
        
        # After synthesis, end workflow
        workflow.add_edge("synthesize_results", END)
        workflow.add_edge("handle_error", END)
        
        return workflow
    
    def _interpret_question(self, state: WorkflowState) -> WorkflowState:
        """Business Analyst interprets the user question."""
        try:
            # Convert conversation history to expected format
            conversation_history = []
            for entry in state.get("conversation_history", []):
                if isinstance(entry, tuple) and len(entry) == 2:
                    role, content = entry
                    conversation_history.append({"role": role, "content": content})
                elif isinstance(entry, dict):
                    conversation_history.append(entry)
            
            # Interpret with conversation history
            result = self.business_analyst.interpret_user_question(
                state["user_question"], 
                conversation_history
            )
            
            if result["success"]:
                state["question_interpretation"] = result
                
                # Check if clarification is needed - pass conversation history for context
                clarifying_questions = self.business_analyst.ask_clarifying_questions(
                    state["user_question"], 
                    conversation_history
                )
                state["clarifying_questions"] = clarifying_questions
                state["needs_clarification"] = len(clarifying_questions) > 0
            else:
                state["error_occurred"] = True
                state["error_message"] = result.get("error", "Failed to interpret question")
                
        except Exception as e:
            state["error_occurred"] = True
            state["error_message"] = f"Error in question interpretation: {str(e)}"
        
        return state
    
    def _check_clarification(self, state: WorkflowState) -> WorkflowState:
        """Prepare clarifying questions for the user or proceed with a direct answer."""
        questions = state.get("clarifying_questions", [])
        user_question = state.get("user_question", "").lower()
        
        # Verificar si el usuario está solicitando explícitamente una respuesta directa
        direct_answer_phrases = [
            "no quiero", "sin clarificaciones", "respuesta directa", 
            "responde ya", "dame los datos", "no preguntes", "general"
        ]
        
        # Determinar si debemos forzar una respuesta directa
        force_direct_answer = any(phrase in user_question for phrase in direct_answer_phrases)
        
        # Si hay un indicador explícito de solicitud directa o no hay preguntas de clarificación
        if force_direct_answer or not questions:
            # Forzar el flujo a continuar con análisis en lugar de preguntar
            state["needs_clarification"] = False
            state["final_response"] = "Analizando su consulta..."
            return state
            
        # Si llegamos aquí, presentamos las preguntas de clarificación de forma concisa
        clarification_text = "To answer accurately:"
        for i, question in enumerate(questions, 1):
            clarification_text += f"\n{i}. {question}"
        
        state["final_response"] = clarification_text
        return state
    
    def _perform_technical_analysis(self, state: WorkflowState) -> WorkflowState:
        """Data Analyst performs technical analysis."""
        try:
            business_question = state["user_question"]
            context = state.get("question_interpretation", {})
            
            result = self.data_analyst.analyze_request(business_question, context)
            
            if result["success"]:
                state["technical_analysis"] = result
                state["analysis_complete"] = True
            else:
                state["error_occurred"] = True
                state["error_message"] = result.get("error", "Technical analysis failed")
                
        except Exception as e:
            state["error_occurred"] = True
            state["error_message"] = f"Error in technical analysis: {str(e)}"
        
        return state
    
    def _synthesize_business_results(self, state: WorkflowState) -> WorkflowState:
        """Business Analyst synthesizes technical results."""
        try:
            user_question = state["user_question"]
            technical_analysis = state["technical_analysis"]["analysis"]
            
            # Convert conversation history to expected format
            conversation_history = []
            for entry in state.get("conversation_history", []):
                if isinstance(entry, tuple) and len(entry) == 2:
                    role, content = entry
                    conversation_history.append({"role": role, "content": content})
                elif isinstance(entry, dict):
                    conversation_history.append(entry)
            
            # Pass conversation context to synthesis
            result = self.business_analyst.synthesize_results(
                user_question, 
                technical_analysis, 
                conversation_history
            )
            
            if result["success"]:
                state["business_synthesis"] = result
                state["final_response"] = result["business_response"]
            else:
                state["error_occurred"] = True
                state["error_message"] = result.get("error", "Failed to synthesize results")
                
        except Exception as e:
            state["error_occurred"] = True
            state["error_message"] = f"Error in result synthesis: {str(e)}"
        
        return state
    
    def _handle_error(self, state: WorkflowState) -> WorkflowState:
        """Handle errors in the workflow."""
        error_message = state.get("error_message", "An unknown error occurred")
        
        state["final_response"] = f"Error: {error_message}. Please try rephrasing your question or be more specific about time periods, markets, or device types."
        
        return state
    
    def _should_ask_clarification(self, state: WorkflowState) -> Literal["clarify", "analyze", "error"]:
        """Decide whether to ask for clarification or proceed with analysis."""
        if state.get("error_occurred", False):
            return "error"
            
        # Por defecto, SIEMPRE vamos a preferir dar una respuesta directa
        # Solo hacemos clarificaciones en casos extremadamente específicos
        force_direct_answer = True
        
        # Verificar que la pregunta tenga información mínima necesaria para un análisis
        user_question = state.get("user_question", "").lower()
        
        # Si NO hay preguntas de clarificación, simplemente seguimos con el análisis
        clarifying_questions = state.get("clarifying_questions", [])
        if not clarifying_questions:
            force_direct_answer = True
            
        # Lista extendida de indicadores que sugieren respuesta directa
        direct_answer_indicators = [
            "no quiero", "respuesta directa", "dame", "necesito", "ahora", "ya", 
            "por favor", "general", "without", "directly", "datos", "métricas", 
            "resultados", "información", "tasa", "porcentaje", "conversión", 
            "evolución", "tendencia", "quiero saber", "conocer"
        ]
        
        # Si el usuario parece estar pidiendo una respuesta directa, saltamos la clarificación
        if any(phrase in user_question for phrase in direct_answer_indicators):
            force_direct_answer = True
            
        # Verificar si la pregunta incluye una métrica específica y un país o dimensión
        # En ese caso, probablemente es suficientemente clara
        metrics = ["conversión", "conversion", "tráfico", "traffic", "visitas", "visits", "rendimiento"]
        dimensions = ["chile", "brasil", "argentina", "colombia", "peru", "mobile", "desktop", "móvil"]
        
        if any(metric in user_question for metric in metrics) and any(dim in user_question for dim in dimensions):
            force_direct_answer = True
        
        # Revisar el historial de la conversación
        conversation_history = state.get("conversation_history", [])
        if conversation_history:
            # Si ya hubo una clarificación previa, no hacemos más
            if any("clarific" in str(entry).lower() for entry in conversation_history):
                force_direct_answer = True
        
        if force_direct_answer:
            # Forzar el análisis directo sin hacer más preguntas
            state["needs_clarification"] = False
            return "analyze"
        elif state.get("needs_clarification", False):
            return "clarify" 
        else:
            return "analyze"
    
    def _check_analysis_success(self, state: WorkflowState) -> Literal["synthesize", "error"]:
        """Check if technical analysis was successful."""
        if state.get("error_occurred", False) or not state.get("analysis_complete", False):
            return "error"
        else:
            return "synthesize"
    
    def run(self, user_question: str, thread_id: str = "default", conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Run the complete multi-agent workflow.
        
        Args:
            user_question: The user's business question
            thread_id: Unique identifier for conversation thread
            conversation_history: Previous conversation context
            
        Returns:
            Dictionary with workflow results
        """
        try:
            # Initialize state
            initial_state = WorkflowState(
                user_question=user_question,
                conversation_history=conversation_history or [],
                question_interpretation={},
                clarifying_questions=[],
                business_synthesis={},
                technical_analysis={},
                needs_clarification=False,
                analysis_complete=False,
                error_occurred=False,
                error_message="",
                final_response=""
            )
            
            # Configure thread
            config = {"configurable": {"thread_id": thread_id}}
            
            # Run workflow
            final_state = self.app.invoke(initial_state, config)
            
            return {
                "success": not final_state.get("error_occurred", False),
                "response": final_state.get("final_response", "No response generated"),
                "needs_clarification": final_state.get("needs_clarification", False),
                "clarifying_questions": final_state.get("clarifying_questions", []),
                "metadata": {
                    "analysis_completed": final_state.get("analysis_complete", False),
                    "tools_used": final_state.get("technical_analysis", {}).get("technical_details", {}).get("tools_used", []),
                    "thread_id": thread_id
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"Error: {str(e)}",
                "needs_clarification": False,
                "clarifying_questions": [],
                "metadata": {
                    "analysis_completed": False,
                    "tools_used": [],
                    "thread_id": thread_id,
                    "error": str(e)
                }
            }
    
    def get_workflow_graph(self) -> str:
        """
        Get a visual representation of the workflow graph.
        
        Returns:
            String representation of the workflow
        """
        return """
Multi-Agent RAG Workflow:

┌─────────────┐
│    START    │
└──────┬──────┘
       │
┌──────▼──────┐
│  Interpret  │ ← Business Analyst
│  Question   │   understands user needs
└──────┬──────┘
       │
┌──────▼──────┐
│   Check     │
│Clarification│
└─────┬─┬─────┘
      │ │
  Yes │ │ No
      │ │
┌─────▼─┴─────┐    ┌──────────────┐
│    Ask      │    │   Perform    │ ← Data Analyst
│Clarification│    │   Analysis   │   executes queries
└─────────────┘    └──────┬───────┘
      │                   │
      │            ┌──────▼───────┐
      │            │  Synthesize  │ ← Business Analyst
      │            │   Results    │   interprets findings
      │            └──────┬───────┘
      │                   │
┌─────▼───────────────────▼─┐
│         END             │
└─────────────────────────┘

Key Features:
• Automatic question interpretation
• Clarification when needed
• Technical SQL analysis
• Business-friendly responses
• Error handling throughout
"""
