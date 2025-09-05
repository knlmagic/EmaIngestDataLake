#!/usr/bin/env python3
"""
OCR Demo Setup Script
Installs dependencies and generates sample scanned documents
"""

import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install OCR dependencies"""
    print("📦 Installing OCR dependencies...")
    
    dependencies = [
        "pytesseract==0.3.10",
        "Pillow==10.4.0", 
        "pdf2image==1.17.0",
        "opencv-python==4.9.0.80"
    ]
    
    for dep in dependencies:
        try:
            print(f"Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False
    
    print("✅ Dependencies installed successfully!")
    return True

def check_tesseract():
    """Check if Tesseract is available"""
    try:
        import pytesseract
        # Try to get Tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract OCR found: {version}")
        return True
    except Exception as e:
        print("❌ Tesseract OCR not found!")
        print("\n📝 To install Tesseract on Windows:")
        print("1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Or use: winget install UB-Mannheim.TesseractOCR")
        print("3. Or use Chocolatey: choco install tesseract")
        print("\n📝 On macOS: brew install tesseract")
        print("📝 On Ubuntu: sudo apt install tesseract-ocr")
        return False

def generate_sample_documents():
    """Generate sample scanned documents"""
    print("🖼️  Generating sample scanned documents...")
    
    try:
        from pipeline.ocr_sample_generator import generate_sample_scanned_documents
        
        output_dir = Path("data_lake/raw")
        files = generate_sample_scanned_documents(output_dir, count=3)
        
        if files:
            print(f"✅ Generated {len(files)} sample scanned documents!")
            for file in files:
                print(f"   📄 {file.name}")
        else:
            print("❌ Failed to generate sample documents")
            
    except ImportError as e:
        print(f"❌ Could not import sample generator: {e}")
        return False
    except Exception as e:
        print(f"❌ Error generating samples: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up OCR Demo for EMA Data Lake Ingest")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed: Could not install dependencies")
        return
    
    # Check Tesseract
    if not check_tesseract():
        print("⚠️  Tesseract not found - OCR will not work until installed")
        print("   But you can still run the demo with text/PDF files!")
    
    # Generate sample documents
    print("\n" + "=" * 50)
    generate_sample_documents()
    
    # Final instructions
    print("\n" + "=" * 50)
    print("🎉 OCR Demo Setup Complete!")
    print("\n🚀 To run the demo:")
    print("   streamlit run app.py")
    print("\n📋 Demo steps:")
    print("1. Click 'Generate sample data' (creates text/PDF files)")
    print("2. Click 'Ingest & Reconcile' (processes all files)")
    print("3. Check the OCR metrics in the Overview tab!")
    print("4. Try dropping your own scanned PDFs or images into data_lake/raw/")
    
    print("\n📊 OCR Features:")
    print("• Supports: JPG, PNG, PDF (scanned), TXT")
    print("• Shows confidence scores")
    print("• Automatic fallback to text extraction")
    print("• Real-time processing metrics")

if __name__ == "__main__":
    main()
