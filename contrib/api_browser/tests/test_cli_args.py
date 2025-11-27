#!/usr/bin/env python3
"""Unit tests for CLI arguments parsing"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

# Add the parent directory to Python path to allow import
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_browser import main


def test_cli_args_query():
    """Test --query/-q argument parsing"""
    with patch('sys.argv', ['api_browser.py', '--query', 'weather']):
        with patch('api_browser.parse_readme') as mock_parse:
            with patch('api_browser.filter_apis') as mock_filter:
                with patch('api_browser.print_table') as mock_print:
                    mock_parse.return_value = []
                    main()
                    mock_filter.assert_called_once_with([], 'weather', None)

    with patch('sys.argv', ['api_browser.py', '-q', 'cat']):
        with patch('api_browser.parse_readme') as mock_parse:
            with patch('api_browser.filter_apis') as mock_filter:
                with patch('api_browser.print_table') as mock_print:
                    mock_parse.return_value = []
                    main()
                    mock_filter.assert_called_once_with([], 'cat', None)


def test_cli_args_category():
    """Test --category/-c argument parsing"""
    with patch('sys.argv', ['api_browser.py', '--category', 'Animals']):
        with patch('api_browser.parse_readme') as mock_parse:
            with patch('api_browser.filter_apis') as mock_filter:
                with patch('api_browser.print_table') as mock_print:
                    mock_parse.return_value = []
                    main()
                    mock_filter.assert_called_once_with([], None, 'Animals')

    with patch('sys.argv', ['api_browser.py', '-c', 'Weather']):
        with patch('api_browser.parse_readme') as mock_parse:
            with patch('api_browser.filter_apis') as mock_filter:
                with patch('api_browser.print_table') as mock_print:
                    mock_parse.return_value = []
                    main()
                    mock_filter.assert_called_once_with([], None, 'Weather')


def test_cli_args_output():
    """Test --output/-o argument parsing"""
    with patch('sys.argv', ['api_browser.py', '--output', 'json']):
        with patch('api_browser.parse_readme') as mock_parse:
            with patch('api_browser.filter_apis') as mock_filter:
                with patch('api_browser.print_json') as mock_print:
                    mock_parse.return_value = []
                    mock_filter.return_value = []
                    main()
                    mock_print.assert_called_once()

    with patch('sys.argv', ['api_browser.py', '-o', 'table']):
        with patch('api_browser.parse_readme') as mock_parse:
            with patch('api_browser.filter_apis') as mock_filter:
                with patch('api_browser.print_table') as mock_print:
                    mock_parse.return_value = []
                    mock_filter.return_value = []
                    main()
                    mock_print.assert_called_once()


def test_cli_args_file():
    """Test --file/-f argument parsing"""
    test_file = 'test_readme.md'
    with patch('sys.argv', ['api_browser.py', '--file', test_file, '--cache-refresh']):
        with patch('api_browser.parse_readme') as mock_parse:
            with patch('api_browser.save_cache') as mock_save:
                with patch('api_browser.filter_apis') as mock_filter:
                    with patch('api_browser.print_table') as mock_print:
                        mock_parse.return_value = []
                        main()
                        mock_parse.assert_called_once_with(test_file)

    with patch('sys.argv', ['api_browser.py', '-f', test_file, '--cache-refresh']):
        with patch('api_browser.parse_readme') as mock_parse:
            with patch('api_browser.save_cache') as mock_save:
                with patch('api_browser.filter_apis') as mock_filter:
                    with patch('api_browser.print_table') as mock_print:
                        mock_parse.return_value = []
                        main()
                        mock_parse.assert_called_once_with(test_file)


def test_cli_args_cache_refresh():
    """Test --cache-refresh argument parsing"""
    with patch('sys.argv', ['api_browser.py', '--cache-refresh']):
        with patch('api_browser.is_cache_valid') as mock_valid:
            with patch('api_browser.parse_readme') as mock_parse:
                with patch('api_browser.save_cache') as mock_save:
                    with patch('api_browser.filter_apis') as mock_filter:
                        with patch('api_browser.print_table') as mock_print:
                            mock_valid.return_value = True  # Normally would use cache, but --cache-refresh overrides
                            mock_parse.return_value = []
                            main()
                            mock_parse.assert_called_once()  # Should parse even if cache is valid
                            mock_save.assert_called_once()


def test_cli_args_combined():
    """Test combined arguments parsing"""
    with patch('sys.argv', ['api_browser.py', '-q', 'facts', '-c', 'Animals', '-o', 'json', '-f', 'test.md', '--cache-refresh']):
        with patch('api_browser.parse_readme') as mock_parse:
            with patch('api_browser.save_cache') as mock_save:
                with patch('api_browser.filter_apis') as mock_filter:
                    with patch('api_browser.print_json') as mock_print:
                        mock_parse.return_value = []
                        main()
                        mock_parse.assert_called_once_with('test.md')
                        mock_filter.assert_called_once_with([], 'facts', 'Animals')
                        mock_print.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
