# hooperits_agent/state_manager.py
import json
from pathlib import Path
from typing import Optional, Dict, Any
from .config import REPOS_BASE_PATH # Necesitamos la ruta base para validación

# Definir la ubicación del archivo de estado
# ~/.config/hooperits_agent_cli/state.json
CONFIG_DIR = Path.home() / ".config" / "hooperits_agent_cli"
STATE_FILE_PATH = CONFIG_DIR / "state.json"

# Asegurarse de que el directorio de configuración exista
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def _load_state() -> Dict[str, Any]:
    """Carga el estado desde el archivo JSON. Devuelve un diccionario vacío si no existe o hay error."""
    if STATE_FILE_PATH.exists():
        try:
            with open(STATE_FILE_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Si el archivo está corrupto, tratarlo como si no existiera
            return {}
        except Exception:
            # Otros errores de lectura
            return {}
    return {}

def _save_state(state_data: Dict[str, Any]) -> None:
    """Guarda el estado en el archivo JSON."""
    try:
        with open(STATE_FILE_PATH, 'w') as f:
            json.dump(state_data, f, indent=2)
    except Exception as e:
        # Aquí podrías usar `rich.print` si la consola está disponible
        # o simplemente imprimir un error estándar.
        print(f"Error crítico al guardar el estado en {STATE_FILE_PATH}: {e}")


def set_active_repo(repo_name: str) -> bool:
    """Establece el repositorio activo. Verifica si el repositorio existe localmente."""
    repo_path_to_check = REPOS_BASE_PATH / repo_name
    if not repo_path_to_check.is_dir():
        # Podríamos también verificar si es un repo Git válido aquí, pero
        # por ahora, solo la existencia del directorio es suficiente.
        # git_ops.py se encarga de la validez del repo al listar.
        return False # Repositorio no encontrado en la ubicación esperada

    state = _load_state()
    state["active_repo"] = repo_name
    state["repos_base_path"] = str(REPOS_BASE_PATH.resolve()) # Guardar ruta absoluta
    _save_state(state)
    return True

def get_active_repo_name() -> Optional[str]:
    """Obtiene el nombre del repositorio activo actual."""
    state = _load_state()
    return state.get("active_repo")

def get_active_repo_path() -> Optional[Path]:
    """Obtiene la ruta completa (Path object) al repositorio activo actual."""
    repo_name = get_active_repo_name()
    if repo_name:
        # Podríamos verificar si state["repos_base_path"] coincide con config.REPOS_BASE_PATH
        # por si el proyecto se movió, pero por simplicidad, asumimos que es consistente
        # o usamos la configuración actual.
        return REPOS_BASE_PATH / repo_name
    return None

def clear_active_repo() -> None:
    """Limpia la selección del repositorio activo."""
    state = _load_state()
    if "active_repo" in state:
        del state["active_repo"]
    # Opcionalmente, podrías querer mantener repos_base_path si existe
    _save_state(state)
