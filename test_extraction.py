#!/usr/bin/env python3
"""
Test the extraction logic directly on OCR text
"""
from pipeline.pdf_processor import extract_text_from_image
from pipeline.classify_extract import extract
from pathlib import Path

# Get OCR text
img_path = Path('data_lake/raw/SCANNED_INV_2003_Wayne_Parts_Co.jpg')
if img_path.exists():
    print("=== TESTING EXTRACTION ON OCR TEXT ===")
    
    # Step 1: Get OCR text
    ocr_text = extract_text_from_image(img_path)
    print(f"1. OCR Text extracted: {len(ocr_text)} characters")
    print(f"First 200 chars: {repr(ocr_text[:200])}")
    
    # Step 2: Run extraction
    print("\n2. Running extraction...")
    try:
        extracted_data = extract(ocr_text, "INVOICE")
        print("✅ Extraction successful!")
        print(f"Extracted data: {extracted_data}")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Image file not found")
