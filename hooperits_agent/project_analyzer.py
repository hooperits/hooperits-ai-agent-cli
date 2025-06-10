# hooperits_agent/project_analyzer.py
from pathlib import Path
from typing import List, Dict, Tuple, Any
from rich.console import Console
import chardet 

console = Console()

# Configuración para el análisis (ajustada según la discusión)
KEY_FILES_PREFERENCES: Dict[str, int] = {
    # --- Nivel 1: Documentación y Configuración General del Proyecto ---
    "README.md": 1, "README.rst": 1, "README.txt": 1, "README": 1,
    "package.json": 1, 
    "vite.config.js": 2, "vite.config.ts": 2, 
    "tailwind.config.js": 2, "tailwind.config.ts": 2,
    "postcss.config.js": 2,
    "tsconfig.json": 2, 
    "firebase.json": 2, # Ejemplo añadido

    # --- Nivel 2: Puntos de Entrada Principales y Archivos de Ruteo ---
    "main.jsx": 2, "main.tsx": 2,       
    "App.jsx": 2, "App.tsx": 2,         
    "index.html": 3, 
    # "router.ts": 2, "routes.jsx": 2, # Descomentar y ajustar si tienes patrones de ruteo

    "server.js": 2, "index.js": 2, "app.js": 2, 
    "main.py": 2, "app.py": 2, 
    
    # --- Nivel 3: Lógica Principal de la Aplicación (Páginas, Componentes Core) ---
    "tsx": 3,  
    "jsx": 3,  
    "ts": 4,   
    "js": 4,   

    # --- Nivel 4: Otros Archivos de Código o Configuración Relevante ---
    "py": 5, 
    "java": 5, "go": 5, "rb": 5, "php": 5, 
    "requirements.txt": 4, "pyproject.toml": 4, "setup.py": 4, 
    "docker-compose.yml": 4, "Dockerfile": 4,
    ".env.example": 4, ".env": 4, 
    ".eslintrc.js": 5, ".prettierrc.js": 5, 
    "netlify.toml": 3,

    # --- Nivel 5: Estilos, HTML (menos prioritarios para entender la lógica central que TSX/JSX) ---
    "html": 6, # index.html ya tiene prioridad 3
    "css": 7, "scss": 7, "less": 7, "pcss": 7, 
    "json": 6, # package.json ya tiene prioridad 1

    # --- Nivel 6: Menos Prioritarios ---
    "md": 8, 
    "txt": 8,
    "ipynb": 9 
}
EXCLUDE_DIRS = ['.git', '.venv', 'venv', 'ENV', 'node_modules', '__pycache__', 'target', 'build', 'dist', '.vscode', '.idea', 'public/mockServiceWorker.js'] # Añadido mockServiceWorker
EXCLUDE_EXTENSIONS = ['log', 'tmp', 'lock', 'bak', 'swp', 'map', 'min.js', 'min.css', 'svg', 'ico', 'webmanifest'] # Añadidas extensiones comunes de assets
BINARY_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'tar', 'gz', 'rar', 'exe', 'dll', 'so', 'o', 'a', 'lib', 'jar', 'war', 'ear', 'class', 'pyc', 'pyo', 'mp3', 'mp4', 'avi', 'mkv', 'webm', 'mov', 'wav', 'ogg', 'flac', 'iso', 'img', 'dmg', 'sqlite', 'db', 'eot', 'ttf', 'woff', 'woff2'] # Añadidas fuentes

MAX_FILES_TO_CONSIDER_FOR_PROMPT = 10  
MAX_CONTENT_LENGTH_PER_FILE = 7000   
MAX_TOTAL_CONTENT_LENGTH = 60000   

def _detect_encoding(file_path: Path) -> str:
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10240) 
            if not raw_data: # Archivo vacío
                return 'utf-8'
            result = chardet.detect(raw_data)
            return result['encoding'] if result and result['encoding'] and result.get('confidence', 0) > 0.5 else 'utf-8'
    except Exception:
        return 'utf-8' 

def get_project_files_for_analysis(path_to_scan: Path, repo_root_path: Path) -> List[Dict[str, str]]:
    if not path_to_scan or not path_to_scan.is_dir():
        console.print(f"[bold red]Error: La ruta a escanear '{path_to_scan}' no es válida.[/bold red]")
        return []

    display_scan_path = path_to_scan.relative_to(repo_root_path) if path_to_scan != repo_root_path else repo_root_path.name
    console.print(f"\n[dim]Escaneando archivos en [cyan]{display_scan_path}[/cyan] para análisis (relativo a la raíz del repo)...[/dim]")
    
    potential_files: List[Dict[str, Any]] = []
    for item in path_to_scan.rglob('*'):
        # Comprobar si alguna parte de la ruta absoluta contiene directorios excluidos
        # Esto es para evitar descender en directorios como node_modules incluso si el path_to_scan está dentro de uno.
        # La comprobación original también es útil si path_to_scan es la raíz.
        try:
            # relative_to_root_for_exclusion_check = item.absolute().relative_to(repo_root_path.absolute())
            # if any(excluded_dir.lower() in part.lower() for part in relative_to_root_for_exclusion_check.parts for excluded_dir in EXCLUDE_DIRS):
            #     continue
            # Simplificando la comprobación de exclusión de directorios:
            is_excluded_dir = False
            for part in item.parts:
                if part.lower() in [d.lower() for d in EXCLUDE_DIRS]:
                    is_excluded_dir = True
                    break
            if is_excluded_dir:
                continue

        except ValueError: # item podría no estar dentro de repo_root_path si path_to_scan es un enlace simbólico fuera.
            pass # Continuar con la siguiente comprobación si esto falla.

        if item.is_file():
            relative_path_from_repo_root = item.relative_to(repo_root_path) # Siempre relativo a la raíz
            
            file_name_lower = item.name.lower()
            file_ext_lower = item.suffix.lower().lstrip('.')

            if file_ext_lower in EXCLUDE_EXTENSIONS or file_ext_lower in BINARY_EXTENSIONS:
                continue
            # Excluir archivos ocultos más genéricamente, pero permitir algunos conocidos
            # También excluir archivos de assets que pueden estar en `public` o `assets`
            if item.name.startswith('.') and item.name.lower() not in ['.gitignore', '.env', '.dockerignore', '.npmrc', '.yarnrc', '.prettierrc', '.eslintrc.cjs']:
                continue
            if "public" in [p.lower() for p in relative_path_from_repo_root.parts[:-1]] or \
               "assets" in [p.lower() for p in relative_path_from_repo_root.parts[:-1]]:
                if file_ext_lower not in ['html', 'js', 'css', 'ts', 'tsx', 'jsx']: # Permitir HTML/JS/CSS en public/assets
                    continue


            priority = KEY_FILES_PREFERENCES.get(file_name_lower, KEY_FILES_PREFERENCES.get(file_ext_lower, 99))
            
            path_str_lower_for_priority = str(relative_path_from_repo_root).lower().replace('\\', '/')
            
            if path_str_lower_for_priority.startswith(("frontend/src/pages/", "src/pages/")):
                priority = max(1, priority - 3) # Mayor prioridad
            elif path_str_lower_for_priority.startswith(("frontend/src/components/", "src/components/", "frontend/src/layouts/", "src/layouts/")):
                priority = max(1, priority - 2) 
            elif path_str_lower_for_priority.startswith(("frontend/src/core/", "src/core/", "frontend/src/lib/", "src/lib/", "frontend/src/hooks/", "src/hooks/")):
                priority = max(1, priority - 1)
            elif path_str_lower_for_priority.startswith(("backend/", "server/", "api/")): # Rutas comunes de backend
                 priority = max(1, priority - 2) 
            elif file_name_lower in ("app.tsx", "app.jsx", "main.tsx", "main.jsx", "_app.tsx", "_app.jsx", "index.ts", "index.js"): # Archivos raíz de frontend
                if path_str_lower_for_priority.startswith(("frontend/src/", "src/")):
                    priority = max(1, priority-1)


            try:
                file_size = item.stat().st_size
                if file_size == 0 or file_size > (MAX_CONTENT_LENGTH_PER_FILE * 10): 
                    continue
                potential_files.append({
                    "path_obj": item, 
                    "path_str": str(relative_path_from_repo_root).replace('\\', '/'),
                    "priority": priority, 
                    "size": file_size
                })
            except OSError:
                continue 

    potential_files.sort(key=lambda x: (x["priority"], x["size"]))

    selected_files_content: List[Dict[str, str]] = []
    current_total_length = 0
    files_added_count = 0

    for file_info in potential_files:
        if files_added_count >= MAX_FILES_TO_CONSIDER_FOR_PROMPT:
            console.print(f"[yellow]Límite de {MAX_FILES_TO_CONSIDER_FOR_PROMPT} archivos para prompt alcanzado.[/yellow]")
            break
        if current_total_length >= MAX_TOTAL_CONTENT_LENGTH:
            console.print(f"[yellow]Límite de contenido total ({MAX_TOTAL_CONTENT_LENGTH} chars) para prompt alcanzado.[/yellow]")
            break

        try:
            encoding = _detect_encoding(file_info["path_obj"])
            with open(file_info["path_obj"], 'r', encoding=encoding, errors='replace') as f:
                content = f.read(MAX_CONTENT_LENGTH_PER_FILE)
            
            if len(content) == 0 and file_info["size"] > 0 : 
                # console.print(f"  [yellow]~[/yellow] Omitiendo [dim]{file_info['path_str']}[/dim] (no se pudo leer como texto o está vacío después de leer).")
                continue

            if current_total_length + len(content) <= MAX_TOTAL_CONTENT_LENGTH:
                selected_files_content.append({
                    "path": file_info["path_str"],
                    "content": content
                })
                current_total_length += len(content)
                files_added_count += 1
                console.print(f"  [green]✓[/green] Incluyendo [dim]{file_info['path_str']}[/dim] (prioridad: {file_info['priority']}, tamaño: {file_info['size'] // 1024}KB, {len(content)} chars)")
            else:
                console.print(f"  [yellow]✗[/yellow] Omitiendo [dim]{file_info['path_str']}[/dim] para no exceder límite de contenido total.")
                continue 
        except Exception as e:
            console.print(f"  [red]✗[/red] No se pudo leer o procesar [dim]{file_info['path_str']}[/dim]: {e}")
    
    if not selected_files_content:
        console.print("[yellow]No se seleccionaron archivos para el análisis.[/yellow]")
    
    return selected_files_content