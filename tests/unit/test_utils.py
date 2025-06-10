"""
Tests unitarios para el módulo utils.
"""
import pytest
from pathlib import Path
import tempfile
import json
from datetime import datetime, timedelta

from hooperits_agent.utils import (
    validate_repo_name,
    validate_file_path,
    format_file_size,
    truncate_text,
    count_tokens_estimate,
    sanitize_filename,
    format_cost,
    SimpleCache,
)


class TestValidation:
    """Tests para funciones de validación."""
    
    def test_validate_repo_name_valid(self):
        """Test nombres de repositorio válidos."""
        assert validate_repo_name("my-repo") is True
        assert validate_repo_name("my_repo") is True
        assert validate_repo_name("MyRepo123") is True
        assert validate_repo_name("repo.with.dots") is True
    
    def test_validate_repo_name_invalid(self):
        """Test nombres de repositorio inválidos."""
        assert validate_repo_name("") is False
        assert validate_repo_name("   ") is False
        assert validate_repo_name("repo/with/slash") is False
        assert validate_repo_name("repo\\with\\backslash") is False
        assert validate_repo_name("repo:with:colon") is False
        assert validate_repo_name("repo*with*asterisk") is False
        assert validate_repo_name("repo?with?question") is False
        assert validate_repo_name('repo"with"quotes') is False
        assert validate_repo_name("repo<with>brackets") is False
        assert validate_repo_name("repo|with|pipe") is False
    
    def test_validate_file_path(self):
        """Test validación de rutas de archivo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            
            # Rutas válidas
            assert validate_file_path(base_path / "file.txt", base_path) is True
            assert validate_file_path(base_path / "subdir" / "file.txt", base_path) is True
            
            # Rutas inválidas (fuera del directorio base)
            assert validate_file_path("/etc/passwd", base_path) is False
            assert validate_file_path(base_path / ".." / "file.txt", base_path) is False


class TestFormatting:
    """Tests para funciones de formateo."""
    
    def test_format_file_size(self):
        """Test formateo de tamaños de archivo."""
        assert format_file_size(0) == "0.0 B"
        assert format_file_size(512) == "512.0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(1048576) == "1.0 MB"
        assert format_file_size(1073741824) == "1.0 GB"
        assert format_file_size(1099511627776) == "1.0 TB"
    
    def test_truncate_text(self):
        """Test truncado de texto."""
        assert truncate_text("Short text", 20) == "Short text"
        assert truncate_text("This is a very long text that needs truncation", 20) == "This is a very lo..."
        assert truncate_text("Custom suffix test", 15, " [...]") == "Custom su [...]"
    
    def test_format_cost(self):
        """Test formateo de costos."""
        assert format_cost(0.0) == "$0.000000"
        assert format_cost(0.000001) == "$0.000001"
        assert format_cost(1.234567) == "$1.234567"
        assert format_cost(100.0, "EUR") == "100.000000 EUR"


class TestAnalysis:
    """Tests para funciones de análisis."""
    
    def test_count_tokens_estimate(self):
        """Test estimación de tokens."""
        assert count_tokens_estimate("") == 0
        assert count_tokens_estimate("test") == 1  # 4 chars = 1 token
        assert count_tokens_estimate("This is a test") == 3  # 14 chars ≈ 3 tokens
        assert count_tokens_estimate("a" * 100) == 25  # 100 chars = 25 tokens


class TestSanitization:
    """Tests para funciones de sanitización."""
    
    def test_sanitize_filename(self):
        """Test sanitización de nombres de archivo."""
        assert sanitize_filename("normal_file.txt") == "normal_file.txt"
        assert sanitize_filename("file/with/slashes.txt") == "file_with_slashes.txt"
        assert sanitize_filename("file\\with\\backslashes.txt") == "file_with_backslashes.txt"
        assert sanitize_filename("file:with:colons.txt") == "file_with_colons.txt"
        assert sanitize_filename("file*with*asterisks.txt") == "file_with_asterisks.txt"
        assert sanitize_filename('file"with"quotes.txt') == "file_with_quotes.txt"
        assert sanitize_filename("  spaces  ") == "spaces"
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("   ") == "unnamed"


class TestSimpleCache:
    """Tests para el sistema de caché."""
    
    def test_cache_basic_operations(self):
        """Test operaciones básicas del caché."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SimpleCache(Path(tmpdir), expiration_seconds=10)
            
            # Test set and get
            cache.set("test prompt", "model-1", "test response")
            assert cache.get("test prompt", "model-1") == "test response"
            
            # Test different prompt
            assert cache.get("different prompt", "model-1") is None
            
            # Test different model
            assert cache.get("test prompt", "model-2") is None
    
    def test_cache_expiration(self):
        """Test expiración del caché."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Caché con expiración muy corta
            cache = SimpleCache(Path(tmpdir), expiration_seconds=0)
            
            cache.set("test prompt", "model-1", "test response")
            # Debe expirar inmediatamente
            assert cache.get("test prompt", "model-1") is None
    
    def test_cache_clear(self):
        """Test limpieza del caché."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SimpleCache(Path(tmpdir), expiration_seconds=3600)
            
            cache.set("prompt1", "model", "response1")
            cache.set("prompt2", "model", "response2")
            
            cache.clear()
            
            assert cache.get("prompt1", "model") is None
            assert cache.get("prompt2", "model") is None
    
    def test_cache_cleanup_expired(self):
        """Test limpieza de entradas expiradas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache_file = cache_dir / "gemini_responses.json"
            
            # Crear caché con entradas mezcladas (expiradas y válidas)
            now = datetime.now()
            cache_data = {
                "expired_key": {
                    "response": "expired response",
                    "expiration": (now - timedelta(hours=1)).isoformat(),
                    "model": "model",
                    "created": (now - timedelta(hours=2)).isoformat()
                },
                "valid_key": {
                    "response": "valid response",
                    "expiration": (now + timedelta(hours=1)).isoformat(),
                    "model": "model",
                    "created": now.isoformat()
                }
            }
            
            # Guardar datos de caché
            cache_dir.mkdir(exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            
            cache = SimpleCache(cache_dir, expiration_seconds=3600)
            cache.cleanup_expired()
            
            # Verificar que solo queda la entrada válida
            with open(cache_file, 'r') as f:
                cleaned_data = json.load(f)
            
            assert "expired_key" not in cleaned_data
            assert "valid_key" in cleaned_data 