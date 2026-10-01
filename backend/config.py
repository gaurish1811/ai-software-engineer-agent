import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "AI Software Engineer Agent"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # Workspace & Repos storage directory
    WORKSPACE_DIR: str = str(BASE_DIR / "workspaces")
    
    # LLM Settings
    DEFAULT_PROVIDER: str = "openai"  # openai, anthropic, gemini, ollama
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-pro"
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "codellama"
    
    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None
    
    # Neo4j Settings (Optional Graph DB integration)
    NEO4J_URI: Optional[str] = "bolt://localhost:7687"
    NEO4J_USER: Optional[str] = "neo4j"
    NEO4J_PASSWORD: Optional[str] = "password"
    ENABLE_NEO4J: bool = False

    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore")

settings = Settings()

# Ensure workspace directory exists
os.makedirs(settings.WORKSPACE_DIR, exist_ok=True)
