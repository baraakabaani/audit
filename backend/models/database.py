import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / "audit.db"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS engagements (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        entity_name TEXT,
        period      TEXT,
        currency    TEXT DEFAULT 'AED',
        overall_materiality  REAL,
        performance_materiality REAL,
        trivial_threshold    REAL,
        status      TEXT DEFAULT 'draft',
        created_at  TEXT DEFAULT (datetime('now')),
        updated_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS uploaded_files (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        engagement_id   INTEGER REFERENCES engagements(id),
        original_name   TEXT,
        stored_name     TEXT,
        file_type       TEXT,  -- 'tb', 'prior_tb', 'audit_template', 'fs_template', 'other'
        uploaded_at     TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS tb_accounts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        engagement_id   INTEGER REFERENCES engagements(id),
        account_code    TEXT,
        account_name    TEXT,
        sub_account     TEXT,
        account_type_raw TEXT,
        beginning_balance REAL DEFAULT 0,
        period_activity   REAL DEFAULT 0,
        ending_balance    REAL DEFAULT 0,
        source_row        INTEGER,
        is_zero           INTEGER DEFAULT 0,
        is_unusual        INTEGER DEFAULT 0,
        unusual_reason    TEXT
    );

    CREATE TABLE IF NOT EXISTS account_mappings (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        engagement_id    INTEGER REFERENCES engagements(id),
        account_code     TEXT,
        fs_category      TEXT,
        fs_line_item     TEXT,
        fs_statement     TEXT,   -- 'balance_sheet', 'pnl', 'equity', 'cashflow'
        lead_line        TEXT,
        confidence       REAL,
        confidence_level TEXT,   -- 'HIGH', 'MEDIUM', 'LOW'
        reason           TEXT,
        ifrs_reference   TEXT,
        source           TEXT DEFAULT 'AI',  -- 'AI', 'RULE', 'USER'
        user_approved    INTEGER DEFAULT 0,
        user_modified    INTEGER DEFAULT 0,
        user_note        TEXT,
        created_at       TEXT DEFAULT (datetime('now')),
        updated_at       TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS validation_results (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        engagement_id INTEGER REFERENCES engagements(id),
        check_name    TEXT,
        result        TEXT,    -- 'PASS', 'WARNING', 'ERROR'
        expected      TEXT,
        actual        TEXT,
        difference    TEXT,
        severity      TEXT,
        explanation   TEXT,
        created_at    TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS audit_trail (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        engagement_id INTEGER REFERENCES engagements(id),
        action        TEXT,
        account_code  TEXT,
        field         TEXT,
        old_value     TEXT,
        new_value     TEXT,
        source        TEXT,  -- 'AI', 'RULE', 'USER'
        reason        TEXT,
        created_at    TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS generated_files (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        engagement_id INTEGER REFERENCES engagements(id),
        file_type     TEXT,
        stored_name   TEXT,
        original_template TEXT,
        generated_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS template_metadata (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        engagement_id INTEGER REFERENCES engagements(id),
        file_type     TEXT,
        metadata_json TEXT,
        created_at    TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()


def log_audit(engagement_id: int, action: str, account_code: str,
              field: str, old_value: str, new_value: str,
              source: str = "SYSTEM", reason: str = ""):
    conn = get_conn()
    conn.execute(
        """INSERT INTO audit_trail
           (engagement_id, action, account_code, field, old_value, new_value, source, reason)
           VALUES (?,?,?,?,?,?,?,?)""",
        (engagement_id, action, account_code, field,
         str(old_value), str(new_value), source, reason)
    )
    conn.commit()
    conn.close()
