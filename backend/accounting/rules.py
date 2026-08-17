"""
Deterministic account classification rules.

Rules are applied before AI to handle clear-cut cases.
Every rule produces: fs_statement, fs_category, fs_line_item, lead_line, confidence, reason, ifrs_ref.

The FS line items map exactly to the Audit Draft template cells.
The lead_line maps to the LEAD sheet aggregation rows.
"""

import re
from typing import Optional


# ── Balance Sheet line items (match Audit Draft template labels) ─────────────
BS_LINE = {
    "PPE":                      "Property, plant and equipment",
    "INTANGIBLES":              "Intangible assets",
    "INVESTMENTS":              "Investments",
    "OTHER_NCA":                "Other non-current assets",
    "INVENTORIES":              "Inventories",
    "TRADE_RECEIVABLES":        "Trade and other receivables",
    "CASH":                     "Cash and bank balances",
    "EOSB":                     "Provision for end of service benefits",
    "TRADE_PAYABLES":           "Trade and other payables",
    "REVALUATION_RESERVE":      "Revaluation reserve",
    "ACCUMULATED_LOSSES":       "Accumulated losses",
    "GOVERNMENT_GRANTS_EQUITY": "Government grants (equity)",
}

# ── P&L line items ───────────────────────────────────────────────────────────
PL_LINE = {
    "REVENUE":          "Revenue",
    "COS":              "Cost of revenue",
    "GRANT_INCOME":     "Grant received",
    "OTHER_INCOME":     "Other income",
    "ADMIN_EXPENSES":   "General and administrative expenses",
    "FINANCE_COST":     "Finance cost",
}

# ── LEAD sheet line mapping ──────────────────────────────────────────────────
LEAD_LINES = {
    "PPE":               "Property, plant and equipment",
    "INTANGIBLES":       "Intangible assets",
    "INVESTMENTS":       "Investments",
    "OTHER_NCA":         "Other non-current assets",
    "INVENTORIES":       "Inventories",
    "TRADE_RECEIVABLES": "Trade and other receivables",
    "CASH":              "Cash and bank balances",
    "EOSB":              "Provision for EOSB",
    "TRADE_PAYABLES":    "Trade and other payables",
    "EQUITY":            "Equity",
    "REVENUE":           "Revenue",
    "COS":               "Cost of revenue",
    "GRANT_INCOME":      "Government grant received",
    "OTHER_INCOME":      "Other income",
    "ADMIN_EXPENSES":    "General and administrative expenses",
    "FINANCE_COST":      "Finance cost",
}


# ── Keyword rule sets ─────────────────────────────────────────────────────────
# Each entry: (name_keywords, code_prefixes, account_types, classification_key, confidence, reason, ifrs)
# account_types: list of partial strings to match against Account Type column
# code_prefixes: list of numeric prefixes (as strings) for the NNNNN part

RULES = [
    # ── ACCUMULATED DEPRECIATION / AMORTISATION (contra-asset, often typed Liability) ──
    {
        "name_kw": ["accum'd dep'n", "accumulated dep", "accum dep", "accumulated depreciation",
                    "provision for depreciation"],
        "code_prefix": [],
        "account_types": ["liability", "asset"],
        "fs_statement": "balance_sheet",
        "fs_category": "Non-Current Assets",
        "fs_line": "PPE",
        "lead_line": "PPE",
        "confidence": 0.92,
        "reason": "Accumulated depreciation is a contra-asset presented net in PPE.",
        "ifrs": "IAS 16 — Property, Plant and Equipment",
    },
    {
        "name_kw": ["accum'd amort", "accumulated amort", "accum amort"],
        "code_prefix": [],
        "account_types": ["liability", "asset"],
        "fs_statement": "balance_sheet",
        "fs_category": "Non-Current Assets",
        "fs_line": "INTANGIBLES",
        "lead_line": "INTANGIBLES",
        "confidence": 0.90,
        "reason": "Accumulated amortisation is a contra-asset presented net in Intangibles.",
        "ifrs": "IAS 38 — Intangible Assets",
    },

    # ── CASH & BANK ──────────────────────────────────────────────────────────
    {
        "name_kw": ["cash", "petty cash", "bank account", "bank balance", "current account",
                    "savings account", "remittance"],
        "code_prefix": [],
        "account_types": ["asset"],
        "fs_statement": "balance_sheet",
        "fs_category": "Current Assets",
        "fs_line": "CASH",
        "lead_line": "CASH",
        "confidence": 0.95,
        "reason": "Name and account type indicate cash or bank balance.",
        "ifrs": "IAS 7 — Cash and Cash Equivalents",
    },

    # ── TRADE & OTHER RECEIVABLES ─────────────────────────────────────────────
    {
        "name_kw": ["receivable", "debtor", "trade receivable", "accounts receivable",
                    "vat receivable", "prepayment", "prepaid", "advance to",
                    "miscellaneous debtor", "due from"],
        "code_prefix": [],
        "account_types": ["asset"],
        "fs_statement": "balance_sheet",
        "fs_category": "Current Assets",
        "fs_line": "TRADE_RECEIVABLES",
        "lead_line": "TRADE_RECEIVABLES",
        "confidence": 0.90,
        "reason": "Name indicates trade or other receivable.",
        "ifrs": "IFRS 9 / IAS 32 — Financial Assets",
    },

    # ── INVENTORIES ───────────────────────────────────────────────────────────
    {
        "name_kw": ["inventory", "inventories", "stock", "goods for sale", "wip",
                    "work in progress", "merchandise"],
        "code_prefix": [],
        "account_types": ["asset"],
        "fs_statement": "balance_sheet",
        "fs_category": "Current Assets",
        "fs_line": "INVENTORIES",
        "lead_line": "INVENTORIES",
        "confidence": 0.92,
        "reason": "Name indicates inventories or stock.",
        "ifrs": "IAS 2 — Inventories",
    },

    # ── PPE ───────────────────────────────────────────────────────────────────
    {
        "name_kw": ["property", "plant", "equipment", "furniture", "fixture",
                    "motor vehicle", "vehicle", "land", "building", "leasehold",
                    "improvement", "machinery", "computer", "hardware",
                    "accumulated depreciation", "depreciation - ppe",
                    "fixed asset", "capital work"],
        "code_prefix": [],
        "account_types": ["asset"],
        "fs_statement": "balance_sheet",
        "fs_category": "Non-Current Assets",
        "fs_line": "PPE",
        "lead_line": "PPE",
        "confidence": 0.90,
        "reason": "Name indicates property, plant and equipment.",
        "ifrs": "IAS 16 — Property, Plant and Equipment",
    },

    # ── INTANGIBLE ASSETS ─────────────────────────────────────────────────────
    {
        "name_kw": ["intangible", "software", "license", "trademark", "patent",
                    "goodwill", "brand", "amortisation", "amortization",
                    "accumulated amortisation"],
        "code_prefix": [],
        "account_types": ["asset"],
        "fs_statement": "balance_sheet",
        "fs_category": "Non-Current Assets",
        "fs_line": "INTANGIBLES",
        "lead_line": "INTANGIBLES",
        "confidence": 0.90,
        "reason": "Name indicates intangible asset.",
        "ifrs": "IAS 38 — Intangible Assets",
    },

    # ── INVESTMENTS ───────────────────────────────────────────────────────────
    {
        "name_kw": ["investment", "equity investment", "subsidiary", "associate",
                    "joint venture", "financial asset", "long-term investment"],
        "code_prefix": [],
        "account_types": ["asset"],
        "fs_statement": "balance_sheet",
        "fs_category": "Non-Current Assets",
        "fs_line": "INVESTMENTS",
        "lead_line": "INVESTMENTS",
        "confidence": 0.85,
        "reason": "Name indicates investment or financial asset.",
        "ifrs": "IFRS 9 / IAS 28 / IFRS 10",
    },

    # ── TRADE PAYABLES / OTHER PAYABLES ──────────────────────────────────────
    {
        "name_kw": ["payable", "creditor", "trade payable", "accounts payable",
                    "accrued", "accrual", "vat payable", "withholding",
                    "other payable", "due to", "deferred revenue", "advance from"],
        "code_prefix": [],
        "account_types": ["liability"],
        "fs_statement": "balance_sheet",
        "fs_category": "Current Liabilities",
        "fs_line": "TRADE_PAYABLES",
        "lead_line": "TRADE_PAYABLES",
        "confidence": 0.90,
        "reason": "Name indicates trade or other payable.",
        "ifrs": "IFRS 9 / IAS 32 — Financial Liabilities",
    },

    # ── EOSB / GRATUITY — LIABILITY accounts (balance sheet) ─────────────────
    {
        "name_kw": ["end of service", "eosb", "gratuity", "provision for leave",
                    "provision for end of service", "provision for end-of-service"],
        "code_prefix": [],
        "account_types": ["liability"],   # Only Liability type goes to BS
        "fs_statement": "balance_sheet",
        "fs_category": "Non-Current Liabilities",
        "fs_line": "EOSB",
        "lead_line": "EOSB",
        "confidence": 0.90,
        "reason": "Liability account indicates EOSB provision on the balance sheet.",
        "ifrs": "IAS 19 — Employee Benefits",
    },
    # ── EOSB / GRATUITY — EXPENSE accounts (P&L) ─────────────────────────────
    {
        "name_kw": ["provision expense for end of service", "eosb expense",
                    "provision for end of service gra", "provision for leave expense",
                    "movement in provision", "provision - payroll",
                    "annual leave expense", "employee benefit expense"],
        "code_prefix": [],
        "account_types": ["expense"],   # Expense type goes to P&L
        "fs_statement": "pnl",
        "fs_category": "General and Administrative Expenses",
        "fs_line": "ADMIN_EXPENSES",
        "lead_line": "ADMIN_EXPENSES",
        "confidence": 0.82,
        "reason": "EOSB / leave provision expense recognized in P&L.",
        "ifrs": "IAS 19 — Employee Benefits",
    },

    # ── EQUITY ────────────────────────────────────────────────────────────────
    {
        "name_kw": ["retained earning", "accumulated loss", "accumulated profit",
                    "profit and loss", "reserve", "equity", "share capital",
                    "share premium", "dof payment", "government contribution"],
        "code_prefix": [],
        "account_types": ["owners' equity", "equity"],
        "fs_statement": "balance_sheet",
        "fs_category": "Equity",
        "fs_line": "ACCUMULATED_LOSSES",
        "lead_line": "EQUITY",
        "confidence": 0.88,
        "reason": "Account type is equity and name indicates equity component.",
        "ifrs": "IAS 1 — Presentation of Financial Statements",
    },
    {
        "name_kw": ["revaluation reserve", "revaluation surplus"],
        "code_prefix": [],
        "account_types": ["owners' equity", "equity"],
        "fs_statement": "balance_sheet",
        "fs_category": "Equity",
        "fs_line": "REVALUATION_RESERVE",
        "lead_line": "EQUITY",
        "confidence": 0.92,
        "reason": "Name indicates revaluation reserve.",
        "ifrs": "IAS 16 / IAS 1",
    },

    # ── REVENUE ───────────────────────────────────────────────────────────────
    {
        "name_kw": ["revenue", "sales", "income from", "membership", "subscription",
                    "rental income", "rental revenue", "service fee", "registration",
                    "event", "exhibition", "facility", "courtyard", "lounge",
                    "competitively priced", "other rental", "sale of goods",
                    "programme fee", "certification"],
        "code_prefix": [],
        "account_types": ["revenue"],
        "fs_statement": "pnl",
        "fs_category": "Revenue",
        "fs_line": "REVENUE",
        "lead_line": "REVENUE",
        "confidence": 0.88,
        "reason": "Account type is revenue.",
        "ifrs": "IFRS 15 — Revenue from Contracts with Customers",
    },

    # ── GOVERNMENT GRANTS ─────────────────────────────────────────────────────
    {
        "name_kw": ["grant", "government grant", "subsidy", "subvention"],
        "code_prefix": [],
        "account_types": ["revenue"],
        "fs_statement": "pnl",
        "fs_category": "Grant Received",
        "fs_line": "GRANT_INCOME",
        "lead_line": "GRANT_INCOME",
        "confidence": 0.90,
        "reason": "Name indicates government grant or subsidy income.",
        "ifrs": "IAS 20 — Government Grants",
    },

    # ── OTHER INCOME ──────────────────────────────────────────────────────────
    {
        "name_kw": ["other income", "miscellaneous income", "miscellaneous revenue",
                    "gain on disposal", "profit on disposal", "foreign exchange gain",
                    "fx gain", "reversal of provision", "income from investment",
                    "interest income", "management fee income", "write-back",
                    "penalty income", "fines income", "sale of fixed assets",
                    "prior period"],
        "code_prefix": [],
        "account_types": ["revenue"],
        "fs_statement": "pnl",
        "fs_category": "Other Income",
        "fs_line": "OTHER_INCOME",
        "lead_line": "OTHER_INCOME",
        "confidence": 0.82,
        "reason": "Name indicates other / miscellaneous income.",
        "ifrs": "IAS 1 — Other income presentation",
    },

    # ── COST OF SALES / REVENUE ───────────────────────────────────────────────
    {
        "name_kw": ["cost of sales", "cost of revenue", "cost of service",
                    "cost of goods", "direct cost", "programme cost",
                    "cost of event", "direct labour"],
        "code_prefix": [],
        "account_types": ["expense"],
        "fs_statement": "pnl",
        "fs_category": "Cost of Revenue",
        "fs_line": "COS",
        "lead_line": "COS",
        "confidence": 0.88,
        "reason": "Name indicates direct cost of sales or services.",
        "ifrs": "IAS 2 / IFRS 15 — Cost of revenue",
    },

    # ── FINANCE COST ──────────────────────────────────────────────────────────
    {
        "name_kw": ["finance cost", "interest expense", "interest on loan",
                    "loan interest", "lease interest", "ifrs 16 interest",
                    "bank charges", "bank fee", "bank commission",
                    "foreign exchange loss", "fx loss", "financing fee",
                    "letter of credit"],
        "code_prefix": [],
        "account_types": ["expense"],
        "fs_statement": "pnl",
        "fs_category": "Finance Cost",
        "fs_line": "FINANCE_COST",
        "lead_line": "FINANCE_COST",
        "confidence": 0.85,
        "reason": "Name indicates finance cost or bank charge.",
        "ifrs": "IAS 23 / IFRS 9 — Borrowing Costs / Finance Costs",
    },

    # ── GENERAL & ADMINISTRATIVE EXPENSES (catch-all for expenses) ───────────
    {
        "name_kw": ["salary", "salaries", "wage", "wages", "payroll", "staff",
                    "employee cost", "annual leave", "sick leave", "overtime",
                    "allowance", "bonus", "incentive",
                    "rent", "office rent", "lease", "utility", "electricity",
                    "water", "internet", "telephone", "communication",
                    "depreciation", "amortisation", "amortization",
                    "insurance", "professional fee", "audit fee", "legal fee",
                    "consultant", "advisory", "marketing", "advertising",
                    "event expense", "printing", "stationery", "office supply",
                    "maintenance", "repair", "cleaning", "security",
                    "travel", "entertainment", "hospitality",
                    "it expense", "software expense", "subscription fee",
                    "training", "development", "outsource",
                    "miscellaneous expense", "general expense", "other expense",
                    "admin", "management fee expense"],
        "code_prefix": [],
        "account_types": ["expense"],
        "fs_statement": "pnl",
        "fs_category": "General and Administrative Expenses",
        "fs_line": "ADMIN_EXPENSES",
        "lead_line": "ADMIN_EXPENSES",
        "confidence": 0.80,
        "reason": "Name and type indicate general and administrative expense.",
        "ifrs": "IAS 1 — Presentation",
    },
]


def apply_rules(account: dict) -> Optional[dict]:
    """
    Apply deterministic rules to classify a single TB account.

    Returns a classification dict or None if no rule matches.
    """
    name = (account.get("account_name") or "").lower()
    acc_type = (account.get("account_type_raw") or "").lower()
    code = (account.get("account_code") or "").split("-")[0]  # numeric prefix

    best_match = None
    best_confidence = 0.0

    for rule in RULES:
        # Check account type
        type_ok = any(t in acc_type for t in rule["account_types"])
        if not type_ok:
            continue

        # Check name keywords
        name_ok = any(kw in name for kw in rule["name_kw"])
        if not name_ok:
            continue

        # Check code prefix if specified
        if rule["code_prefix"]:
            code_ok = any(code.startswith(p) for p in rule["code_prefix"])
            if not code_ok:
                continue

        if rule["confidence"] > best_confidence:
            best_confidence = rule["confidence"]
            best_match = rule

    if best_match is None:
        return None

    return {
        "fs_statement": best_match["fs_statement"],
        "fs_category": best_match["fs_category"],
        "fs_line_item": best_match["fs_line"],
        "lead_line": best_match["lead_line"],
        "confidence": best_match["confidence"],
        "confidence_level": _level(best_match["confidence"]),
        "reason": best_match["reason"],
        "ifrs_reference": best_match["ifrs"],
        "source": "RULE",
    }


def _level(confidence: float) -> str:
    if confidence >= 0.90:
        return "HIGH"
    if confidence >= 0.70:
        return "MEDIUM"
    return "LOW"


def fallback_by_type(account: dict) -> dict:
    """Last-resort classification using only the Account Type column."""
    acc_type = (account.get("account_type_raw") or "").lower()

    if "asset" in acc_type:
        return {
            "fs_statement": "balance_sheet",
            "fs_category": "Current Assets",
            "fs_line_item": "TRADE_RECEIVABLES",
            "lead_line": "TRADE_RECEIVABLES",
            "confidence": 0.40,
            "confidence_level": "LOW",
            "reason": "Classified as Asset by Account Type only — name inspection required.",
            "ifrs_reference": "IAS 1",
            "source": "RULE",
        }
    if "liability" in acc_type:
        return {
            "fs_statement": "balance_sheet",
            "fs_category": "Current Liabilities",
            "fs_line_item": "TRADE_PAYABLES",
            "lead_line": "TRADE_PAYABLES",
            "confidence": 0.40,
            "confidence_level": "LOW",
            "reason": "Classified as Liability by Account Type only — name inspection required.",
            "ifrs_reference": "IAS 1",
            "source": "RULE",
        }
    if "revenue" in acc_type:
        return {
            "fs_statement": "pnl",
            "fs_category": "Revenue",
            "fs_line_item": "REVENUE",
            "lead_line": "REVENUE",
            "confidence": 0.50,
            "confidence_level": "LOW",
            "reason": "Classified as Revenue by Account Type only.",
            "ifrs_reference": "IFRS 15",
            "source": "RULE",
        }
    if "expense" in acc_type:
        return {
            "fs_statement": "pnl",
            "fs_category": "General and Administrative Expenses",
            "fs_line_item": "ADMIN_EXPENSES",
            "lead_line": "ADMIN_EXPENSES",
            "confidence": 0.50,
            "confidence_level": "LOW",
            "reason": "Classified as Expense by Account Type only.",
            "ifrs_reference": "IAS 1",
            "source": "RULE",
        }
    if "equity" in acc_type or "owner" in acc_type:
        return {
            "fs_statement": "balance_sheet",
            "fs_category": "Equity",
            "fs_line_item": "ACCUMULATED_LOSSES",
            "lead_line": "EQUITY",
            "confidence": 0.50,
            "confidence_level": "LOW",
            "reason": "Classified as Equity by Account Type only.",
            "ifrs_reference": "IAS 1",
            "source": "RULE",
        }

    return {
        "fs_statement": "unclassified",
        "fs_category": "Unclassified",
        "fs_line_item": "UNCLASSIFIED",
        "lead_line": "UNCLASSIFIED",
        "confidence": 0.10,
        "confidence_level": "LOW",
        "reason": "Account type unrecognized. Manual classification required.",
        "ifrs_reference": None,
        "source": "RULE",
    }
