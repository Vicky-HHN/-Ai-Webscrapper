import time
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth
from config import SCRAPERAPI_KEY, SCRAPINGBEE_KEY, MAX_RETRIES, MIN_DELAY
from core.logger import setup_logger

class Fetcher:
    def __init__(self):
        self.logger = setup_logger("fetcher")
        self.scraperapi_key = SCRAPERAPI_KEY
        self.scrapingbee_key = SCRAPINGBEE_KEY

    def fetch(self, url):
        """
        Orchestrates fetching: ScraperAPI -> ScrapingBee -> Playwright
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/"
        }

        # 1. Try ScraperAPI
        if self.scraperapi_key:
            for i in range(MAX_RETRIES):
                try:
                    self.logger.info(f"Trying ScraperAPI (Attempt {i+1})...")
                    # Using advanced features for bot bypass
                    payload = {
                        'api_key': self.scraperapi_key,
                        'url': url,
                        'render': 'true',
                        'premium': 'true',
                        'country_code': 'us',
                        'keep_headers': 'true'
                    }
                    response = requests.get('http://api.scraperapi.com', params=payload, headers=headers, timeout=60)
                    if response.status_code == 200:
                        return response.text
                    elif response.status_code == 403:
                        self.logger.warning("ScraperAPI blocked or limit reached.")
                except Exception as e:
                    self.logger.error(f"ScraperAPI attempt {i+1} failed: {e}")
                time.sleep(MIN_DELAY * (2 ** i))

        # 2. Try ScrapingBee
        if self.scrapingbee_key:
            for i in range(MAX_RETRIES):
                try:
                    self.logger.info(f"Trying ScrapingBee (Attempt {i+1})...")
                    # Using stealth mode and premium proxies if possible
                    payload = {
                        'api_key': self.scrapingbee_key,
                        'url': url,
                        'render_js': 'true',
                        'stealth_proxy': 'true',
                        'premium_proxy': 'true'
                    }
                    # ScrapingBee uses headers if passed
                    response = requests.get('https://app.scrapingbee.com/api/v1/', params=payload, headers=headers, timeout=60)
                    if response.status_code == 200:
                        return response.text
                except Exception as e:
                    self.logger.error(f"ScrapingBee attempt {i+1} failed: {e}")
                time.sleep(MIN_DELAY * (2 ** i))

        # 3. Local Playwright Fallback
        self.logger.info("Falling back to local Playwright...")
        # Add a longer delay for playwright to ensure things load
        time.sleep(3)
        return self._fetch_with_playwright(url)

    def _fetch_with_playwright(self, url):
        with sync_playwright() as p:
            # Enhanced Playwright settings for bot bypass
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True
            )
            page = context.new_page()

            # Apply stealth
            stealth(page)

            # Mimic human behavior
            try:
                # Add randomized delay before navigation
                time.sleep(1)
                page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # Randomized scroll to trigger lazy loading and look human
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, window.innerHeight)")
                    time.sleep(0.8)

                # Wait for network idle
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except:
                    pass

                time.sleep(1)
                content = page.content()
                return content
            except Exception as e:
                self.logger.error(f"Playwright fetching failed: {e}")
                return None
            finally:
                browser.close()
