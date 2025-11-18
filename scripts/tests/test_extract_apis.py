#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for API extraction tool
"""

import pytest
import os
import sys
import json

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from extract_apis import generate_slug, normalize_auth, extract_domain, parse_readme

class TestExtractAPIs:
    """Test cases for API extraction tool"""
    
    def test_slug_generation(self):
        """Test slug generation"""
        # Test normal case
        assert generate_slug("Axolotl", "theaxolotlapi.netlify.app") == "axolotl-theaxolotlapi.netlify.app"
        
        # Test with special characters
        assert generate_slug("Cat Facts", "example.com") == "cat-facts-example.com"
        
        # Test with multiple dashes
        assert generate_slug("Test-API", "example.com") == "test-api-example.com"
        
        # Test with backticks
        assert generate_slug("`Test` API", "example.com") == "test-api-example.com"
        
        # Test with uppercase
        assert generate_slug("TEST API", "EXAMPLE.COM") == "test-api-example.com"
    
    def test_auth_normalization(self):
        """Test authentication normalization"""
        # Test No → none
        auth_org, auth_norm = normalize_auth("No")
        assert auth_norm == "none"
        
        # Test apiKey variants
        auth_org, auth_norm = normalize_auth("apiKey")
        assert auth_norm == "apikey"
        
        auth_org, auth_norm = normalize_auth("`apiKey`")
        assert auth_norm == "apikey"
        
        auth_org, auth_norm = normalize_auth("api_key")
        assert auth_norm == "apikey"
        
        # Test OAuth variants
        auth_org, auth_norm = normalize_auth("OAuth")
        assert auth_norm == "oauth"
        
        auth_org, auth_norm = normalize_auth("`OAuth`")
        assert auth_norm == "oauth"
        
        auth_org, auth_norm = normalize_auth("OAuth2")
        assert auth_norm == "oauth"
        
        # Test X-Mashape-Key
        auth_org, auth_norm = normalize_auth("X-Mashape-Key")
        assert auth_norm == "x-mashape-key"
        
        # Test User-Agent
        auth_org, auth_norm = normalize_auth("User-Agent")
        assert auth_norm == "user-agent"
        
        # Test Unknown
        auth_org, auth_norm = normalize_auth("Unknown")
        assert auth_norm == "unknown"
        
        # Test empty string
        auth_org, auth_norm = normalize_auth("")
        assert auth_norm == "none"
        
        # Test multiple auth types
        auth_org, auth_norm = normalize_auth("apiKey or OAuth")
        assert auth_norm == "apikey"
    
    def test_domain_extraction(self):
        """Test domain extraction from URL"""
        # Test HTTPS URL
        assert extract_domain("https://example.com/api") == "example.com"
        
        # Test HTTP URL
        assert extract_domain("http://example.com/api") == "example.com"
        
        # Test URL with www
        assert extract_domain("https://www.example.com/api") == "example.com"
        
        # Test URL with path and query
        assert extract_domain("https://example.com/api/v1?param=1") == "example.com"
        
        # Test URL without scheme
        assert extract_domain("example.com/api") == "example.com"
    
    def test_parse_readme(self, tmp_path):
        """Test README parsing"""
        # Create a test README
        test_content = '''### Animals
API | Description | Auth | HTTPS | CORS 
|:---|:---|:---|:---|:---|
| [Axolotl](https://theaxolotlapi.netlify.app/) | Collection of axolotl pictures and facts | No | Yes | No |
| [Cat Facts](https://example.com/cat-facts) | Daily cat facts | apiKey | Yes | Yes |

### Weather
API | Description | Auth | HTTPS | CORS 
|:---|:---|:---|:---|:---|
| [OpenWeatherMap](https://openweathermap.org/api) | Weather data | apiKey | Yes | Yes |
'''        
        readme_path = tmp_path / "README.md"
        readme_path.write_text(test_content)
        
        # Test parsing
        from extract_apis import parse_readme as test_parse_readme
        apis = test_parse_readme(str(readme_path))
        
        # Check number of APIs
        assert len(apis) == 3
        
        # Check first API
        assert apis[0].name == "Axolotl"
        assert apis[0].category == "Animals"
        assert apis[0].auth_normalized == "none"
        assert apis[0].https == True
        
        # Check second API
        assert apis[1].name == "Cat Facts"
        assert apis[1].auth_normalized == "apikey"
        
        # Check third API
        assert apis[2].name == "OpenWeatherMap"
        assert apis[2].category == "Weather"
    
    def test_short_description_detection(self, tmp_path):
        """Test short description detection"""
        test_content = '''### Animals
API | Description | Auth | HTTPS | CORS 
|:---|:---|:---|:---|:---|
| [Test API](https://example.com) | Short | No | Yes | No |
'''        
        readme_path = tmp_path / "README.md"
        readme_path.write_text(test_content)
        
        apis = parse_readme(str(readme_path))
        assert "short_description" in apis[0].problems
    
    def test_unknown_auth_detection(self, tmp_path):
        """Test unknown auth detection"""
        test_content = '''### Animals
API | Description | Auth | HTTPS | CORS 
|:---|:---|:---|:---|:---|
| [Test API](https://example.com) | Test API with custom auth | Custom | Yes | No |
'''        
        readme_path = tmp_path / "README.md"
        readme_path.write_text(test_content)
        
        apis = parse_readme(str(readme_path))
        assert "unknown_auth" in apis[0].problems
    
    def test_illegal_url_detection(self, tmp_path):
        """Test illegal URL detection"""
        test_content = '''### Animals
API | Description | Auth | HTTPS | CORS 
|:---|:---|:---|:---|:---|
| [Test API](invalid-url) | Test API with invalid URL | No | Yes | No |
'''        
        readme_path = tmp_path / "README.md"
        readme_path.write_text(test_content)
        
        apis = parse_readme(str(readme_path))
        assert "illegal_url" in apis[0].problems

if __name__ == '__main__':
    pytest.main([-v])