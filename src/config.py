import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATA_DIR: str = os.getenv("DATA_DIR", "/app/data")
    ADGM_REF_DIR: str = os.path.join(DATA_DIR, "adgm_reference")
    TEMPLATES_DIR: str = os.path.join(DATA_DIR, "templates")
    UPLOADS_DIR: str = os.path.join(DATA_DIR, "uploads")
    VECTOR_DIR: str = os.getenv("VECTOR_DIR", "/app/vector_store")
    EMBED_MODEL: str = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 1000))   # characters
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 200))
    RETRIEVE_K: int = int(os.getenv("RETRIEVE_K", 6))
    USE_OLLAMA: bool = os.getenv("USE_OLLAMA","true").lower() == "true"
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    USE_TGI: bool = os.getenv("USE_TGI","false").lower() == "true"
    TGI_URL: str = os.getenv("TGI_URL", "http://tgi:8080")
    CHROMA_PERSIST: str = os.getenv("CHROMA_PERSIST", "/app/chroma_db")
    class Config:
        env_file = ".env"

settings = Settings()
