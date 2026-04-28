# SmartScraper

AI-powered web scraping application that translates natural language prompts into structured data.

## Features
- **Natural Language Processing:** Interpret scraping requests using local Ollama LLMs.
- **Robust Fetching:** Multi-stage fetching with ScraperAPI, ScrapingBee, and Playwright fallback.
- **Smart Parsing:** Automatic field extraction with LLM-suggested selectors and fallback heuristics.
- **Data Validation & Cleaning:** Ensures high-quality, deduplicated, and properly formatted output.
- **Dual Interface:** Professional CLI and an interactive Streamlit dashboard.

## Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) installed and running.
- Pull the default model: `ollama pull llama3`

## Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
3. Set up environment variables:
   Copy `.env.example` to `.env` and fill in your API keys.
   ```bash
   cp .env.example .env
   ```

## Usage

### CLI
Run the scraper directly from your terminal:
```bash
python main.py scrape --prompt "Scrape the product name, price, and rating of the iPhone 15 from Amazon"
```

### Dashboard
Launch the interactive web interface:
```bash
streamlit run app_streamlit.py
# OR
python main.py dashboard
```

## Example Prompts
- "Scrape the title and price of the top 10 books from books.toscrape.com"
- "Extract news headlines and their links from news.ycombinator.com"
- "Get the latest smartphone names and prices from an e-commerce site"

## Architecture
- `core/llm_agent.py`: Ollama integration.
- `core/fetcher.py`: ScraperAPI / ScrapingBee / Playwright orchestration.
- `core/parser.py`: BeautifulSoup field extraction.
- `core/validator.py`: Content and data validation.
- `core/cleaner.py`: Data cleaning and type enforcement.
- `core/exporter.py`: JSON and CSV export logic.
- `core/scraper.py`: The main scraping pipeline.
