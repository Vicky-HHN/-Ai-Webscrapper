import time
import requests
from playwright.sync_api import sync_playwright
from config import SCRAPERAPI_KEY, SCRAPINGBEE_KEY, MAX_RETRIES, MIN_DELAY

class Fetcher:
    def __init__(self):
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
                    print(f"Trying ScraperAPI (Attempt {i+1})...")
                    # Using advanced features for bot bypass
                    payload = {
                        'api_key': self.scraperapi_key,
                        'url': url,
                        'render': 'true',
                        'premium': 'true',
                        'country_code': 'us'
                    }
                    response = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
                    if response.status_code == 200:
                        return response.text
                    elif response.status_code == 403:
                        print("ScraperAPI blocked or limit reached.")
                except Exception as e:
                    print(f"ScraperAPI attempt {i+1} failed: {e}")
                time.sleep(MIN_DELAY * (2 ** i))

        # 2. Try ScrapingBee
        if self.scrapingbee_key:
            for i in range(MAX_RETRIES):
                try:
                    print(f"Trying ScrapingBee (Attempt {i+1})...")
                    # Using stealth mode and premium proxies if possible
                    payload = {
                        'api_key': self.scrapingbee_key,
                        'url': url,
                        'render_js': 'true',
                        'stealth_proxy': 'true',
                        'premium_proxy': 'true'
                    }
                    response = requests.get('https://app.scrapingbee.com/api/v1/', params=payload, timeout=60)
                    if response.status_code == 200:
                        return response.text
                except Exception as e:
                    print(f"ScrapingBee attempt {i+1} failed: {e}")
                time.sleep(MIN_DELAY * (2 ** i))

        # 3. Local Playwright Fallback
        print("Falling back to local Playwright...")
        return self._fetch_with_playwright(url)

    def _fetch_with_playwright(self, url):
        with sync_playwright() as p:
            # Enhanced Playwright settings for bot bypass
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            # Mimic human behavior
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # Randomized scroll to trigger lazy loading and look human
                for _ in range(3):
                    page.mouse.wheel(0, 500)
                    time.sleep(0.5)

                # Wait for network idle
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except:
                    pass

                time.sleep(1)
                content = page.content()
                return content
            except Exception as e:
                print(f"Playwright fetching failed: {e}")
                return None
            finally:
                browser.close()
