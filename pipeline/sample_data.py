
from __future__ import annotations
from pathlib import Path
import random, datetime
import time

VENDORS = [
    ("Acme Components Ltd", "US", "USD"),
    ("Globex Manufacturing", "US", "USD"),
    ("Initech Pvt Ltd", "IN", "INR"),
    ("Umbrella Supplies", "GB", "GBP"),
    ("Stark Industrial", "US", "USD"),
    ("Wayne Parts Co", "US", "USD"),
    ("Nakatomi Trading", "JP", "USD"),
    ("Hooli Metals", "US", "USD"),
    ("MegaCorp Industries", "CA", "CAD"),
    ("Phoenix Materials", "AU", "AUD"),
    ("Dragon Supplies", "CN", "USD"),
    ("Alpine Components", "DE", "EUR"),
]

SKUS = [
    ("WID-100", "Widget Basic"),
    ("WID-200", "Widget Pro"),
    ("WID-300", "Widget Deluxe"),
    ("BLT-050", "Bolt 50mm"),
    ("BLT-075", "Bolt 75mm"),
    ("SCR-020", "Screw 20mm"),
    ("SCR-030", "Screw 30mm"),
    ("PNL-300", "Panel 300x300"),
    ("PNL-600", "Panel 600x600"),
    ("BRG-001", "Bearing Assembly"),
    ("SPG-100", "Spring Coil"),
    ("GSK-200", "Gasket Set"),
    ("FLT-050", "Filter Element"),
    ("CBL-100", "Cable Assembly"),
    ("CNR-250", "Connector Set"),
]

DOCUMENT_SCENARIOS = [
    "complete_match",      # Perfect 3-way match
    "missing_grn",         # PO + Invoice, no GRN
    "missing_invoice",     # PO + GRN, no Invoice
    "price_variance",      # Price differences
    "quantity_variance",   # Quantity differences
    "duplicate_invoice",   # Multiple invoices for same PO
    "late_delivery",       # GRN comes much later
    "partial_delivery",    # GRN has fewer items
]

def _rand_date():
    base = datetime.date(2025, 7, 1)
    delta = datetime.timedelta(days=random.randint(0, 50))
    return (base + delta).isoformat()

def generate(folder: Path, n_sets: int = 10):
    random.seed(7)
    folder.mkdir(parents=True, exist_ok=True)
    seq = 1000
    for _ in range(n_sets):
        vendor, country, currency = random.choice(VENDORS)
        # one PO with 2-3 lines
        po_no = f"PO-{seq}"
        order_date = _rand_date()
        lines = random.sample(SKUS, k=random.randint(2,3))
        contents = []
        total = 0.0
        for sku, desc in lines:
            qty = random.randint(5, 20)
            unit = round(random.uniform(5, 25), 2)
            total += qty * unit
            contents.append(f" - SKU: {sku} | Description: {desc} | Qty: {qty} | Unit Price: {unit}")
        po_text = f"""
        Document Type: Purchase Order
        PO Number: {po_no}
        Vendor: {vendor}
        Country: {country}
        Currency: {currency}
        Date: {order_date}
        {chr(10).join(contents)}
        Total: {round(total,2)}
        """.strip()
        (folder / f"{po_no}_{vendor.replace(' ','_')}.txt").write_text(po_text)

        # 1 GRN with received qty (sometimes under/over by 0-2 units per line to create exceptions)
        grn_no = f"GRN-{seq}"
        grn_lines = []
        for sku, desc in lines:
            adj = random.choice([0,0,0,1,-1,2])  # mostly matches
            qty = max(0, random.randint(5, 20) + adj)
            grn_lines.append(f" - SKU: {sku} | Qty: {qty}")
        grn_text = f"""
        Document Type: Goods Receipt (GRN)
        GRN Number: {grn_no}
        PO Number: {po_no}
        Vendor: {vendor}
        Country: {country}
        Date: {_rand_date()}
        {chr(10).join(grn_lines)}
        """.strip()
        (folder / f"{grn_no}_{vendor.replace(' ','_')}.txt").write_text(grn_text)

        # 1-2 invoices; sometimes price variance or duplicate
        num_invoices = random.choice([1,1,2])
        inv_total = 0.0
        inv_lines_txt = []
        for sku, desc in lines:
            qty = random.randint(5, 20)
            unit = round(random.uniform(5, 25), 2)
            # introduce occasional price variance
            if random.random() < 0.2:
                unit = round(unit * random.uniform(1.05, 1.12), 2)
            inv_total += qty * unit
            inv_lines_txt.append(f" - SKU: {sku} | Description: {desc} | Qty: {qty} | Unit Price: {unit}")
        for j in range(num_invoices):
            inv_no = f"INV-{seq}-{j+1}"
            inv_text = f"""
            Document Type: Invoice
            Invoice Number: {inv_no}
            PO Number: {po_no}
            Vendor: {vendor}
            Country: {country}
            Currency: {currency}
            Date: {_rand_date()}
            {chr(10).join(inv_lines_txt)}
            Total: {round(inv_total,2)}
            """.strip()
            (folder / f"{inv_no}_{vendor.replace(' ','_')}.txt").write_text(inv_text)

        seq += 1

def _get_next_sequence_number(folder: Path) -> int:
    """Get the next available sequence number by checking existing files"""
    existing_files = list(folder.glob("*-*.txt")) + list(folder.glob("*-*.jpg")) + list(folder.glob("*-*.pdf"))
    max_seq = 1000
    
    for file in existing_files:
        try:
            # Extract number from filename patterns like PO-1234, INV-1234-1, GRN-1234, SCANNED_INV_1234
            parts = file.stem.replace("SCANNED_", "").split("_")[0].split("-")
            if len(parts) >= 2 and parts[1].isdigit():
                seq_num = int(parts[1])
                if seq_num > max_seq:
                    max_seq = seq_num
        except (ValueError, IndexError):
            continue
    
    return max_seq + 1

def _create_random_date_range():
    """Create a date range for related documents with some variation"""
    base = datetime.date(2025, 7, 1)
    po_date = base + datetime.timedelta(days=random.randint(0, 30))
    grn_date = po_date + datetime.timedelta(days=random.randint(1, 14))  # GRN after PO
    inv_date = po_date + datetime.timedelta(days=random.randint(5, 20))  # Invoice can be before/after GRN
    
    return {
        'po_date': po_date.isoformat(),
        'grn_date': grn_date.isoformat(),
        'inv_date': inv_date.isoformat()
    }

def _generate_document_set_scenario(folder: Path, seq: int, scenario: str, vendor_info: tuple, lines: list):
    """Generate a document set based on a specific scenario"""
    vendor, country, currency = vendor_info
    dates = _create_random_date_range()
    po_no = f"PO-{seq}"
    grn_no = f"GRN-{seq}"
    
    generated_files = []
    
    # Always generate PO
    po_lines = []
    po_total = 0.0
    for sku, desc in lines:
        qty = random.randint(5, 20)
        unit = round(random.uniform(5, 25), 2)
        po_total += qty * unit
        po_lines.append({
            'sku': sku, 'desc': desc, 'qty': qty, 'unit': unit,
            'text': f" - SKU: {sku} | Description: {desc} | Qty: {qty} | Unit Price: {unit}"
        })
    
    po_text = f"""Document Type: Purchase Order
PO Number: {po_no}
Vendor: {vendor}
Country: {country}
Currency: {currency}
Date: {dates['po_date']}
{chr(10).join([line['text'] for line in po_lines])}
Total: {round(po_total,2)}""".strip()
    
    po_file = folder / f"{po_no}_{vendor.replace(' ','_')}.txt"
    po_file.write_text(po_text)
    generated_files.append(po_file)
    
    # Generate GRN based on scenario
    if scenario not in ["missing_grn"]:
        grn_lines = []
        for line_info in po_lines:
            if scenario == "quantity_variance":
                # Random quantity variance
                adj = random.choice([-2, -1, 0, 0, 1, 2])
                qty = max(0, line_info['qty'] + adj)
            elif scenario == "partial_delivery":
                # Reduce quantities for partial delivery
                qty = max(0, line_info['qty'] - random.randint(1, 3))
            else:
                # Use PO quantity with small random variance
                adj = random.choice([0, 0, 0, 1, -1])
                qty = max(0, line_info['qty'] + adj)
            
            grn_lines.append(f" - SKU: {line_info['sku']} | Qty: {qty}")
        
        grn_text = f"""Document Type: Goods Receipt Note
GRN Number: {grn_no}
PO Number: {po_no}
Vendor: {vendor}
Country: {country}
Date: {dates['grn_date']}
{chr(10).join(grn_lines)}""".strip()
        
        grn_file = folder / f"{grn_no}_{vendor.replace(' ','_')}.txt"
        grn_file.write_text(grn_text)
        generated_files.append(grn_file)
    
    # Generate Invoice(s) based on scenario
    if scenario not in ["missing_invoice"]:
        num_invoices = 2 if scenario == "duplicate_invoice" else 1
        
        for j in range(num_invoices):
            inv_no = f"INV-{seq}-{j+1}"
            inv_lines = []
            inv_total = 0.0
            
            for line_info in po_lines:
                qty = line_info['qty']
                unit = line_info['unit']
                
                if scenario == "price_variance":
                    # Add price variance
                    unit = round(unit * random.uniform(0.95, 1.08), 2)
                elif scenario == "quantity_variance" and j == 0:
                    # First invoice has quantity variance
                    qty = max(1, qty + random.choice([-1, 1, 2]))
                
                inv_total += qty * unit
                inv_lines.append(f" - SKU: {line_info['sku']} | Description: {line_info['desc']} | Qty: {qty} | Unit Price: {unit}")
            
            inv_text = f"""Document Type: Invoice
Invoice Number: {inv_no}
PO Number: {po_no}
Vendor: {vendor}
Country: {country}
Currency: {currency}
Date: {dates['inv_date']}
{chr(10).join(inv_lines)}
Total: {round(inv_total,2)}""".strip()
            
            inv_file = folder / f"{inv_no}_{vendor.replace(' ','_')}.txt"
            inv_file.write_text(inv_text)
            generated_files.append(inv_file)
    
    return generated_files

def generate_additional_samples(folder: Path, n_sets: int = 5, mixed_formats: bool = True):
    """
    Generate additional sample data with randomness and various scenarios
    
    Args:
        folder: Target folder for generated files
        n_sets: Number of document sets to generate
        mixed_formats: Whether to generate mixed formats (TXT, PDF, OCR images)
    """
    folder.mkdir(parents=True, exist_ok=True)
    
    # Use current time as seed for randomness each call
    random.seed(int(time.time()))
    
    start_seq = _get_next_sequence_number(folder)
    generated_files = []
    
    for i in range(n_sets):
        seq = start_seq + i
        vendor_info = random.choice(VENDORS)
        scenario = random.choice(DOCUMENT_SCENARIOS)
        
        # Generate 2-4 line items per document set
        lines = random.sample(SKUS, k=random.randint(2, 4))
        
        # Generate document set based on scenario
        files = _generate_document_set_scenario(folder, seq, scenario, vendor_info, lines)
        generated_files.extend(files)
        
        # Optionally create some documents in different formats
        if mixed_formats and random.random() < 0.4:  # 40% chance of format variation
            format_choice = random.choice(["pdf", "ocr"])
            
            if format_choice == "pdf" and files:
                # Convert one of the generated TXT files to PDF
                try:
                    from .pdf_sample_generator import create_sample_pdf
                    txt_file = random.choice(files)
                    pdf_folder = folder.parent / "raw_pdf"
                    pdf_folder.mkdir(exist_ok=True)
                    
                    pdf_path = pdf_folder / (txt_file.stem + ".pdf")
                    content = txt_file.read_text()
                    title = "Purchase Order" if "PO-" in txt_file.name else ("Invoice" if "INV-" in txt_file.name else "Goods Receipt Note")
                    
                    create_sample_pdf(pdf_path, content, title)
                    generated_files.append(pdf_path)
                except ImportError:
                    pass  # PDF generation not available
            
            elif format_choice == "ocr" and any("INV-" in f.name for f in files):
                # Create OCR version of an invoice
                try:
                    from .ocr_sample_generator import create_sample_scanned_invoice
                    
                    # Find invoice file and create OCR version
                    inv_files = [f for f in files if "INV-" in f.name]
                    if inv_files:
                        inv_file = inv_files[0]
                        content = inv_file.read_text()
                        
                        # Parse invoice content for OCR generation
                        lines_data = content.split('\n')
                        invoice_data = {
                            'invoice_number': f"SCAN-{inv_file.stem.split('_')[0]}",
                            'po_number': f"PO-{seq}",
                            'date': _rand_date(),
                            'vendor': vendor_info[0],
                            'country': vendor_info[1],
                            'currency': vendor_info[2],
                            'items': []
                        }
                        
                        # Extract items from content
                        for line in lines_data:
                            if " - SKU:" in line:
                                parts = line.split("|")
                                if len(parts) >= 4:
                                    sku = parts[0].split("SKU:")[1].strip()
                                    desc = parts[1].split("Description:")[1].strip()
                                    qty = int(parts[2].split("Qty:")[1].strip())
                                    unit = float(parts[3].split("Unit Price:")[1].strip())
                                    
                                    invoice_data['items'].append({
                                        'sku': sku, 'description': desc,
                                        'qty': qty, 'unit_price': unit
                                    })
                        
                        vendor_clean = vendor_info[0].replace(' ', '_').replace('.', '')
                        ocr_filename = f"SCANNED_{inv_file.stem}_{vendor_clean}.jpg"
                        ocr_path = folder / ocr_filename
                        
                        create_sample_scanned_invoice(ocr_path, invoice_data)
                        generated_files.append(ocr_path)
                        
                except ImportError:
                    pass  # OCR generation not available
    
    return generated_files, start_seq

def generate_enhanced(folder: Path, n_sets: int = 8):
    """
    Enhanced sample generation with mixed scenarios and formats.
    This is the main function to call for enhanced sample generation.
    """
    folder.mkdir(parents=True, exist_ok=True)
    
    print(f"🎲 Generating {n_sets} enhanced document sets with random scenarios...")
    
    # Generate main document sets
    files, start_seq = generate_additional_samples(folder, n_sets, mixed_formats=True)
    
    print(f"✅ Generated {len(files)} files starting from sequence {start_seq}")
    print("📊 Scenarios included: complete matches, missing documents, variances, duplicates")
    print("📄 Formats: TXT, PDF, OCR images (mixed)")
    
    return files
