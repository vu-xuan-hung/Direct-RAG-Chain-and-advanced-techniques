import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from core.device import DEVICE

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "FPT HR Assistant API"
    CORS_ORIGINS: List[str] = ["*"]
    HNSW_metadata: dict = {
        'hnsw:space': 'cosine',
        'hnsw:M': 64,
        'hnsw:construction_ef': 128,
        'hnsw:search_ef': 128
    }
    SEARCH_ORDER: str = "mmr_first" 
    # Paths
    CHROMA_PERSIST_DIR: str = str(BACKEND_DIR / "indexing" / "chroma_db")
    POLICY_PATH: str = str(BASE_DIR / "resources" / "fpt_policy.txt")
    BM25_PERSIST_PATH: str = str(BACKEND_DIR / "indexing" / "bm25_retriever.pkl")
    # Model Configurations
    LLM_MODEL: str = "qwen2.5:3b"
    EMBEDDING_MODEL: str = "keepitreal/vietnamese-sbert"
    CROSS_ENCODER_MODEL: str = "BAAI/bge-reranker-base"
    CROSS_ENCODER_DEVICE: str = DEVICE  # auto-detect: cuda / mps / cpu
    LLM_TEMPERATURE: float = 0.0
    breakpoint_threshold_type: str = "percentile"
    breakpoint_threshold_amount: int = 85
    # Vector Store / RAG Configurations
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVER_K: int = 3
    RETRIEVER_K_BM25: int=3
    SEARCH_TYPE: str = "similarity"  # or "mmr"
    COLLECTION_NAME: str = "fpt_policy"
    RRF:int=60
    # Cache settings for retrieval results (TTL-based in-memory cache)
    CACHE_TTL_SECONDS: int = 3600   # 1 hour TTL for retrieval results
    CACHE_MAX_SIZE: int = 256       # Max number of cached queries
    # LLM prompt optimization
    MAX_CONTEXT_CHARS: int = 3000   # Max total chars of context sent to LLM (~750 tokens)
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), 
        env_file_encoding='utf-8', 
        extra='ignore'
    )

settings = Settings()
