from core.llm_agent import LLMAgent
from core.fetcher import Fetcher
from core.parser import Parser
from core.validator import Validator
from core.cleaner import Cleaner
from core.exporter import Exporter
import time

class ScraperOrchestrator:
    def __init__(self):
        self.llm = LLMAgent()
        self.fetcher = Fetcher()
        self.validator = Validator()
        self.cleaner = Cleaner()
        self.exporter = Exporter()

    def run(self, prompt, status_callback=None):
        """
        Executes the full multi-page scraping pipeline.
        """
        def report(msg):
            print(msg)
            if status_callback:
                status_callback(msg)

        # 1. Interpret prompt
        report(f"🔍 Analyzing prompt with AI...")
        interpretation = self.llm.interpret_prompt(prompt)
        base_url = interpretation.get('url')
        fields = interpretation.get('fields')
        selectors = interpretation.get('selectors')
        pagination = interpretation.get('pagination', {})
        max_pages = int(pagination.get('max_pages', 1))

        if not base_url:
            raise ValueError("Could not identify target URL from prompt.")

        all_unique_records = []
        current_url = base_url

        for page_num in range(1, max_pages + 1):
            report(f"🚀 Processing Page {page_num}/{max_pages}...")

            # 2. Fetch page
            report(f"🌐 Fetching: {current_url}")
            html = self.fetcher.fetch(current_url)
            if not html:
                report(f"⚠️ Failed to fetch page {page_num}. Stopping.")
                break

            # 3. Validate page
            report("🛡️ Validating page authenticity...")
            is_valid_page, reason = self.validator.validate_page(html, current_url)
            if not is_valid_page:
                report(f"⚠️ Page validation failed: {reason}. Skipping page.")
                break

            # 4. Parse fields
            report(f"🏗️ Extracting {len(fields)} fields...")
            raw_records = Parser.parse(html, fields, selectors)
            if not raw_records:
                 report("No records found on this page.")
            else:
                # 5. Clean and Validate Data
                report(f"🧹 Cleaning and validating {len(raw_records)} records...")
                cleaned_records = [self.cleaner.clean_record(r) for r in raw_records]
                valid_records = self.validator.validate_data(cleaned_records)
                all_unique_records.extend(valid_records)

            # 6. Pagination Logic: Find next URL
            if page_num < max_pages:
                next_url = self._get_next_url(current_url, html, pagination, page_num + 1)
                if next_url and next_url != current_url:
                    current_url = next_url
                    report(f"🔗 Found next page: {current_url}")
                    time.sleep(2) # Respect delay between pages
                else:
                    report("🏁 No more pages found.")
                    break

        # Deduplicate total results
        unique_records = self.validator.deduplicate(all_unique_records)

        if not unique_records:
            print("No valid records remaining after cleaning and validation.")
            return None

        # 7. LLM Final Validation
        report("🧠 Performing final LLM data validation...")
        validation_result = self.llm.validate_data(unique_records, prompt)
        if not validation_result.get('is_valid'):
            report(f"🧠 LLM Warning: {', '.join(validation_result.get('anomalies', []))}")

        # 8. Export
        report("💾 Exporting results...")
        metadata = {
            "source_url": base_url,
            "user_prompt": prompt,
            "fields_extracted": fields,
            "pages_scraped": page_num
        }
        json_path, csv_path = self.exporter.export(unique_records, metadata)

        return {
            "records": unique_records,
            "json_path": json_path,
            "csv_path": csv_path,
            "interpretation": interpretation
        }

    def _get_next_url(self, current_url, html, pagination, next_page_num):
        """
        Determines the URL of the next page.
        """
        ptype = pagination.get('type')

        if ptype == 'url_parameter':
            param = pagination.get('parameter_name', 'page')
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            u = urlparse(current_url)
            query = parse_qs(u.query)
            query[param] = [str(next_page_num)]
            new_query = urlencode(query, doseq=True)
            return urlunparse(u._replace(query=new_query))

        elif ptype == 'selector':
            selector = pagination.get('next_selector')
            if selector:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'lxml')
                next_tag = soup.select_one(selector)
                if next_tag and next_tag.get('href'):
                    href = next_tag['href']
                    if href.startswith('http'):
                        return href
                    else:
                        from urllib.parse import urljoin
                        return urljoin(current_url, href)

        return None
