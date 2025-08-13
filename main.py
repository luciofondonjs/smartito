"""
SMARTito - Multi-Agent RAG System for Business Analytics
Main application entry point
"""

import os
import sys
import asyncio
from typing import Optional
from dotenv import load_dotenv

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.workflows.multi_agent_workflow import MultiAgentWorkflow
from src.config.database import get_database_connection, get_database_config


class SMARTitoApp:
    """Main application class for SMARTito multi-agent system."""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Validate required environment variables
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize workflow
        self.workflow = MultiAgentWorkflow(self.openai_api_key)
        
        print("🤖 SMARTito Multi-Agent RAG System initialized!")
        print("📊 Ready to analyze your business metrics!")
    
    def test_database_connection(self) -> bool:
        """Test database connectivity."""
        try:
            print("\n🔍 Testing database connection...")
            db = get_database_connection()
            success = db.test_connection()
            
            if success:
                print("✅ Database connection successful!")
                return True
            else:
                print("❌ Database connection failed!")
                return False
                
        except Exception as e:
            print(f"❌ Database connection error: {str(e)}")
            return False
    
    def show_workflow_diagram(self):
        """Display the workflow diagram."""
        print("\n" + "="*60)
        print("📋 WORKFLOW DIAGRAM")
        print("="*60)
        print(self.workflow.get_workflow_graph())
        print("="*60)
    
    def ask_question(self, question: str, thread_id: str = "default") -> dict:
        """
        Process a business question through the multi-agent workflow.
        
        This method is now a wrapper around ask_question_with_context with empty context.
        
        Args:
            question: User's business question
            thread_id: Unique identifier for conversation thread
            
        Returns:
            Dictionary with response and metadata
        """
        return self.ask_question_with_context(question, thread_id, [])
    
    def _display_result(self, result: dict) -> None:
        """Display the result of the question analysis."""
        if result["success"]:
            print("✅ Analysis completed successfully!")
            
            if result["needs_clarification"]:
                print("\n❓ CLARIFICATION NEEDED:")
                print("-" * 40)
                print(result["response"])
            else:
                print("\n📈 BUSINESS ANALYSIS RESULTS:")
                print("-" * 40)
                print(result["response"])
            
            # Show metadata
            metadata = result.get("metadata", {})
            if metadata.get("tools_used"):
                print(f"\n🔧 Tools used: {', '.join(metadata['tools_used'])}")
            
        else:
            print("❌ Analysis failed!")
            print(f"Error: {result['response']}")
    
    def ask_question_with_context(self, question: str, thread_id: str, context: list) -> dict:
        """
        Process a business question with conversation context.
        
        Args:
            question: User's current question
            thread_id: Unique identifier for conversation thread
            context: Previous conversation context
            
        Returns:
            Dictionary with response and metadata
        """
        print(f"\n🤔 Processing question: '{question}'")
        
        # No modificamos la pregunta original, solo enviamos el contexto como estructura de datos
        # al workflow. Esto evita el problema de que la pregunta se muestre con todo el contexto
        
        # Convertir el contexto a formato adecuado para el workflow
        formatted_history = []
        if context and len(context) > 1:  # Si hay contexto previo
            print("💭 Using conversation context...")
            for i, (role, message) in enumerate(context[:-1]):  # Excluimos la pregunta actual
                formatted_history.append({
                    "role": role,
                    "content": message
                })
        
        print("⏳ Running multi-agent analysis...")
        
        # Pasamos el contexto como parámetro separado al workflow
        return self.workflow.run(question, thread_id, formatted_history)
    
    def interactive_mode(self):
        """Run the application in interactive mode."""
        print("\n" + "="*60)
        print("🚀 SMARTITO INTERACTIVE MODE")
        print("="*60)
        print("Ask questions about your website metrics!")
        print("Examples:")
        print("• 'What's the conversion rate for Brazil last month?'")
        print("• 'Compare mobile vs desktop performance'") 
        print("• 'Show me traffic trends for Q4 2024'")
        print("\nType 'quit' to exit, 'help' for more info")
        print("-" * 60)
        
        # Use consistent thread_id for conversation continuity
        thread_id = f"interactive_session_{hash(self)}"
        conversation_context = []
        
        while True:
            try:
                question = input("\n📝 Your question: ").strip()
                
                if not question:
                    continue
                    
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye! Thanks for using SMARTito!")
                    break
                    
                elif question.lower() in ['help', 'h']:
                    self.show_help()
                    continue
                    
                elif question.lower() in ['diagram', 'workflow']:
                    self.show_workflow_diagram()
                    continue
                    
                elif question.lower() in ['test', 'test-db']:
                    self.test_database_connection()
                    continue
                
                # Add question to context
                conversation_context.append(("user", question))
                
                # Process the question with context
                result = self.ask_question_with_context(question, thread_id, conversation_context)
                
                # Display the result
                self._display_result(result)
                
                # Add response to context
                if result["success"]:
                    conversation_context.append(("assistant", result["response"]))
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for using SMARTito!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
    
    def show_help(self):
        """Show help information."""
        help_text = """
📚 SMARTito Help Guide

🎯 WHAT SMARTITO DOES:
SMARTito is a multi-agent AI system that helps you analyze website metrics 
and business performance using natural language questions.

🤖 THE AGENTS:
• Business Analyst: Understands your business questions and context
• Data Analyst: Executes SQL queries and performs technical analysis

📊 AVAILABLE DATA:
• Website traffic by country/market
• Conversion rates and funnel performance  
• Device performance (mobile vs desktop)
• Traffic source analysis (organic, paid, promoted)
• Time-based trends and comparisons

💬 EXAMPLE QUESTIONS:
• "What's our conversion rate in Brazil for December?"
• "Compare mobile vs desktop performance last quarter"
• "Which countries have the highest traffic?"
• "Show me the funnel drop-off rates by device"
• "How did paid traffic perform vs organic last month?"

🔧 COMMANDS:
• 'help' or 'h' - Show this help
• 'diagram' or 'workflow' - Show workflow diagram
• 'test' or 'test-db' - Test database connection
• 'quit', 'exit', or 'q' - Exit the application

💡 TIPS:
• Be specific about time periods when possible
• Mention specific countries/markets if relevant
• Ask follow-up questions to dive deeper
• The system will ask for clarification if needed
"""
        print(help_text)


def main():
    """Main application entry point."""
    try:
        # Initialize the application
        app = SMARTitoApp()
        
        # Test database connection on startup
        db_ok = app.test_database_connection()
        if not db_ok:
            print("\n⚠️  Warning: Database connection failed. Some features may not work.")
            proceed = input("Continue anyway? (y/n): ").strip().lower()
            if proceed not in ['y', 'yes']:
                print("Exiting...")
                return
        
        # Show workflow diagram
        app.show_workflow_diagram()
        
        # Check if running with command line arguments
        if len(sys.argv) > 1:
            # Command line mode - process single question
            question = " ".join(sys.argv[1:])
            result = app.ask_question(question)
            
            # Exit with appropriate code
            sys.exit(0 if result["success"] else 1)
        else:
            # Interactive mode
            app.interactive_mode()
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
