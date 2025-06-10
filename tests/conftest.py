"""
Configuración de pytest y fixtures compartidas.
"""
import pytest
import tempfile
from pathlib import Path
import shutil
import os

@pytest.fixture
def temp_dir():
    """
    Crea un directorio temporal para las pruebas.
    Se limpia automáticamente al finalizar.
    """
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_env(monkeypatch):
    """
    Fixture para mockear variables de entorno.
    """
    def _mock_env(**kwargs):
        for key, value in kwargs.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, str(value))
    
    return _mock_env


@pytest.fixture
def mock_repos_dir(temp_dir, monkeypatch):
    """
    Crea un directorio temporal para repositorios y lo configura.
    """
    repos_path = temp_dir / "test_repositories"
    repos_path.mkdir()
    
    # Mockear la variable de entorno
    monkeypatch.setattr("hooperits_agent.config.REPOS_BASE_PATH", repos_path)
    
    return repos_path


@pytest.fixture
def mock_api_key(monkeypatch):
    """
    Mockea una API key de prueba.
    """
    test_key = "test-api-key-12345"
    monkeypatch.setenv("GOOGLE_API_KEY", test_key)
    monkeypatch.setattr("hooperits_agent.config.API_KEY", test_key)
    return test_key


@pytest.fixture
def sample_git_repo(temp_dir):
    """
    Crea un repositorio Git de ejemplo.
    """
    import git
    
    repo_path = temp_dir / "sample_repo"
    repo_path.mkdir()
    
    # Inicializar repo
    repo = git.Repo.init(repo_path)
    
    # Crear algunos archivos
    (repo_path / "README.md").write_text("# Sample Repository\n")
    (repo_path / "main.py").write_text("print('Hello, World!')\n")
    
    # Hacer commit inicial
    repo.index.add(["README.md", "main.py"])
    repo.index.commit("Initial commit")
    
    return repo_path


@pytest.fixture
def mock_gemini_response():
    """
    Simula una respuesta de Gemini AI.
    """
    class MockResponse:
        def __init__(self, text="Mock response from Gemini"):
            self.text = text
            self.candidates = []
            self.prompt_feedback = None
            self.usage_metadata = MockUsageMetadata()
    
    class MockUsageMetadata:
        def __init__(self):
            self.prompt_token_count = 10
            self.candidates_token_count = 20
            self.total_token_count = 30
    
    return MockResponse


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Resetea los singletons entre tests.
    """
    # Resetear el modelo de Gemini
    import hooperits_agent.gemini_ops as gemini_ops
    gemini_ops._genai_model_instance = None
    gemini_ops._selected_model_name = None
    gemini_ops._model_tier_info_cache = None 