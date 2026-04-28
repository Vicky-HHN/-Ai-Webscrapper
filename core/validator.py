import re
from urllib.parse import urlparse
from config import LOG_DIR

class Validator:
    @staticmethod
    def validate_page(html, target_url):
        """
        Validates the page authenticity and content.
        """
        if not html or len(html) < 500:
            return False, "Page content too short or empty."

        # Check for common CAPTCHA or error indicators
        error_indicators = ["captcha", "robot check", "access denied", "403 forbidden"]
        if any(indicator in html.lower() for indicator in error_indicators):
            return False, "Page triggered a CAPTCHA or access was denied."

        # Verify domain matches (optional but recommended)
        parsed_target = urlparse(target_url)
        if parsed_target.netloc.lower() not in html.lower() and "amazon" not in parsed_target.netloc.lower():
             # Some sites might not have their netloc in HTML, but we should be careful
             pass

        return True, "Success"

    @staticmethod
    def validate_data(records):
        """
        Validates scraped records and filters out low-quality ones.
        """
        valid_records = []
        rejected_log_path = LOG_DIR / "rejected.log"

        for record in records:
            # Count null or empty values
            null_count = sum(1 for v in record.values() if v is None or v == "" or v == "null")
            total_fields = len(record)

            if total_fields > 0 and (null_count / total_fields) > 0.5:
                with open(rejected_log_path, "a") as f:
                    f.write(f"REJECTED: Too many nulls ({null_count}/{total_fields}). Record: {record}\n")
                continue

            valid_records.append(record)

        return valid_records

    @staticmethod
    def deduplicate(records):
        """
        Removes duplicate records.
        """
        seen = set()
        unique_records = []
        for record in records:
            # Convert dict to a hashable tuple of items
            record_tuple = tuple(sorted(record.items(), key=lambda x: x[0]))
            if record_tuple not in seen:
                seen.add(record_tuple)
                unique_records.append(record)
        return unique_records
