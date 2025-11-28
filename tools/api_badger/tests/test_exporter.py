# -*- coding: utf-8 -*-

import os
import tempfile
import shutil
import csv
import pytest
from typing import Dict, List

from ..exporter import APIExporter, export_md_badges, export_html_page, export_to_csv
from ..parser import generate_all_badges


@pytest.fixture
def sample_categories_with_badges():
    categories = {
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
    return generate_all_badges(categories)


def test_export_md_with_badges(sample_categories_with_badges):
    # Create a temporary file for output
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        temp_file = f.name
    
    try:
        export_md_badges(sample_categories_with_badges, temp_file)
        
        # Check if file was created
        assert os.path.exists(temp_file)
        
        # Check content
        with open(temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check for category header
            assert '## Test Category' in content
            
            # Check for API entries
            assert '[Test API 1](https://example.com/api1)' in content
            assert '[Test API 2](https://example.com/api2)' in content
            
            # Check for badges
            assert '![yes](https://img.shields.io/badge/HTTPS-yes-brightgreen)' in content
            assert '![no](https://img.shields.io/badge/Auth-no-lightgrey)' in content
            
    finally:
        os.unlink(temp_file)


def test_export_html(sample_categories_with_badges):
    # Create a temporary directory for output
    temp_dir = tempfile.mkdtemp()
    
    try:
        export_html_page(sample_categories_with_badges, temp_dir)
        
        # Check if HTML file was created
        html_path = os.path.join(temp_dir, 'index.html')
        assert os.path.exists(html_path)
        
        # Check content
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check for category header
            assert '<h2>Test Category</h2>' in content
            
            # Check for API entries
            assert '<a href="https://example.com/api1" target="_blank">Test API 1</a>' in content
            assert '<a href="https://example.com/api2" target="_blank">Test API 2</a>' in content
            
            # Check for badges
            assert 'src="https://img.shields.io/badge/HTTPS-yes-brightgreen"' in content
            assert 'src="https://img.shields.io/badge/HTTPS-no-lightgrey"' in content
            
    finally:
        shutil.rmtree(temp_dir)


def test_export_to_csv(sample_categories_with_badges):
    # Create a temporary directory for output
    temp_dir = tempfile.mkdtemp()
    
    try:
        export_to_csv(sample_categories_with_badges, temp_dir)
        
        # Check if CSV file was created
        csv_path = os.path.join(temp_dir, 'apis.csv')
        assert os.path.exists(csv_path)
        
        # Check content
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check header
            assert reader.fieldnames == ['name', 'description', 'auth', 'https', 'cors', 'link', 'category']
            
            # Check number of rows
            assert len(rows) == 2
            
            # Check first row
            assert rows[0]['name'] == 'Test API 1'
            assert rows[0]['description'] == 'Test description 1'
            assert rows[0]['auth'] == 'no'
            assert rows[0]['https'] == 'yes'
            assert rows[0]['cors'] == 'unknown'
            assert rows[0]['link'] == 'https://example.com/api1'
            assert rows[0]['category'] == 'Test Category'
            
    finally:
        shutil.rmtree(temp_dir)


def test_exporter_directory_creation():
    # Create a temporary directory path that doesn't exist
    temp_dir = os.path.join(tempfile.gettempdir(), 'test_api_badger')
    assert not os.path.exists(temp_dir)
    
    try:
        # Exporter should create the directory
        exporter = APIExporter(temp_dir)
        assert os.path.exists(temp_dir)
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_export_md_default_filename(sample_categories_with_badges):
    # Test that default filename is used when not specified
    export_md_badges(sample_categories_with_badges)
    
    # Check if file was created with default name
    assert os.path.exists('README_BADGES.md')
    
    # Clean up
    os.unlink('README_BADGES.md')
