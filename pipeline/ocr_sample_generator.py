"""
Sample Scanned Document Generator for OCR Demo
Creates realistic-looking scanned invoice images for testing OCR capabilities
"""

import random
from pathlib import Path
from typing import Dict, Any, List

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def create_sample_scanned_invoice(output_path: Path, invoice_data: Dict[str, Any]) -> bool:
    """
    Create a realistic-looking scanned invoice image
    
    Args:
        output_path: Where to save the image
        invoice_data: Invoice data dictionary
        
    Returns:
        True if successful, False otherwise
    """
    if not PIL_AVAILABLE:
        print("PIL/Pillow not available. Install with: pip install Pillow")
        return False
    
    try:
        # Create base image (A4-ish proportions at 200 DPI)
        width, height = 1700, 2200  # ~8.5x11 inches at 200 DPI
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Try to use system fonts, fall back to default
        try:
            title_font = ImageFont.truetype("arial.ttf", 36)
            header_font = ImageFont.truetype("arial.ttf", 24) 
            body_font = ImageFont.truetype("arial.ttf", 18)
            small_font = ImageFont.truetype("arial.ttf", 14)
        except:
            try:
                # Try alternative font names
                title_font = ImageFont.truetype("Arial.ttf", 36)
                header_font = ImageFont.truetype("Arial.ttf", 24)
                body_font = ImageFont.truetype("Arial.ttf", 18)
                small_font = ImageFont.truetype("Arial.ttf", 14)
            except:
                # Fallback to default font
                title_font = ImageFont.load_default()
                header_font = ImageFont.load_default()
                body_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
        
        # Draw invoice content in format that matches regex patterns
        y = 80
        
        # Invoice details in expected format (matching TXT file structure)
        draw.text((80, y), "Document Type: Invoice", fill='black', font=header_font)
        y += 35
        draw.text((80, y), f"Invoice Number: {invoice_data['invoice_number']}", fill='black', font=header_font)
        y += 35
        draw.text((80, y), f"PO Number: {invoice_data['po_number']}", fill='black', font=header_font)
        y += 35
        draw.text((80, y), f"Vendor: {invoice_data['vendor']}", fill='black', font=header_font)
        y += 35
        draw.text((80, y), f"Country: {invoice_data['country']}", fill='black', font=header_font)
        y += 35
        draw.text((80, y), f"Currency: {invoice_data['currency']}", fill='black', font=header_font)
        y += 35
        draw.text((80, y), f"Date: {invoice_data['date']}", fill='black', font=header_font)
        y += 60
        
        # Items in expected format (matching TXT file structure)
        total_amount = 0
        for item in invoice_data['items']:
            item_total = item['qty'] * item['unit_price']
            total_amount += item_total
            
            # Format: " - SKU: ABC | Description: ... | Qty: 10 | Unit Price: 12.5"
            item_line = f" - SKU: {item['sku']} | Description: {item['description']} | Qty: {int(item['qty'])} | Unit Price: {item['unit_price']:.2f}"
            draw.text((80, y), item_line, fill='black', font=body_font)
            y += 25
        
        y += 20
        draw.text((80, y), f"Total: {total_amount:.1f}", fill='black', font=header_font)
        
        # Add some "scanning" artifacts for realism
        # 1. Slight rotation to simulate scanning misalignment
        angle = random.uniform(-1.5, 1.5)
        img = img.rotate(angle, fillcolor='white', expand=False)
        
        # 2. Add slight blur to simulate scanning quality
        img = img.filter(ImageFilter.GaussianBlur(0.3))
        
        # 3. Adjust brightness/contrast slightly
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(random.uniform(0.95, 1.05))
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(random.uniform(0.95, 1.05))
        
        # 4. Add some noise by slightly adjusting individual pixels
        # (This is optional and might be too much for simple demo)
        
        # Save as JPEG with slight compression to simulate scanning
        img.save(output_path, 'JPEG', quality=random.randint(88, 95))
        
        return True
        
    except Exception as e:
        print(f"Failed to create scanned invoice {output_path}: {e}")
        return False

def generate_sample_scanned_documents(output_dir: Path, count: int = 5) -> List[Path]:
    """
    Generate multiple sample scanned invoice images
    
    Args:
        output_dir: Directory to save images
        count: Number of documents to generate
        
    Returns:
        List of generated file paths
    """
    if not PIL_AVAILABLE:
        print("Cannot generate scanned documents: PIL/Pillow not available")
        return []
    
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files = []
    
    vendors = ["Wayne Parts Co", "Stark Industrial", "Acme Components Ltd", "Initech Pvt Ltd", "Umbrella Supplies"]
    countries = ["US", "CA", "UK", "DE", "JP"]
    currencies = ["USD", "CAD", "GBP", "EUR", "JPY"]
    
    descriptions = [
        "Widget Assembly A-100", 
        "Component X-Series", 
        "Industrial Bearing", 
        "Steel Bracket",
        "Electronic Module",
        "Mechanical Part",
        "Assembly Kit",
        "Replacement Part"
    ]
    
    for i in range(count):
        vendor = random.choice(vendors)
        country = random.choice(countries)
        currency = random.choice(currencies)
        
        # Generate realistic invoice data
        invoice_data = {
            'invoice_number': f"SCAN-INV-{2000+i}",
            'po_number': f"PO-{3000+i}",
            'date': f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            'vendor': vendor,
            'country': country,
            'currency': currency,
            'items': []
        }
        
        # Generate 1-4 items per invoice
        num_items = random.randint(1, 4)
        for j in range(num_items):
            invoice_data['items'].append({
                'sku': f"PART-{random.randint(100,999)}-{chr(65+j)}",
                'description': random.choice(descriptions),
                'qty': random.randint(1, 20),
                'unit_price': round(random.uniform(10.00, 150.00), 2)
            })
        
        # Create filename
        vendor_clean = vendor.replace(' ', '_').replace('.', '')
        filename = f"SCANNED_INV_{2000+i}_{vendor_clean}.jpg"
        output_path = output_dir / filename
        
        # Generate the image
        if create_sample_scanned_invoice(output_path, invoice_data):
            generated_files.append(output_path)
            print(f"✅ Generated scanned invoice: {filename}")
        else:
            print(f"❌ Failed to generate: {filename}")
    
    return generated_files

def main():
    """Generate sample scanned documents for demo"""
    output_dir = Path("data_lake/raw")
    
    print("🖼️  Generating sample scanned documents for OCR demo...")
    files = generate_sample_scanned_documents(output_dir, count=5)
    
    print(f"\n✅ Generated {len(files)} scanned invoice images!")
    print("📁 Files saved to: data_lake/raw/")
    print("\n🔍 To test OCR:")
    print("1. Run: streamlit run app.py")
    print("2. Click 'Ingest & Reconcile'")
    print("3. Check the OCR metrics in the dashboard!")

if __name__ == "__main__":
    main()
