import re

class Cleaner:
    @staticmethod
    def clean_record(record):
        """
        Cleans and formats a single record.
        """
        cleaned = {}
        for key, value in record.items():
            if value is None:
                cleaned[key] = None
                continue

            # Convert to string and strip
            val_str = str(value).strip()

            # Remove HTML tags if any
            val_str = re.sub(r'<[^>]+>', '', val_str)

            # Detect field type and clean accordingly
            if "price" in key.lower():
                cleaned[key] = Cleaner.clean_price(val_str)
            elif "rating" in key.lower():
                cleaned[key] = Cleaner.clean_rating(val_str)
            else:
                cleaned[key] = val_str

        return cleaned

    @staticmethod
    def clean_price(value):
        """
        Extracts float from price string.
        """
        try:
            # Remove currency symbols and commas
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", value.replace(',', ''))
            return float(nums[0]) if nums else None
        except:
            return None

    @staticmethod
    def clean_rating(value):
        """
        Extracts float from rating string and ensures it's between 0-5.
        """
        try:
            # Handle cases like "4.5/5" or "90/100"
            if "/" in value:
                parts = value.split("/")
                nums_numerator = re.findall(r"[-+]?\d*\.\d+|\d+", parts[0])
                nums_denominator = re.findall(r"[-+]?\d*\.\d+|\d+", parts[1])
                if nums_numerator and nums_denominator:
                    numerator = float(nums_numerator[0])
                    denominator = float(nums_denominator[0])
                    if denominator != 0:
                        # Normalize to 5-point scale
                        return round((numerator / denominator) * 5, 2)

            nums = re.findall(r"[-+]?\d*\.\d+|\d+", value)
            if nums:
                rating = float(nums[0])
                # Cap to 5.0 if it's already on a 5-point scale
                return min(max(rating, 0.0), 5.0)
            return None
        except:
            return None
