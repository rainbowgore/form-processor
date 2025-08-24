import os
from dotenv import load_dotenv

load_dotenv()

# -------- Document Intelligence ----------
# Your names:
DI_ENDPOINT = os.getenv("AZURE_DOC_INTEL_ENDPOINT", "")
DI_KEY      = os.getenv("AZURE_DOC_INTEL_KEY", "")
# Fallbacks (if someone uses earlier names):
if not DI_ENDPOINT:
    DI_ENDPOINT = os.getenv("AZURE_DI_ENDPOINT", "")
if not DI_KEY:
    DI_KEY = os.getenv("AZURE_DI_KEY", "")

# -------- Azure OpenAI ----------
# Your names:
AOAI_ENDPOINT   = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AOAI_API_KEY    = os.getenv("AOAI_API_KEY", "")  # your provided var name
AOAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
# Optional: allow either var for version; default to your value
AOAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# Optional embeddings if you want to extend later
AOAI_EMBEDDINGS_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", "text-embedding-ada-002")

# Tunables
DEFAULT_TEMPERATURE = float(os.getenv("AOAI_TEMPERATURE", "0.1"))
MAX_OCR_PAGES = int(os.getenv("MAX_OCR_PAGES", "6"))  # safety bound