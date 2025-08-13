"""
SMARTito - Interfaz de chat con Streamlit
"""

import os
import sys
import streamlit as st
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple

# Añadir src al Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.workflows.multi_agent_workflow import MultiAgentWorkflow

# Configuración de la página
st.set_page_config(
    page_title="SMARTito Chat",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Carga de variables de entorno
load_dotenv()

# Estilos CSS personalizados para tema oscuro similar a ChatGPT
st.markdown("""
<style>
    /* Estilo general de la página */
    .main {
        background-color: #1e1e1e; /* Fondo oscuro */
        color: #ffffff;
    }
    
    /* Estilos de Streamlit generales */
    .stApp {
        background-color: #1e1e1e;
    }
    
    /* Cabecera del chat */
    .chat-header {
        background-color: #202123;
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Mensajes del usuario */
    .user-message {
        background-color: #343541;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.8rem 0;
        border-left: 4px solid #10a37f;
        box-shadow: 0 1px 4px rgba(0,0,0,0.3);
        color: #ffffff;
    }
    
    /* Mensajes del asistente */
    .assistant-message {
        background-color: #444654;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.8rem 0;
        border-left: 4px solid #5436da;
        box-shadow: 0 1px 4px rgba(0,0,0,0.3);
        color: #ffffff;
    }
    
    /* Cuadro de entrada */
    .stTextInput>div>div>input {
        border-radius: 25px;
        padding: 12px 20px;
        border: 1px solid #4d4d4f;
        font-size: 1rem;
        background-color: #40414f;
        color: #ffffff;
        box-shadow: 0 0 10px rgba(0,0,0,0.2);
    }
    
    /* Enfoque en el cuadro de entrada */
    .stTextInput>div>div>input:focus {
        border-color: #5436da;
        box-shadow: 0 0 0 1px #5436da;
    }
    
    /* Placeholder del cuadro de entrada */
    .stTextInput>div>div>input::placeholder {
        color: #c5c5d2;
    }
    
    /* Estilos para metadata */
    .metadata {
        font-size: 0.75rem;
        color: #a9a9b3;
        margin-top: 5px;
        padding-top: 5px;
        border-top: 1px solid #444654;
    }
    
    /* Estilos para tablas */
    .dataframe {
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 0.9rem;
        min-width: 400px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.4);
        background-color: #343541;
        color: #ffffff;
    }
    
    .dataframe thead th {
        background-color: #5436da;
        color: white;
        text-align: left;
        padding: 12px 15px;
    }
    
    .dataframe tbody tr {
        border-bottom: 1px solid #444654;
    }
    
    .dataframe tbody tr:nth-of-type(even) {
        background-color: #444654;
    }
    
    .dataframe tbody tr:last-of-type {
        border-bottom: 2px solid #5436da;
    }
    
    .dataframe tbody td {
        padding: 10px 15px;
        color: #ffffff;
    }
    
    /* Contenedor de tablas */
    .table-container {
        margin: 15px 0;
        padding: 10px;
        border-radius: 8px;
        background-color: #40414f;
        border-left: 4px solid #10a37f;
    }
    
    /* Animación de carga */
    .loading {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255,255,255,.2);
        border-radius: 50%;
        border-top-color: #5436da;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Texto de pensando */
    .thinking {
        display: inline-block;
        color: #a9a9b3;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    
    /* Oculta el spinner nativo de Streamlit */
    .stSpinner {
        display: none !important;
    }
    
    /* Botón de enviar */
    .stButton>button {
        background-color: #5436da;
        color: white;
        border-radius: 25px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #7b61ff;
        box-shadow: 0 0 15px rgba(84, 54, 218, 0.4);
    }   
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #202123;
        color: #ffffff;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    /* Ajustes para elementos streamlit nativos */
    .element-container, div.row-widget.stRadio > div {
        background-color: transparent !important;
        color: #ffffff !important;
    }
    
    /* Estilos para links */
    a {
        color: #7b61ff !important;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    /* Footer */
    footer {
        background-color: #1e1e1e !important;
        color: #a9a9b3 !important;
    }
    
    /* Ocultando marca de agua y menú de Streamlit */
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 10px;
        background-color: #1e1e1e;
    }
    
    ::-webkit-scrollbar-thumb {
        background-color: #444654;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background-color: #5436da;
    }
</style>
""", unsafe_allow_html=True)

# Título y descripción
st.markdown('<div class="chat-header"><h1>🤖 SMARTito</h1><p>Asistente de Análisis de Métricas de Negocio</p></div>', unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = f"streamlit_session_{hash(os.urandom(32))}"
    
    if "workflow" not in st.session_state:
        # Inicializar SMARTito
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("⚠️ No se encontró la API key de OpenAI. Por favor, configura el archivo .env")
            st.stop()
        
        st.session_state.workflow = MultiAgentWorkflow(openai_api_key)

def format_message(msg_obj: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    """Format message with metadata."""
    role = msg_obj.get("role", "user")
    content = msg_obj.get("content", "")
    metadata = msg_obj.get("metadata", {})
    
    return role, content, metadata

def extract_table_from_markdown(content):
    """Extract markdown tables from content and convert them to DataFrames."""
    import re
    import pandas as pd
    import io
    
    # Regex para encontrar tablas markdown
    table_pattern = r'(\|[^\n]*\|\n\|([-:\s]*\|)+\n[\s\S]*?(?=\n\n|\n#|\n$))'
    tables = re.findall(table_pattern, content)
    
    extracted_tables = []
    for table_str in tables:
        table_str = table_str[0] if isinstance(table_str, tuple) else table_str
        
        try:
            # Intentar convertir la tabla de markdown a DataFrame
            # Convertimos la tabla markdown a StringIO para que pandas la pueda leer
            df = pd.read_csv(io.StringIO(table_str), sep='|', skipinitialspace=True)
            
            # Limpiar el DataFrame
            df = df.dropna(axis=1, how='all')  # Eliminar columnas vacías
            df.columns = df.columns.str.strip()  # Eliminar espacios en nombres de columnas
            
            # Si las columnas tienen nombres como 'Unnamed: X', intentar usar la primera fila como encabezados
            if any(['Unnamed:' in col for col in df.columns]):
                headers = df.iloc[0].values
                df = df.iloc[1:]
                df.columns = headers
                df = df.reset_index(drop=True)
            
            extracted_tables.append(df)
            
            # Reemplazar la tabla en el contenido con un marcador
            content = content.replace(table_str, f'[[TABLE_{len(extracted_tables)-1}]]')
        except Exception as e:
            print(f"Error al convertir tabla markdown a DataFrame: {e}")
    
    return content, extracted_tables

def display_messages():
    """Display all messages in the chat."""
    for msg in st.session_state.messages:
        role, content, metadata = format_message(msg)
        
        if role == "user":
            st.markdown(f'<div class="user-message"><strong>👤 Usuario:</strong> {content}</div>', unsafe_allow_html=True)
        else:
            # Procesar tablas en la respuesta
            processed_content, tables = extract_table_from_markdown(content)
            
            # Si se encontraron tablas, mostrar el contenido con las tablas reemplazadas
            if tables:
                # Dividir el contenido por los marcadores de tabla
                content_parts = processed_content.split('[[TABLE_')
                
                # Mostrar el primer fragmento de texto
                if content_parts[0].strip():
                    st.markdown(f'<div class="assistant-message"><strong>🤖 SMARTito:</strong> {content_parts[0]}</div>', unsafe_allow_html=True)
                
                # Para cada marcador de tabla, mostrar la tabla correspondiente
                for i, part in enumerate(content_parts[1:], 0):
                    if ']]' in part:
                        table_idx, remaining = part.split(']]', 1)
                        try:
                            table_idx = int(table_idx)
                            if table_idx < len(tables):
                                st.markdown('<div class="table-container">', unsafe_allow_html=True)
                                st.markdown("**📊 Tabla de datos:**")
                                st.dataframe(tables[table_idx], use_container_width=True, 
                                            column_config={col: st.column_config.Column(
                                                width="auto",
                                            ) for col in tables[table_idx].columns})
                                st.markdown('</div>', unsafe_allow_html=True)
                                
                                # Mostrar el texto restante si existe
                                if remaining.strip():
                                    st.markdown(f'<div class="assistant-message">{remaining}</div>', unsafe_allow_html=True)
                        except ValueError:
                            # Si no se puede convertir a entero, mostrar como texto normal
                            st.markdown(f'<div class="assistant-message">{part}</div>', unsafe_allow_html=True)
            else:
                # Si no hay tablas, mostrar el contenido normal
                st.markdown(f'<div class="assistant-message"><strong>🤖 SMARTito:</strong> {content}</div>', unsafe_allow_html=True)
            
            # Display metadata if available
            if metadata and "tools_used" in metadata:
                tools_used = metadata.get("tools_used", [])
                if tools_used:
                    st.markdown(f'<div class="metadata">🔧 Herramientas utilizadas: {", ".join(tools_used)}</div>', unsafe_allow_html=True)
                    
                # Si se usó sql_query, mostrar también los datos devueltos como tabla
                if "sql_query" in tools_used and "query_executed" in metadata:
                    if "debug_info" in metadata and "tool_results" in metadata["debug_info"]:
                        for tool_result in metadata["debug_info"]["tool_results"]:
                            if tool_result.get("tool") == "sql_query" and "result" in tool_result:
                                try:
                                    import json
                                    result_data = json.loads(tool_result["result"])
                                    if result_data.get("success") and result_data.get("has_data", False):
                                        import pandas as pd
                                        df = pd.DataFrame(result_data["data"])
                                        if not df.empty:
                                            st.markdown('<div class="table-container">', unsafe_allow_html=True)
                                            st.markdown("**📊 Datos obtenidos de la base de datos:**")
                                            
                                            # Configurar las columnas para mejor visualización
                                            column_configs = {}
                                            for col in df.columns:
                                                if col.lower() in ["date", "fecha"]:
                                                    column_configs[col] = st.column_config.DateColumn("Fecha", format="DD-MM-YYYY")
                                                elif any(name in col.lower() for name in ["rate", "ratio", "conversion", "porcentaje"]):
                                                    column_configs[col] = st.column_config.NumberColumn(
                                                        col, 
                                                        format="%.2f%%", 
                                                        width="medium"
                                                    )
                                                else:
                                                    column_configs[col] = st.column_config.Column(width="auto")
                                                    
                                            # Mostrar el DataFrame con configuraciones personalizadas
                                            st.dataframe(df, 
                                                        use_container_width=True,
                                                        column_config=column_configs,
                                                        hide_index=True)
                                            st.markdown('</div>', unsafe_allow_html=True)
                                except Exception as e:
                                    print(f"Error al procesar resultados SQL: {e}")

def process_user_input():
    """Process user input and get response from SMARTito."""
    user_input = st.session_state.user_input
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Clear input field
        st.session_state.user_input = ""
        
        # Get previous conversation context
        conversation_context = []
        for msg in st.session_state.messages[:-1]:  # Exclude current message
            role, content, _ = format_message(msg)
            conversation_context.append((role, content))
        
        # Display thinking indicator with custom styling
        with st.spinner():
            # Add temporary thinking message
            thinking_container = st.empty()
            thinking_container.markdown(
                '<div class="assistant-message"><strong>🤖 SMARTito:</strong> <span class="thinking">Pensando...</span></div>',
                unsafe_allow_html=True
            )
            
            # Process the query
            result = st.session_state.workflow.run(
                user_input, 
                st.session_state.conversation_id,
                conversation_context
            )
            
            # Remove thinking message
            thinking_container.empty()
        
        # Add assistant response to chat
        st.session_state.messages.append({
            "role": "assistant",
            "content": result["response"],
            "metadata": result["metadata"]
        })
        
        # Force refresh
        st.rerun()

def main():
    """Main application function."""
    initialize_session_state()
    display_messages()
    
    # Input container with custom styling
    input_container = st.container()
    
    # Add a subtle divider before the input
    st.markdown('<hr style="border: 0; height: 1px; background-color: #444654; margin: 20px 0;">', unsafe_allow_html=True)
    
    # Create columnas para el input y botones
    col1, col2 = st.columns([8, 1])
    
    # Input text en la columna principal
    with col1:
        st.text_input(
            "",  # Sin label
            key="user_input",
            on_change=process_user_input,
            placeholder="¿Con qué puedo ayudarte?",
            label_visibility="collapsed"
        )
    
    # Botón en la segunda columna (opcional)
    with col2:
        if st.button("💬", key="send_button", help="Enviar mensaje"):
            if st.session_state.user_input:
                process_user_input()
    
    # Tips in the sidebar
    with st.sidebar:
        st.markdown("### 💡 Ejemplos de preguntas")
        st.markdown("""
        - ¿Cuál es la tasa de conversión en Brasil para diciembre?
        - Compara el rendimiento móvil vs desktop
        - ¿Qué países tienen el mayor tráfico orgánico?
        - Muéstrame las tendencias de conversión por fuente de tráfico
        """)
        
        st.markdown("### ⚙️ Datos disponibles")
        st.markdown("""
        - **Países**: Chile (CL), Brasil (BR), Perú (PE), etc.
        - **Dispositivos**: Mobile, Desktop
        - **Fuentes**: Orgánico, Pagado, Promoted
        - **Métricas**: Conversión, Tráfico, Tiempo de conversión
        """)
        
        st.markdown("---")
        st.markdown("Desarrollado con 💚 por el equipo SMARTito")

if __name__ == "__main__":
    main()
