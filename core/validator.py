import re
from urllib.parse import urlparse
from config import LOG_DIR
from core.logger import setup_logger

logger = setup_logger("validator")

class Validator:
    @staticmethod
    def validate_page(html, target_url):
        """
        Validates the page authenticity and content.
        """
        if not html:
            return False, "Page content empty."

        # Check for common CAPTCHA or error indicators
        error_indicators = ["captcha", "robot check", "access denied", "403 forbidden", "unusual activity", "verify you are a human"]
        if any(indicator in html.lower() for indicator in error_indicators):
            # Special case: some pages might have "captcha" in some hidden script but still be valid.
            # But usually it's a bad sign.
            return False, f"Page triggered a CAPTCHA or access was denied (detected '{[i for i in error_indicators if i in html.lower()][0]}')."

        if len(html) < 500:
             # Soften the length check if it looks like a valid JSON or small valid page
             if html.strip().startswith('{') and html.strip().endswith('}'):
                 return True, "Success (JSON detected)"
             return False, f"Page content too short ({len(html)} chars)."

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
                msg = f"REJECTED: Too many nulls ({null_count}/{total_fields}). Record: {record}"
                logger.warning(msg)
                with open(rejected_log_path, "a") as f:
                    f.write(msg + "\n")
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
