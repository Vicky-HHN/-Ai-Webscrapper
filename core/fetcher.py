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
        # 1. Try ScraperAPI
        if self.scraperapi_key:
            for i in range(MAX_RETRIES):
                try:
                    print(f"Trying ScraperAPI (Attempt {i+1})...")
                    payload = {'api_key': self.scraperapi_key, 'url': url, 'render': 'true'}
                    response = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
                    if response.status_code == 200:
                        return response.text
                except Exception as e:
                    print(f"ScraperAPI attempt {i+1} failed: {e}")
                time.sleep(MIN_DELAY * (2 ** i))

        # 2. Try ScrapingBee
        if self.scrapingbee_key:
            for i in range(MAX_RETRIES):
                try:
                    print(f"Trying ScrapingBee (Attempt {i+1})...")
                    payload = {'api_key': self.scrapingbee_key, 'url': url, 'render_js': 'true'}
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
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
                # Wait a bit more for JS rendering if needed
                time.sleep(2)
                content = page.content()
                return content
            except Exception as e:
                print(f"Playwright fetching failed: {e}")
                return None
            finally:
                browser.close()
