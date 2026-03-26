"""Main entry point for hotel market analysis agent."""

import logging
import sys
from pathlib import Path

from src.agent.agent import HotelMarketAnalysisAgent
from src.config.settings import LOG_LEVEL, LOG_FILE

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function."""
    try:
        # Initialize agent
        agent = HotelMarketAnalysisAgent()

        # Example: Run analysis for a destination
        logger.info("Starting hotel market analysis...")
        report = agent.run_analysis(
            destination="New York",
            check_in="2024-06-01",
            check_out="2024-06-07"
        )

        logger.info("Market analysis completed successfully")
        return report

    except Exception as e:
        logger.error(f"Error during market analysis: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
