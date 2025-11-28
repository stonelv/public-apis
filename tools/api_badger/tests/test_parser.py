# -*- coding: utf-8 -*-

import os
import tempfile
import pytest
from typing import Dict, List

from ..parser import APIParser, parse_apis, generate_api_badges, generate_all_badges


@pytest.fixture
def sample_md_content():
    return """# Test APIs

## Index
* [Test Category](#test-category)

### Test Category
API | Description | Auth | HTTPS | CORS
|:---|:---|:---|:---|:---|
| [Test API 1](https://example.com/api1) | Test description 1 | No | Yes | Unknown |
| [Test API 2](https://example.com/api2) | Test description 2 | `apiKey` | No | Yes |
| [Test API 3](https://example.com/api3) | Test description 3 | `OAuth` | Yes | No |
| [Test API 4](https://example.com/api4) | | No | Yes | Yes |
"""


@pytest.fixture
def sample_api_data():
    return {
        'name': 'Test API',
        'description': 'Test description',
        'auth': 'no',
        'https': 'yes',
        'cors': 'unknown',
        'link': 'https://example.com',
        'category': 'Test Category'
    }


@pytest.fixture
def sample_categories():
    return {
        'Test Category': [
            {
                'name': 'Test API 1',
                'description': 'Test description 1',
                'auth': 'no',
                'https': 'yes',
                'cors': 'unknown',
                'link': 'https://example.com/api1',
                'category': 'Test Category'
            },
            {
                'name': 'Test API 2',
                'description': 'Test description 2',
                'auth': '`apikey`',
                'https': 'no',
                'cors': 'yes',
                'link': 'https://example.com/api2',
                'category': 'Test Category'
            }
        ]
    }


def test_parse_md_file(sample_md_content):
    # Create a temporary file with sample content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(sample_md_content)
        temp_file = f.name
    
    try:
        parser = APIParser()
        parser.parse_md_file(temp_file)
        
        # Check if categories were parsed correctly
        assert 'Test Category' in parser.categories
        assert len(parser.categories['Test Category']) == 4
        
        # Check first API
        api1 = parser.categories['Test Category'][0]
        assert api1['name'] == 'Test API 1'
        assert api1['description'] == 'Test description 1'
        assert api1['auth'] == 'no'
        assert api1['https'] == 'yes'
        assert api1['cors'] == 'unknown'
        assert api1['link'] == 'https://example.com/api1'
        assert api1['category'] == 'Test Category'
        
        # Check API with empty description
        api4 = parser.categories['Test Category'][3]
        assert api4['description'] == 'empty'
        
    finally:
        os.unlink(temp_file)


def test_parse_md_file_skip_invalid(sample_md_content):
    # Create a temporary file with sample content and an invalid entry
    invalid_content = sample_md_content + "| Invalid API | Missing columns | No |\n"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(invalid_content)
        temp_file = f.name
    
    try:
        parser = APIParser(skip_invalid=True)
        parser.parse_md_file(temp_file)
        
        # Check if invalid entry was skipped
        assert len(parser.categories['Test Category']) == 4
        
    finally:
        os.unlink(temp_file)


def test_generate_badges(sample_api_data):
    badges = generate_api_badges(sample_api_data)
    
    assert 'https' in badges
    assert 'auth' in badges
    assert 'cors' in badges
    
    # Check badge URLs are valid
    assert badges['https'].startswith('https://img.shields.io/badge/HTTPS-yes-brightgreen')
    assert badges['auth'].startswith('https://img.shields.io/badge/Auth-no-lightgrey')
    assert badges['cors'].startswith('https://img.shields.io/badge/CORS-unknown-orange')


def test_generate_all_badges(sample_categories):
    categories_with_badges = generate_all_badges(sample_categories)
    
    # Check if all APIs have badges
    for category, apis in categories_with_badges.items():
        for api in apis:
            assert 'badges' in api
            assert 'https' in api['badges']
            assert 'auth' in api['badges']
            assert 'cors' in api['badges']


def test_color_mapping():
    parser = APIParser()
    
    # Test valid colors
    assert parser._create_badge('HTTPS', 'yes').endswith('brightgreen')
    assert parser._create_badge('HTTPS', 'no').endswith('lightgrey')
    assert parser._create_badge('CORS', 'unknown').endswith('orange')
    assert parser._create_badge('Auth', 'empty').endswith('red')
    
    # Test case insensitivity
    assert parser._create_badge('HTTPS', 'YES').endswith('brightgreen')
    assert parser._create_badge('HTTPS', 'NO').endswith('lightgrey')


def test_parse_apis_function(sample_md_content):
    # Create a temporary file with sample content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(sample_md_content)
        temp_file = f.name
    
    try:
        categories = parse_apis(temp_file)
        
        # Check if function returns correct data structure
        assert isinstance(categories, dict)
        assert 'Test Category' in categories
        assert len(categories['Test Category']) == 4
        
    finally:
        os.unlink(temp_file)
