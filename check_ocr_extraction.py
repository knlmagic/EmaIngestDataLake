#!/usr/bin/env python3
"""
Check what the OCR extraction actually produced
"""
import sqlite3
import json

def check_ocr_extraction():
    conn = sqlite3.connect('ema_demo.sqlite')
    cur = conn.cursor()
    
    print("=== OCR EXTRACTION RESULTS ===")
    cur.execute("SELECT path, parsed_json FROM documents WHERE processing_method = 'ocr_required' LIMIT 2")
    
    for row in cur.fetchall():
        path, parsed_json_str = row
        print(f"\nFile: {path}")
        print("Parsed data:")
        try:
            parsed = json.loads(parsed_json_str)
            print(json.dumps(parsed, indent=2))
        except:
            print(f"Raw JSON: {parsed_json_str}")
    
    conn.close()

if __name__ == "__main__":
    check_ocr_extraction()
