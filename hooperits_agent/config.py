# hooperits_agent/config.py
"""
Configuración central para HOOPERITS AI CODE AGENT.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables desde el archivo .env en el directorio raíz del proyecto
# Asumimos que config.py está en hooperits_agent/ y .env está un nivel arriba
project_root = Path(__file__).parent.parent 
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path=dotenv_path)

# API Key de Google Gemini (REQUERIDO)
API_KEY = os.getenv("GOOGLE_API_KEY")

# Directorio base para los repositorios clonados
REPOS_DIR_NAME = os.getenv("REPOS_BASE_DIRECTORY_NAME", "repositories")
REPOS_BASE_PATH = project_root / REPOS_DIR_NAME
REPOS_BASE_PATH.mkdir(parents=True, exist_ok=True)

# Configuración de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "hooperits_agent.log")

# Modelo de Gemini por defecto
DEFAULT_GEMINI_MODEL = os.getenv("DEFAULT_GEMINI_MODEL", "")

# Límites para análisis
MAX_FILE_SIZE_FOR_ANALYSIS = int(os.getenv("MAX_FILE_SIZE_FOR_ANALYSIS", "1048576"))  # 1MB por defecto

# Configuración de caché
ENABLE_GEMINI_CACHE = os.getenv("ENABLE_GEMINI_CACHE", "true").lower() == "true"
CACHE_EXPIRATION_SECONDS = int(os.getenv("CACHE_EXPIRATION_SECONDS", "3600"))  # 1 hora por defecto

# Directorio de caché
CACHE_DIR = project_root / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Archivo de estado
STATE_FILE = project_root / ".hooperits_state.json"

if not API_KEY:
    # No imprimir aquí, dejar que el logger lo maneje
    pass
