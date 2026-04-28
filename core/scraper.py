from core.llm_agent import LLMAgent
from core.fetcher import Fetcher
from core.parser import Parser
from core.validator import Validator
from core.cleaner import Cleaner
from core.exporter import Exporter

class ScraperOrchestrator:
    def __init__(self):
        self.llm = LLMAgent()
        self.fetcher = Fetcher()
        self.validator = Validator()
        self.cleaner = Cleaner()
        self.exporter = Exporter()

    def run(self, prompt):
        """
        Executes the full scraping pipeline.
        """
        # 1. Interpret prompt
        print(f"Interpreting prompt: {prompt}")
        interpretation = self.llm.interpret_prompt(prompt)
        url = interpretation.get('url')
        fields = interpretation.get('fields')
        selectors = interpretation.get('selectors')

        if not url:
            raise ValueError("Could not identify target URL from prompt.")

        # 2. Fetch page
        print(f"Fetching page: {url}")
        html = self.fetcher.fetch(url)
        if not html:
            raise Exception(f"Failed to fetch content from {url}")

        # 3. Validate page
        is_valid_page, reason = self.validator.validate_page(html, url)
        if not is_valid_page:
            raise Exception(f"Page validation failed: {reason}")

        # 4. Parse fields
        print("Parsing content...")
        raw_records = Parser.parse(html, fields, selectors)
        if not raw_records:
             print("No records found during parsing.")
             return None

        # 5. Clean and Validate Data
        print("Cleaning and validating data...")
        cleaned_records = [self.cleaner.clean_record(r) for r in raw_records]
        valid_records = self.validator.validate_data(cleaned_records)
        unique_records = self.validator.deduplicate(valid_records)

        if not unique_records:
            print("No valid records remaining after cleaning and validation.")
            return None

        # 6. LLM Final Validation
        print("Final LLM validation...")
        validation_result = self.llm.validate_data(unique_records, prompt)
        if not validation_result.get('is_valid'):
            print(f"LLM Warning: {', '.join(validation_result.get('anomalies', []))}")

        # 7. Export
        print("Exporting data...")
        metadata = {
            "source_url": url,
            "user_prompt": prompt,
            "fields_extracted": fields
        }
        json_path, csv_path = self.exporter.export(unique_records, metadata)

        return {
            "records": unique_records,
            "json_path": json_path,
            "csv_path": csv_path,
            "interpretation": interpretation
        }
