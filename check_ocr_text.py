#!/usr/bin/env python3
"""
Check the raw OCR text to see formatting differences
"""
from pipeline.pdf_processor import extract_text_from_image
from pathlib import Path

# Check what OCR actually extracted
image_path = Path("data_lake/raw/SCANNED_INV_2000_Wayne_Parts_Co.jpg")

if image_path.exists():
    print("=== RAW OCR TEXT ===")
    try:
        raw_text = extract_text_from_image(image_path)
        print(f"OCR Text from {image_path.name}:")
        print("=" * 40)
        print(repr(raw_text))  # Use repr to see exact formatting
        print("=" * 40)
        print(raw_text)
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Image file not found")

# For comparison, show what a regular TXT file looks like
txt_path = Path("data_lake/raw/INV-1000-1_Wayne_Parts_Co.txt")
if txt_path.exists():
    print("\n=== REGULAR TXT FILE (for comparison) ===")
    txt_content = txt_path.read_text()
    print(f"TXT file content:")
    print("=" * 40)
    print(repr(txt_content))  # Use repr to see exact formatting
    print("=" * 40)
    print(txt_content)
