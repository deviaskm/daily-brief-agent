"""Tests for the scraper module."""

import pytest
from datetime import datetime
from src.scraper.hotel_scraper import HotelScraper
from src.scraper.utils import normalize_price, parse_date, retry_request


class TestNormalizePrice:
    """Test cases for normalize_price utility function."""

    def test_normalize_usd_price(self):
        """Test USD price normalization."""
        assert normalize_price('$159.99') == 159.99
        assert normalize_price('$100') == 100.0

    def test_normalize_euro_price(self):
        """Test EUR price normalization."""
        assert normalize_price('€120.50') == 120.50
        assert normalize_price('€1.000,50') == 1000.50

    def test_normalize_pound_price(self):
        """Test GBP price normalization."""
        assert normalize_price('£99.99') == 99.99

    def test_normalize_numeric_input(self):
        """Test numeric input."""
        assert normalize_price(159.99) == 159.99
        assert normalize_price(100) == 100.0

    def test_normalize_price_with_commas(self):
        """Test price with thousand separators."""
        assert normalize_price('$1,234.56') == 1234.56
        assert normalize_price('$10,000') == 10000.0

    def test_normalize_price_invalid(self):
        """Test invalid price input."""
        with pytest.raises(ValueError):
            normalize_price('invalid')
        with pytest.raises(ValueError):
            normalize_price(None)


class TestParseDate:
    """Test cases for parse_date utility function."""

    def test_parse_iso_format(self):
        """Test ISO format date."""
        assert parse_date('2024-06-15') == '2024-06-15'

    def test_parse_us_format(self):
        """Test US format date."""
        result = parse_date('06/15/2024')
        assert result == '2024-06-15'

    def test_parse_long_format(self):
        """Test long format date."""
        result = parse_date('June 15, 2024')
        assert result == '2024-06-15'

    def test_parse_european_format(self):
        """Test European format date."""
        result = parse_date('15/06/2024')
        assert result == '2024-06-15'

    def test_parse_datetime_object(self):
        """Test datetime object input."""
        dt = datetime(2024, 6, 15)
        assert parse_date(dt) == '2024-06-15'

    def test_parse_date_invalid(self):
        """Test invalid date input."""
        with pytest.raises(ValueError):
            parse_date('invalid-date')
        with pytest.raises(ValueError):
            parse_date(None)


class TestRetryRequest:
    """Test cases for retry_request decorator."""

    def test_retry_successful_first_attempt(self):
        """Test successful call on first attempt."""
        call_count = 0

        @retry_request
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_fails_then_succeeds(self):
        """Test retry after initial failure."""
        call_count = 0

        @retry_request
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Failed")
            return "success"

        result = failing_func()
        assert result == "success"
        assert call_count == 2

    def test_retry_all_attempts_fail(self):
        """Test all retry attempts fail."""
        call_count = 0

        @retry_request
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            always_fails()
        assert call_count == 3  # Default max_retries


class TestHotelScraper:
    """Test cases for HotelScraper."""

    @pytest.fixture
    def scraper(self):
        """Fixture to create scraper instance."""
        return HotelScraper()

    def test_initialization(self, scraper):
        """Test scraper initialization."""
        assert scraper is not None
        assert scraper.timeout == 30
        assert scraper.rate_limit_delay == 1.0
        assert scraper.driver is None

    def test_initialization_with_custom_config(self):
        """Test scraper initialization with custom config."""
        custom_config = {
            'timeout': 60,
            'max_retries': 5,
            'rate_limit_delay': 2.0,
        }
        scraper = HotelScraper(config=custom_config)
        assert scraper.timeout == 60
        assert scraper.rate_limit_delay == 2.0

    def test_validate_empty_data(self, scraper):
        """Test validation with empty data."""
        result = scraper.validate_data([])
        assert result == []

    def test_validate_invalid_data_type(self, scraper):
        """Test validation with non-list data."""
        result = scraper.validate_data("not a list")
        assert result == []

    def test_validate_data_missing_required_fields(self, scraper):
        """Test validation with missing required fields."""
        invalid_hotels = [
            {'hotel_name': 'Hotel A'},  # Missing destination, check_in, check_out
            {'destination': 'New York'},  # Missing hotel_name, etc.
        ]
        result = scraper.validate_data(invalid_hotels)
        assert result == []

    def test_validate_data_complete_hotel(self, scraper):
        """Test validation with complete hotel data."""
        valid_hotel = {
            'hotel_name': 'Test Hotel',
            'destination': 'New York',
            'check_in': '2024-06-15',
            'check_out': '2024-06-18',
            'price_per_night': 159.99,
            'star_rating': 4.5,
            'review_count': 150,
            'available': True,
        }
        result = scraper.validate_data([valid_hotel])
        assert len(result) == 1
        assert result[0] == valid_hotel

    def test_validate_data_invalid_price(self, scraper):
        """Test validation rejects invalid price."""
        invalid_hotel = {
            'hotel_name': 'Test Hotel',
            'destination': 'New York',
            'check_in': '2024-06-15',
            'check_out': '2024-06-18',
            'price_per_night': -100.0,  # Negative price
        }
        result = scraper.validate_data([invalid_hotel])
        assert result == []

    def test_validate_data_invalid_rating(self, scraper):
        """Test validation rejects invalid rating."""
        invalid_hotel = {
            'hotel_name': 'Test Hotel',
            'destination': 'New York',
            'check_in': '2024-06-15',
            'check_out': '2024-06-18',
            'star_rating': 6.0,  # Rating out of range
        }
        result = scraper.validate_data([invalid_hotel])
        assert result == []

    def test_build_google_hotels_url(self, scraper):
        """Test Google Hotels URL building."""
        url = scraper._build_google_hotels_url('New York', '2024-06-15', '2024-06-18')
        assert 'google.com/travel/hotels' in url
        assert 'New%20York' in url
        assert '06/15/2024' in url
        assert '06/18/2024' in url

    def test_scrape_hotels_empty_destination(self, scraper):
        """Test scraping with invalid destination returns empty list."""
        # This would require actual Selenium execution, so we test error handling
        result = scraper.scrape_hotels('', '2024-06-15', '2024-06-18')
        assert isinstance(result, list)

    def test_scrape_hotels_returns_list(self, scraper):
        """Test that scrape_hotels returns a list."""
        # Basic test - in real scenario would need mocking or real browser
        result = scraper.scrape_hotels('New York', '2024-06-15', '2024-06-18')
        assert isinstance(result, list)
