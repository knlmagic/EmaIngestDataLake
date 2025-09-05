
# EMA Take‑Home Demo — 3‑Way Match (PO/Invoice/GRN)

This repo is a complete **live demo** you can run locally to showcase an **agentic ingestion, classification, and 3‑way reconciliation** pipeline on a simulated data lake.

**What it shows**
- Ingest a folder that acts like a "chaotic data lake" (mixed docs across vendors/countries)
- Support for **TXT, PDF, and image formats** (JPG, PNG) with **OCR capabilities**
- Classify docs (PO / Invoice / Goods Receipt/GRN) from both text and scanned documents
- Extract structured fields using **text extraction + OCR fallback**
- Reconcile POs ↔ Invoices ↔ GRNs (3‑way match) with exception codes
- Generate **actionable insights** dashboards for procurement & finance
- **OCR processing metrics** and confidence scoring for document quality
- (Optional) Use OpenAI for robust doc parsing via **Structured Outputs JSON Schema** (falls back to regex so the demo runs offline too)
- SQLite persistence and **replayable audit trail**

## Quickstart

```bash
# 1) Create & activate a virtualenv (recommended)
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)

# 2) Install deps
pip install -r requirements.txt

# 3) Run the Streamlit app
streamlit run app.py
```

> The app ships with sample data. You can also drag‑drop your own `.txt`, `.pdf`, or **image files** (JPG, PNG) into `data_lake/raw/` and click **Ingest & Reconcile**.

### 🔍 OCR Enhancement Setup
For **real-world scanned document processing**:
```bash
# Quick setup (installs OCR dependencies + generates sample scanned docs)
python setup_ocr_demo.py

# Manual setup
pip install pytesseract opencv-python pdf2image Pillow
# Install Tesseract: winget install UB-Mannheim.TesseractOCR (Windows)
```

### Optional: Enable OpenAI parsing
Create `.env` with your key:
```
OPENAI_API_KEY=sk-...yourkey...
USE_OPENAI=true
OPENAI_MODEL=gpt-4o-mini
```
If no key is set, the pipeline **automatically falls back to a fast regex parser** built for the provided sample docs.

## Demo flow (script)

1. **Context slide (1 min):** This demo simulates a failed vendor’s data lake — unstructured, mixed docs, multiple countries.
2. In the app, click **Generate sample data** ⇒ it drops 30+ mixed docs into `data_lake/raw/` across 3 countries & 8 vendors.
3. Click **Ingest & Reconcile** ⇒ watch classification, extraction, and 3‑way matching run. SQLite DB is created.
4. **Overview** tab: show KPIs (Match %, $ at risk, Top vendors by exceptions).
5. **Exceptions** tab: drill into *Overbill*, *Missing GRN*, *Price variance*, *Duplicate invoice*.
6. **Vendor Insights** tab: show exception rates by vendor/country; click a row to see audit trail (raw doc vs extracted JSON).
7. **Scalability** (talk track): Explain how this pipeline fans out via queues (S3 + SQS + Lambda/ECS + Postgres/Databricks) and uses **OpenAI Structured Outputs** to make parsing robust, plus streaming+idempotency to be safe at high volume.
8. **Export** any table to CSV from Streamlit (built‑in).

## Architecture (demo)

```
[data_lake/raw/*.txt|*.pdf|*.jpg|*.png] --> ingest() --> classify() --> extract() --> persist(SQLite) --> reconcile() --> insights()
                                                              ^                           ^
                                                    (OpenAI Structured Outputs)    (OCR metadata)
```

- **Multi-format support**: processes TXT, PDF, and image documents with OCR capabilities
- **Idempotent runs**: files are hashed; re‑ingesting won't duplicate rows.
- **Three‑way match** with thresholds (configurable in UI).
- **Audit**: every parsed doc stored as JSON with source path + timestamp.

## Why it wins vs the previous vendor

- **Deterministic core** (classification rules + reconciliation SQL) with **LLM augmentation** (Structured Outputs) only where it helps.
- **Replayable** pipeline with audit trail + raw/extracted side‑by‑side views.
- **Scales** to cloud primitives: blob storage, event queues, stateless workers, external warehouse (Snowflake/Databricks).

---

© 2025 Kunal Kochhar demo, built with Streamlit + SQLite. Modify freely.
