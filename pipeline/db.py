
from __future__ import annotations
import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE,
  hash TEXT,
  doc_type TEXT, -- 'PO' | 'INVOICE' | 'GRN'
  country TEXT,
  vendor TEXT,
  parsed_json TEXT,
  ingested_at TEXT,
  -- OCR Enhancement fields
  file_type TEXT, -- 'txt', 'pdf', 'jpg', etc.
  processing_method TEXT, -- 'text_file', 'pdf_text', 'pdf_ocr', 'image_ocr'
  ocr_confidence REAL, -- 0-100 confidence score for OCR processing
  requires_ocr BOOLEAN DEFAULT 0 -- 1 if file required OCR processing
);
CREATE TABLE IF NOT EXISTS purchase_orders (
  po_number TEXT,
  vendor TEXT,
  country TEXT,
  currency TEXT,
  order_date TEXT,
  total_amount REAL,
  PRIMARY KEY (po_number, vendor)
);
CREATE TABLE IF NOT EXISTS po_lines (
  po_number TEXT,
  sku TEXT,
  description TEXT,
  qty REAL,
  unit_price REAL,
  PRIMARY KEY (po_number, sku)
);
CREATE TABLE IF NOT EXISTS invoices (
  invoice_number TEXT,
  po_number TEXT,
  vendor TEXT,
  country TEXT,
  currency TEXT,
  invoice_date TEXT,
  total_amount REAL,
  PRIMARY KEY (invoice_number)
);
CREATE TABLE IF NOT EXISTS invoice_lines (
  invoice_number TEXT,
  sku TEXT,
  description TEXT,
  qty REAL,
  unit_price REAL,
  PRIMARY KEY (invoice_number, sku)
);
CREATE TABLE IF NOT EXISTS grns (
  grn_number TEXT,
  po_number TEXT,
  vendor TEXT,
  country TEXT,
  grn_date TEXT,
  PRIMARY KEY (grn_number)
);
CREATE TABLE IF NOT EXISTS grn_lines (
  grn_number TEXT,
  sku TEXT,
  qty REAL,
  PRIMARY KEY (grn_number, sku)
);
CREATE TABLE IF NOT EXISTS reconciliation (
  invoice_number TEXT PRIMARY KEY,
  po_number TEXT,
  vendor TEXT,
  status TEXT,           -- MATCH | MISSING_GRN | PRICE_VAR | QTY_VAR | OVERBILL | DUP_INVOICE | NO_PO
  qty_var REAL,
  price_var_pct REAL,
  comments TEXT
);
"""

def connect(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn
