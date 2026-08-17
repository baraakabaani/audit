import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
DB_PATH = BASE_DIR / "audit.db"

UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

# Materiality not set by default — auditor must enter
DEFAULT_MATERIALITY = None

DISCLAIMER = (
    "AI-generated classifications, calculations, and draft reporting outputs are subject to "
    "auditor review and approval. The system does not replace professional judgment or the "
    "auditor's responsibility for the financial statements or audit opinion."
)
