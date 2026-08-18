import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
# Use Railway persistent volume if available
_data_dir = Path("/data") if Path("/data").exists() else BASE_DIR
UPLOADS_DIR = _data_dir / "uploads"
OUTPUTS_DIR = _data_dir / "outputs"
DB_PATH = _data_dir / "audit.db"

UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama3-70b-8192"

# Materiality not set by default — auditor must enter
DEFAULT_MATERIALITY = None

DISCLAIMER = (
    "AI-generated classifications, calculations, and draft reporting outputs are subject to "
    "auditor review and approval. The system does not replace professional judgment or the "
    "auditor's responsibility for the financial statements or audit opinion."
)
