from bs4 import BeautifulSoup

class Parser:
    @staticmethod
    def parse(html, fields, selectors_hints=None):
        """
        Parses HTML using BeautifulSoup and LLM hints.
        """
        soup = BeautifulSoup(html, 'lxml')
        records = []

        # Attempt to find repeating elements (items) if it's a list page
        # Heuristic: find a common container for items
        containers = Parser.find_item_containers(soup)

        if containers:
            for container in containers:
                record = {}
                for field in fields:
                    selector = selectors_hints.get(field) if selectors_hints else None
                    record[field] = Parser.extract_field(container, field, selector)
                records.append(record)
        else:
            # Single item page or couldn't find containers
            record = {}
            for field in fields:
                selector = selectors_hints.get(field) if selectors_hints else None
                record[field] = Parser.extract_field(soup, field, selector)
            records.append(record)

        return records

    @staticmethod
    def extract_field(element, field_name, selector=None):
        """
        Extracts a single field from an element.
        """
        if selector:
            try:
                found = element.select_one(selector)
                if found:
                    return found.get_text(strip=True)
            except:
                pass

        # Fallback heuristics
        field_lower = field_name.lower()

        # Try finding by class name or id containing the field name
        fallbacks = element.find_all(attrs={"class": lambda x: x and field_lower in x.lower()})
        if not fallbacks:
             fallbacks = element.find_all(attrs={"id": lambda x: x and field_lower in x.lower()})

        if fallbacks:
            return fallbacks[0].get_text(strip=True)

        # Further fallbacks for specific common fields
        if "price" in field_lower:
            price_elem = element.find(string=re.compile(r'\$|£|€|₹'))
            if price_elem:
                return price_elem.parent.get_text(strip=True)

        return None

    @staticmethod
    def find_item_containers(soup):
        """
        Heuristic to find repeating item containers (e.g., search results).
        """
        # Look for common tags used for lists
        for tag in ['div', 'li', 'article', 'section']:
            items = soup.find_all(tag, class_=True)
            if not items: continue

            # Count class frequencies
            classes = {}
            for item in items:
                cls = tuple(sorted(item.get('class')))
                classes[cls] = classes.get(cls, 0) + 1

            # If many elements share the same class, it's likely a container
            for cls, count in classes.items():
                if count > 3: # Arbitrary threshold
                    return soup.find_all(tag, class_=list(cls))

        return []

import re # needed for extract_field fallback
