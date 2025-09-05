"""
PDF Sample Generator for EMA Demo
Creates sample PDF documents that match the TXT format for testing.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import random

def create_sample_pdf(output_path: Path, content: str, title: str = "Document"):
    """
    Create a sample PDF with the given content
    
    Args:
        output_path: Path where to save the PDF
        content: Text content to include in the PDF
        title: Title for the PDF document
    """
    try:
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Create custom style for document content
        content_style = ParagraphStyle(
            'CustomContent',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leftIndent=0,
            rightIndent=0
        )
        
        # Build the PDF content
        story = []
        
        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            alignment=1  # Center alignment
        )
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Add content
        lines = content.split('\n')
        for line in lines:
            if line.strip():
                # Handle special formatting for key-value pairs
                if ':' in line and '|' not in line:
                    # This is a key-value pair, make it bold
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key, value = parts
                        formatted_line = f"<b>{key.strip()}:</b> {value.strip()}"
                    else:
                        formatted_line = line
                else:
                    formatted_line = line
                
                story.append(Paragraph(formatted_line, content_style))
            else:
                story.append(Spacer(1, 6))
        
        # Build the PDF
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error creating PDF {output_path}: {e}")
        return False

def generate_pdf_samples_from_txt(txt_folder: Path, pdf_folder: Path, count: int = 5):
    """
    Generate PDF samples based on existing TXT files
    
    Args:
        txt_folder: Folder containing TXT sample files
        pdf_folder: Folder where to save PDF samples
        count: Number of PDF samples to generate
    """
    pdf_folder.mkdir(exist_ok=True)
    
    # Get list of TXT files
    txt_files = list(txt_folder.glob("*.txt"))
    if not txt_files:
        print("No TXT files found to convert")
        return
    
    generated = 0
    for txt_file in txt_files[:count]:
        try:
            # Read TXT content
            content = txt_file.read_text(encoding="utf-8")
            
            # Create PDF filename
            pdf_name = txt_file.stem + ".pdf"
            pdf_path = pdf_folder / pdf_name
            
            # Determine document type for title
            if "PO-" in txt_file.name:
                title = "Purchase Order"
            elif "INV-" in txt_file.name:
                title = "Invoice"
            elif "GRN-" in txt_file.name:
                title = "Goods Receipt Note"
            else:
                title = "Document"
            
            # Create PDF
            if create_sample_pdf(pdf_path, content, title):
                print(f"Generated PDF: {pdf_path}")
                generated += 1
            else:
                print(f"Failed to generate PDF: {pdf_path}")
                
        except Exception as e:
            print(f"Error processing {txt_file}: {e}")
    
    print(f"Generated {generated} PDF samples in {pdf_folder}")

def create_sample_pdf_content(doc_type: str, doc_number: str, vendor: str, country: str = "US") -> str:
    """
    Create sample PDF content in the expected format
    
    Args:
        doc_type: Type of document (PO, INVOICE, GRN)
        doc_number: Document number
        vendor: Vendor name
        country: Country code
        
    Returns:
        Formatted content string
    """
    if doc_type == "PO":
        return f"""Document Type: Purchase Order
PO Number: {doc_number}
Vendor: {vendor}
Country: {country}
Currency: USD
Date: 2025-01-27
 - SKU: ABC-123 | Description: Sample Component | Qty: 10 | Unit Price: 25.50
 - SKU: XYZ-456 | Description: Another Part | Qty: 5 | Unit Price: 15.75
Total: 332.25"""
    
    elif doc_type == "INVOICE":
        return f"""Document Type: Invoice
Invoice Number: {doc_number}
PO Number: PO-{doc_number.split('-')[1]}
Vendor: {vendor}
Country: {country}
Currency: USD
Date: 2025-01-27
 - SKU: ABC-123 | Description: Sample Component | Qty: 10 | Unit Price: 25.50
 - SKU: XYZ-456 | Description: Another Part | Qty: 5 | Unit Price: 15.75
Total: 332.25"""
    
    elif doc_type == "GRN":
        return f"""Document Type: Goods Receipt Note
GRN Number: {doc_number}
PO Number: PO-{doc_number.split('-')[1]}
Vendor: {vendor}
Country: {country}
Date: 2025-01-27
 - SKU: ABC-123 | Qty: 10
 - SKU: XYZ-456 | Qty: 5"""
    
    else:
        return f"""Document Type: {doc_type}
Document Number: {doc_number}
Vendor: {vendor}
Country: {country}
Date: 2025-01-27"""

if __name__ == "__main__":
    # Example usage
    txt_folder = Path("data_lake/raw")
    pdf_folder = Path("data_lake/raw_pdf")
    
    if txt_folder.exists():
        generate_pdf_samples_from_txt(txt_folder, pdf_folder, count=3)
    else:
        print(f"TXT folder not found: {txt_folder}")
