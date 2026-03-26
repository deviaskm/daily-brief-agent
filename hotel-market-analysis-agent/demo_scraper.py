"""Demonstration script showing the hotel scraper in action."""

import logging
from src.scraper.hotel_scraper import HotelScraper
from src.scraper.utils import normalize_price, parse_date
from src.agent.agent import HotelMarketAnalysisAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_utilities():
    """Demonstrate utility functions."""
    logger.info("=" * 60)
    logger.info("DEMO 1: Utility Functions")
    logger.info("=" * 60)

    # Test price normalization
    prices = ['$159.99', '€120.50', '£99.99', '$1,234.56', '₹5,000']
    logger.info("Testing normalize_price():")
    for price in prices:
        normalized = normalize_price(price)
        logger.info(f"  {price:15} → {normalized}")

    # Test date parsing
    logger.info("\nTesting parse_date():")
    dates = ['2024-06-15', '06/15/2024', 'June 15, 2024', '15/06/2024']
    for date_str in dates:
        parsed = parse_date(date_str)
        logger.info(f"  {date_str:20} → {parsed}")


def demo_scraper_validation():
    """Demonstrate data validation."""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 2: Data Validation")
    logger.info("=" * 60)

    scraper = HotelScraper()

    # Valid hotel data
    valid_hotels = [
        {
            'destination': 'New York',
            'check_in': '2024-06-15',
            'check_out': '2024-06-18',
            'hotel_name': 'Grand Hotel',
            'address': '123 Main St, New York, NY',
            'price_per_night': 159.99,
            'currency': 'USD',
            'star_rating': 4.5,
            'review_count': 250,
            'available': True,
            'url': 'https://example.com/grand-hotel',
            'scraped_at': '2024-01-10T12:00:00',
        },
        {
            'destination': 'New York',
            'check_in': '2024-06-15',
            'check_out': '2024-06-18',
            'hotel_name': 'Budget Inn',
            'address': '456 Oak Ave, New York, NY',
            'price_per_night': 79.99,
            'currency': 'USD',
            'star_rating': 3.2,
            'review_count': 120,
            'available': True,
            'url': 'https://example.com/budget-inn',
            'scraped_at': '2024-01-10T12:00:00',
        },
    ]

    logger.info(f"Validating {len(valid_hotels)} hotels...")
    validated = scraper.validate_data(valid_hotels)
    logger.info(f"✓ Validation result: {len(validated)}/{len(valid_hotels)} valid hotels")

    for hotel in validated:
        logger.info(f"  • {hotel['hotel_name']}: ${hotel['price_per_night']}/night (⭐ {hotel['star_rating']})")

    # Invalid hotel data (missing required field)
    logger.info("\nTesting validation with invalid data...")
    invalid_hotels = [
        {
            'destination': 'New York',
            'check_in': '2024-06-15',
            'check_out': '2024-06-18',
            # Missing hotel_name - required field
            'price_per_night': 99.99,
        },
        {
            'destination': 'New York',
            'check_in': '2024-06-15',
            'check_out': '2024-06-18',
            'hotel_name': 'Luxury Suite',
            'price_per_night': -50.0,  # Invalid: negative price
        },
        {
            'destination': 'New York',
            'check_in': '2024-06-15',
            'check_out': '2024-06-18',
            'hotel_name': 'Bad Rating Hotel',
            'price_per_night': 99.99,
            'star_rating': 6.5,  # Invalid: rating > 5
        },
    ]

    validated_invalid = scraper.validate_data(invalid_hotels)
    logger.info(f"✓ Invalid data rejected: {len(validated_invalid)}/{len(invalid_hotels)} passed validation")


def demo_url_building():
    """Demonstrate Google Hotels URL construction."""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 3: Google Hotels URL Construction")
    logger.info("=" * 60)

    scraper = HotelScraper()

    destinations = [
        ('New York', '2024-06-15', '2024-06-18'),
        ('Los Angeles', '2024-07-01', '2024-07-05'),
        ('Miami', '2024-08-10', '2024-08-15'),
    ]

    for dest, check_in, check_out in destinations:
        url = scraper._build_google_hotels_url(dest, check_in, check_out)
        logger.info(f"\nDestination: {dest}")
        logger.info(f"Check-in: {check_in}, Check-out: {check_out}")
        logger.info(f"URL: {url[:80]}...")


def demo_full_pipeline():
    """Demonstrate full analysis pipeline."""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 4: Full Analysis Pipeline")
    logger.info("=" * 60)

    agent = HotelMarketAnalysisAgent()

    logger.info("Running analysis for New York (June 15-18, 2024)...")
    logger.info("Note: Actual Google Hotels scraping requires Selenium WebDriver setup")
    logger.info("      In production, this would scrape real-time data from Google Hotels")

    result = agent.run_analysis('New York', '2024-06-15', '2024-06-18')

    if result:
        logger.info("\n✓ Pipeline completed successfully!")
        logger.info(f"  Hotels scraped: {result.get('hotels_scraped', 0)}")
        logger.info(f"  Destination: {result.get('destination')}")
        logger.info(f"  Analysis keys: {list(result.get('analysis', {}).keys())}")
    else:
        logger.info("\n✓ Pipeline executed (no live data - scraper requires Selenium)")
        logger.info("  To use with real Google Hotels data:")
        logger.info("  1. Install ChromeDriver: https://chromedriver.chromium.org/")
        logger.info("  2. Ensure Chrome/Chromium browser is installed")
        logger.info("  3. Run: python -c \"from src.agent.agent import HotelMarketAnalysisAgent; ...")


def main():
    """Run all demonstrations."""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 58 + "║")
    logger.info("║" + "  HOTEL MARKET ANALYSIS AGENT - DEMO".center(58) + "║")
    logger.info("║" + " " * 58 + "║")
    logger.info("╚" + "=" * 58 + "╝")

    try:
        demo_utilities()
        demo_scraper_validation()
        demo_url_building()
        demo_full_pipeline()

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during demonstration: {str(e)}", exc_info=True)


if __name__ == '__main__':
    main()
