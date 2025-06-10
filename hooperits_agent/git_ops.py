# hooperits_agent/git_ops.py
"""
Operaciones Git para gestión de repositorios.
"""
import git
from pathlib import Path
from rich.console import Console
from .config import REPOS_BASE_PATH, LOG_LEVEL, LOG_FILE
from .utils import setup_logging, validate_repo_name, show_progress
from typing import List, Optional

console = Console()
logger = setup_logging(LOG_LEVEL, LOG_FILE)

def clone_repo(repo_url: str, dir_name: Optional[str] = None) -> bool:
    """
    Clona un repositorio en el directorio base gestionado.
    
    Args:
        repo_url: URL del repositorio a clonar
        dir_name: Nombre opcional del directorio local
        
    Returns:
        True si se clonó exitosamente, False en caso contrario
    """
    logger.info(f"Intentando clonar repositorio: {repo_url}")
    
    if not repo_url:
        console.print("[bold red]Error: URL del repositorio no puede estar vacía.[/bold red]")
        logger.error("URL del repositorio vacía")
        return False

    if dir_name:
        # Validar nombre del directorio
        if not validate_repo_name(dir_name):
            console.print(f"[bold red]Error: Nombre de directorio local '{dir_name}' inválido.[/bold red]")
            logger.error(f"Nombre de directorio inválido: {dir_name}")
            return False
        repo_path = REPOS_BASE_PATH / dir_name
    else:
        # Derivar nombre del directorio desde la URL si no se proporciona
        try:
            dir_name_from_url = Path(repo_url).stem # Toma el nombre del archivo sin extensión .git
            if not dir_name_from_url: # Si stem está vacío (ej. URL termina en /)
                raise ValueError("No se pudo derivar el nombre del repo desde la URL.")
            repo_path = REPOS_BASE_PATH / dir_name_from_url
        except Exception as e:
            console.print(f"[bold red]Error: No se pudo determinar el nombre del directorio desde la URL: {e}[/bold red]")
            console.print("Por favor, especifica un nombre con --name.")
            return False
    
    if repo_path.exists():
        try:
            git.Repo(repo_path) # Verificar si ya es un repo Git
            console.print(f"[yellow]El directorio '{repo_path.name}' ya existe y es un repositorio Git.[/yellow]")
            return True # Considerarlo un éxito si ya existe y es repo
        except git.InvalidGitRepositoryError:
            console.print(f"[bold red]Error: El directorio '{repo_path.name}' ya existe pero NO es un repositorio Git.[/bold red]")
            return False
        except Exception as e:
            console.print(f"[bold red]Error verificando el directorio existente '{repo_path.name}': {e}[/bold red]")
            return False

    console.print(f"Clonando [cyan]{repo_url}[/cyan] en [green]{repo_path}[/green]...")
    try:
        git.Repo.clone_from(repo_url, repo_path)
        console.print(f"[bold green]Repositorio clonado exitosamente como '{repo_path.name}'.[/bold green]")
        return True
    except git.GitCommandError as e:
        console.print(f"[bold red]Error de Git al clonar: {e.stderr}[/bold red]")
        return False
    except Exception as e:
        console.print(f"[bold red]Error inesperado al clonar: {e}[/bold red]")
        return False

def list_local_repos() -> List[str]:
    """
    Lista los repositorios locales gestionados.
    
    Returns:
        Lista ordenada de nombres de repositorios
    """
    logger.debug("Listando repositorios locales")
    
    if not REPOS_BASE_PATH.exists() or not REPOS_BASE_PATH.is_dir():
        logger.warning(f"Directorio de repositorios no existe: {REPOS_BASE_PATH}")
        return []
    
    local_repos = []
    for item in REPOS_BASE_PATH.iterdir():
        if item.is_dir():
            try:
                git.Repo(item) # Verificar si es un repo Git
                local_repos.append(item.name)
                logger.debug(f"Repositorio encontrado: {item.name}")
            except git.InvalidGitRepositoryError:
                logger.debug(f"Directorio no es un repositorio Git: {item.name}")
                continue # No es un repo, ignorar
            except Exception as e:
                logger.warning(f"Error al verificar directorio {item.name}: {e}")
                continue # Otros errores, ignorar
    
    logger.info(f"Se encontraron {len(local_repos)} repositorios")
    return sorted(local_repos)
