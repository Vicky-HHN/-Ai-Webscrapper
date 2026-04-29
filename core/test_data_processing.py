import pytest
import os
import json
from unittest.mock import patch
from core.validator import Validator
from core.cleaner import Cleaner
from core.parser import Parser
from core.exporter import Exporter
from pathlib import Path

def test_validator_page():
    html = "<html><body>This is a real page with enough content to pass the validator. It should be at least 500 characters long. " * 10
    is_valid, reason = Validator.validate_page(html, "https://example.com")
    assert is_valid == True

def test_validator_data_rejection(tmp_path):
    records = [
        {"name": "Valid", "price": "10"},
        {"name": None, "price": None} # 100% null
    ]
    # Mock LOG_DIR
    with patch('core.validator.LOG_DIR', tmp_path):
        valid = Validator.validate_data(records)
        assert len(valid) == 1
        assert valid[0]["name"] == "Valid"

def test_cleaner_price():
    assert Cleaner.clean_price("$1,234.56") == 1234.56
    assert Cleaner.clean_price("Price: 50.00") == 50.0

def test_cleaner_rating():
    assert Cleaner.clean_rating("4.5 out of 5 stars") == 4.5
    assert Cleaner.clean_rating("9.0") == 5.0 # Maxed to 5.0

def test_parser_basic():
    html = "<html><div class='product'><h1 class='title'>iPhone</h1><span class='price'>$999</span></div></html>"
    fields = ["title", "price"]
    selectors = {"title": "h1.title", "price": "span.price"}
    records = Parser.parse(html, fields, selectors)
    assert len(records) > 0
    assert records[0]["title"] == "iPhone"

def test_exporter(tmp_path):
    # Setup tmp_path as the output dir for this test
    with patch('core.exporter.OUTPUT_DIR', tmp_path):
        data = [{"name": "Test", "price": 100.0}]
        metadata = {
            "source_url": "https://test.com",
            "user_prompt": "Test Prompt",
            "fields_extracted": ["name", "price"]
        }
        json_path, csv_path = Exporter.export(data, metadata)

        assert os.path.exists(json_path)
        assert os.path.exists(csv_path)

        with open(json_path, 'r') as f:
            saved_json = json.load(f)
            assert saved_json["metadata"]["total_records"] == 1
            assert saved_json["records"][0]["name"] == "Test"

from unittest.mock import patch
import re
