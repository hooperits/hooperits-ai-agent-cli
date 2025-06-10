# 🤖 HOOPERITS AI CODE AGENT

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Gemini AI](https://img.shields.io/badge/Powered%20by-Gemini%20AI-orange.svg)](https://deepmind.google/technologies/gemini/)

Un asistente inteligente de línea de comandos que te ayuda a gestionar y analizar múltiples repositorios de código usando el poder de Google Gemini AI.

## ✨ Características

- 🔧 **Gestión de Repositorios**: Clona, lista y selecciona repositorios activos fácilmente
- 🤖 **Chat con IA**: Interactúa con Gemini AI para obtener respuestas sobre tu código
- 📊 **Análisis de Proyectos**: Obtén análisis inteligentes de la estructura y arquitectura de tus proyectos
- 💰 **Control de Costos**: Estimación de costos en tiempo real para modelos de pago
- 🎯 **Selección de Modelos**: Elige entre múltiples modelos de Gemini según tus necesidades
- 🎨 **Interfaz Rica**: Salida formateada con colores y tablas usando Rich

## 📋 Prerequisitos

- Python 3.8 o superior
- Una clave API de Google Gemini ([Obtener aquí](https://makersuite.google.com/app/apikey))
- Git instalado en tu sistema

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/hooperits-ai-agent-cli.git
cd hooperits-ai-agent-cli
```

### 2. Crear entorno virtual (recomendado)
```bash
python -m venv .venv
source .venv/bin/activate  # En Linux/Mac
# o
.venv\Scripts\activate  # En Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp env.example .env
# Edita .env y agrega tu GOOGLE_API_KEY
```

### 5. Verificar instalación
```bash
python -m hooperits_agent.main --help
```

## 📖 Uso

### Comandos Principales

#### Ver estado actual
```bash
python -m hooperits_agent.main
```

#### Gestión de Repositorios

**Clonar un repositorio:**
```bash
python -m hooperits_agent.main repo clone https://github.com/usuario/repo.git
# o con nombre personalizado
python -m hooperits_agent.main repo clone https://github.com/usuario/repo.git --name mi-proyecto
```

**Listar repositorios:**
```bash
python -m hooperits_agent.main repo list
```

**Seleccionar repositorio activo:**
```bash
python -m hooperits_agent.main repo select nombre-repo
```

**Ver repositorio actual:**
```bash
python -m hooperits_agent.main repo current
```

#### Interacción con Gemini AI

**Chat simple:**
```bash
python -m hooperits_agent.main chat "¿Cuál es la mejor práctica para manejar errores en Python?"
```

**Chat con contexto de archivo:**
```bash
python -m hooperits_agent.main chat "Explica qué hace esta función" --file src/utils.py
```

**Análisis de proyecto:**
```bash
# Analizar repositorio activo
python -m hooperits_agent.main analyze-project

# Analizar repositorio específico
python -m hooperits_agent.main analyze-project --repo otro-proyecto

# Analizar subdirectorio específico
python -m hooperits_agent.main analyze-project --path backend/src
```

#### Gestión de Modelos

**Listar modelos disponibles:**
```bash
python -m hooperits_agent.main model list
```

**Seleccionar modelo:**
```bash
python -m hooperits_agent.main model select models/gemini-1.5-flash-latest
```

### Opciones Globales

- `--yes` o `-y`: Saltar confirmaciones para modelos de pago
- `--help`: Ver ayuda de cualquier comando

## 🔧 Configuración Avanzada

El archivo `.env` soporta las siguientes configuraciones:

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `GOOGLE_API_KEY` | **Requerido**. Tu clave API de Gemini | - |
| `REPOS_BASE_DIRECTORY_NAME` | Directorio para repositorios | `repositories` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `DEFAULT_GEMINI_MODEL` | Modelo por defecto | Auto-selección |
| `MAX_FILE_SIZE_FOR_ANALYSIS` | Tamaño máximo de archivo (bytes) | `1048576` |
| `ENABLE_GEMINI_CACHE` | Habilitar caché de respuestas | `true` |

## 🏗️ Arquitectura

```
hooperits-ai-agent-cli/
├── hooperits_agent/        # Código fuente principal
│   ├── main.py            # CLI principal con Typer
│   ├── gemini_ops.py      # Operaciones con Gemini AI
│   ├── git_ops.py         # Operaciones Git
│   ├── project_analyzer.py # Análisis de proyectos
│   ├── state_manager.py   # Gestión de estado
│   ├── config.py          # Configuración
│   └── utils.py           # Utilidades comunes
├── repositories/          # Repositorios clonados
├── requirements.txt       # Dependencias Python
├── env.example           # Plantilla de configuración
├── model_tiers.json      # Información de modelos
└── README.md            # Este archivo
```

## 💡 Ejemplos de Uso

### Flujo de trabajo típico

1. **Configurar el agente:**
```bash
# Clonar y activar un repositorio
python -m hooperits_agent.main repo clone https://github.com/mi-org/mi-proyecto.git
python -m hooperits_agent.main repo select mi-proyecto
```

2. **Analizar el proyecto:**
```bash
# Obtener un análisis general
python -m hooperits_agent.main analyze-project

# Analizar el backend específicamente
python -m hooperits_agent.main analyze-project --path backend
```

3. **Hacer preguntas sobre el código:**
```bash
# Preguntar sobre un archivo específico
python -m hooperits_agent.main chat "¿Qué patrones de diseño usa este código?" --file src/services/auth.py

# Consulta general
python -m hooperits_agent.main chat "¿Cómo puedo mejorar el rendimiento de las consultas a la base de datos?"
```

### Casos de uso avanzados

**Análisis comparativo:**
```bash
# Analizar arquitectura de múltiples proyectos
for repo in proyecto1 proyecto2 proyecto3; do
    python -m hooperits_agent.main analyze-project --repo $repo > analisis_$repo.md
done
```

**Revisión de código automatizada:**
```bash
# Usar con --yes para automatización
python -m hooperits_agent.main chat "Revisa este código y sugiere mejoras" --file src/api/endpoints.py --yes
```

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea tu rama de características (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [Google Gemini AI](https://deepmind.google/technologies/gemini/) por proporcionar la IA
- [Typer](https://typer.tiangolo.com/) por el excelente framework CLI
- [Rich](https://rich.readthedocs.io/) por la hermosa salida de terminal

## 📧 Contacto

Para preguntas y soporte, por favor abre un issue en GitHub.

---

Hecho con ❤️ y 🤖 por HOOPERITS 