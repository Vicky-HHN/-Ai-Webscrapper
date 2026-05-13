import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from core.logger import setup_logger

logger = setup_logger("parser")

class Parser:
    @staticmethod
    def parse(html, fields, selectors_hints=None, base_url=None, container_selector=None):
        """
        Parses HTML using BeautifulSoup and LLM hints.
        """
        soup = BeautifulSoup(html, 'lxml')
        records = []

        # Try to find JSON-LD first as it's often more reliable
        json_ld_data = Parser.extract_json_ld(soup)
        if json_ld_data:
            logger.info("Found JSON-LD data. Attempting to extract records...")
            # Simple heuristic: if it's a list of items or contains a 'itemListElement'
            items = []
            if isinstance(json_ld_data, list):
                items = json_ld_data
            elif isinstance(json_ld_data, dict):
                if 'itemListElement' in json_ld_data:
                    items = json_ld_data['itemListElement']
                elif '@graph' in json_ld_data:
                    items = json_ld_data['@graph']

            if items:
                for item in items:
                    record = {}
                    # If item is a dict, try to map fields
                    if isinstance(item, dict):
                        # Some JSON-LD items are wrapped in 'item'
                        inner_item = item.get('item', item)
                        if isinstance(inner_item, dict):
                            for field in fields:
                                # Try common JSON keys
                                val = inner_item.get(field) or inner_item.get(field.lower())
                                if not val:
                                    # Deep search for price in offers
                                    if 'price' in field.lower() and 'offers' in inner_item:
                                        offers = inner_item['offers']
                                        if isinstance(offers, dict):
                                            val = offers.get('price')
                                        elif isinstance(offers, list) and offers:
                                            val = offers[0].get('price')
                                    # Deep search for name/title
                                    elif ('title' in field.lower() or 'name' in field.lower()) and 'headline' in inner_item:
                                        val = inner_item['headline']
                                record[field] = val
                    if any(record.values()):
                        records.append(record)
                if records:
                    return records

        # 1. Identify item containers
        containers = None
        if container_selector:
            try:
                containers = soup.select(container_selector)
            except:
                pass

        if not containers:
            # Heuristic: find a common container for items
            containers = Parser.find_item_containers(soup)

        if containers:
            logger.info(f"Parsing {len(containers)} containers...")
            for container in containers:
                record = {}
                for field in fields:
                    selector = selectors_hints.get(field) if selectors_hints else None
                    val = Parser.extract_field(container, field, selector, base_url=base_url)
                    record[field] = val
                records.append(record)
        else:
            logger.info("No containers found, parsing as single item page.")
            # Single item page or couldn't find containers
            record = {}
            for field in fields:
                selector = selectors_hints.get(field) if selectors_hints else None
                val = Parser.extract_field(soup, field, selector, base_url=base_url)
                record[field] = val
            records.append(record)

        return records

    @staticmethod
    def extract_field(element, field_name, selector=None, base_url=None):
        """
        Extracts a single field from an element with attribute awareness and deep search.
        """
        field_lower = field_name.lower()
        found = None

        if selector:
            try:
                found = element.select_one(selector)
                # If selector specifically targeted an attribute but returned the element
                if found and "image" in field_lower and found.name != 'img':
                    img = found.find('img')
                    if img: found = img
            except:
                pass

        # Fallback heuristics
        if not found:
            # Try finding by class name or id containing the field name
            # We look for partial matches in class names
            found = element.find(attrs={"class": re.compile(field_lower, re.I)})
            if not found:
                 found = element.find(attrs={"id": re.compile(field_lower, re.I)})

        if not found:
            # Further fallbacks for specific common fields
            if "price" in field_lower:
                # Look for currency symbols
                price_elem = element.find(string=re.compile(r'[\$\£\€\₹]'))
                if price_elem:
                    # Search upwards for a container that likely holds the full price
                    found = price_elem.find_parent(lambda tag: len(tag.get_text()) > 1 and len(tag.get_text()) < 50)
                    if not found: found = price_elem.parent
            elif "image" in field_lower or "img" in field_lower:
                found = element.find('img')
            elif "link" in field_lower or "url" in field_lower:
                found = element.find('a')
            elif "rating" in field_lower:
                found = element.find(attrs={"class": re.compile(r'rating|star', re.I)})
                if not found:
                    found = element.find(string=re.compile(r'\d\.\d\s?(out of|/)\s?\d'))
                    if found: found = found.parent

        if not found:
            return None

        # Extract content based on field type
        if "image" in field_lower or "img" in field_lower:
            src = found.get('src') or found.get('data-src') or found.get('srcset')
            if src and base_url:
                return urljoin(base_url, src.split(' ')[0])
            return src

        if "link" in field_lower or "url" in field_lower:
            href = found.get('href')
            if href and base_url:
                return urljoin(base_url, href)
            return href

        # Default: extract text
        return found.get_text(strip=True, separator=' ')

    @staticmethod
    def extract_json_ld(soup):
        """
        Extracts JSON-LD data from the page.
        """
        try:
            script = soup.find('script', type='application/ld+json')
            if script:
                return json.loads(script.string)
        except:
            pass
        return None

    @staticmethod
    def find_item_containers(soup):
        """
        Heuristic to find repeating item containers by analyzing common classes.
        """
        candidates = []
        # Look for common tags used for lists
        for tag in ['div', 'li', 'article', 'section', 'tr']:
            elements = soup.find_all(tag, class_=True)
            if not elements: continue

            # Count frequency of individual classes
            class_counts = {}
            for el in elements:
                for cls in el.get('class', []):
                    class_counts[cls] = class_counts.get(cls, 0) + 1

            # Filter classes that appear multiple times (likely item containers)
            for cls, count in class_counts.items():
                if count >= 2:
                    # Find all elements with this class and tag
                    items = soup.find_all(tag, class_=cls)
                    # Use a score based on count and depth (prefer deeper elements for items)
                    # Also prefer items that are not in header/footer
                    score = count
                    parent_names = [p.name for p in items[0].parents]
                    if 'header' in parent_names or 'footer' in parent_names:
                        score -= 10

                    candidates.append({
                        'score': score,
                        'items': items,
                        'tag': tag,
                        'class': cls
                    })

        if not candidates:
            return []

        # Return the items of the candidate with highest score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        logger.info(f"Selected item container: {candidates[0]['tag']}.{candidates[0]['class']} (count: {len(candidates[0]['items'])})")
        return candidates[0]['items']
