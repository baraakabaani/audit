"""
Account classification service.

Strategy:
1. Apply deterministic rules (fast, no API cost)
2. For accounts with LOW confidence or no rule match, call Groq AI
3. Store results with source (RULE / AI / USER)
"""

import os
from backend.accounting.rules import apply_rules, fallback_by_type
from backend.models.database import get_conn, log_audit


def classify_all_accounts(engagement_id: int, use_ai: bool = True) -> list[dict]:
    """
    Classify all TB accounts for an engagement.
    Returns list of mapping records (also saved to DB).
    """
    conn = get_conn()

    accounts = [
        dict(row) for row in conn.execute(
            "SELECT * FROM tb_accounts WHERE engagement_id = ?", (engagement_id,)
        ).fetchall()
    ]
    conn.close()

    results = []
    low_conf_accounts = []

    for acc in accounts:
        rule_result = apply_rules(acc)
        if rule_result and rule_result["confidence"] >= 0.70:
            classification = rule_result
        elif rule_result:
            classification = rule_result
            low_conf_accounts.append((acc, classification))
        else:
            classification = fallback_by_type(acc)
            low_conf_accounts.append((acc, classification))

        record = {
            "engagement_id": engagement_id,
            "account_code": acc["account_code"],
            "fs_category": classification["fs_category"],
            "fs_line_item": classification["fs_line_item"],
            "fs_statement": classification["fs_statement"],
            "lead_line": classification.get("lead_line", classification["fs_line_item"]),
            "confidence": classification["confidence"],
            "confidence_level": classification["confidence_level"],
            "reason": classification["reason"],
            "ifrs_reference": classification.get("ifrs_reference", ""),
            "source": classification["source"],
            "user_approved": 0,
            "user_modified": 0,
            "user_note": "",
        }
        results.append(record)

    # ── AI enhancement for low-confidence accounts ───────────────────────────
    if use_ai and low_conf_accounts and os.getenv("GROQ_API_KEY"):
        try:
            from backend.ai.groq_client import classify_account_ai
            for acc, existing in low_conf_accounts:
                ai_result = classify_account_ai(acc)
                if ai_result and ai_result["confidence"] > existing["confidence"]:
                    # Update the record in results
                    for r in results:
                        if r["account_code"] == acc["account_code"]:
                            r.update({
                                "fs_category": ai_result["fs_category"],
                                "fs_line_item": ai_result["fs_line_item"],
                                "fs_statement": ai_result["fs_statement"],
                                "lead_line": ai_result["lead_line"],
                                "confidence": ai_result["confidence"],
                                "confidence_level": ai_result["confidence_level"],
                                "reason": ai_result["reason"],
                                "ifrs_reference": ai_result.get("ifrs_reference", ""),
                                "source": "AI",
                            })
                            break
        except Exception:
            pass  # AI failed — use rule results

    # ── Persist to DB ─────────────────────────────────────────────────────────
    conn = get_conn()
    conn.execute("DELETE FROM account_mappings WHERE engagement_id = ?", (engagement_id,))
    conn.execute("DELETE FROM audit_trail WHERE engagement_id = ? AND action = 'CLASSIFY'", (engagement_id,))

    for r in results:
        conn.execute(
            """INSERT INTO account_mappings
               (engagement_id, account_code, fs_category, fs_line_item, fs_statement,
                lead_line, confidence, confidence_level, reason, ifrs_reference,
                source, user_approved, user_modified, user_note)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                r["engagement_id"], r["account_code"], r["fs_category"],
                r["fs_line_item"], r["fs_statement"], r["lead_line"],
                r["confidence"], r["confidence_level"], r["reason"],
                r["ifrs_reference"], r["source"], r["user_approved"],
                r["user_modified"], r["user_note"],
            )
        )
        # Write audit trail directly using same connection (avoids lock)
        conn.execute(
            """INSERT INTO audit_trail
               (engagement_id, action, account_code, field, old_value, new_value, source, reason)
               VALUES (?,?,?,?,?,?,?,?)""",
            (engagement_id, "CLASSIFY", r["account_code"], "classification", "none",
             f"{r['fs_statement']}|{r['fs_line_item']}|{r['confidence']:.0%}",
             r["source"], r["reason"])
        )

    conn.commit()
    conn.close()
    return results


def get_mappings(engagement_id: int) -> list[dict]:
    """Return all mappings for an engagement, joined with account data."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT m.*, a.account_name, a.account_type_raw,
                  a.beginning_balance, a.period_activity, a.ending_balance,
                  a.is_zero, a.is_unusual, a.unusual_reason
           FROM account_mappings m
           JOIN tb_accounts a ON m.account_code = a.account_code
                              AND a.engagement_id = m.engagement_id
           WHERE m.engagement_id = ?
           ORDER BY m.fs_statement, m.fs_category, ABS(a.ending_balance) DESC""",
        (engagement_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_mapping(engagement_id: int, account_code: str, updates: dict) -> None:
    """Apply user correction to a mapping."""
    conn = get_conn()
    old = conn.execute(
        "SELECT * FROM account_mappings WHERE engagement_id=? AND account_code=?",
        (engagement_id, account_code)
    ).fetchone()

    sets = []
    vals = []
    for key, val in updates.items():
        sets.append(f"{key} = ?")
        vals.append(val)
    sets.append("user_modified = 1")
    sets.append("updated_at = datetime('now')")
    vals += [engagement_id, account_code]

    conn.execute(
        f"UPDATE account_mappings SET {', '.join(sets)} WHERE engagement_id=? AND account_code=?",
        vals
    )
    conn.commit()

    log_audit(
        engagement_id, "USER_EDIT", account_code,
        "mapping",
        str(dict(old)) if old else "",
        str(updates),
        "USER",
        updates.get("user_note", ""),
    )
    conn.close()


def approve_mapping(engagement_id: int, account_code: str) -> None:
    conn = get_conn()
    conn.execute(
        """UPDATE account_mappings SET user_approved=1, updated_at=datetime('now')
           WHERE engagement_id=? AND account_code=?""",
        (engagement_id, account_code)
    )
    conn.commit()
    log_audit(engagement_id, "APPROVE", account_code, "user_approved", "0", "1", "USER", "")
    conn.close()


def bulk_approve(engagement_id: int, account_codes: list[str]) -> int:
    conn = get_conn()
    placeholders = ",".join("?" * len(account_codes))
    conn.execute(
        f"""UPDATE account_mappings SET user_approved=1, updated_at=datetime('now')
            WHERE engagement_id=? AND account_code IN ({placeholders})""",
        [engagement_id] + account_codes
    )
    count = conn.execute(
        f"SELECT changes()"
    ).fetchone()[0]
    conn.commit()
    conn.close()
    return count
