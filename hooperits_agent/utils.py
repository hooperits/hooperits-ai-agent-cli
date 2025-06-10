"""
Utilidades comunes para HOOPERITS AI CODE AGENT.
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

console = Console()

# Configuración de logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configura el sistema de logging para la aplicación.
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_file: Archivo opcional para guardar logs
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger("hooperits_agent")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Formato de logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo si se especifica
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Sistema de caché simple
class SimpleCache:
    """Sistema de caché simple basado en archivos JSON."""
    
    def __init__(self, cache_dir: Path = None, expiration_seconds: int = 3600):
        """
        Inicializa el sistema de caché.
        
        Args:
            cache_dir: Directorio para almacenar caché
            expiration_seconds: Tiempo de expiración en segundos
        """
        self.cache_dir = cache_dir or Path.home() / ".hooperits_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.expiration_seconds = expiration_seconds
        self.cache_file = self.cache_dir / "gemini_responses.json"
        
    def _get_cache_key(self, prompt: str, model: str) -> str:
        """Genera una clave única para el prompt y modelo."""
        content = f"{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, prompt: str, model: str) -> Optional[str]:
        """
        Obtiene una respuesta del caché si existe y no ha expirado.
        
        Args:
            prompt: El prompt original
            model: El modelo usado
            
        Returns:
            La respuesta cacheada o None si no existe/expiró
        """
        if not self.cache_file.exists():
            return None
            
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
            
        key = self._get_cache_key(prompt, model)
        if key not in cache_data:
            return None
            
        entry = cache_data[key]
        expiration = datetime.fromisoformat(entry['expiration'])
        
        if datetime.now() > expiration:
            # Entrada expirada
            return None
            
        return entry['response']
    
    def set(self, prompt: str, model: str, response: str):
        """
        Guarda una respuesta en el caché.
        
        Args:
            prompt: El prompt original
            model: El modelo usado
            response: La respuesta a cachear
        """
        cache_data = {}
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        key = self._get_cache_key(prompt, model)
        expiration = datetime.now() + timedelta(seconds=self.expiration_seconds)
        
        cache_data[key] = {
            'response': response,
            'expiration': expiration.isoformat(),
            'model': model,
            'created': datetime.now().isoformat()
        }
        
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    
    def clear(self):
        """Limpia todo el caché."""
        if self.cache_file.exists():
            self.cache_file.unlink()
            
    def cleanup_expired(self):
        """Elimina entradas expiradas del caché."""
        if not self.cache_file.exists():
            return
            
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return
            
        now = datetime.now()
        cleaned_data = {}
        
        for key, entry in cache_data.items():
            expiration = datetime.fromisoformat(entry['expiration'])
            if now <= expiration:
                cleaned_data[key] = entry
                
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

# Funciones de validación
def validate_repo_name(name: str) -> bool:
    """
    Valida que el nombre del repositorio sea válido.
    
    Args:
        name: Nombre del repositorio
        
    Returns:
        True si es válido, False si no
    """
    if not name or not name.strip():
        return False
    
    # Caracteres no permitidos en nombres de directorios
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0']
    return not any(char in name for char in invalid_chars)

def validate_file_path(file_path: Union[str, Path], base_path: Path) -> bool:
    """
    Valida que una ruta de archivo esté dentro del directorio base.
    
    Args:
        file_path: Ruta del archivo a validar
        base_path: Directorio base permitido
        
    Returns:
        True si la ruta es segura, False si no
    """
    try:
        file_path = Path(file_path).resolve()
        base_path = Path(base_path).resolve()
        return file_path.is_relative_to(base_path)
    except (ValueError, RuntimeError):
        return False

# Funciones de formateo
def format_file_size(size_bytes: int) -> str:
    """
    Formatea un tamaño en bytes a formato legible.
    
    Args:
        size_bytes: Tamaño en bytes
        
    Returns:
        Cadena formateada (ej: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca texto a una longitud máxima.
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a agregar si se trunca
        
    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

# Funciones de progreso
def show_progress(task_description: str, duration: float = 2.0):
    """
    Muestra un spinner de progreso durante una operación.
    
    Args:
        task_description: Descripción de la tarea
        duration: Duración simulada en segundos
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(task_description, total=None)
        time.sleep(duration)

# Funciones de análisis
def count_tokens_estimate(text: str) -> int:
    """
    Estima el número de tokens en un texto.
    Usa una aproximación simple (1 token ≈ 4 caracteres).
    
    Args:
        text: Texto a analizar
        
    Returns:
        Número estimado de tokens
    """
    # Aproximación simple: 1 token ≈ 4 caracteres
    # Esto es una estimación muy básica, los modelos reales usan tokenización compleja
    return len(text) // 4

def get_file_info(file_path: Path) -> Dict[str, Any]:
    """
    Obtiene información detallada sobre un archivo.
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        Diccionario con información del archivo
    """
    if not file_path.exists():
        return {"error": "File not found"}
        
    stat = file_path.stat()
    
    return {
        "name": file_path.name,
        "path": str(file_path),
        "size": stat.st_size,
        "size_formatted": format_file_size(stat.st_size),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "is_file": file_path.is_file(),
        "is_dir": file_path.is_dir(),
        "extension": file_path.suffix if file_path.is_file() else None,
    }

# Funciones de sanitización
def sanitize_filename(filename: str) -> str:
    """
    Sanitiza un nombre de archivo eliminando caracteres no válidos.
    
    Args:
        filename: Nombre de archivo a sanitizar
        
    Returns:
        Nombre de archivo sanitizado
    """
    # Caracteres no válidos en nombres de archivo
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0']
    
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Eliminar espacios al inicio y final
    sanitized = sanitized.strip()
    
    # Si queda vacío, usar un nombre por defecto
    if not sanitized:
        sanitized = "unnamed"
    
    return sanitized

# Funciones de costo
def format_cost(cost: float, currency: str = "USD") -> str:
    """
    Formatea un costo monetario.
    
    Args:
        cost: Valor del costo
        currency: Moneda (por defecto USD)
        
    Returns:
        Costo formateado
    """
    if currency == "USD":
        return f"${cost:.6f}"
    else:
        return f"{cost:.6f} {currency}"

# Exportar todas las funciones y clases públicas
__all__ = [
    'setup_logging',
    'SimpleCache',
    'validate_repo_name',
    'validate_file_path',
    'format_file_size',
    'truncate_text',
    'show_progress',
    'count_tokens_estimate',
    'get_file_info',
    'sanitize_filename',
    'format_cost',
]
