import sys
import os
import pytest
from unittest.mock import patch

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.extract_apis import parse_readme, main

class TestStrictMode:
    def test_format_anomaly_detection(self):
        # Create a mock README content with format anomalies
        mock_readme = """# Public APIs

## Animals
| API | Description | Auth | HTTPS | CORS |
|-----|-------------|------|-------|------|
| [API 1](https://example.com) | Test | - | Yes | Yes |
| [API 2](https://test.com) | Another | API Key | Yes |
| API 3 | Missing link | - | Yes | Yes |
"""
        
        with open('test_readme.md', 'w', encoding='utf-8') as f:
            f.write(mock_readme)
        
        try:
            # Parse with format anomalies
            apis, format_anomalies_found = parse_readme('test_readme.md')
            
            # Should detect format anomalies
            assert format_anomalies_found == True
            
            # Check if format_anomaly is in problems
            format_anomaly_count = sum(1 for api in apis if "format_anomaly" in api.problems)
            assert format_anomaly_count >= 2
            
        finally:
            os.remove('test_readme.md')
    
    def test_strict_mode_format_anomaly_exit(self):
        # Create a mock README with format anomaly
        mock_readme = """# Public APIs

## Animals
| API | Description | Auth | HTTPS | CORS |
|-----|-------------|------|-------|------|
| [API 1](https://example.com) | Test | - | Yes | Yes |
| [API 2](https://test.com) | Another | API Key | Yes |
"""
        
        with open('test_strict.md', 'w', encoding='utf-8') as f:
            f.write(mock_readme)
        
        try:
            with patch('sys.argv', ['extract_apis.py', '--strict', 'test_strict.md']):
                with pytest.raises(SystemExit) as excinfo:
                    main()
                
            # Should exit with error code 1
            assert excinfo.type == SystemExit
            assert excinfo.value.code == 1
            
        finally:
            os.remove('test_strict.md')
    
    def test_strict_mode_quality_problems_no_exit(self):
        # Create a mock README with quality problems but no format anomalies
        mock_readme = """# Public APIs

## Animals
| API | Description | Auth | HTTPS | CORS |
|-----|-------------|------|-------|------|
| [API 1](https://example.com) | Shrt | - | Yes | Yes |  # Short description (quality problem)
"""
        
        with open('test_quality.md', 'w', encoding='utf-8') as f:
            f.write(mock_readme)
        
        try:
            with patch('sys.argv', ['extract_apis.py', '--strict', 'test_quality.md']):
                main()  # Should not raise SystemExit
            
        finally:
            os.remove('test_quality.md')