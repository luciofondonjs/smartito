# 🤖 SMARTito - Multi-Agent RAG System

Un sistema de IA multi-agente para análisis de métricas de negocio usando LangGraph y LangChain.

## 📋 Descripción

SMARTito automatiza el análisis de métricas web mediante un flujo conversacional que traduce preguntas de negocio en insights accionables con datos reales. El sistema utiliza dos agentes especializados que trabajan en conjunto:

- **Business Analyst Agent**: Interpreta contexto de negocio y comunica resultados
- **Data Analyst Agent**: Ejecuta consultas SQL y realiza análisis técnico

## 🏗 Arquitectura

```
Usuario → Business Analyst → Data Analyst → Business Analyst → Respuesta
```

### Flujo de Trabajo
1. **Usuario** hace una pregunta sobre métricas
2. **Business Analyst** interpreta el contexto de negocio
3. **Data Analyst** convierte en consultas SQL y analiza datos
4. **Business Analyst** contextualiza resultados técnicos
5. **Respuesta integrada** al usuario

## 📊 Datos Disponibles

El sistema analiza la tabla `funnels_resumido` que contiene:

- **Traffic**: Tráfico del website por cultura, dispositivo y tipo
- **Conversiones**: Páginas de vuelos y confirmaciones de pago  
- **Segmentación**: Por país, dispositivo (mobile/desktop), fuente de tráfico
- **Métricas temporales**: Datos diarios agregados

### Mercados Disponibles
- BR (Brasil), CL (Chile), PE (Perú), PY (Paraguay)
- US (Estados Unidos), CO (Colombia), AR (Argentina)
- EC (Ecuador), UY (Uruguay)

## 🚀 Instalación

### Prerrequisitos
- Python 3.11+
- Acceso a base de datos Redshift
- OpenAI API Key

### Configuración

1. **Clona el repositorio**:
```bash
git clone <repository-url>
cd SMARTito
```

2. **Crea entorno virtual**:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Instala dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configura variables de entorno**:
   
   Edita el archivo `.env` con tus credenciales:
```env
# OpenAI API Key
OPENAI_API_KEY=tu_openai_api_key

# Redshift Configuration  
REDSHIFT_HOST=tu_host_redshift
REDSHIFT_PORT=5439
REDSHIFT_DATABASE=tu_base_datos
REDSHIFT_USERNAME=tu_usuario
REDSHIFT_PASSWORD=tu_contraseña
REDSHIFT_SCHEMA=amplitude
```

## 💻 Uso

### Modo Interactivo
```bash
python main.py
```

### Pregunta Única (CLI)
```bash
python main.py "¿Cuál es la tasa de conversión en Brasil el mes pasado?"
```

### Ejemplos de Preguntas

**📈 Métricas de Conversión**:
- "¿Cuál es la tasa de conversión en Brasil para diciembre?"
- "Muéstrame el embudo de conversión por dispositivo"

**🔍 Análisis Comparativo**:
- "Compara el rendimiento móvil vs desktop el último trimestre"
- "¿Qué países tienen el mayor tráfico?"

**📊 Tendencias Temporales**:
- "Muéstrame las tendencias de tráfico para Q4 2024"
- "¿Cómo se desempeñó el tráfico pagado vs orgánico el mes pasado?"

**🎯 Segmentación**:
- "Analiza el rendimiento por fuente de tráfico"
- "¿Cuáles son las tasas de abandono por dispositivo?"

## 🛠 Estructura del Proyecto

```
SMARTito/
├── src/
│   ├── agents/              # Agentes de IA
│   │   ├── business_analyst.py
│   │   └── data_analyst.py
│   ├── tools/               # Herramientas de base datos
│   │   └── database_tools.py
│   ├── config/              # Configuración
│   │   └── database.py
│   └── workflows/           # Flujos LangGraph
│       └── multi_agent_workflow.py
├── tests/                   # Pruebas unitarias
├── data/                    # Datos de prueba
├── requirements.txt         # Dependencias
├── .env                     # Variables de entorno
├── main.py                  # Aplicación principal
└── README.md               # Documentación
```

## 🔧 Comandos Disponibles

En modo interactivo:
- `help` - Mostrar ayuda
- `diagram` - Ver diagrama del flujo
- `test` - Probar conexión a base de datos  
- `quit` - Salir

## 📝 Características Técnicas

### Agentes Especializados
- **Business Analyst**: GPT-4 optimizado para contexto de negocio
- **Data Analyst**: GPT-4 con herramientas SQL y análisis estadístico

### Herramientas Integradas
- **SQL Query Tool**: Ejecución segura de consultas
- **Data Analysis Tool**: Análisis estadístico automatizado
- **Schema Info Tool**: Información de estructura de datos

### LangGraph Workflow
- Orquestación automática entre agentes
- Manejo de errores y validación
- Preguntas de clarificación cuando es necesario
- Estado de conversación persistente

## 🔒 Seguridad

- Validación de consultas SQL (solo SELECT)
- Sanitización de entradas
- Manejo seguro de credenciales
- Logs de auditoría

## 🚧 Próximas Características

- [ ] Visualizaciones automáticas
- [ ] Exportación de reportes
- [ ] Alertas automáticas
- [ ] API REST
- [ ] Dashboard web
- [ ] Integración con Slack/Teams

## 🤝 Contribución

1. Fork el proyecto
2. Crea tu rama de características (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -am 'Agrega nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)  
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 👥 Equipo

Desarrollado por el equipo SMARTito siguiendo las mejores prácticas de LangChain y LangGraph.

---

*¿Preguntas? Abre un issue o contacta al equipo de desarrollo.*
