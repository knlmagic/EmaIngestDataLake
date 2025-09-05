
from __future__ import annotations
import sqlite3, json

def reconcile(conn: sqlite3.Connection, qty_tol_units=1, price_tol_pct=2.0, progress_callback=None):
    """
    Perform 3-way reconciliation of Purchase Orders, Invoices, and GRNs.
    
    Args:
        conn: Database connection
        qty_tol_units: Quantity tolerance in units
        price_tol_pct: Price tolerance in percentage
        progress_callback: Optional callback for progress updates
                          Called with (message, processed_count, total_count, current_invoice)
    """
    cur = conn.cursor()
    # clear prior results
    cur.execute("DELETE FROM reconciliation")
    conn.commit()
    # find duplicate invoices (same vendor, total, date)
    cur.execute("""
        WITH dup AS (
          SELECT invoice_number, vendor, total_amount, invoice_date,
                 COUNT(*) OVER (PARTITION BY vendor, total_amount, invoice_date) as c
          FROM invoices
        )
        SELECT invoice_number FROM dup WHERE c > 1
    """)
    dups = {row[0] for row in cur.fetchall()}
    
    # iterate invoices
    cur.execute("SELECT invoice_number, po_number, vendor FROM invoices")
    invoices = cur.fetchall()
    total_invoices = len(invoices)
    
    if progress_callback:
        progress_callback(f"🔄 Starting reconciliation of {total_invoices} invoices...", 0, total_invoices, None)
    
    for invoice_index, (inv_no, po_no, vendor) in enumerate(invoices, 1):
        if progress_callback:
            progress_callback(f"🔍 Reconciling invoice {inv_no}", invoice_index - 1, total_invoices, inv_no)
        status = "MATCH"; qty_var = 0.0; price_var_pct = 0.0; comments = ""
        if inv_no in dups:
            status = "DUP_INVOICE"; comments = "Duplicate invoice"
        
        # Fetch details
        cur.execute("SELECT currency, total_amount FROM invoices WHERE invoice_number=?", (inv_no,))
        inv_row = cur.fetchone()
        if inv_row is None:
            status = "MISSING_INVOICE_DATA"; comments = "Invoice data missing from invoices table"
            _upsert(conn, inv_no, po_no, vendor, status, qty_var, price_var_pct, comments)
            continue
        inv_currency, inv_total = inv_row
        
        cur.execute("SELECT total_amount, currency FROM purchase_orders WHERE po_number=? AND vendor=?", (po_no, vendor))
        po_row = cur.fetchone()
        if po_row is None:
            status = "NO_PO"; comments = "No matching PO"
            _upsert(conn, inv_no, po_no, vendor, status, qty_var, price_var_pct, comments)
            continue
        po_total, po_currency = po_row
        
        # Check GRN exists
        cur.execute("SELECT COUNT(1) FROM grns WHERE po_number=? AND vendor=?", (po_no, vendor))
        has_grn = cur.fetchone()[0] > 0
        if not has_grn and status == "MATCH":
            status = "MISSING_GRN"; comments = "No goods receipt for PO"
        
        # Compare lines (qty/price) on shared SKUs
        cur.execute("SELECT sku, qty, unit_price FROM invoice_lines WHERE invoice_number=?", (inv_no,))
        inv_lines = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
        
        # aggregate GRN qty per SKU
        cur.execute("SELECT sku, SUM(qty) FROM grn_lines gl JOIN grns g ON g.grn_number=gl.grn_number WHERE g.po_number=? GROUP BY sku", (po_no,))
        grn_qty = {r[0]: r[1] for r in cur.fetchall()}
        
        cur.execute("SELECT sku, qty, unit_price FROM po_lines WHERE po_number=?", (po_no,))
        po_lines = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
        
        # Compute variances
        for sku, (iqty, iprice) in inv_lines.items():
            pqty, pprice = po_lines.get(sku, (0, iprice))
            rqty = grn_qty.get(sku, 0)
            if abs(iqty - rqty) > qty_tol_units:
                status = "QTY_VAR"
                qty_var = (iqty - rqty)
            # price variance vs PO
            if pprice:
                pv = (iprice - pprice) / pprice * 100.0
                if abs(pv) > price_tol_pct and status == "MATCH":
                    status = "PRICE_VAR"
                    price_var_pct = pv
        
        # Overbill simple check: invoice total > PO total by > price_tol_pct
        if po_total and ((inv_total - po_total)/po_total*100.0) > price_tol_pct and status == "MATCH":
            status = "OVERBILL"; comments = "Invoice total exceeds PO total"
        
        _upsert(conn, inv_no, po_no, vendor, status, qty_var, price_var_pct, comments)
    
    if progress_callback:
        progress_callback(f"✅ Reconciliation complete: {total_invoices} invoices processed", 
                         total_invoices, total_invoices, None)

def _upsert(conn, invoice_number, po_number, vendor, status, qty_var, price_var_pct, comments):
    conn.execute("""INSERT OR REPLACE INTO reconciliation
                    (invoice_number, po_number, vendor, status, qty_var, price_var_pct, comments)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                 (invoice_number, po_number, vendor, status, qty_var, price_var_pct, comments))
    conn.commit()
