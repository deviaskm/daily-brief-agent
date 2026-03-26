"""Configuration settings."""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"

# Scraping configuration
SCRAPER_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "rate_limit_delay": 1.0,
}

# Analysis configuration
ANALYSIS_CONFIG = {
    "min_data_points": 10,
    "outlier_threshold": 2.0,
}

# Reporting configuration
REPORT_CONFIG = {
    "output_format": "pdf",
    "include_visualizations": True,
    "company_name": "Hotel Market Analysis",
}

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = PROJECT_ROOT / "logs" / "agent.log"
