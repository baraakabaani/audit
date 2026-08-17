"""
Groq AI client for account classification.

Used only when rule-based classification fails or confidence is LOW.
Deterministic calculations are NEVER delegated to the LLM.
"""

import json
import os
from typing import Optional
from groq import Groq

_client: Optional[Groq] = None


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY environment variable not set. "
                "Get a free key at https://console.groq.com"
            )
        _client = Groq(api_key=api_key)
    return _client


CLASSIFICATION_PROMPT = """You are a senior IFRS financial reporting expert and UAE external auditor.

Classify the following trial balance account for a UAE entity into the correct financial statement line item.

Account Details:
- Account Code: {code}
- Account Name: {name}
- Sub-Account: {sub}
- Account Type (from ERP): {acc_type}
- Ending Balance: {balance} AED
- Beginning Balance: {beginning} AED

Available financial statement categories and line items:

BALANCE SHEET:
- Non-Current Assets: Property plant and equipment (PPE), Intangible assets, Investments, Other non-current assets
- Current Assets: Inventories, Trade and other receivables, Cash and bank balances
- Equity: Revaluation reserve, Accumulated losses (or retained earnings)
- Non-Current Liabilities: Provision for end of service benefits (EOSB)
- Current Liabilities: Trade and other payables

PROFIT OR LOSS:
- Revenue
- Cost of revenue
- Grant received (government grants)
- Other income
- General and administrative expenses
- Finance cost

Respond with ONLY valid JSON in this exact format:
{{
  "fs_statement": "balance_sheet" | "pnl",
  "fs_category": "<category name>",
  "fs_line_item": "PPE" | "INTANGIBLES" | "INVESTMENTS" | "OTHER_NCA" | "INVENTORIES" | "TRADE_RECEIVABLES" | "CASH" | "EOSB" | "TRADE_PAYABLES" | "REVALUATION_RESERVE" | "ACCUMULATED_LOSSES" | "REVENUE" | "COS" | "GRANT_INCOME" | "OTHER_INCOME" | "ADMIN_EXPENSES" | "FINANCE_COST",
  "lead_line": "<same as fs_line_item>",
  "confidence": <float between 0.0 and 1.0>,
  "reason": "<one sentence explanation>",
  "ifrs_reference": "<primary IFRS/IAS standard>",
  "flags": "<any special considerations or empty string>"
}}

Rules:
1. Do NOT invent account types or categories not in the list above.
2. Bank charges are Finance Cost, NOT administrative expenses.
3. Salary/payroll expenses are General and Administrative Expenses.
4. EOSB/gratuity provisions are Non-Current Liabilities (EOSB).
5. Government grants received are Grant received on P&L.
6. Prior period adjustments require auditor review — set confidence below 0.5.
7. Movement in provisions can be either expense or liability adjustment — note this in flags.
8. If you are uncertain, set confidence below 0.70."""


def classify_account_ai(account: dict) -> Optional[dict]:
    """
    Use Groq LLM to classify a single account.
    Returns classification dict or None on failure.
    """
    try:
        client = get_client()
        prompt = CLASSIFICATION_PROMPT.format(
            code=account.get("account_code", ""),
            name=account.get("account_name", ""),
            sub=account.get("sub_account", "") or "Default",
            acc_type=account.get("account_type_raw", ""),
            balance=f"{account.get('ending_balance', 0):,.2f}",
            beginning=f"{account.get('beginning_balance', 0):,.2f}",
        )

        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=400,
            response_format={"type": "json_object"},
        )

        raw = resp.choices[0].message.content
        data = json.loads(raw)

        # Validate required fields
        required = ["fs_statement", "fs_category", "fs_line_item", "confidence", "reason"]
        for field in required:
            if field not in data:
                return None

        confidence = float(data["confidence"])
        level = "HIGH" if confidence >= 0.90 else "MEDIUM" if confidence >= 0.70 else "LOW"

        return {
            "fs_statement": data["fs_statement"],
            "fs_category": data["fs_category"],
            "fs_line_item": data["fs_line_item"],
            "lead_line": data.get("lead_line", data["fs_line_item"]),
            "confidence": confidence,
            "confidence_level": level,
            "reason": data.get("reason", "AI classification"),
            "ifrs_reference": data.get("ifrs_reference", ""),
            "ai_flags": data.get("flags", ""),
            "source": "AI",
        }

    except Exception as exc:
        return None


def batch_classify(accounts: list[dict], low_confidence_only: bool = False) -> dict[str, dict]:
    """
    Classify a batch of accounts using AI.

    Returns a dict keyed by account_code.
    """
    results = {}
    for acc in accounts:
        if low_confidence_only:
            # Only call AI for low/medium confidence accounts
            existing_conf = acc.get("confidence", 0)
            if existing_conf >= 0.90:
                continue
        code = acc.get("account_code", "")
        result = classify_account_ai(acc)
        if result:
            results[code] = result
    return results
