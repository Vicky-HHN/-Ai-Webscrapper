import json
import csv
import datetime
import pandas as pd
from config import OUTPUT_DIR

class Exporter:
    @staticmethod
    def export(data, metadata):
        """
        Exports data to JSON and CSV with metadata.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        # Sanitize filename from source_url or prompt
        site_name = metadata.get("source_url", "scrape").split("//")[-1].split(".")[0]
        filename_base = f"{site_name}_{timestamp}"

        json_path = OUTPUT_DIR / f"{filename_base}.json"
        csv_path = OUTPUT_DIR / f"{filename_base}.csv"
        meta_path = OUTPUT_DIR / f"{filename_base}_metadata.txt"

        # 1. Save JSON
        output_json = {
            "metadata": {
                "source_url": metadata.get("source_url"),
                "scraped_at": timestamp,
                "user_prompt": metadata.get("user_prompt"),
                "fields_extracted": metadata.get("fields_extracted"),
                "total_records": len(data)
            },
            "records": data
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_json, f, indent=4, ensure_ascii=False)

        # 2. Save CSV
        if data:
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')

        # 3. Save Metadata TXT
        with open(meta_path, 'w', encoding='utf-8') as f:
            f.write(f"Scrape Session Metadata\n")
            f.write(f"=======================\n")
            f.write(f"Source URL: {metadata.get('source_url')}\n")
            f.write(f"Scraped At: {timestamp}\n")
            f.write(f"User Prompt: {metadata.get('user_prompt')}\n")
            f.write(f"Fields Extracted: {', '.join(metadata.get('fields_extracted', []))}\n")
            f.write(f"Total Records: {len(data)}\n")

        return str(json_path), str(csv_path)
