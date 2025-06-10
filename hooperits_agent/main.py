# hooperits_agent/main.py
import typer
from typing_extensions import Annotated 
from typing import Optional 
from rich.console import Console
from rich.table import Table
from pathlib import Path 
from rich.markdown import Markdown 
from rich.panel import Panel 
from rich.text import Text 

from . import git_ops 
from . import config  
from . import state_manager 
from . import gemini_ops 
from . import project_analyzer 

app = typer.Typer(
    name="hooperits-agent", 
    help="HOOPERITS AI CODE AGENT - Tu asistente de desarrollo con IA.",
    add_completion=False 
)
repo_app = typer.Typer(name="repo", help="Gestionar repositorios de código.")
app.add_typer(repo_app)
model_app = typer.Typer(name="model", help="Gestionar y seleccionar modelos de IA de Gemini.")
app.add_typer(model_app)
console = Console()

@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    if not config.API_KEY:
        console.print("[bold red]ADVERTENCIA: GOOGLE_API_KEY no está configurada en tu .env[/bold red]")
        console.print("Algunas funcionalidades (como el chat con IA) no funcionarán.")
        console.print(f"Asegúrate de crear un archivo .env en la raíz del proyecto con tu clave.")
    
    if ctx.invoked_subcommand is None:
        console.print("\n[bold magenta]=== Estado Actual de HOOPERITS AI CODE AGENT ===[/bold magenta]")
        active_repo = state_manager.get_active_repo_name()
        if active_repo:
            console.print(f"Repositorio Activo: [bold green]{active_repo}[/bold green]")
            console.print(f"Ruta Base de Repos: [dim]{config.REPOS_BASE_PATH}[/dim]")
        else:
            console.print("Repositorio Activo: [yellow]Ninguno seleccionado.[/yellow]")
            console.print("  Usa `repo select <nombre_repo>` para seleccionar uno.")
        current_gemini_model = gemini_ops.get_current_gemini_model_name()
        if current_gemini_model:
            current_model_details = gemini_ops.get_model_pricing_details(current_model)
            current_model_tier_display = current_model_details.get('tier', 'N/A')
            console.print(f"Modelo Gemini por Defecto: [bold green]{current_gemini_model}[/bold green] (Tier: [yellow]{current_model_tier_display}[/yellow])")
        else:
            console.print("Modelo Gemini por Defecto: [yellow]Ninguno seleccionado (se usará uno automáticamente).[/yellow]")
            console.print("  Usa `model list` para ver opciones y `model select <nombre_modelo_api>` para elegir.")
        console.print("\nEjecuta `[b]hooperits-agent --help[/b]` para ver todos los comandos.")

@repo_app.command("clone")
def repo_clone(
    repo_url: Annotated[str, typer.Argument(help="URL del repositorio Git (HTTPS o SSH).")],
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Nombre local opcional.")] = None
):
    """Clona un repositorio Git."""
    success = git_ops.clone_repo(repo_url, name)
    if success:
        repo_to_check = name if name else Path(repo_url).stem
        if repo_to_check and not state_manager.get_active_repo_name():
            if state_manager.set_active_repo(repo_to_check):
                console.print(f"[italic blue]Repositorio '{repo_to_check}' establecido como activo automáticamente.[/italic blue]")

@repo_app.command("list")
def repo_list_command(): # Renombrado para evitar colisión con list de Python si se importa
    """Lista los repositorios locales gestionados."""
    console.print("\n[bold cyan]Repositorios Locales Gestionados:[/bold cyan]")
    repos = git_ops.list_local_repos()
    active_repo = state_manager.get_active_repo_name()
    if not repos:
        console.print("  No se encontraron repositorios. Usa `repo clone` para añadir uno.")
        return
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Nombre del Repositorio", style="dim", width=50)
    table.add_column("Activo", justify="center")
    for repo_name in repos:
        is_active_marker = "✅" if repo_name == active_repo else ""
        display_name = f"[bold green]{repo_name}[/bold green]" if repo_name == active_repo else repo_name
        table.add_row(display_name, is_active_marker)
    console.print(table)

@repo_app.command("select")
def repo_select(
    repo_name: Annotated[str, typer.Argument(help="Nombre del repositorio a activar.")]
):
    """Establece un repositorio local como activo."""
    if state_manager.set_active_repo(repo_name):
        console.print(f"[bold green]Repositorio activo ahora es: {repo_name}[/bold green]")
    else:
        console.print(f"[bold red]Error: No se pudo activar '{repo_name}'.[/bold red]")
        console.print(f"  Asegúrate que '{config.REPOS_BASE_PATH / repo_name}' exista.")

@repo_app.command("current")
def repo_current():
    """Muestra el repositorio activo actual."""
    active_repo = state_manager.get_active_repo_name()
    if active_repo:
        console.print(f"Repositorio Activo: [bold green]{active_repo}[/bold green]")
        active_path = state_manager.get_active_repo_path()
        if active_path: console.print(f"  Ruta: [dim]{active_path}[/dim]")
    else:
        console.print("No hay repositorio activo seleccionado.")

@repo_app.command("unselect")
def repo_unselect():
    """Desactiva el repositorio activo."""
    state_manager.clear_active_repo()
    console.print("[bold yellow]Repositorio activo desactivado.[/bold yellow]")

@model_app.command("list")
def model_list_command():
    """Lista los modelos de Gemini disponibles y su información de tier."""
    console.print("\n[bold cyan]Consultando modelos de Gemini y tiers...[/bold cyan]")
    models_with_tier_info = gemini_ops.get_available_gemini_models() 
    if not models_with_tier_info:
        console.print("  [yellow]No se encontraron modelos o hubo un error.[/yellow]")
        return
    table = Table(title="Modelos Gemini Disponibles y Tiers", show_header=True, header_style="bold magenta")
    table.add_column("Nombre (API)", style="cyan", width=40, overflow="fold")
    table.add_column("Tier", width=18, style="yellow") 
    table.add_column("Notas / Info de Precios", overflow="fold")
    for model_info in models_with_tier_info:
        tier_display_str = model_info.get('tier', 'unknown')
        tier_styled = f"[{'green' if 'free' in tier_display_str or 'gemma' in tier_display_str else 'bold red' if tier_display_str.startswith('paid') else 'dim' if 'unknown' in tier_display_str else 'yellow'}]{tier_display_str}[/]"
        notes = model_info.get('notes', "N/A")
        pricing_info_str_parts = []
        if isinstance(model_info.get("pricing_details"), dict):
            paid_tier_details = model_info["pricing_details"].get("paid_tier")
            if isinstance(paid_tier_details, dict):
                for key, value in paid_tier_details.items():
                    if "per_1M_tokens_usd" in key or "usd_per_image" in key:
                         price_key_display = key.replace('_per_1M_tokens_usd', ' (1M tok)').replace('_usd_per_image', '/img').replace('_', ' ').capitalize()
                         pricing_info_str_parts.append(f"{price_key_display}: ${value}")
        if pricing_info_str_parts:
            notes_suffix = f" | Precios: {'; '.join(pricing_info_str_parts)}"
            if "Precios:" not in notes: notes += notes_suffix
        table.add_row(model_info['name'], Text.from_markup(tier_styled), notes)
    console.print(table)
    current_model = gemini_ops.get_current_gemini_model_name()
    if current_model:
        current_model_details = gemini_ops.get_model_pricing_details(current_model)
        current_model_tier_display = current_model_details.get('tier', 'N/A')
        console.print(f"\nModelo seleccionado: [bold green]{current_model}[/bold green] (Tier: [yellow]{current_model_tier_display}[/yellow])")
    else:
        console.print("\n[yellow]No hay modelo seleccionado por defecto.[/yellow]")
    console.print("  Usa `hooperits-agent model select <nombre_modelo_api>` para elegir.")

@model_app.command("select")
def model_select_command( 
    model_name: Annotated[str, typer.Argument(help="Nombre API del modelo (ej. 'models/gemini-1.5-flash-latest').")]
):
    """Selecciona un modelo de Gemini por defecto."""
    available_models = gemini_ops.get_available_gemini_models()
    if not any(m['name'] == model_name for m in available_models):
        console.print(f"[bold red]Error: Modelo '{model_name}' no encontrado en la lista.[/bold red]")
        raise typer.Exit(code=1)
    gemini_ops.set_default_gemini_model(model_name)

@app.command("chat")
def chat_with_gemini_command( # Renombrado para evitar conflicto
    message: Annotated[str, typer.Argument(help="Mensaje o pregunta para Gemini.")],
    file_path_str: Annotated[Optional[str], typer.Option("--file", "-f", help="Ruta relativa a un archivo en el repo activo para contexto.")] = None,
    no_confirm_cost: Annotated[bool, typer.Option("--yes", "-y", help="Saltar confirmación para modelos de pago.")] = False
):
    """Envía un mensaje a Gemini, opcionalmente con contexto de archivo."""
    final_prompt = message
    active_repo_path = state_manager.get_active_repo_path()
    if file_path_str:
        if not active_repo_path:
            console.print("[bold red]Error: No hay repo activo. Usa `repo select` para usar --file.[/bold red]")
            raise typer.Exit(code=1)
        full_file_path = active_repo_path / file_path_str
        if not full_file_path.is_file():
            console.print(f"[bold red]Error: Archivo '{full_file_path}' no existe.[/bold red]")
            raise typer.Exit(code=1)
        try:
            # project_analyzer ya tiene _detect_encoding, podríamos usarlo o simplificar aquí
            encoding_to_try = project_analyzer._detect_encoding(full_file_path) # Usar la función de project_analyzer
            console.print(f"[dim]Leyendo [cyan]{file_path_str}[/cyan] (encoding: {encoding_to_try}) para contexto...[/dim]")
            with open(full_file_path, 'r', encoding=encoding_to_try, errors='replace') as f:
                file_content = f.read()
            MAX_FILE_CONTENT_FOR_PROMPT = 15000 
            if len(file_content) > MAX_FILE_CONTENT_FOR_PROMPT:
                file_content = file_content[:MAX_FILE_CONTENT_FOR_PROMPT] + "\n... (archivo truncado)"
            final_prompt = (
                f"Contenido del archivo '{file_path_str}':\n"
                f"---------------- FILE CONTENT START ----------------\n{file_content}\n---------------- FILE CONTENT END ------------------\n\n"
                f"Pregunta/instrucción: {message}"
            )
        except Exception as e:
            console.print(f"[bold red]Error al leer '{full_file_path}': {e}[/bold red]")
            raise typer.Exit(code=1)
    
    response_text = gemini_ops.send_prompt_to_gemini(final_prompt, confirm_paid_model_use=not no_confirm_cost)
    if response_text:
        title_text = "Respuesta de Gemini"
        border_s = "dim cyan"
        text_style = ""
        if response_text.startswith(("[ERROR_GEMINI]", "[INFO_USER]")):
            title_text = "Mensaje del Agente"
            prefix_to_remove = "[ERROR_GEMINI] " if response_text.startswith("[ERROR_GEMINI]") else "[INFO_USER] "
            display_text = response_text.replace(prefix_to_remove, '')
            text_style = "bold red" if response_text.startswith("[ERROR_GEMINI]") else "yellow"
            border_s = "dim red" if response_text.startswith("[ERROR_GEMINI]") else "dim yellow"
            content_to_render = Text.from_markup(f"[{text_style}]{display_text}[/{text_style}]")
        else:
            content_to_render = Markdown(response_text)
        
        console.print(Panel(content_to_render, title=title_text, border_style=border_s, expand=False,
                            padding=(1,2) if not response_text.startswith(("[ERROR_GEMINI]", "[INFO_USER]")) else 0 ))
    else:
        console.print("[bold yellow]No se recibió respuesta de Gemini o hubo un error.[/bold yellow]")

@app.command("analyze-project")
def analyze_project_command_func( # Renombrado para evitar conflicto
    repo_name: Annotated[Optional[str], typer.Option("--repo", "-r", help="Repo local a analizar (usa activo si se omite).")] = None,
    sub_path_str: Annotated[Optional[str], typer.Option("--path", "-p", help="Subdirectorio relativo para enfocar el análisis.")] = None,
    no_confirm_cost: Annotated[bool, typer.Option("--yes", "-y", help="Saltar confirmación para modelos de pago.")] = False
):
    """Realiza un análisis inicial del proyecto/subdirectorio usando Gemini."""
    root_repo_path = None
    repo_to_scan_display_name = ""
    if repo_name:
        potential_path = config.REPOS_BASE_PATH / repo_name
        if not potential_path.is_dir():
            console.print(f"[bold red]Error: Repo '{repo_name}' no encontrado.[/bold red]")
            raise typer.Exit(code=1)
        root_repo_path = potential_path
        repo_to_scan_display_name = repo_name
    else:
        root_repo_path = state_manager.get_active_repo_path()
        if not root_repo_path:
            console.print("[bold red]Error: No hay repo activo. Usa `repo select` o --repo.[/bold red]")
            raise typer.Exit(code=1)
        repo_to_scan_display_name = root_repo_path.name
    
    path_to_analyze = root_repo_path
    focus_area_for_prompt = f"el proyecto '{repo_to_scan_display_name}'"
    if sub_path_str:
        path_to_analyze = root_repo_path / sub_path_str
        if not path_to_analyze.is_dir():
            console.print(f"[bold red]Error: Subdirectorio '{sub_path_str}' no existe en '{repo_to_scan_display_name}'.[/bold red]")
            raise typer.Exit(code=1)
        focus_area_for_prompt = f"el subdirectorio '{sub_path_str}' del proyecto '{repo_to_scan_display_name}'"
    
    console.print(f"\n[bold blue]Iniciando análisis de {focus_area_for_prompt}[/bold blue]")
    # La función ahora espera path_to_scan y repo_root_path
    selected_contents = project_analyzer.get_project_files_for_analysis(path_to_scan=path_to_analyze, repo_root_path=root_repo_path)

    if not selected_contents:
        console.print("[bold yellow]No se pudo obtener contenido de archivos para enviar a Gemini.[/bold yellow]")
        raise typer.Exit(code=1)

    prompt_parts = [f"Actúa como un arquitecto de software experimentado revisando {focus_area_for_prompt}.\n"
                    "Basado en el contenido de los siguientes archivos clave de esta área, proporciona un análisis estructurado usando Markdown con los siguientes encabezados:\n\n"
                    "## Propósito Principal\n(Resumen conciso en 1-2 frases).\n\n"
                    "## Tecnologías y Lenguajes Clave\n(Lista).\n\n"
                    "## Estructura General\n(Describe brevemente organización y arquitectura, 2-4 frases).\n\n"
                    "## Puntos de Partida o Interés\n(Opcional: 1-2 archivos/directorios clave para un nuevo desarrollador).\n\n"
                    "Sé claro, conciso y técnico.\n\n"
                    "--- CONTENIDO DE ARCHIVOS PROPORCIONADOS ---\n"]
    for item in selected_contents:
        prompt_parts.append(f"\n--- Archivo: {item['path']} ---\n{item['content']}\n--- Fin Archivo: {item['path']} ---")
    final_prompt = "".join(prompt_parts)
    
    console.print(f"\n[magenta]Enviando {len(selected_contents)} archivos a Gemini para análisis...[/magenta]")
    response_text = gemini_ops.send_prompt_to_gemini(final_prompt, confirm_paid_model_use=not no_confirm_cost)

    if response_text: # Reutilizar la lógica de formato de panel del comando chat
        title_text = f"Análisis de {focus_area_for_prompt} por Gemini"
        border_s = "dim cyan"
        text_style = ""
        if response_text.startswith(("[ERROR_GEMINI]", "[INFO_USER]")):
            title_text = "Mensaje del Agente"
            prefix_to_remove = "[ERROR_GEMINI] " if response_text.startswith("[ERROR_GEMINI]") else "[INFO_USER] "
            display_text = response_text.replace(prefix_to_remove, '')
            text_style = "bold red" if response_text.startswith("[ERROR_GEMINI]") else "yellow"
            border_s = "dim red" if response_text.startswith("[ERROR_GEMINI]") else "dim yellow"
            content_to_render = Text.from_markup(f"[{text_style}]{display_text}[/{text_style}]")
        else:
            content_to_render = Markdown(response_text)
        
        console.print(Panel(content_to_render, title=title_text, border_style=border_s, expand=False,
                            padding=(1,2) if not response_text.startswith(("[ERROR_GEMINI]", "[INFO_USER]")) else 0 ))
    else:
        console.print("[bold yellow]No se recibió un análisis del proyecto de Gemini.[/bold yellow]")

if __name__ == "__main__":
    app()