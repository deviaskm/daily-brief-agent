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
        # Scrape data
        raw_data = self.scraper.scrape_hotels(destination, check_in, check_out)

        # Analyze market
        analysis = self.analyzer.calculate_statistics()
        analysis.update(self.analyzer.identify_trends())

        # Generate report
        report = self.reporter.generate_executive_summary()

        return report
