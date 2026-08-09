from config import (
    GROQ_API_KEY,
    LANGSMITH_API_KEY,
    LANGSMITH_PROJECT,
    EMBEDDING_MODEL,
)

print("Environment check")
print("-----------------")

print("Groq API key loaded:", bool(GROQ_API_KEY))
print("LangSmith API key loaded:", bool(LANGSMITH_API_KEY))
print("LangSmith project:", LANGSMITH_PROJECT)
print("Embedding model:", EMBEDDING_MODEL)