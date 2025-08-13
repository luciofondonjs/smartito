"""
Ejemplo de uso del sistema SMARTito Multi-Agent RAG
"""

import os
import sys
from dotenv import load_dotenv

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.workflows.multi_agent_workflow import MultiAgentWorkflow


def run_examples():
    """Ejecutar ejemplos de preguntas de negocio."""
    
    # Cargar variables de entorno
    load_dotenv()
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Error: OPENAI_API_KEY no configurada en .env")
        return
    
    # Inicializar workflow
    print("🤖 Inicializando SMARTito...")
    workflow = MultiAgentWorkflow(openai_api_key)
    
    # Ejemplos de preguntas
    examples = [
        "¿Cuál es la tasa de conversión en Brasil para diciembre 2024?",
        "Compara el rendimiento móvil vs desktop el último mes",
        "¿Qué países tienen el mayor tráfico orgánico?",
        "Muéstrame las tendencias de conversión por fuente de tráfico",
        "¿Cuál es el tiempo promedio de conversión por dispositivo?"
    ]
    
    print("\n" + "="*60)
    print("📊 EJEMPLOS DE ANÁLISIS DE NEGOCIO")
    print("="*60)
    
    for i, question in enumerate(examples, 1):
        print(f"\n🔍 EJEMPLO {i}:")
        print(f"Pregunta: {question}")
        print("-" * 50)
        
        try:
            result = workflow.run(question, f"example_{i}")
            
            if result["success"]:
                if result["needs_clarification"]:
                    print("❓ CLARIFICACIÓN NECESARIA:")
                    print(result["response"])
                else:
                    print("✅ ANÁLISIS COMPLETADO:")
                    print(result["response"])
                    
                    # Mostrar metadata
                    metadata = result.get("metadata", {})
                    if metadata.get("tools_used"):
                        print(f"\n🔧 Herramientas utilizadas: {', '.join(metadata['tools_used'])}")
            else:
                print("❌ Error en el análisis:")
                print(result["response"])
                
        except Exception as e:
            print(f"❌ Error inesperado: {str(e)}")
        
        print("\n" + "="*60)
        
        # Pausa entre ejemplos
        input("Presiona Enter para continuar al siguiente ejemplo...")


def test_individual_agents():
    """Probar agentes individuales."""
    
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        print("❌ Error: OPENAI_API_KEY no configurada")
        return
    
    print("\n🧪 PRUEBAS DE AGENTES INDIVIDUALES")
    print("="*50)
    
    # Importar agentes
    from src.agents.business_analyst import BusinessAnalystAgent
    from src.agents.data_analyst import DataAnalystAgent
    
    # Probar Business Analyst
    print("\n1️⃣ Prueba del Business Analyst:")
    ba = BusinessAnalystAgent(openai_api_key)
    
    test_question = "¿Cuál es la conversión en Brasil?"
    result = ba.interpret_user_question(test_question)
    
    if result["success"]:
        print("✅ Interpretación exitosa:")
        print(result["interpretation"])
    else:
        print("❌ Error en Business Analyst:", result["error"])
    
    # Probar Data Analyst (sin ejecución real)
    print("\n2️⃣ Prueba del Data Analyst:")
    da = DataAnalystAgent(openai_api_key)
    
    print("✅ Data Analyst inicializado correctamente")
    print(f"🔧 Herramientas disponibles: {[tool.name for tool in da.tools]}")


def show_system_info():
    """Mostrar información del sistema."""
    
    print("\n🔍 INFORMACIÓN DEL SISTEMA")
    print("="*40)
    
    # Verificar dependencias
    try:
        import langchain
        print(f"✅ LangChain: {langchain.__version__}")
    except ImportError:
        print("❌ LangChain no instalado")
    
    try:
        import langgraph
        print(f"✅ LangGraph: Instalado")
    except ImportError:
        print("❌ LangGraph no instalado")
    
    try:
        import pandas
        print(f"✅ Pandas: {pandas.__version__}")
    except ImportError:
        print("❌ Pandas no instalado")
    
    try:
        import psycopg2
        print(f"✅ Psycopg2: Instalado")
    except ImportError:
        print("❌ Psycopg2 no instalado")
    
    # Verificar variables de entorno
    load_dotenv()
    
    print("\n🔧 CONFIGURACIÓN:")
    print(f"OpenAI API Key: {'✅ Configurada' if os.getenv('OPENAI_API_KEY') else '❌ No configurada'}")
    print(f"Redshift Host: {'✅ Configurado' if os.getenv('REDSHIFT_HOST') else '❌ No configurado'}")
    print(f"Redshift Database: {'✅ Configurado' if os.getenv('REDSHIFT_DATABASE') else '❌ No configurado'}")


def main():
    """Función principal del script de ejemplos."""
    
    print("🤖 SMARTito - Sistema Multi-Agente RAG")
    print("Ejemplos de Uso y Pruebas")
    print("="*50)
    
    while True:
        print("\n📋 OPCIONES DISPONIBLES:")
        print("1. Ejecutar ejemplos completos")
        print("2. Probar agentes individuales")
        print("3. Mostrar información del sistema")
        print("4. Salir")
        
        choice = input("\nSelecciona una opción (1-4): ").strip()
        
        if choice == "1":
            run_examples()
        elif choice == "2":
            test_individual_agents()
        elif choice == "3":
            show_system_info()
        elif choice == "4":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida. Por favor selecciona 1-4.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
