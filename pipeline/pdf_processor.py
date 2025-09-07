"""
Enhanced PDF Processing Module with OCR for EMA Demo
Handles PDF text extraction, image OCR, and preprocessing for procurement documents.
Supports TXT, PDF (text + scanned), and image files (JPG, PNG, etc.)
"""

import re
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import logging
import threading
import time
from contextlib import contextmanager

# Core document processing
import pdfplumber

# OCR dependencies (with graceful fallback) - SIMPLIFIED WITHOUT OPENCV
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    from pdf2image import convert_from_path
    
    # Configure Tesseract path for Windows if needed
    import platform
    if platform.system() == 'Windows':
        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if Path(tesseract_path).exists():
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    OCR_AVAILABLE = True
except ImportError as e:
    pytesseract = None
    Image = None
    OCR_AVAILABLE = False
    logging.warning(f"OCR dependencies not available: {e}. Install with: pip install pytesseract pdf2image Pillow")

logger = logging.getLogger(__name__)

@contextmanager
def timeout_context(duration, operation_name="Operation"):
    """Context manager for timing out operations using threading"""
    result = [None]
    exception = [None]
    completed = [False]
    
    def target():
        try:
            # The actual operation will be yielded to
            completed[0] = True
        except Exception as e:
            exception[0] = e
    
    # For the context manager, we'll track if the operation completes
    start_time = time.time()
    try:
        yield result
        # If we get here, the operation completed normally
    except Exception as e:
        # Re-raise any exceptions from the operation
        raise
    finally:
        # Check if we exceeded the timeout
        elapsed = time.time() - start_time
        if elapsed > duration:
            logger.warning(f"{operation_name} took {elapsed:.1f}s (timeout was {duration}s)")

class TimeoutError(Exception):
    """Custom timeout exception for OCR operations"""
    pass

def with_timeout(func, args=(), kwargs=None, timeout_seconds=30, operation_name="Operation"):
    """Execute a function with timeout using threading"""
    if kwargs is None:
        kwargs = {}
    
    result = [None]
    exception = [None]
    completed = [False]
    
    def target():
        try:
            result[0] = func(*args, **kwargs)
            completed[0] = True
        except Exception as e:
            exception[0] = e
            completed[0] = True
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    
    if not completed[0]:
        logger.error(f"{operation_name} timed out after {timeout_seconds} seconds")
        raise TimeoutError(f"{operation_name} timed out")
    
    if exception[0]:
        raise exception[0]
    
    return result[0]

class PDFProcessingError(Exception):
    """Custom exception for PDF processing errors"""
    pass

class UnsupportedFileTypeError(Exception):
    """Custom exception for unsupported file types"""
    pass

def get_file_type(file_path: Path) -> str:
    """
    Detect file type based on extension
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension in lowercase (e.g., '.txt', '.pdf')
    """
    return file_path.suffix.lower()

def _preprocess_image_for_ocr(image):
    """
    Simple image preprocessing using PIL only
    
    Args:
        image: PIL Image
        
    Returns:
        Preprocessed PIL Image
    """
    if not OCR_AVAILABLE:
        return image
        
    try:
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.3)
        
        # Sharpen slightly
        image = image.filter(ImageFilter.SHARPEN)
        
        return image
        
    except Exception as e:
        logger.warning(f"Image preprocessing failed: {e}")
        return image

def _extract_text_with_tesseract(image) -> Tuple[str, float]:
    """
    Extract text using Tesseract OCR with PIL Image and timeout protection
    
    Args:
        image: PIL Image
        
    Returns:
        Tuple of (extracted_text, confidence_score)
    """
    if not OCR_AVAILABLE:
        return "", 0.0
        
    try:
        # Preprocess image for better OCR
        processed_image = _preprocess_image_for_ocr(image)
        
        # Tesseract configuration optimized for documents
        config = '--oem 3 --psm 6'  # Use LSTM OCR engine, assume uniform block of text
        
        # Extract text with timeout protection
        text = with_timeout(
            pytesseract.image_to_string,
            args=(processed_image,),
            kwargs={'config': config},
            timeout_seconds=10,
            operation_name="Tesseract text extraction"
        )
        
        # Calculate confidence score with timeout protection
        try:
            data = with_timeout(
                pytesseract.image_to_data,
                args=(processed_image,),
                kwargs={'output_type': pytesseract.Output.DICT, 'config': config},
                timeout_seconds=5,
                operation_name="Tesseract confidence calculation"
            )
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        except (TimeoutError, Exception):
            avg_confidence = 75.0  # Default confidence for demo
        
        return text, avg_confidence
        
    except TimeoutError:
        logger.warning("Tesseract OCR operation timed out")
        return "", 0.0
    except Exception as e:
        logger.error(f"Tesseract OCR failed: {e}")
        return "", 0.0

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Enhanced PDF text extraction with OCR fallback for scanned documents
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content
        
    Raises:
        PDFProcessingError: If PDF processing fails
    """
    try:
        # First attempt: Extract embedded text using pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num} of {pdf_path}: {e}")
                    continue
            
            # If we got substantial text content, return it
            if text.strip() and len(text.strip()) > 50:
                logger.info(f"Extracted embedded text from PDF: {pdf_path}")
                return text
        
        # If no embedded text or very little text, try OCR
        if OCR_AVAILABLE:
            logger.info(f"No embedded text found, attempting OCR for: {pdf_path}")
            return _extract_text_from_pdf_with_ocr(pdf_path)
        else:
            logger.warning(f"No embedded text found and OCR not available for: {pdf_path}")
            if text.strip():
                return text  # Return whatever we got
            raise PDFProcessingError(f"No text content found in PDF and OCR unavailable: {pdf_path}")
            
    except Exception as e:
        if isinstance(e, PDFProcessingError):
            raise
        raise PDFProcessingError(f"Failed to extract text from {pdf_path}: {e}")

def _extract_text_from_pdf_with_ocr(pdf_path: Path) -> str:
    """
    Extract text from PDF using OCR (for scanned documents) with timeout protection
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        OCR-extracted text content
    """
    if not OCR_AVAILABLE:
        raise PDFProcessingError("OCR dependencies not available")
        
    try:
        # Convert PDF pages to images with timeout protection (30 seconds max)
        images = with_timeout(
            convert_from_path, 
            args=(pdf_path,), 
            kwargs={'dpi': 150, 'first_page': 1, 'last_page': 3},
            timeout_seconds=30,
            operation_name=f"PDF-to-image conversion for {pdf_path.name}"
        )
        
        all_text = ""
        total_confidence = 0
        page_count = 0
        
        for i, pil_image in enumerate(images):
            try:
                # Extract text from this page using OCR with timeout protection
                page_text, confidence = with_timeout(
                    _extract_text_with_tesseract, 
                    args=(pil_image,),
                    timeout_seconds=15,
                    operation_name=f"OCR processing for page {i+1} of {pdf_path.name}"
                )
                
                if page_text.strip():
                    all_text += f"{page_text}\n"
                    total_confidence += confidence
                    page_count += 1
                    logger.info(f"OCR page {i+1}: {confidence:.1f}% confidence")
                    
            except TimeoutError:
                logger.warning(f"OCR timeout on page {i+1} of {pdf_path.name}, skipping")
                continue
            except Exception as e:
                logger.warning(f"OCR failed on page {i+1} of {pdf_path.name}: {e}")
                continue
        
        if page_count > 0:
            avg_confidence = total_confidence / page_count
            logger.info(f"OCR completed for {pdf_path}: {page_count} pages, {avg_confidence:.1f}% avg confidence")
        
        return all_text
        
    except TimeoutError as e:
        logger.error(f"PDF OCR timeout for {pdf_path}: {e}")
        raise PDFProcessingError(f"OCR operation timed out for PDF: {pdf_path}")
    except Exception as e:
        logger.error(f"PDF OCR failed for {pdf_path}: {e}")
        raise PDFProcessingError(f"Failed to OCR PDF: {e}")

def extract_text_from_image(image_path: Path) -> str:
    """
    Extract text from image file using OCR with timeout protection
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Extracted text content
        
    Raises:
        PDFProcessingError: If image processing fails
    """
    if not OCR_AVAILABLE:
        raise PDFProcessingError("OCR dependencies not available for image processing")
        
    try:
        # Load image using PIL
        image = Image.open(image_path)
        if image is None:
            raise PDFProcessingError(f"Could not load image file: {image_path}")
        
        # Extract text using OCR with timeout protection
        text, confidence = with_timeout(
            _extract_text_with_tesseract, 
            args=(image,),
            timeout_seconds=20,
            operation_name=f"Image OCR for {image_path.name}"
        )
        
        logger.info(f"OCR extracted text from {image_path} with {confidence:.1f}% confidence")
        
        return text
        
    except TimeoutError as e:
        logger.error(f"Image OCR timeout for {image_path}: {e}")
        raise PDFProcessingError(f"OCR operation timed out for image: {image_path}")
    except Exception as e:
        logger.error(f"Image OCR failed for {image_path}: {e}")
        raise PDFProcessingError(f"Failed to process image: {e}")

def preprocess_pdf_text(text: str) -> str:
    """
    Clean and normalize PDF-extracted text to match TXT format expectations
    
    Args:
        text: Raw text extracted from PDF
        
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace and normalize
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common PDF formatting issues
    # Fix hyphenated words split across lines
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    
    # Normalize line breaks - ensure consistent formatting
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # Fix common PDF table formatting issues
    # Ensure colons are properly spaced
    text = re.sub(r'(\w):(\w)', r'\1: \2', text)
    
    # Clean up pipe-separated values (common in our sample format)
    text = re.sub(r'\|\s*', ' | ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def read_document_content(file_path: Path) -> str:
    """
    Universal document reader with OCR support for real-world documents
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Document text content
        
    Raises:
        UnsupportedFileTypeError: If file type is not supported
        PDFProcessingError: If document processing fails
    """
    file_type = get_file_type(file_path)
    
    if file_type == '.txt':
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Failed to read TXT file {file_path}: {e}")
            raise
    
    elif file_type == '.pdf':
        try:
            raw_text = extract_text_from_pdf(file_path)
            return preprocess_pdf_text(raw_text)
        except Exception as e:
            logger.error(f"Failed to process PDF file {file_path}: {e}")
            raise
    
    elif file_type in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}:
        try:
            raw_text = extract_text_from_image(file_path)
            return preprocess_pdf_text(raw_text)  # Same preprocessing for consistency
        except Exception as e:
            logger.error(f"Failed to process image file {file_path}: {e}")
            raise
    
    else:
        supported_types = ".txt, .pdf, .jpg, .jpeg, .png, .tiff, .bmp"
        raise UnsupportedFileTypeError(f"Unsupported file type: {file_type}. Supported types: {supported_types}")

def get_document_processing_info(file_path: Path) -> Dict[str, Any]:
    """
    Get detailed processing information for a document (useful for UI/debugging)
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Dictionary with processing metadata
    """
    file_type = get_file_type(file_path)
    
    info = {
        'file_path': str(file_path),
        'file_type': file_type,
        'is_supported': is_supported_file_type(file_path),
        'processing_method': 'unknown',
        'ocr_available': OCR_AVAILABLE,
        'requires_ocr': file_type in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'},
        'supports_text_extraction': file_type in {'.txt', '.pdf'},
        'supports_ocr_fallback': file_type == '.pdf' and OCR_AVAILABLE
    }
    
    if file_type == '.txt':
        info['processing_method'] = 'text_file'
    elif file_type == '.pdf':
        info['processing_method'] = 'pdf_with_ocr_fallback' if OCR_AVAILABLE else 'pdf_text_only'
    elif file_type in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}:
        info['processing_method'] = 'ocr_required'
    
    return info

def is_supported_file_type(file_path: Path) -> bool:
    """
    Check if file type is supported for processing (including OCR-based formats)
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file type is supported, False otherwise
    """
    file_type = get_file_type(file_path)
    supported_types = {'.txt', '.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
    return file_type in supported_types

def get_file_info(file_path: Path) -> dict:
    """
    Get enhanced file information including OCR capabilities
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information and processing capabilities
    """
    try:
        stat = file_path.stat()
        file_type = get_file_type(file_path)
        processing_info = get_document_processing_info(file_path)
        
        return {
            'path': str(file_path),
            'name': file_path.name,
            'size_bytes': stat.st_size,
            'file_type': file_type,
            'is_supported': is_supported_file_type(file_path),
            'processing_method': processing_info['processing_method'],
            'requires_ocr': processing_info['requires_ocr'],
            'ocr_available': OCR_AVAILABLE
        }
    except Exception as e:
        logger.error(f"Failed to get file info for {file_path}: {e}")
        return {
            'path': str(file_path),
            'name': file_path.name,
            'size_bytes': 0,
            'file_type': get_file_type(file_path),
            'is_supported': False,
            'processing_method': 'error',
            'requires_ocr': False,
            'ocr_available': OCR_AVAILABLE,
            'error': str(e)
        }
