"""Main agent orchestration."""

from src.scraper.hotel_scraper import HotelScraper
from src.analyzer.market_analyzer import MarketAnalyzer
from src.reporter.report_generator import ReportGenerator


class HotelMarketAnalysisAgent:
    """Main agent that orchestrates data collection, analysis, and reporting."""

    def __init__(self, config=None):
        """Initialize agent with configuration."""
        self.config = config
        self.scraper = HotelScraper(config)
        self.analyzer = MarketAnalyzer()
        self.reporter = ReportGenerator()

    def run_analysis(self, destination, check_in, check_out):
        """
        Run complete market analysis pipeline.

        Args:
            destination: Target hotel destination
            check_in: Check-in date
            check_out: Check-out date

        Returns:
            Generated report
        """
        import logging
        logger = logging.getLogger(__name__)

        # Scrape data
        logger.info(f"Scraping hotel data for {destination}")
        raw_data = self.scraper.scrape_hotels(destination, check_in, check_out)

        if not raw_data:
            logger.warning(f"No hotel data scraped for {destination}")
            return None

        logger.info(f"Successfully scraped {len(raw_data)} hotels")

        # Analyze market
        logger.info("Running market analysis")
        self.analyzer.data = raw_data
        analysis = self.analyzer.calculate_statistics() or {}
        trends = self.analyzer.identify_trends() or {}
        analysis.update(trends)

        # Generate report
        logger.info("Generating executive report")
        self.reporter.analysis_results = analysis
        report = self.reporter.generate_executive_summary()

        logger.info("Analysis pipeline completed successfully")
        return {
            'destination': destination,
            'check_in': check_in,
            'check_out': check_out,
            'hotels_scraped': len(raw_data),
            'analysis': analysis,
            'report': report,
        }
