# Hotel Market Analysis Agent

An intelligent agent that scrapes public hotel pricing data and generates comprehensive executive reports for market analysis.

## Features

- **Data Scraping**: Collects hotel pricing data from public sources
- **Market Analysis**: Calculates key metrics and identifies trends
- **Competitive Intelligence**: Analyzes competitor positioning and market share
- **Executive Reports**: Generates professional PDF/HTML reports with visualizations
- **Automated Pipeline**: End-to-end orchestration from data collection to reporting

## Project Structure

```
hotel-market-analysis-agent/
├── src/
│   ├── scraper/           # Web scraping modules
│   ├── analyzer/          # Market analysis engine
│   ├── reporter/          # Report generation
│   ├── agent/             # Main orchestration
│   └── config/            # Configuration management
├── data/
│   ├── raw/              # Raw scraped data
│   ├── processed/        # Processed datasets
│   └── reports/          # Generated reports
├── tests/                # Test suite
├── config/               # Configuration files
└── main.py              # Entry point
```

## Installation

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```python
from src.agent.agent import HotelMarketAnalysisAgent

agent = HotelMarketAnalysisAgent()
report = agent.run_analysis(
    destination="New York",
    check_in="2024-06-01",
    check_out="2024-06-07"
)
```

## Configuration

Edit `src/config/settings.py` to customize:
- Scraper timeouts and retry logic
- Analysis parameters
- Report formatting
- Logging levels

## Testing

```bash
pytest tests/
pytest --cov=src tests/
```

## Legal Notice

This agent scrapes only publicly available data. Ensure compliance with:
- Website terms of service
- Local data protection regulations (GDPR, CCPA, etc.)
- Robots.txt guidelines
- Rate limiting best practices

## License

MIT License
