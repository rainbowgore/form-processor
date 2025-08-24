import os
from dotenv import load_dotenv

load_dotenv()

def _get(name: str, default: str = "") -> str:
    """Get value from Streamlit secrets (Cloud) or environment variables (local)"""
    # 1) First try environment variables (works locally with .env)
    env_value = os.getenv(name, None)
    if env_value is not None:
        return env_value
    
    # 2) Only try Streamlit secrets if env var not found (Cloud deployment)
    try:
        # Import streamlit only when needed and in a try block
        import streamlit as st
        # Check if we're in a Streamlit context and secrets exist
        if hasattr(st, '_get_option') and name in st.secrets:
            return str(st.secrets[name])
    except:
        # If any error (including missing secrets), just fall back to default
        pass
    
    return default

# -------- Document Intelligence ----------
DI_ENDPOINT = _get("AZURE_DOC_INTEL_ENDPOINT") or _get("AZURE_DI_ENDPOINT")
DI_KEY = _get("AZURE_DOC_INTEL_KEY") or _get("AZURE_DI_KEY")

# -------- Azure OpenAI ----------
AOAI_ENDPOINT = _get("AZURE_OPENAI_ENDPOINT")
AOAI_API_KEY = _get("AOAI_API_KEY")
AOAI_DEPLOYMENT = _get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AOAI_API_VERSION = _get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# Optional embeddings if you want to extend later
AOAI_EMBEDDINGS_DEPLOYMENT = _get("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", "text-embedding-ada-002")

# Tunables
DEFAULT_TEMPERATURE = float(_get("AOAI_TEMPERATURE", "0.1"))
MAX_OCR_PAGES = int(_get("MAX_OCR_PAGES", "6"))