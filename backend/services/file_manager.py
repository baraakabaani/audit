"""File management — secure upload handling and output generation."""

import uuid
from pathlib import Path
from backend.config import UPLOADS_DIR, OUTPUTS_DIR
from backend.models.database import get_conn


ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".xlsm"}


def save_upload(engagement_id: int, filename: str, content: bytes, file_type: str) -> dict:
    """Save an uploaded file and register it in the database."""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type {suffix} not allowed. Only Excel files are accepted.")

    stored_name = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOADS_DIR / stored_name
    dest.write_bytes(content)

    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO uploaded_files (engagement_id, original_name, stored_name, file_type)
           VALUES (?, ?, ?, ?)""",
        (engagement_id, filename, stored_name, file_type)
    )
    file_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": file_id,
        "original_name": filename,
        "stored_name": stored_name,
        "path": str(dest),
        "file_type": file_type,
    }


def get_uploads(engagement_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM uploaded_files WHERE engagement_id = ?", (engagement_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_upload_path(engagement_id: int, file_type: str) -> Path | None:
    conn = get_conn()
    row = conn.execute(
        """SELECT stored_name FROM uploaded_files
           WHERE engagement_id = ? AND file_type = ?
           ORDER BY id DESC LIMIT 1""",
        (engagement_id, file_type)
    ).fetchone()
    conn.close()
    if row:
        p = UPLOADS_DIR / row["stored_name"]
        return p if p.exists() else None
    return None


def register_output(engagement_id: int, file_type: str, stored_name: str, template_name: str) -> None:
    conn = get_conn()
    conn.execute(
        """INSERT INTO generated_files (engagement_id, file_type, stored_name, original_template)
           VALUES (?,?,?,?)""",
        (engagement_id, file_type, stored_name, template_name)
    )
    conn.commit()
    conn.close()


def get_output_path(engagement_id: int, file_type: str) -> Path | None:
    conn = get_conn()
    row = conn.execute(
        """SELECT stored_name FROM generated_files
           WHERE engagement_id = ? AND file_type = ?
           ORDER BY id DESC LIMIT 1""",
        (engagement_id, file_type)
    ).fetchone()
    conn.close()
    if row:
        p = OUTPUTS_DIR / row["stored_name"]
        return p if p.exists() else None
    return None
