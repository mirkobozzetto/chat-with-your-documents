import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in environment variables")

EMBEDDING_MODEL = "text-embedding-3-large"
CHAT_MODEL = "gpt-4o"

CHUNK_SIZE = 512
CHUNK_OVERLAP = 100
CHUNK_STRATEGY = "semantic"

CHROMA_PERSIST_DIRECTORY = "./chroma_db"
