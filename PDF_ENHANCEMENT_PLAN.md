# PDF Enhancement Implementation Plan
## EMA Take-Home Demo — Adding PDF Support

### Executive Summary
Enhancing the EMA 3-Way Match demo to support PDF documents alongside TXT files. This will make the demo more realistic for real-world procurement scenarios where documents are typically in PDF format.

### Current Architecture Analysis
- **Text Processing**: Direct file reading with `path.read_text()`
- **Classification**: Simple heuristic-based document type detection
- **Extraction**: Regex patterns + optional OpenAI structured outputs
- **Storage**: SQLite with structured tables for PO/Invoice/GRN data
- **Reconciliation**: 3-way matching with configurable tolerances

### PDF Enhancement Requirements

#### 1. PDF Parsing Library Selection
**Recommended: pdfplumber**
- Built on pdfminer.six for robust text extraction
- Handles complex layouts and tables well
- Simple API for text extraction
- Good performance for procurement documents
- Active maintenance and community support

**Alternative: PyMuPDF (fitz)**
- Faster performance
- Better for complex layouts
- More memory efficient
- Good for production use

#### 2. Implementation Phases

**Phase 1: Core PDF Support**
- Add pdfplumber to requirements.txt
- Implement PDF text extraction function
- Modify ingest pipeline to detect file type
- Add basic error handling for PDF parsing

**Phase 2: Text Preprocessing**
- Clean and normalize PDF-extracted text
- Handle common PDF formatting issues
- Ensure compatibility with existing regex patterns

**Phase 3: Error Handling & Edge Cases**
- Password-protected PDFs
- Corrupted files
- Image-based PDFs (OCR fallback)
- Large file handling

**Phase 4: Testing & Documentation**
- Create sample PDF documents
- Test with mixed TXT/PDF scenarios
- Update README and demo script
- Performance testing

### Technical Implementation Details

#### File Type Detection
```python
def get_file_type(file_path: Path) -> str:
    """Detect file type based on extension"""
    return file_path.suffix.lower()
```

#### PDF Text Extraction
```python
def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using pdfplumber"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        raise PDFProcessingError(f"Failed to extract text from {pdf_path}: {e}")
```

#### Text Preprocessing
```python
def preprocess_pdf_text(text: str) -> str:
    """Clean and normalize PDF-extracted text"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Fix common PDF formatting issues
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)  # Fix hyphenated words
    # Normalize line breaks
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()
```

#### Enhanced Ingest Pipeline
```python
def read_document_content(file_path: Path) -> str:
    """Read document content based on file type"""
    file_type = get_file_type(file_path)
    
    if file_type == '.txt':
        return file_path.read_text(encoding="utf-8", errors="ignore")
    elif file_type == '.pdf':
        raw_text = extract_text_from_pdf(file_path)
        return preprocess_pdf_text(raw_text)
    else:
        raise UnsupportedFileTypeError(f"Unsupported file type: {file_type}")
```

### Database Schema Changes
**No changes required** - the existing schema supports any document type through the `doc_type` field and `parsed_json` storage.

### Error Handling Strategy
1. **PDF Parsing Errors**: Log and skip problematic files
2. **Text Extraction Failures**: Fallback to error message in parsed_json
3. **Classification Failures**: Default to "UNKNOWN" type
4. **Extraction Failures**: Use regex fallback if OpenAI fails

### Performance Considerations
- PDF parsing is ~2-3x slower than TXT reading
- Memory usage increases with PDF size
- Consider async processing for large batches
- Implement file size limits for demo purposes

### Testing Strategy
1. **Unit Tests**: PDF extraction functions
2. **Integration Tests**: Full pipeline with PDF documents
3. **Sample Data**: Create realistic PDF versions of existing TXT samples
4. **Edge Cases**: Corrupted PDFs, password-protected files

### Success Criteria
- [ ] PDF documents process successfully through the pipeline
- [ ] Classification accuracy maintained for PDF documents
- [ ] 3-way matching works with PDF-extracted data
- [ ] Backward compatibility with TXT files preserved
- [ ] Error handling gracefully manages problematic PDFs
- [ ] Demo performance remains acceptable (< 5 seconds for 30 documents)

### Risk Mitigation
- **PDF Complexity**: Start with simple PDFs, add complexity gradually
- **Performance**: Monitor processing times, optimize if needed
- **Compatibility**: Test with various PDF generators and versions
- **Dependencies**: Pin pdfplumber version for stability

### Timeline Estimate
- **Phase 1**: 2-3 hours (core PDF support)
- **Phase 2**: 1-2 hours (text preprocessing)
- **Phase 3**: 2-3 hours (error handling)
- **Phase 4**: 1-2 hours (testing & documentation)
- **Total**: 6-10 hours

### Future Enhancements
- OCR support for image-based PDFs
- Table extraction for structured data
- Multi-language document support
- Batch processing optimization
- Cloud storage integration (S3, Azure Blob)

---
*Document created: 2025-01-27*
*Status: Planning Phase*
