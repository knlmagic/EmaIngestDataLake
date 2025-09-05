#!/usr/bin/env python3
"""
Debug script to see what's happening in reconcile
"""
import sqlite3

def debug_reconcile():
    conn = sqlite3.connect('ema_demo.sqlite')
    cur = conn.cursor()
    
    print("=== INVOICES ===")
    cur.execute("SELECT invoice_number, po_number, vendor, total_amount FROM invoices LIMIT 5")
    for row in cur.fetchall():
        print(f"Invoice: {row[0]}, PO: {row[1]}, Vendor: {row[2]}, Total: {row[3]}")
    
    print("\n=== DOCUMENTS (OCR) ===")
    cur.execute("SELECT path, doc_type, processing_method FROM documents WHERE processing_method = 'ocr_required' LIMIT 5")
    for row in cur.fetchall():
        print(f"OCR Doc: {row[0]}, Type: {row[1]}, Method: {row[2]}")
    
    print("\n=== RECONCILE ISSUE INVESTIGATION ===")
    # Try to run the first part of reconcile to see where it fails
    cur.execute("SELECT invoice_number, po_number, vendor FROM invoices LIMIT 1")
    first_invoice = cur.fetchone()
    
    if first_invoice:
        inv_no, po_no, vendor = first_invoice
        print(f"Testing invoice: {inv_no}")
        
        # This is the failing query
        cur.execute("SELECT currency, total_amount FROM invoices WHERE invoice_number=?", (inv_no,))
        result = cur.fetchone()
        print(f"Query result: {result}")
        
        if result is None:
            print("ERROR: Query returned None - this is the problem!")
        else:
            print("Query successful")
    
    conn.close()

if __name__ == "__main__":
    debug_reconcile()
