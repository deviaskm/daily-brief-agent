"""Utility functions for scraping operations."""

import re
import time
import logging
from functools import wraps
from datetime import datetime
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


def normalize_price(price):
    """
    Normalize price data from various formats to float.

    Args:
        price: Price string like "$159.99", "€120,50", "₹5,000"

    Returns:
        float: Normalized price value

    Raises:
        ValueError: If price cannot be parsed
    """
    if isinstance(price, (int, float)):
        return float(price)

    if not isinstance(price, str):
        raise ValueError(f"Price must be string or number, got {type(price)}")

    # Remove common currency symbols and whitespace
    price_cleaned = re.sub(r'[$€£¥₹₽₩₪₫₱₡₲₴₵₸]|\s', '', price)

    # Handle mixed comma and period (determine which is decimal separator)
    if ',' in price_cleaned and '.' in price_cleaned:
        last_comma_pos = price_cleaned.rfind(',')
        last_period_pos = price_cleaned.rfind('.')

        if last_comma_pos > last_period_pos:
            # European format: 1.000,50 → 1000.50
            price_cleaned = price_cleaned.replace('.', '').replace(',', '.')
        else:
            # US format: 1,234.56 → 1234.56
            price_cleaned = price_cleaned.replace(',', '')
    elif ',' in price_cleaned:
        # Only comma - could be European (1000,50) or US thousands (1,00)
        # If only 2 decimals likely, it's European; otherwise thousands separator
        decimal_part = price_cleaned.split(',')[1] if ',' in price_cleaned else ''
        if len(decimal_part) == 2:
            # Likely European format
            price_cleaned = price_cleaned.replace(',', '.')
        else:
            # US thousands separator
            price_cleaned = price_cleaned.replace(',', '')

    # Extract numeric value
    match = re.search(r'[\d.]+', price_cleaned)
    if not match:
        raise ValueError(f"Could not extract numeric value from price: {price}")

    return float(match.group())


def parse_date(date_str):
    """
    Parse date strings in various formats to YYYY-MM-DD.

    Args:
        date_str: Date string like "Jun 15, 2024", "2024-06-15", "15/06/2024"

    Returns:
        str: Standardized date in YYYY-MM-DD format

    Raises:
        ValueError: If date cannot be parsed
    """
    if isinstance(date_str, datetime):
        return date_str.strftime('%Y-%m-%d')

    if not isinstance(date_str, str):
        raise ValueError(f"Date must be string or datetime, got {type(date_str)}")

    try:
        parsed_date = date_parser.parse(date_str)
        return parsed_date.strftime('%Y-%m-%d')
    except Exception as e:
        raise ValueError(f"Could not parse date: {date_str}") from e


def retry_request(func, max_retries=3):
    """
    Decorator for retrying failed function calls with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts

    Returns:
        Decorated function that retries on failure
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from src.config.settings import SCRAPER_CONFIG

        rate_limit_delay = SCRAPER_CONFIG.get('rate_limit_delay', 1.0)
        last_exception = None

        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s, ...
                    wait_time = rate_limit_delay * (2 ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}. "
                        f"Retrying in {wait_time}s... Error: {str(e)}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"All {max_retries} attempts failed for {func.__name__}. "
                        f"Last error: {str(e)}"
                    )

        raise last_exception

    return wrapper
