# config.py
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in environment variables")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4.1-2025-04-14")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
CHUNK_STRATEGY = os.getenv("CHUNK_STRATEGY", "semantic")

CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", "0.1"))
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "3"))
RETRIEVAL_FETCH_K = int(os.getenv("RETRIEVAL_FETCH_K", "15"))
RETRIEVAL_LAMBDA_MULT = float(os.getenv("RETRIEVAL_LAMBDA_MULT", "0.95"))

VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "chroma")

CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

QDRANT_URL = os.getenv("QDRANT_URL", "https://qdrant.mirko.re")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag_documents")
QDRANT_TIMEOUT = int(os.getenv("QDRANT_TIMEOUT", "60"))
QDRANT_VERIFY_SSL = os.getenv("QDRANT_VERIFY_SSL", "false").lower() == "true"

AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
AUTH_USERS = os.getenv("AUTH_USERS", "")
AUTH_GLOBAL_ACCESS = os.getenv("AUTH_GLOBAL_ACCESS", "true").lower() == "true"
