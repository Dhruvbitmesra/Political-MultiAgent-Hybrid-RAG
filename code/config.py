import os

from dotenv import load_dotenv


load_dotenv()


# ============================================================
# API KEYS
# ============================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

LANGSMITH_TRACING = os.getenv(
    "LANGSMITH_TRACING",
    "false"
)

LANGSMITH_API_KEY = os.getenv(
    "LANGSMITH_API_KEY"
)

LANGSMITH_PROJECT = os.getenv(
    "LANGSMITH_PROJECT",
    "political-gpt"
)




EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)




CHROMA_PATH = (
    "database/chroma_db"
)




GROQ_MODEL = (
    "llama-3.3-70b-versatile"
)