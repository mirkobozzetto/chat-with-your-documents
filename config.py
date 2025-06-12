import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in environment variables")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
CHAT_MODEL = os.getenv("CHAT_MODEL")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
CHUNK_STRATEGY = os.getenv("CHUNK_STRATEGY", "semantic")

CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", "0.1"))
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "4"))
RETRIEVAL_FETCH_K = int(os.getenv("RETRIEVAL_FETCH_K", "20"))
RETRIEVAL_LAMBDA_MULT = float(os.getenv("RETRIEVAL_LAMBDA_MULT", "0.7"))

CHROMA_PERSIST_DIRECTORY = "./chroma_db"
