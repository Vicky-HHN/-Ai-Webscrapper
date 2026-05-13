import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
SCRAPINGBEE_KEY = os.getenv("SCRAPINGBEE_KEY")

# Ollama Config
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "outputs")
LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Scraping settings
MIN_DELAY = 2  # seconds
MAX_RETRIES = 3
