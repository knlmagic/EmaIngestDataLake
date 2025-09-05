
from __future__ import annotations
import json, sqlite3
from pathlib import Path
from datetime import datetime
from .classify_extract import classify, extract, file_hash
from .pdf_processor import read_document_content, is_supported_file_type, get_file_info, get_document_processing_info

def ingest_folder(conn: sqlite3.Connection, folder: Path):
    # returns (ingested_count, skipped_count, error_count)
    ingested = 0; skipped = 0; errors = 0
    for path in sorted(folder.glob("*")):
        if path.is_dir():
            continue
        
        # Check if file type is supported
        if not is_supported_file_type(path):
            print(f"Skipping unsupported file type: {path}")
            skipped += 1
            continue
        
        try:
            # Read document content (handles TXT, PDF, and images with OCR)
            text = read_document_content(path)
            h = file_hash(str(path))
            
            # de-dup by hash+path
            row = conn.execute("SELECT id FROM documents WHERE path=? OR hash=?", (str(path), h)).fetchone()
            if row:
                skipped += 1
                continue
            
            # Get enhanced file info including OCR metadata
            file_info = get_file_info(path)
            processing_info = get_document_processing_info(path)
            
            doc_type = classify(text)
            parsed = extract(text, doc_type)
            vendor = parsed.get("vendor", "Unknown Vendor")
            country = parsed.get("country", "US")
            
            # Add enhanced metadata to parsed data
            parsed["source_file_type"] = file_info["file_type"]
            parsed["source_file_size"] = file_info["size_bytes"]
            parsed["processing_method"] = processing_info["processing_method"]
            parsed["requires_ocr"] = processing_info["requires_ocr"]
            
            # Determine OCR confidence (simplified for demo)
            ocr_confidence = None
            processing_method = processing_info["processing_method"]
            
            if processing_method == 'text_file':
                ocr_confidence = 100.0  # Text files are 100% confident
            elif processing_method == 'pdf_text_only':
                ocr_confidence = 95.0   # PDF text extraction is very reliable
            elif 'ocr' in processing_method:
                ocr_confidence = 75.0   # Default OCR confidence for demo
            else:
                ocr_confidence = 90.0   # Default for other methods
            
            # Enhanced database insert with OCR metadata
            conn.execute("""INSERT INTO documents(
                path, hash, doc_type, country, vendor, parsed_json, ingested_at,
                file_type, processing_method, ocr_confidence, requires_ocr
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                         (str(path), h, doc_type, country, vendor, json.dumps(parsed), 
                          datetime.utcnow().isoformat(), file_info["file_type"], 
                          processing_method, ocr_confidence, processing_info["requires_ocr"]))
            
            # fan out into typed tables
            _persist_structured(conn, parsed)
            ingested += 1
            
            # Enhanced logging with OCR info
            ocr_info = f" | OCR: {ocr_confidence:.1f}%" if processing_info["requires_ocr"] else ""
            print(f"✅ Processed {path.name} | Method: {processing_method}{ocr_info}")
            
        except Exception as e:
            print(f"Error processing {path}: {e}")
            errors += 1
            continue
    
    conn.commit()
    return ingested, skipped, errors

def _persist_structured(conn: sqlite3.Connection, doc: dict):
    t = doc.get("type")
    
    if t == "PO":
        conn.execute("""INSERT OR IGNORE INTO purchase_orders(po_number, vendor, country, currency, order_date, total_amount)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                     (doc.get("po_number"), doc.get("vendor"), doc.get("country"),
                      doc.get("currency"), doc.get("order_date"), doc.get("total_amount")))
        for it in doc.get("items", []):
            conn.execute("""INSERT OR REPLACE INTO po_lines(po_number, sku, description, qty, unit_price)
                            VALUES (?, ?, ?, ?, ?)""",
                         (doc.get("po_number"), it.get("sku"), it.get("description"), it.get("qty"), it.get("unit_price")))
    elif t == "INVOICE":
        conn.execute("""INSERT OR REPLACE INTO invoices(invoice_number, po_number, vendor, country, currency, invoice_date, total_amount)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                     (doc.get("invoice_number"), doc.get("po_number"), doc.get("vendor"),
                      doc.get("country"), doc.get("currency"), doc.get("invoice_date"), doc.get("total_amount")))
        for it in doc.get("items", []):
            conn.execute("""INSERT OR REPLACE INTO invoice_lines(invoice_number, sku, description, qty, unit_price)
                            VALUES (?, ?, ?, ?, ?)""",
                         (doc.get("invoice_number"), it.get("sku"), it.get("description"), it.get("qty"), it.get("unit_price")))
    elif t == "GRN":
        conn.execute("""INSERT OR IGNORE INTO grns(grn_number, po_number, vendor, country, grn_date)
                        VALUES (?, ?, ?, ?, ?)""",
                     (doc.get("grn_number"), doc.get("po_number"), doc.get("vendor"),
                      doc.get("country"), doc.get("grn_date")))
        for it in doc.get("items", []):
            conn.execute("""INSERT OR REPLACE INTO grn_lines(grn_number, sku, qty)
                            VALUES (?, ?, ?)""",
                         (doc.get("grn_number"), it.get("sku"), it.get("qty")))
