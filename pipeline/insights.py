
from __future__ import annotations
import sqlite3, pandas as pd, json

def kpis(conn: sqlite3.Connection) -> dict:
    # Get document type breakdown
    df_docs = pd.read_sql_query("SELECT doc_type, COUNT(*) as c FROM documents GROUP BY doc_type", conn)
    doc_type_counts = {row["doc_type"]: int(row["c"]) for _, row in df_docs.iterrows()}
    total_documents = sum(doc_type_counts.values())
    
    # Get invoice-specific metrics for reconciliation
    df_inv = pd.read_sql_query("SELECT COUNT(*) as c FROM invoices", conn)
    df_rec = pd.read_sql_query("SELECT status, COUNT(*) as c FROM reconciliation GROUP BY status", conn)
    total_invoices = int(df_inv["c"].iloc[0]) if not df_inv.empty else 0
    by_status = {row["status"]: int(row["c"]) for _, row in df_rec.iterrows()}
    matched = by_status.get("MATCH", 0)
    match_rate = (matched / total_invoices * 100.0) if total_invoices else 0.0
    
    return {
        "total_documents": total_documents,
        "doc_type_counts": doc_type_counts,
        "total_invoices": total_invoices,
        "matched": matched,
        "match_rate": match_rate,
        "by_status": by_status
    }

def exceptions_table(conn: sqlite3.Connection) -> pd.DataFrame:
    q = """
    SELECT r.invoice_number, r.po_number, r.vendor, r.status, r.qty_var, r.price_var_pct, r.comments,
           i.total_amount as invoice_total, i.invoice_date, i.currency, i.country
    FROM reconciliation r
    JOIN invoices i ON i.invoice_number = r.invoice_number
    WHERE r.status <> 'MATCH'
    ORDER BY i.invoice_date DESC
    """
    return pd.read_sql_query(q, conn)

def vendor_summary(conn: sqlite3.Connection) -> pd.DataFrame:
    q = """
    WITH base AS (
      SELECT i.vendor, i.country, COUNT(*) as invoices
      FROM invoices i GROUP BY i.vendor, i.country
    ),
    ex AS (
      SELECT i.vendor, COALESCE(SUM(CASE WHEN r.status <> 'MATCH' THEN 1 ELSE 0 END),0) as exceptions
      FROM invoices i LEFT JOIN reconciliation r ON r.invoice_number=i.invoice_number
      GROUP BY i.vendor
    )
    SELECT b.vendor, b.country, b.invoices, e.exceptions,
           CAST(e.exceptions as FLOAT)/NULLIF(b.invoices,0) as exception_rate
    FROM base b JOIN ex e ON e.vendor=b.vendor
    ORDER BY exception_rate DESC NULLS LAST, b.invoices DESC
    """
    return pd.read_sql_query(q, conn)

def audit_for_invoice(conn: sqlite3.Connection, invoice_number: str) -> dict:
    row = conn.execute("SELECT parsed_json, path FROM documents WHERE doc_type='INVOICE' AND json_extract(parsed_json, '$.invoice_number') = ?", (invoice_number,)).fetchone()
    if not row:
        return {}
    parsed_json, path = row
    return {"source_path": path, "parsed_json": json.loads(parsed_json)}
