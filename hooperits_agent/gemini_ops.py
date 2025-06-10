# hooperits_agent/gemini_ops.py
import json
from pathlib import Path
from typing import Optional, List, Dict, Any 
import typer 
from rich.console import Console
from rich.table import Table
from rich.text import Text # Importar Text
from .config import (
    API_KEY, project_root, ENABLE_GEMINI_CACHE, 
    CACHE_EXPIRATION_SECONDS, CACHE_DIR, DEFAULT_GEMINI_MODEL,
    LOG_LEVEL, LOG_FILE
)
from .state_manager import _load_state, _save_state
from .utils import setup_logging, SimpleCache, format_cost
import traceback
import google.generativeai as genai

console = Console()
logger = setup_logging(LOG_LEVEL, LOG_FILE)

# Inicializar caché si está habilitado
cache = SimpleCache(CACHE_DIR, CACHE_EXPIRATION_SECONDS) if ENABLE_GEMINI_CACHE else None

_genai_model_instance = None
_selected_model_name = None 
_model_tier_info_cache: Optional[Dict[str, Any]] = None 

def _load_model_tier_info() -> Dict[str, Any]:
    global _model_tier_info_cache
    if _model_tier_info_cache is None: 
        tier_file_path = project_root / "model_tiers.json"
        if tier_file_path.exists():
            try:
                with open(tier_file_path, 'r', encoding='utf-8') as f:
                    _model_tier_info_cache = json.load(f)
            except json.JSONDecodeError as e:
                console.print(f"[bold red]Error al parsear {tier_file_path}: {e}[/bold red]")
                _model_tier_info_cache = {}
            except Exception as e:
                console.print(f"[bold red]Error al cargar {tier_file_path}: {e}[/bold red]")
                _model_tier_info_cache = {}
        else:
            console.print(f"[yellow]Advertencia: Archivo de tiers de modelos ({tier_file_path}) no encontrado.[/yellow]")
            console.print("[yellow]No se mostrará información detallada de precios/tiers.[/yellow]")
            _model_tier_info_cache = {}
    return _model_tier_info_cache

def get_model_pricing_details(model_name: str) -> Dict[str, Any]:
    all_tier_info = _load_model_tier_info()
    return all_tier_info.get(model_name, {})

def get_available_gemini_models() -> List[Dict[str, Any]]:
    if not API_KEY:
        console.print("[bold red]Error: API Key de Gemini no configurada.[/bold red]")
        return []
    try:
        genai.configure(api_key=API_KEY)
        all_api_models_raw = list(genai.list_models())
        
        models_list: List[Dict[str, Any]] = []
        if not all_api_models_raw:
            console.print("[yellow]Advertencia: La API de Gemini no devolvió ningún modelo.[/yellow]")
            return []

        tier_info_map = _load_model_tier_info()

        for m in all_api_models_raw: 
            if 'generateContent' in m.supported_generation_methods and "vision" not in m.name:
                model_data = {
                    "name": m.name,
                    "display_name": getattr(m, 'display_name', m.name) 
                }
                tier_data_for_model = tier_info_map.get(m.name, {})
                model_data["tier"] = tier_data_for_model.get("tier", "unknown")
                model_data["notes"] = tier_data_for_model.get("notes", "Info no disponible.")
                model_data["pricing_details"] = tier_data_for_model 
                
                models_list.append(model_data)
        
        if not models_list:
            console.print("[yellow]Advertencia: No quedaron modelos después de filtrar por 'generateContent' y no ser de visión.[/yellow]")
            return []

        models_list.sort(key=lambda x: (
            x.get('tier', 'zzz') == 'paid_preview_only',
            x.get('tier', 'zzz') == 'paid_preview',
            x.get('tier', 'zzz') == 'paid',
            not (x.get('tier', 'zzz').startswith('free')),
            not ("pro" in x['name'] or "2.5" in x['name'] or "2.0" in x['name'] or "1.5" in x['name']),
            x['name'] 
        ))
        return models_list
    except Exception as e:
        console.print(f"[bold red]Error al listar modelos de Gemini: {e}[/bold red]")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return []

def _initialize_and_get_gemini_model_instance():
    global _genai_model_instance, _selected_model_name
    state_check = _load_state()
    saved_model_name_check = state_check.get("selected_gemini_model")

    if _genai_model_instance is not None and _selected_model_name == saved_model_name_check and _selected_model_name is not None:
        return _genai_model_instance

    if not API_KEY:
        console.print("[bold red]Error Crítico: API Key de Gemini no configurada.[/bold red]")
        return None
    try:
        genai.configure(api_key=API_KEY)
        state = _load_state()
        model_to_use = state.get("selected_gemini_model")

        if not model_to_use:
            console.print("[yellow]Ningún modelo Gemini ha sido seleccionado. Intentando seleccionar uno gratuito automáticamente...[/yellow]")
            available_models = get_available_gemini_models()
            if available_models:
                free_or_cheaper_models = [m for m in available_models if m.get('tier', '').startswith('free')]
                
                if free_or_cheaper_models:
                    model_to_use = free_or_cheaper_models[0]['name']
                elif available_models: 
                    model_to_use = available_models[0]['name'] 
                    console.print(f"[yellow]Advertencia: No se encontró un modelo gratuito explícito. Se usará: {model_to_use}. Verifica su tier.[/yellow]")
                
                if model_to_use:
                    console.print(f"[bold green]Modelo seleccionado automáticamente: {model_to_use}[/bold green]")
                    state["selected_gemini_model"] = model_to_use
                    _save_state(state)
                else:
                    console.print("[bold red]Fallo en la selección automática: No se encontraron modelos adecuados.[/bold red]")
                    return None
            else:
                console.print("[bold red]Fallo en la selección automática: No se pudieron obtener modelos disponibles.[/bold red]")
                return None
        
        console.print(f"[dim]Inicializando el motor de Gemini con el modelo: [cyan]{model_to_use}[/cyan]...[/dim]")
        _genai_model_instance = genai.GenerativeModel(model_to_use)
        _selected_model_name = model_to_use
        console.print("[italic green]Motor de Gemini listo para consultas.[/italic green]")
        return _genai_model_instance
    except Exception as e:
        console.print(f"[bold red]Error catastrófico al inicializar el modelo Gemini ('{model_to_use or 'desconocido'}'): {e}[/bold red]")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        _genai_model_instance = None
        _selected_model_name = None
        return None

def _calculate_cost_for_call(model_api_name: str, input_tokens: int, output_tokens: int) -> Optional[float]:
    model_pricing_data = get_model_pricing_details(model_api_name)
    paid_tier_info = model_pricing_data.get("paid_tier")

    if not isinstance(paid_tier_info, dict):
        return None 

    cost = 0.0
    tokens_1M = 1_000_000.0
    
    # --- Lógica de Costo de Entrada ---
    # Esto necesitará ser mucho más robusto para manejar todos los casos de tu model_tiers.json
    # Ejemplo muy simplificado:
    if input_tokens > 0:
        # Intentar con claves más específicas primero
        if "input_per_1M_tokens_usd_le_128k" in paid_tier_info and input_tokens <= 128000:
            cost += (input_tokens / tokens_1M) * paid_tier_info["input_per_1M_tokens_usd_le_128k"]
        elif "input_per_1M_tokens_usd_gt_128k" in paid_tier_info and input_tokens > 128000:
            cost += (input_tokens / tokens_1M) * paid_tier_info["input_per_1M_tokens_usd_gt_128k"]
        elif "input_per_1M_tokens_usd_le_200k" in paid_tier_info and input_tokens <= 200000: # Para modelos como 2.5 Pro Preview
            cost += (input_tokens / tokens_1M) * paid_tier_info["input_per_1M_tokens_usd_le_200k"]
        elif "input_per_1M_tokens_usd_gt_200k" in paid_tier_info and input_tokens > 200000:
            cost += (input_tokens / tokens_1M) * paid_tier_info["input_per_1M_tokens_usd_gt_200k"]
        elif "input_text_img_vid_per_1M_tokens_usd" in paid_tier_info:
             cost += (input_tokens / tokens_1M) * paid_tier_info["input_text_img_vid_per_1M_tokens_usd"]
        elif "input_per_1M_tokens_usd" in paid_tier_info: # Genérico
             cost += (input_tokens / tokens_1M) * paid_tier_info["input_per_1M_tokens_usd"]
        # Podrías añadir lógica para 'input_audio_per_1M_tokens_usd' si tu agente maneja audio

    # --- Lógica de Costo de Salida ---
    if output_tokens > 0:
        # Similar a la entrada, intentar con claves específicas primero
        if "output_per_1M_tokens_usd_le_128k" in paid_tier_info: # Asumiendo que el umbral del prompt aplica
            cost += (output_tokens / tokens_1M) * paid_tier_info["output_per_1M_tokens_usd_le_128k"]
        elif "output_per_1M_tokens_usd_gt_128k" in paid_tier_info:
             cost += (output_tokens / tokens_1M) * paid_tier_info["output_per_1M_tokens_usd_gt_128k"]
        elif "output_per_1M_tokens_usd_le_200k" in paid_tier_info: # Para 2.5 Pro Preview
            cost += (output_tokens / tokens_1M) * paid_tier_info["output_per_1M_tokens_usd_le_200k"]
        elif "output_per_1M_tokens_usd_gt_200k" in paid_tier_info:
             cost += (output_tokens / tokens_1M) * paid_tier_info["output_per_1M_tokens_usd_gt_200k"]
        elif "output_no_thought_per_1M_tokens_usd" in paid_tier_info: # Para Flash 2.5 Preview
            cost += (output_tokens / tokens_1M) * paid_tier_info["output_no_thought_per_1M_tokens_usd"]
            # Aquí podrías necesitar una forma de saber si es "con pensamiento" o no
        elif "output_per_1M_tokens_usd" in paid_tier_info: # Genérico
            cost += (output_tokens / tokens_1M) * paid_tier_info["output_per_1M_tokens_usd"]
            
    return cost if cost > 0.0 else None


def send_prompt_to_gemini(prompt: str, confirm_paid_model_use: bool = True) -> str | None:
    model_instance = _initialize_and_get_gemini_model_instance()
    if not model_instance:
        logger.error("El motor de Gemini no pudo ser inicializado")
        return "[ERROR_GEMINI] El motor de Gemini no pudo ser inicializado."

    current_model_being_used = _selected_model_name 
    if not current_model_being_used:
        logger.error("No se pudo determinar el modelo a usar tras la inicialización")
        return "[ERROR_GEMINI] No se pudo determinar el modelo a usar tras la inicialización."
    
    # Verificar caché si está habilitado
    if cache:
        logger.debug(f"Verificando caché para modelo {current_model_being_used}")
        cached_response = cache.get(prompt, current_model_being_used)
        if cached_response:
            logger.info("Respuesta encontrada en caché")
            console.print("[dim italic]💾 Respuesta obtenida del caché[/dim italic]")
            return cached_response

    model_pricing_info = get_model_pricing_details(current_model_being_used)
    tier = model_pricing_info.get("tier", "unknown")
    is_potentially_paid = not (tier.startswith("free") or "gemma" in tier) or "paid" in tier 

    if is_potentially_paid and confirm_paid_model_use:
        console.print(f"\n[bold yellow]⚠️  ADVERTENCIA DE COSTO POTENCIAL[/bold yellow]")
        # Corrección de la etiqueta de Rich Markup
        console.print(f"   Modelo a usar: [cyan][u]{current_model_being_used}[/u][/cyan]") 
        console.print(f"   Tier       : [bold]{tier}[/bold]")
        if model_pricing_info.get("notes"):
            console.print(f"   Notas      : {model_pricing_info['notes']}")
        
        paid_details = model_pricing_info.get("paid_tier")
        if isinstance(paid_details, dict):
            console.print("   Detalles de Precios (si aplican, USD por 1M de tokens o por unidad):")
            for key, value in paid_details.items():
                display_key = key.replace('_per_1M_tokens_usd', ' (1M tok)').replace('_usd_per_image', '/img').replace('_', ' ').capitalize()
                console.print(f"     - {display_key}: ${value}")
        try:
            if model_instance: # Asegurarse que model_instance existe
                prompt_token_count_obj = model_instance.count_tokens(prompt)
                prompt_tokens = prompt_token_count_obj.total_tokens
                console.print(f"   Tokens estimados para tu prompt: [bold cyan]{prompt_tokens}[/bold cyan]")
                
                cost_estimate_input_only = _calculate_cost_for_call(current_model_being_used, prompt_tokens, 0)
                if cost_estimate_input_only is not None:
                    console.print(f"   Costo MÍNIMO estimado (solo por la entrada de este prompt): [bold red]${cost_estimate_input_only:.6f}[/bold red]")
            else:
                console.print("[yellow]  No se pudo contar tokens: instancia del modelo no disponible.[/yellow]")
        except Exception as e:
            console.print(f"   [yellow]No se pudo estimar el conteo de tokens del prompt: {e}[/yellow]")

        if not typer.confirm("¿Deseas continuar y potencialmente incurrir en costos?", default=False): 
            console.print("[bold red]Operación cancelada por el usuario.[/bold red]")
            return "[INFO_USER] Operación cancelada para evitar costos."
    
    console.print("\n[blue i]Tu Agente HOOPERITS está consultando a Gemini...[/blue i]")
    try:
        response = model_instance.generate_content(prompt)
        
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            reason_name = response.prompt_feedback.block_reason.name if hasattr(response.prompt_feedback.block_reason, 'name') else str(response.prompt_feedback.block_reason)
            reason_message = getattr(response.prompt_feedback, 'block_reason_message', reason_name)
            error_message = f"Solicitud bloqueada por Gemini. Razón: {reason_message or reason_name}"
            console.print(f"[bold red]{error_message}[/bold red]")
            return f"[ERROR_GEMINI] {error_message}"

        response_text = ""
        if hasattr(response, 'text') and response.text: 
            response_text = response.text
        elif hasattr(response, 'parts') and response.parts: 
            response_text = " ".join([part.text for part in response.parts if hasattr(part, 'text') and part.text])
        
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = response.usage_metadata
            console.print(Text.assemble(("\n📊 ", "bold blue"), ("Uso de Tokens para esta consulta con '", "italic blue"), (f"{current_model_being_used}", "italic blue u"), ("':", "italic blue")))
            prompt_t_usage = getattr(usage, 'prompt_token_count', 0)
            candidates_t_usage = getattr(usage, 'candidates_token_count', 0)
            total_t_usage = getattr(usage, 'total_token_count', 0)

            console.print(f"  - Tokens del Prompt  : {prompt_t_usage}")
            console.print(f"  - Tokens de Respuesta: {candidates_t_usage}")
            console.print(f"  - Tokens Totales     : {total_t_usage}")

            if is_potentially_paid:
                if isinstance(prompt_t_usage, int) and isinstance(candidates_t_usage, int):
                    estimated_cost_this_call = _calculate_cost_for_call(current_model_being_used, prompt_t_usage, candidates_t_usage)
                    if estimated_cost_this_call is not None:
                        console.print(f"  - [bold red]Costo Real Estimado de esta Llamada: ${estimated_cost_this_call:.6f}[/bold red]")
                else:
                    console.print("[yellow]  No se pudo calcular el costo real: contadores de tokens de uso no son enteros o no disponibles.[/yellow]")
        
        if not response_text.strip():
            candidate_info = "Sin candidatos claros."
            if hasattr(response, 'candidates') and response.candidates:
                first_candidate = response.candidates[0]
                if hasattr(first_candidate, 'finish_reason'):
                    reason_name = first_candidate.finish_reason.name if hasattr(first_candidate.finish_reason, 'name') else str(first_candidate.finish_reason)
                    candidate_info = f"Candidato finalizó por: {reason_name}."
            console.print(f"[bold yellow]Advertencia: Gemini devolvió una respuesta sin contenido textual visible. {candidate_info}[/bold yellow]")
            logger.warning(f"Respuesta vacía de Gemini: {candidate_info}")
            return f"[ERROR_GEMINI] Respuesta vacía o no textual de Gemini. {candidate_info}"
        
        # Guardar en caché si está habilitado
        if cache and response_text:
            logger.debug("Guardando respuesta en caché")
            cache.set(prompt, current_model_being_used, response_text)
            
        return response_text
    except Exception as e:
        console.print(f"[bold red]¡Rayos! Hubo un problema en la comunicación con Gemini: {e}[/bold red]")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return f"[ERROR_GEMINI] Error de comunicación: {str(e)}"

def set_default_gemini_model(model_name: str) -> bool:
    state = _load_state()
    state["selected_gemini_model"] = model_name
    _save_state(state)
    
    global _genai_model_instance, _selected_model_name
    _genai_model_instance = None 
    _selected_model_name = None  
    
    console.print(f"[green]Modelo Gemini por defecto establecido a: [bold]{model_name}[/bold]. Se usará en la próxima consulta.[/green]")
    return True

def get_current_gemini_model_name() -> Optional[str]:
    state = _load_state()
    return state.get("selected_gemini_model")
