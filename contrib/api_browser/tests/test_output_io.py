#!/usr/bin/env python3
"""Unit tests for output formats"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add the parent directory to Python path to allow import
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_browser import print_json, print_table, main


def test_print_json():
    """Test JSON output format"""
    apis = [
        {
            "name": "Cat Facts",
            "url": "https://cat-fact.herokuapp.com/facts",
            "description": "Daily cat facts",
            "auth": "No",
            "https": True,
            "cors": "Unknown",
            "category": "Animals"
        }
    ]

    from io import StringIO
    import sys
    original_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        print_json(apis)
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = original_stdout

    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "Cat Facts"
    assert parsed[0]["url"] == "https://cat-fact.herokuapp.com/facts"
    assert parsed[0]["description"] == "Daily cat facts"
    assert parsed[0]["auth"] == "No"
    assert parsed[0]["https"] == True
    assert parsed[0]["cors"] == "Unknown"
    assert parsed[0]["category"] == "Animals"


def test_print_table():
    """Test table output format"""
    apis = [
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
        }
    ]

    with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
        print_table(apis)
        output = ''.join(call[0][0] for call in mock_stdout.write.call_args_list)
        # Check if header contains expected keywords
        assert "Name" in output
        assert "Description" in output
        assert "Auth" in output
        assert "HTTPS" in output
        assert "CORS" in output
        assert "Category" in output
        # Check if data rows contain expected values
        assert "Cat Facts" in output
        assert "Dog Facts" in output
        assert "Daily cat facts" in output
        assert "Random dog facts" in output
        assert "Animals" in output
        assert "Yes" in output  # HTTPS and CORS values
        assert "Unknown" in output


def test_main_json_output():
    """Test main function with JSON output"""
    apis = [
        {
            "name": "Cat Facts",
            "url": "https://cat-fact.herokuapp.com/facts",
            "description": "Daily cat facts",
            "auth": "No",
            "https": True,
            "cors": "Unknown",
            "category": "Animals"
        }
    ]

    from io import StringIO
    import sys
    original_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        with patch('sys.argv', ['api_browser.py', '--output', 'json', '--cache-refresh']):
            with patch('api_browser.parse_readme') as mock_parse:
                with patch('api_browser.save_cache') as mock_save:
                    with patch('api_browser.filter_apis') as mock_filter:
                        mock_parse.return_value = apis
                        mock_filter.return_value = apis
                        main()
                        output = sys.stdout.getvalue()
    finally:
        sys.stdout = original_stdout

    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "Cat Facts"


def test_main_table_output():
    """Test main function with table output"""
    apis = [
        {
            "name": "Cat Facts",
            "url": "https://cat-fact.herokuapp.com/facts",
            "description": "Daily cat facts",
            "auth": "No",
            "https": True,
            "cors": "Unknown",
            "category": "Animals"
        }
    ]

    with patch('sys.argv', ['api_browser.py', '--output', 'table']):
        with patch('api_browser.parse_readme') as mock_parse:
            with patch('api_browser.filter_apis') as mock_filter:
                with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                    mock_parse.return_value = apis
                    mock_filter.return_value = apis
                    main()
                    output = ''.join(call[0][0] for call in mock_stdout.write.call_args_list)
                    assert "Name" in output
                    assert "Cat Facts" in output
                    assert "Daily cat facts" in output


def test_main_with_fixture_file():
    """Test main function with fixture file"""
    fixture_path = str(Path(__file__).parent.parent / "fixtures" / "sample_README.md")
    with patch('sys.argv', ['api_browser.py', '--file', fixture_path, '--cache-refresh']):
        with patch('api_browser.save_cache') as mock_save:
            with patch('api_browser.print_table') as mock_print:
                main()
                mock_save.assert_called_once()
                # Check that print_table was called with some data
                assert mock_print.called
                args, _ = mock_print.call_args
                assert isinstance(args[0], list)
                assert len(args[0]) > 0


if __name__ == "__main__":
    pytest.main([__file__])
