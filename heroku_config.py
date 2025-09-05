"""
Heroku-specific configuration for EMA Data Lake Ingest
Handles cloud-compatible paths and environment variables
"""

import os
import tempfile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def get_heroku_paths():
    """Get Heroku-compatible file paths using temp directory"""
    # Use /tmp for Heroku's ephemeral filesystem
    temp_dir = Path("/tmp") if os.getenv("DYNO") else Path(tempfile.gettempdir())
    
    paths = {
        "db_path": temp_dir / "ema_demo.sqlite",
        "data_raw": temp_dir / "data_lake_raw", 
        "backups": temp_dir / "backups",
        "uploads": temp_dir / "uploads",
        "config_path": temp_dir / "config.json"
    }
    
    # Ensure directories exist
    for key, path in paths.items():
        if key != "db_path" and key != "config_path":  # Don't create files, only dirs
            path.mkdir(parents=True, exist_ok=True)
    
    return paths

def get_heroku_config():
    """Get configuration from environment variables with fallbacks"""
    return {
        "qty_tolerance_units": float(os.getenv("QTY_TOLERANCE", "1")),
        "price_tolerance_pct": float(os.getenv("PRICE_TOLERANCE", "2.0")),
        "fx_rates": {
            "USD": 1.0,
            "GBP": float(os.getenv("GBP_RATE", "1.3")),
            "INR": float(os.getenv("INR_RATE", "0.012"))
        }
    }

def setup_tesseract_for_heroku():
    """Configure Tesseract path for Heroku environment"""
    if os.getenv("DYNO"):  # Running on Heroku
        # Tesseract installed via Aptfile should be in PATH
        logger.info("Running on Heroku - Tesseract should be available in PATH")
        return True
    else:
        # Local development - try to find Tesseract
        import platform
        if platform.system() == 'Windows':
            tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if Path(tesseract_path).exists():
                try:
                    import pytesseract
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    logger.info(f"Found Tesseract at {tesseract_path}")
                    return True
                except ImportError:
                    pass
        
        logger.warning("Tesseract path configuration may be needed")
        return False

def is_heroku_environment():
    """Check if running on Heroku"""
    return os.getenv("DYNO") is not None

def get_database_url():
    """Get database URL - PostgreSQL on Heroku, SQLite locally"""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # Heroku PostgreSQL
        # Fix for SQLAlchemy 1.4+ compatibility
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return db_url
    return None  # Use SQLite
