
from __future__ import annotations
import os, re, json, hashlib
from dataclasses import dataclass
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def classify(text: str) -> str:
    # simple heuristic classifier
    t = text.lower()
    if "goods receipt" in t or "grn" in t or "received qty" in t:
        return "GRN"
    if "invoice number" in t or "invoice" in t:
        return "INVOICE"
    if "purchase order" in t or "po number" in t:
        return "PO"
    # fallback
    return "UNKNOWN"

def _regex_extract(text: str, doc_type: str) -> Dict[str, Any]:
    # Designed for the sample docs format created by sample_data.py
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    kv = {}
    for ln in lines:
        if ":" in ln and "|" not in ln:
            k, v = ln.split(":", 1)
            # Normalize key to handle both "Invoice Number" and "invoice number" formats
            key_normalized = k.strip().lower()
            kv[key_normalized] = v.strip()
    country = kv.get("country", "US")
    vendor = kv.get("vendor", "Unknown Vendor")
    currency = kv.get("currency", "USD")
    if doc_type == "PO":
        po_number = kv.get("po number")
        order_date = kv.get("date")
        total_amount = float(kv.get("total", "0").replace(",", ""))
        items = []
        for ln in lines:
            if "sku:" in ln and "unit price" in ln:
                # " - SKU: ABC | Description: ... | Qty: 10 | Unit Price: 12.5"
                m = re.findall(r"SKU:\s*([^\|]+)\s*\|\s*Description:\s*([^\|]+)\s*\|\s*Qty:\s*([\d\.]+)\s*\|\s*Unit Price:\s*([\d\.]+)", ln, re.I)
                for sku, desc, qty, up in m:
                    items.append({
                        "sku": sku.strip(),
                        "description": desc.strip(),
                        "qty": float(qty),
                        "unit_price": float(up),
                    })
        return {
            "type": "PO",
            "po_number": po_number,
            "vendor": vendor, "country": country, "currency": currency,
            "order_date": order_date, "total_amount": total_amount,
            "items": items
        }
    if doc_type == "INVOICE":
        inv = kv.get("invoice number")
        po = kv.get("po number") 
        inv_date = kv.get("date")
        total_amount = float(kv.get("total", "0").replace(",", ""))
        items = []
        for ln in lines:
            if "sku:" in ln and "unit price" in ln:
                m = re.findall(r"SKU:\s*([^\|]+)\s*\|\s*Description:\s*([^\|]+)\s*\|\s*Qty:\s*([\d\.]+)\s*\|\s*Unit Price:\s*([\d\.]+)", ln, re.I)
                for sku, desc, qty, up in m:
                    items.append({
                        "sku": sku.strip(),
                        "description": desc.strip(),
                        "qty": float(qty),
                        "unit_price": float(up),
                    })
        return {
            "type": "INVOICE",
            "invoice_number": inv,
            "po_number": po,
            "vendor": vendor, "country": country, "currency": currency,
            "invoice_date": inv_date, "total_amount": total_amount,
            "items": items
        }
    if doc_type == "GRN":
        grn = kv.get("grn number")
        po = kv.get("po number")
        grn_date = kv.get("date")
        items = []
        for ln in lines:
            if "sku:" in ln and "qty" in ln:
                m = re.findall(r"SKU:\s*([^\|]+)\s*\|\s*Qty:\s*([\d\.]+)", ln, re.I)
                for sku, qty in m:
                    items.append({"sku": sku.strip(), "qty": float(qty)})
        return {
            "type": "GRN",
            "grn_number": grn,
            "po_number": po,
            "vendor": vendor, "country": country,
            "grn_date": grn_date,
            "items": items
        }
    return {"type": "UNKNOWN"}

def _openai_extract(text: str, doc_type: str) -> Dict[str, Any]:
    # Uses OpenAI Chat Completions API with JSON mode
    from openai import OpenAI
    client = OpenAI()
    
    prompt = f"""Extract structured data from this {doc_type} document and return valid JSON.

Required fields based on document type:
- type: "{doc_type}"
- country: string
- vendor: string  
- currency: string

For PO: po_number, order_date, total_amount, items (array with sku, description, qty, unit_price)
For INVOICE: invoice_number, po_number, invoice_date, total_amount, items (array with sku, description, qty, unit_price)  
For GRN: grn_number, po_number, grn_date, items (array with sku, qty)

Document text:
{text}

Return only valid JSON matching the expected structure."""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a document data extraction expert. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        # If JSON parsing fails, return empty structure
        return {"type": doc_type, "vendor": "Unknown Vendor", "country": "US", "currency": "USD", "items": []}

def extract(text: str, doc_type: str) -> Dict[str, Any]:
    if USE_OPENAI:
        try:
            return _openai_extract(text, doc_type)
        except Exception as e:
            # fallback to regex if anything fails
            return _regex_extract(text, doc_type)
    else:
        return _regex_extract(text, doc_type)
