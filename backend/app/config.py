"""
IBTRRS Configuration and Environment Settings
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    PROJECT_NAME: str = "IBTRRS Backend"
    
    # Auth & Tokens
    TOKEN_FILE_PATH: Path = Path.home() / ".ibtrrs" / "token"
    
    # Artifacts & Corpus
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    ARTIFACTS_DIR: Path = BASE_DIR / "index" / "artifacts"
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "fake"  # 'fake', 'openai', 'anthropic', 'litellm'
    LLM_MODEL: str = "mock-model"
    LLM_API_KEY: str = ""
    LLM_TIMEOUT_SECONDS: int = 25
    
    # Retrieval
    RELEVANCE_FLOOR: float = 0.25
    MAX_EXAMPLES: int = 3

    class Config:
        env_prefix = "IBTRRS_"


settings = Settings()

