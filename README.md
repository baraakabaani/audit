# Audit Automation System

Professional financial statement and audit report preparation tool.

## Quick Start

1. Double-click `start.bat`
2. Open http://localhost:5173 in your browser
3. Click **+ New Engagement**
4. Upload your files in the **Upload** tab
5. Follow the workflow: Upload → Analyze → Classify → Map Review → Validate → Generate

## Groq AI (Free Account Classification)

Get a free API key from https://console.groq.com

Set it before starting:
```
set GROQ_API_KEY=your_key_here
```
Or edit `start.bat` to add the line above the uvicorn command.

Without a key, the system uses deterministic rules only (still classifies ~70% of accounts at HIGH confidence).

## Workflow

1. **Upload** — Upload TB Excel, FS template, Audit File template, set materiality
2. **Analysis** — Parse the TB, see statistics, validate balance
3. **Mapping Review** — Review and approve AI account classifications  
4. **Validation** — Run all QC checks, see balance sheet balance
5. **Generate & Export** — Generate populated Excel files, download reports

## Templates

The system is designed specifically for:
- `Audit Draft template.xlsx` — Financial Statements (Balance Sheet, P&L, Notes)
- `Audit File template.xlsx` — Audit Working Papers (LEAD, AP-01, individual WPs)

## Disclaimer

AI-generated classifications are subject to auditor review and approval.
This system does not replace professional judgment.
