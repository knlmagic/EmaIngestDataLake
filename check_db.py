#!/usr/bin/env python3
from pipeline.db import connect
from pathlib import Path

conn = connect(Path('ema_demo.sqlite'))
cur = conn.cursor()

print("=== OCR INVOICES IN DATABASE ===")
cur.execute("SELECT invoice_number, vendor, total_amount FROM invoices WHERE invoice_number LIKE '%SCAN%'")
ocr_invoices = cur.fetchall()
print(f"Found {len(ocr_invoices)} OCR invoices:")
for inv_num, vendor, total in ocr_invoices:
    print(f"  {inv_num} | {vendor} | ${total}")

print("\n=== ALL RECENT INVOICES ===")
cur.execute("SELECT invoice_number, vendor, total_amount FROM invoices ORDER BY rowid DESC LIMIT 10")
recent = cur.fetchall()
for inv_num, vendor, total in recent:
    print(f"  {inv_num} | {vendor} | ${total}")

print("\n=== OCR DOCUMENTS ===")
cur.execute("SELECT path, doc_type, vendor, processing_method FROM documents WHERE processing_method = 'ocr_required'")
ocr_docs = cur.fetchall()
print(f"Found {len(ocr_docs)} OCR documents:")
for path, doc_type, vendor, method in ocr_docs:
    print(f"  {Path(path).name} | {doc_type} | {vendor} | {method}")

conn.close()
