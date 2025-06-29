# config.py
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in environment variables")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")

CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4.1-2025-04-14")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "300"))
CHUNK_STRATEGY = os.getenv("CHUNK_STRATEGY", "semantic")

AGENTIC_CHUNKING_ENABLED = os.getenv("AGENTIC_CHUNKING_ENABLED", "false").lower() == "true"
AGENTIC_LLM_MODEL = os.getenv("AGENTIC_LLM_MODEL", "gpt-4.1-2025-04-14")
AGENTIC_STRATEGY = os.getenv("AGENTIC_STRATEGY", "agentic_basic")

CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", "0.1"))
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "6"))
RETRIEVAL_FETCH_K = int(os.getenv("RETRIEVAL_FETCH_K", "25"))
RETRIEVAL_LAMBDA_MULT = float(os.getenv("RETRIEVAL_LAMBDA_MULT", "0.8"))

VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "chroma")

CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

ENABLE_CONTEXTUAL_RAG = os.getenv("ENABLE_CONTEXTUAL_RAG", "false").lower() == "true"
DENSE_WEIGHT = float(os.getenv("DENSE_WEIGHT", "0.6"))
SPARSE_WEIGHT = float(os.getenv("SPARSE_WEIGHT", "0.4"))
RRF_K = int(os.getenv("RRF_K", "60"))
USE_NEURAL_RERANKER = os.getenv("USE_NEURAL_RERANKER", "true").lower() == "true"
RELEVANCE_WEIGHT = float(os.getenv("RELEVANCE_WEIGHT", "0.7"))
ORIGINAL_WEIGHT = float(os.getenv("ORIGINAL_WEIGHT", "0.3"))
CONTEXTUAL_RETRIEVAL_K = int(os.getenv("CONTEXTUAL_RETRIEVAL_K", "20"))
FINAL_RETRIEVAL_K = int(os.getenv("FINAL_RETRIEVAL_K", "5"))

QDRANT_URL = os.getenv("QDRANT_URL", "https://qdrant.mirko.re")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag_documents")
QDRANT_TIMEOUT = int(os.getenv("QDRANT_TIMEOUT", "60"))
QDRANT_VERIFY_SSL = os.getenv("QDRANT_VERIFY_SSL", "false").lower() == "true"

AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
AUTH_USERS = os.getenv("AUTH_USERS", "")
AUTH_GLOBAL_ACCESS = os.getenv("AUTH_GLOBAL_ACCESS", "true").lower() == "true"

ENABLE_QUALITY_GATE = os.getenv("ENABLE_QUALITY_GATE", "true").lower() == "true"
ENABLE_EMPIRICAL_VALIDATION = os.getenv("ENABLE_EMPIRICAL_VALIDATION", "false").lower() == "true"
QUALITY_SCORE_THRESHOLD = float(os.getenv("QUALITY_SCORE_THRESHOLD", "0.6"))
