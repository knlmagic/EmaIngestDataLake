#!/usr/bin/env python3
"""
Complete system test from scratch
Tests all 4 priority fixes end-to-end
"""

import os
import shutil
from pathlib import Path
from pipeline.db import connect
from pipeline.ingest import ingest_folder
from pipeline.reconcile import reconcile

def clean_start():
    """Start with clean state"""
    print("🧹 STEP 1: Clean Start")
    
    # Remove old database
    db_path = Path("test_system.sqlite")
    if db_path.exists():
        db_path.unlink()
        print("  ✅ Removed old database")
    
    # Create fresh temp directory for testing
    test_dir = Path("test_data")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    print("  ✅ Created fresh test directory")
    
    return db_path, test_dir

def test_sample_generation(test_dir):
    """Test sample data generation"""
    print("\n📊 STEP 2: Test Sample Generation")
    
    from pipeline.sample_data import generate
    
    try:
        generate(test_dir, n_sets=3)  # Small test set
        files = list(test_dir.glob("*"))
        print(f"  ✅ Generated {len(files)} files")
        return True
    except Exception as e:
        print(f"  ❌ Generation failed: {e}")
        return False

def test_ocr_extraction():
    """Test OCR text extraction specifically"""
    print("\n🔍 STEP 3: Test OCR Extraction")
    
    from pipeline.classify_extract import extract
    
    # Test OCR-style text (what we get from scanned images)
    ocr_text = """Document Type: Invoice

Invoice Number: TEST-123

PO Number: PO-456

Vendor: Test Company

Country: US

Currency: USD

Date: 2024-01-01

 - SKU: PART-001 | Description: Test Part | Qty: 5 | Unit Price: 10.00

Total: 50.00"""
    
    try:
        result = extract(ocr_text, "INVOICE")
        invoice_num = result.get("invoice_number")
        vendor = result.get("vendor")
        
        if invoice_num == "TEST-123" and vendor == "Test Company":
            print("  ✅ OCR extraction working correctly")
            print(f"    - Invoice: {invoice_num}")
            print(f"    - Vendor: {vendor}")
            return True
        else:
            print("  ❌ OCR extraction failed")
            print(f"    - Expected: TEST-123, Got: {invoice_num}")
            print(f"    - Expected: Test Company, Got: {vendor}")
            return False
            
    except Exception as e:
        print(f"  ❌ OCR extraction error: {e}")
        return False

def test_ingest_process(db_path, test_dir):
    """Test complete ingest process"""
    print("\n📥 STEP 4: Test Ingest Process")
    
    try:
        conn = connect(db_path)
        ingested, skipped, errors = ingest_folder(conn, test_dir)
        
        print(f"  📊 Results: {ingested} ingested, {skipped} skipped, {errors} errors")
        
        if errors > 0:
            print("  ❌ Ingest had errors")
            conn.close()
            return False
        
        # Check database contents
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM invoices")
        invoice_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM purchase_orders")
        po_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM grns")
        grn_count = cur.fetchone()[0]
        
        print(f"  📊 Database: {invoice_count} invoices, {po_count} POs, {grn_count} GRNs")
        
        conn.close()
        return invoice_count > 0 and po_count > 0
        
    except Exception as e:
        print(f"  ❌ Ingest failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reconcile_process(db_path):
    """Test reconcile process"""
    print("\n⚖️ STEP 5: Test Reconcile Process")
    
    try:
        conn = connect(db_path)
        reconcile(conn, qty_tol_units=1.0, price_tol_pct=2.0)
        
        # Check results
        cur = conn.cursor()
        cur.execute("SELECT status, COUNT(*) FROM reconciliation GROUP BY status")
        results = dict(cur.fetchall())
        
        print("  📊 Reconciliation Results:")
        for status, count in results.items():
            print(f"    - {status}: {count}")
        
        conn.close()
        return len(results) > 0
        
    except Exception as e:
        print(f"  ❌ Reconcile failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_openai_fallback():
    """Test OpenAI integration doesn't crash"""
    print("\n🤖 STEP 6: Test OpenAI Fallback")
    
    # Save original setting
    original_openai = os.environ.get("USE_OPENAI", "false")
    
    try:
        # Test with OpenAI OFF (should work)
        os.environ["USE_OPENAI"] = "false"
        from pipeline.classify_extract import extract
        
        result = extract("Document Type: Invoice\nInvoice Number: TEST", "INVOICE")
        if result.get("type") == "INVOICE":
            print("  ✅ OpenAI OFF mode working")
        else:
            print("  ❌ OpenAI OFF mode failed")
            return False
        
        # Test with OpenAI ON (should fallback gracefully)
        os.environ["USE_OPENAI"] = "true"
        # Force module reload to pick up new setting
        import importlib
        import pipeline.classify_extract
        importlib.reload(pipeline.classify_extract)
        
        result2 = pipeline.classify_extract.extract("Document Type: Invoice\nInvoice Number: TEST", "INVOICE")
        if result2.get("type") == "INVOICE":
            print("  ✅ OpenAI ON mode working (likely fell back to regex)")
        else:
            print("  ❌ OpenAI ON mode failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ OpenAI test failed: {e}")
        return False
    finally:
        # Restore original setting
        os.environ["USE_OPENAI"] = original_openai

def cleanup(db_path, test_dir):
    """Clean up test files"""
    print("\n🧹 CLEANUP")
    
    if db_path.exists():
        db_path.unlink()
        print("  ✅ Removed test database")
    
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("  ✅ Removed test directory")

def main():
    """Run complete system test"""
    print("=== COMPLETE SYSTEM TEST ===")
    print("Testing all 4 priority bug fixes end-to-end\n")
    
    # Step 1: Clean start
    db_path, test_dir = clean_start()
    
    tests = [
        ("Sample Generation", lambda: test_sample_generation(test_dir)),
        ("OCR Extraction Fix", test_ocr_extraction),
        ("Ingest Process", lambda: test_ingest_process(db_path, test_dir)),
        ("Reconcile Process", lambda: test_reconcile_process(db_path)),
        ("OpenAI Integration", test_openai_fallback)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"  💥 {test_name} crashed: {e}")
            results[test_name] = False
    
    # Final summary
    print("\n" + "="*50)
    print("FINAL RESULTS:")
    print("="*50)
    
    all_passed = True
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not success:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - System is working!")
    else:
        print("💥 SOME TESTS FAILED - Need debugging")
    print("="*50)
    
    # Cleanup
    cleanup(db_path, test_dir)
    
    return all_passed

if __name__ == "__main__":
    main()
