# PDF Creation Guide for EMA Data Lake Ingest

## Overview

To create PDFs that will be correctly ingested by the EMA system, you need to follow the exact text format that the regex parser expects. The system looks for specific patterns and field names to classify and extract data.

## Required Format Structure

The system expects documents to follow this exact pattern:

### 1. **Purchase Order (PO) PDF**

**Required Content:**
```
Document Type: Purchase Order
PO Number: PO-XXXX
Vendor: [Vendor Name]
Country: [Country Code]
Currency: [Currency Code]
Date: YYYY-MM-DD
 - SKU: [SKU_CODE] | Description: [Item Description] | Qty: [Number] | Unit Price: [Decimal]
 - SKU: [SKU_CODE] | Description: [Item Description] | Qty: [Number] | Unit Price: [Decimal]
Total: [Decimal Amount]
```

**Example:**
```
Document Type: Purchase Order
PO Number: PO-2001
Vendor: Acme Components Ltd
Country: US
Currency: USD
Date: 2025-01-15
 - SKU: WID-100 | Description: Widget Basic | Qty: 10 | Unit Price: 15.50
 - SKU: BLT-050 | Description: Bolt 50mm | Qty: 25 | Unit Price: 2.75
Total: 227.50
```

### 2. **Invoice PDF**

**Required Content:**
```
Document Type: Invoice
Invoice Number: INV-XXXX-X
PO Number: PO-XXXX
Vendor: [Vendor Name]
Country: [Country Code]
Currency: [Currency Code]
Date: YYYY-MM-DD
 - SKU: [SKU_CODE] | Description: [Item Description] | Qty: [Number] | Unit Price: [Decimal]
 - SKU: [SKU_CODE] | Description: [Item Description] | Qty: [Number] | Unit Price: [Decimal]
Total: [Decimal Amount]
```

**Example:**
```
Document Type: Invoice
Invoice Number: INV-2001-1
PO Number: PO-2001
Vendor: Acme Components Ltd
Country: US
Currency: USD
Date: 2025-01-20
 - SKU: WID-100 | Description: Widget Basic | Qty: 10 | Unit Price: 15.50
 - SKU: BLT-050 | Description: Bolt 50mm | Qty: 25 | Unit Price: 2.75
Total: 227.50
```

### 3. **Goods Receipt Note (GRN) PDF**

**Required Content:**
```
Document Type: Goods Receipt (GRN)
GRN Number: GRN-XXXX
PO Number: PO-XXXX
Vendor: [Vendor Name]
Country: [Country Code]
Date: YYYY-MM-DD
 - SKU: [SKU_CODE] | Qty: [Number]
 - SKU: [SKU_CODE] | Qty: [Number]
```

**Example:**
```
Document Type: Goods Receipt (GRN)
GRN Number: GRN-2001
PO Number: PO-2001
Vendor: Acme Components Ltd
Country: US
Date: 2025-01-18
 - SKU: WID-100 | Qty: 10
 - SKU: BLT-050 | Qty: 25
```

## Critical Formatting Rules

### **1. Exact Field Names (Case Sensitive)**
- `Document Type:` (must be exactly this)
- `PO Number:` (for PO and Invoice)
- `Invoice Number:` (for Invoice only)
- `GRN Number:` (for GRN only)
- `Vendor:`
- `Country:`
- `Currency:` (for PO and Invoice)
- `Date:`
- `Total:` (for PO and Invoice)

### **2. Line Item Format**
- **PO/Invoice Items:** ` - SKU: [CODE] | Description: [TEXT] | Qty: [NUMBER] | Unit Price: [DECIMAL]`
- **GRN Items:** ` - SKU: [CODE] | Qty: [NUMBER]`
- Must start with ` - ` (space, dash, space)
- Use `|` (pipe) as separator
- No extra spaces around the pipe

### **3. Classification Keywords**
The system classifies documents based on these keywords:
- **GRN:** Must contain "goods receipt" OR "grn" OR "received qty"
- **INVOICE:** Must contain "invoice number" OR "invoice"
- **PO:** Must contain "purchase order" OR "po number"

### **4. Data Types**
- **Dates:** YYYY-MM-DD format
- **Numbers:** Integers or decimals (no commas)
- **Currency:** Standard codes (USD, EUR, GBP, etc.)
- **Country:** Standard codes (US, GB, IN, etc.)

## Sample PDF Content for Testing

### **PDF 1: Purchase Order**
```
Document Type: Purchase Order
PO Number: PO-2001
Vendor: TechCorp Solutions
Country: US
Currency: USD
Date: 2025-01-15
 - SKU: CPU-001 | Description: Intel Core i7 Processor | Qty: 5 | Unit Price: 299.99
 - SKU: RAM-016 | Description: 16GB DDR4 Memory | Qty: 10 | Unit Price: 89.50
 - SKU: SSD-512 | Description: 512GB NVMe SSD | Qty: 8 | Unit Price: 149.99
Total: 3749.85
```

### **PDF 2: Invoice**
```
Document Type: Invoice
Invoice Number: INV-2001-1
PO Number: PO-2001
Vendor: TechCorp Solutions
Country: US
Currency: USD
Date: 2025-01-20
 - SKU: CPU-001 | Description: Intel Core i7 Processor | Qty: 5 | Unit Price: 299.99
 - SKU: RAM-016 | Description: 16GB DDR4 Memory | Qty: 10 | Unit Price: 89.50
 - SKU: SSD-512 | Description: 512GB NVMe SSD | Qty: 8 | Unit Price: 149.99
Total: 3749.85
```

### **PDF 3: Goods Receipt**
```
Document Type: Goods Receipt (GRN)
GRN Number: GRN-2001
PO Number: PO-2001
Vendor: TechCorp Solutions
Country: US
Date: 2025-01-18
 - SKU: CPU-001 | Qty: 5
 - SKU: RAM-016 | Qty: 10
 - SKU: SSD-512 | Qty: 8
```

## PDF Creation Steps

### **Method 1: Text to PDF Conversion**
1. Create a text file with the exact content above
2. Use any PDF converter (Word, Google Docs, online converters)
3. Ensure the text formatting is preserved exactly

### **Method 2: Direct PDF Creation**
1. Use PDF editing software (Adobe Acrobat, LibreOffice, etc.)
2. Create a new document
3. Add text content following the exact format
4. Save as PDF

### **Method 3: Programmatic Creation**
```python
# Example using reportlab (if you want to create PDFs programmatically)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_po_pdf():
    c = canvas.Canvas("PO-2001_TechCorp_Solutions.pdf", pagesize=letter)
    c.drawString(100, 750, "Document Type: Purchase Order")
    c.drawString(100, 730, "PO Number: PO-2001")
    c.drawString(100, 710, "Vendor: TechCorp Solutions")
    # ... continue with exact format
    c.save()
```

## Testing Your PDFs

1. **Place PDFs in:** `data_lake/raw/` directory
2. **Run the system:** Click "Ingest & Reconcile" in the Streamlit app
3. **Check results:** View the Overview tab to see if documents were processed
4. **Verify data:** Check the Exceptions tab for any processing errors

## Common Mistakes to Avoid

❌ **Wrong field names:** "Purchase Order Number" instead of "PO Number:"  
❌ **Missing colons:** "PO Number PO-2001" instead of "PO Number: PO-2001"  
❌ **Wrong line item format:** Missing the ` - ` prefix or using wrong separators  
❌ **Inconsistent spacing:** Extra spaces around pipes or colons  
❌ **Wrong classification keywords:** Missing "Document Type:" or using wrong document type names  
❌ **Invalid data formats:** Using commas in numbers, wrong date formats  

## Expected Results

If your PDFs follow this format exactly, the system will:
- ✅ **Classify correctly:** PO, Invoice, or GRN
- ✅ **Extract all fields:** Vendor, country, currency, dates, amounts
- ✅ **Parse line items:** SKU, description, quantities, prices
- ✅ **Enable 3-way matching:** Link PO ↔ Invoice ↔ GRN
- ✅ **Generate insights:** KPIs, exceptions, vendor analysis

## Troubleshooting

If your PDFs aren't being processed correctly:
1. **Check the console output** for error messages
2. **Verify the exact text format** matches the examples above
3. **Test with a simple TXT file first** to validate the format
4. **Use the audit trail** to see what was extracted from your PDF

The system is designed to be robust, but it relies on consistent formatting patterns. Following this guide exactly will ensure successful ingestion and processing of your custom PDFs.
