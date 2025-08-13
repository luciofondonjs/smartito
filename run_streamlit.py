"""
Script para iniciar la aplicación de Streamlit.
"""

import os
import subprocess
import sys

def main():
    """Función principal para iniciar la aplicación de Streamlit."""
    print("🚀 Iniciando SMARTito Chat...")
    
    # Verificar si Streamlit está instalado
    try:
        import streamlit
        print("✅ Streamlit está instalado.")
    except ImportError:
        print("⚠️ Streamlit no está instalado. Instalando dependencias...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencias instaladas.")
    
    # Verificar variables de entorno
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️ No se encontró la variable de entorno OPENAI_API_KEY.")
        print("⚠️ Intentando cargar desde el archivo .env...")
        
        try:
            from dotenv import load_dotenv
            load_dotenv()
            if os.environ.get("OPENAI_API_KEY"):
                print("✅ Variables de entorno cargadas desde .env.")
            else:
                print("❌ No se encontró OPENAI_API_KEY en .env.")
                print("   Por favor, configure su API key en el archivo .env")
                return
        except ImportError:
            print("❌ No se pudo importar dotenv. Asegúrese de instalar las dependencias.")
            return
    else:
        print("✅ Variable de entorno OPENAI_API_KEY encontrada.")
    
    # Verificar la conexión a la base de datos
    print("\n🔍 Probando conexión a la base de datos...")
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from src.config.database import get_database_connection
        
        db = get_database_connection()
        success = db.test_connection()
        
        if success:
            print("✅ Conexión a la base de datos exitosa.")
        else:
            print("⚠️ Advertencia: La conexión a la base de datos falló.")
            print("   Algunas funcionalidades pueden no estar disponibles.")
            
            # Preguntar al usuario si desea continuar
            response = input("¿Desea continuar de todas formas? (s/n): ").strip().lower()
            if response != 's' and response != 'si' and response != 'yes' and response != 'y':
                print("Saliendo...")
                return
    except Exception as e:
        print(f"⚠️ Error al probar la conexión a la base de datos: {str(e)}")
        print("  Algunas funcionalidades pueden no estar disponibles.")
        
        # Preguntar al usuario si desea continuar
        response = input("¿Desea continuar de todas formas? (s/n): ").strip().lower()
        if response != 's' and response != 'si' and response != 'yes' and response != 'y':
            print("Saliendo...")
            return
    
    # Iniciar Streamlit
    print("\n🚀 Iniciando interfaz web de SMARTito...")
    print("📊 La aplicación estará disponible en http://localhost:8501")
    print("⌨️  Presiona Ctrl+C para detener la aplicación.")
    
    streamlit_command = [sys.executable, "-m", "streamlit", "run", "streamlit_app.py"]
    subprocess.run(streamlit_command)

if __name__ == "__main__":
    main()
