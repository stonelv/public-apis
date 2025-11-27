#!/usr/bin/env python3
"""Unit tests for api-browser CLI tool"""

import os
import sys
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add the parent directory to Python path to allow import
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_browser import (
    parse_readme,
    filter_apis,
    is_cache_valid,
    load_cache,
    save_cache,
    create_cache_dir
)


@pytest.fixture
def sample_readme_content() -> str:
    """Sample README content for testing"""
    return """
### Animals
API | Description | Auth | HTTPS | CORS 
--- | --- | --- | --- | --- 
[Cat Facts](https://cat-fact.herokuapp.com/facts) | Daily cat facts | No | Yes | Unknown 
[Dog Facts](https://dog-api.kinduff.com/api/facts) | Random dog facts | No | Yes | Yes 

### Weather
API | Description | Auth | HTTPS | CORS 
--- | --- | --- | --- | --- 
[OpenWeatherMap](https://openweathermap.org/api) | Weather data | API Key | Yes | Yes 
"""


@pytest.fixture
def sample_apis() -> list:
    """Sample API data for testing"""
    return [
        {
            "name": "Cat Facts",
            "url": "https://cat-fact.herokuapp.com/facts",
            "description": "Daily cat facts",
            "auth": "No",
            "https": True,
            "cors": "Unknown",
            "category": "Animals"
        },
        {
            "name": "Dog Facts",
            "url": "https://dog-api.kinduff.com/api/facts",
            "description": "Random dog facts",
            "auth": "No",
            "https": True,
            "cors": "Yes",
            "category": "Animals"
        },
        {
            "name": "OpenWeatherMap",
            "url": "https://openweathermap.org/api",
            "description": "Weather data",
            "auth": "API Key",
            "https": True,
            "cors": "Yes",
            "category": "Weather"
        }
    ]


def test_parse_readme(sample_readme_content, sample_apis):
    """Test parsing README content"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(sample_readme_content)
        temp_file = f.name

    try:
        apis = parse_readme(temp_file)
        assert len(apis) == 3
        assert apis == sample_apis
    finally:
        os.unlink(temp_file)


def test_filter_apis_by_query(sample_apis):
    """Test filtering APIs by query"""
    # Test by name
    filtered = filter_apis(sample_apis, query="cat")
    assert len(filtered) == 1
    assert filtered[0]["name"] == "Cat Facts"

    # Test by description
    filtered = filter_apis(sample_apis, query="weather")
    assert len(filtered) == 1
    assert filtered[0]["name"] == "OpenWeatherMap"

    # Test by category
    filtered = filter_apis(sample_apis, query="animals")
    assert len(filtered) == 2

    # Test case insensitivity
    filtered = filter_apis(sample_apis, query="DOG")
    assert len(filtered) == 1
    assert filtered[0]["name"] == "Dog Facts"


def test_filter_apis_by_category(sample_apis):
    """Test filtering APIs by category"""
    filtered = filter_apis(sample_apis, category="Animals")
    assert len(filtered) == 2
    assert all(api["category"] == "Animals" for api in filtered)

    filtered = filter_apis(sample_apis, category="Weather")
    assert len(filtered) == 1
    assert filtered[0]["category"] == "Weather"

    # Test case insensitivity
    filtered = filter_apis(sample_apis, category="weather")
    assert len(filtered) == 1
    assert filtered[0]["category"] == "Weather"


def test_filter_apis_by_both(sample_apis):
    """Test filtering APIs by both query and category"""
    filtered = filter_apis(sample_apis, query="facts", category="Animals")
    assert len(filtered) == 2

    filtered = filter_apis(sample_apis, query="facts", category="Weather")
    assert len(filtered) == 0


def test_cache_functions(sample_apis):
    """Test cache functions"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('api_browser.CACHE_DIR', Path(tmpdir) / ".api-browser"):
            with patch('api_browser.CACHE_FILE', Path(tmpdir) / ".api-browser" / "apis_cache.json"):
                # Test create_cache_dir
                create_cache_dir()
                assert (Path(tmpdir) / ".api-browser").exists()

                # Test save_cache and load_cache
                save_cache(sample_apis)
                loaded = load_cache()
                assert loaded == sample_apis

                # Test is_cache_valid
                assert is_cache_valid() is True

                # Test cache expiration
                with patch('api_browser.CACHE_EXPIRY', -1):  # Expired immediately
                    assert is_cache_valid() is False


if __name__ == "__main__":
    pytest.main([__file__])
