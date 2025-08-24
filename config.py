import os
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st  # type: ignore
    _SECRETS = st.secrets
except Exception:  # not running in Streamlit Cloud
    _SECRETS = {}

def _get(name: str, default: str = "") -> str:
    if name in _SECRETS:
        # Streamlit Cloud secrets
        return str(_SECRETS[name])
    # fallback to env (local .env or injected env)
    return os.getenv(name, default)

# -------- Document Intelligence ----------
DI_ENDPOINT = _get("AZURE_DOC_INTEL_ENDPOINT") or _get("AZURE_DI_ENDPOINT")
DI_KEY      = _get("AZURE_DOC_INTEL_KEY") or _get("AZURE_DI_KEY")

# -------- Azure OpenAI ----------
AOAI_ENDPOINT   = _get("AZURE_OPENAI_ENDPOINT")
AOAI_API_KEY    = _get("AOAI_API_KEY")
AOAI_DEPLOYMENT = _get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AOAI_API_VERSION = _get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# Optional embeddings if you want to extend later
AOAI_EMBEDDINGS_DEPLOYMENT = _get("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", "text-embedding-ada-002")

# Tunables
DEFAULT_TEMPERATURE = float(_get("AOAI_TEMPERATURE", "0.1"))
MAX_OCR_PAGES = int(_get("MAX_OCR_PAGES", "6"))  # safety bound