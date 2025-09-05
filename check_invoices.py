#!/usr/bin/env python3
"""
Check if OCR invoices are in the database
"""
import sqlite3

conn = sqlite3.connect('ema_demo.sqlite')
cur = conn.cursor()

print("=== CHECKING INVOICES TABLE ===")

# Check total invoices
cur.execute('SELECT COUNT(*) FROM invoices')
total = cur.fetchone()[0]
print(f"Total invoices: {total}")

# Check for OCR invoices (SCAN-INV format)
cur.execute('SELECT invoice_number, vendor, total_amount FROM invoices WHERE invoice_number LIKE "SCAN-INV-%"')
ocr_invoices = cur.fetchall()
print(f"OCR invoices found: {len(ocr_invoices)}")

for inv in ocr_invoices:
    print(f"  {inv[0]} - {inv[1]} - ${inv[2]}")

# Check first few regular invoices
print("\nFirst few invoices:")
cur.execute('SELECT invoice_number, vendor, total_amount FROM invoices LIMIT 5')
for inv in cur.fetchall():
    print(f"  {inv[0]} - {inv[1]} - ${inv[2]}")

conn.close()
