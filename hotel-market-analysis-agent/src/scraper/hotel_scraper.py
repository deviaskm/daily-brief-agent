"""Hotel pricing data scraper."""

import json
import logging
from datetime import datetime
from pathlib import Path
from time import sleep
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

from src.scraper.utils import normalize_price, parse_date, retry_request
from src.config.settings import SCRAPER_CONFIG, RAW_DATA_DIR

logger = logging.getLogger(__name__)


class HotelScraper:
    """Scrapes public hotel pricing data from Google Hotels."""

    def __init__(self, config=None):
        """Initialize scraper with configuration."""
        self.config = config or SCRAPER_CONFIG
        self.driver = None
        self.timeout = self.config.get('timeout', 30)
        self.rate_limit_delay = self.config.get('rate_limit_delay', 1.0)
        self.user_agent = self.config.get(
            'user_agent',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

    def _init_driver(self):
        """Initialize Selenium WebDriver with Chrome options."""
        chrome_options = Options()
        chrome_options.add_argument(f'user-agent={self.user_agent}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome WebDriver initialized")

    def _close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Chrome WebDriver closed")

    def scrape_hotels(self, destination, check_in, check_out):
        """
        Scrape hotel data for given destination and dates.

        Args:
            destination: Hotel destination/city
            check_in: Check-in date (YYYY-MM-DD or parseable format)
            check_out: Check-out date (YYYY-MM-DD or parseable format)

        Returns:
            List of hotel data dictionaries
        """
        try:
            # Parse and validate dates
            check_in_str = parse_date(check_in)
            check_out_str = parse_date(check_out)
            logger.info(
                f"Scraping hotels in {destination} from {check_in_str} to {check_out_str}"
            )

            # Initialize driver
            self._init_driver()

            # Build Google Hotels URL
            url = self._build_google_hotels_url(destination, check_in_str, check_out_str)
            logger.info(f"Navigating to: {url}")

            # Load page
            self.driver.get(url)
            sleep(self.rate_limit_delay)

            # Wait for hotel listings to load
            wait = WebDriverWait(self.driver, self.timeout)
            wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, '//div[contains(@data-index, "")]')
                )
            )

            # Parse hotel listings
            hotels = self._parse_hotel_listings(destination, check_in_str, check_out_str)

            # Validate data
            validated_hotels = self.validate_data(hotels)

            # Save raw data
            self._save_raw_data(destination, check_in_str, validated_hotels)

            return validated_hotels

        except Exception as e:
            logger.error(f"Error scraping hotels: {str(e)}", exc_info=True)
            return []
        finally:
            self._close_driver()

    def _build_google_hotels_url(self, destination, check_in, check_out):
        """
        Build Google Hotels search URL.

        Args:
            destination: City/location name
            check_in: Date in YYYY-MM-DD format
            check_out: Date in YYYY-MM-DD format

        Returns:
            str: Google Hotels URL
        """
        base_url = 'https://www.google.com/travel/hotels'
        check_in_parts = check_in.split('-')
        check_out_parts = check_out.split('-')

        params = {
            'q': destination,
            'check_in_date': f"{check_in_parts[1]}/{check_in_parts[2]}/{check_in_parts[0]}",
            'check_out_date': f"{check_out_parts[1]}/{check_out_parts[2]}/{check_out_parts[0]}",
            'g2lb': 1,
        }

        query_string = '&'.join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"{base_url}?{query_string}"

    def _parse_hotel_listings(self, destination, check_in, check_out):
        """
        Parse hotel listings from page HTML.

        Args:
            destination: City name
            check_in: Check-in date
            check_out: Check-out date

        Returns:
            List of hotel dictionaries
        """
        hotels = []
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        scraped_at = datetime.utcnow().isoformat()

        # Find all hotel cards - Google Hotels uses divs with specific attributes
        hotel_cards = soup.find_all('div', {'data-index': True})

        logger.info(f"Found {len(hotel_cards)} hotel listings")

        for card in hotel_cards[:20]:  # Limit to first 20 for testing
            try:
                hotel_data = self._extract_hotel_data(
                    card, destination, check_in, check_out, scraped_at
                )
                if hotel_data:
                    hotels.append(hotel_data)
            except Exception as e:
                logger.warning(f"Failed to extract hotel data from card: {str(e)}")
                continue

        return hotels

    def _extract_hotel_data(self, card, destination, check_in, check_out, scraped_at):
        """
        Extract hotel information from a single card element.

        Args:
            card: BeautifulSoup element for hotel card
            destination: City name
            check_in: Check-in date
            check_out: Check-out date
            scraped_at: Timestamp when data was scraped

        Returns:
            dict: Hotel data or None if extraction fails
        """
        try:
            # Extract hotel name
            name_elem = card.find('h2')
            hotel_name = name_elem.text.strip() if name_elem else 'Unknown'

            # Extract price
            price_elem = card.find('span', string=lambda x: x and '$' in str(x))
            price_text = price_elem.text.strip() if price_elem else None

            if not price_text:
                # Try alternative price selectors
                price_span = card.find('span', {'aria-label': lambda x: x and 'per night' in str(x).lower()})
                price_text = price_span.text.strip() if price_span else None

            price = normalize_price(price_text) if price_text else None

            # Extract rating
            rating_elem = card.find('span', {'aria-label': lambda x: x and 'star' in str(x).lower()})
            rating_text = rating_elem.text.strip() if rating_elem else None
            rating = None
            if rating_text:
                try:
                    rating = float(rating_text.split()[0])
                except (ValueError, IndexError):
                    rating = None

            # Extract review score/count
            reviews_elem = card.find('span', string=lambda x: x and 'review' in str(x).lower())
            review_text = reviews_elem.text.strip() if reviews_elem else None
            review_count = None
            if review_text:
                try:
                    review_count = int(''.join(filter(str.isdigit, review_text)))
                except ValueError:
                    review_count = None

            # Extract address/location
            address_elem = card.find('span', {'class': lambda x: x and 'location' in str(x).lower()})
            address = address_elem.text.strip() if address_elem else destination

            # Extract URL if available
            link_elem = card.find('a', href=True)
            url = link_elem['href'] if link_elem else ''

            # Determine availability (assume available unless marked otherwise)
            available_elem = card.find('span', string=lambda x: x and 'sold out' in str(x).lower())
            available = not bool(available_elem)

            hotel_data = {
                'destination': destination,
                'check_in': check_in,
                'check_out': check_out,
                'hotel_name': hotel_name,
                'address': address,
                'price_per_night': price,
                'currency': 'USD',
                'star_rating': rating,
                'review_score': None,  # Google Hotels doesn't always show this
                'review_count': review_count,
                'available': available,
                'url': url,
                'scraped_at': scraped_at,
            }

            return hotel_data

        except Exception as e:
            logger.debug(f"Error extracting hotel data: {str(e)}")
            return None

    def validate_data(self, data):
        """
        Validate scraped data quality and completeness.

        Args:
            data: List of hotel dictionaries

        Returns:
            List of valid hotel dictionaries
        """
        if not isinstance(data, list):
            logger.warning("Data is not a list")
            return []

        valid_hotels = []
        required_fields = {
            'hotel_name', 'destination', 'check_in', 'check_out'
        }

        for hotel in data:
            if not isinstance(hotel, dict):
                logger.warning(f"Hotel record is not a dict: {hotel}")
                continue

            # Check required fields
            missing_fields = required_fields - set(hotel.keys())
            if missing_fields:
                logger.warning(
                    f"Hotel '{hotel.get('hotel_name', 'Unknown')}' missing fields: {missing_fields}"
                )
                continue

            # Validate price if present
            if hotel.get('price_per_night') is not None:
                if not isinstance(hotel['price_per_night'], (int, float)):
                    logger.warning(f"Invalid price for {hotel['hotel_name']}: {hotel['price_per_night']}")
                    continue
                if hotel['price_per_night'] < 0:
                    logger.warning(f"Negative price for {hotel['hotel_name']}: {hotel['price_per_night']}")
                    continue

            # Validate rating if present
            if hotel.get('star_rating') is not None:
                if not isinstance(hotel['star_rating'], (int, float)):
                    logger.warning(f"Invalid rating for {hotel['hotel_name']}: {hotel['star_rating']}")
                    continue
                if not (0 <= hotel['star_rating'] <= 5):
                    logger.warning(f"Rating out of range for {hotel['hotel_name']}: {hotel['star_rating']}")
                    continue

            valid_hotels.append(hotel)

        logger.info(f"Validated {len(valid_hotels)}/{len(data)} hotel records")
        return valid_hotels

    def _save_raw_data(self, destination, check_in, data):
        """
        Save raw scraped data to JSON file.

        Args:
            destination: City name
            check_in: Check-in date
            data: Hotel data list
        """
        try:
            RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
            filename = f"{destination.replace(' ', '_')}_{check_in}.json"
            filepath = RAW_DATA_DIR / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Raw data saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save raw data: {str(e)}")
