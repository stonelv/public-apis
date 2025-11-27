#!/usr/bin/env python3
"""
Test module for output functionality
"""

import unittest
import json
import sys
from io import StringIO

# Use relative imports first, fall back to absolute imports for compatibility
try:
    from . import cli
except ImportError:
    import cli

class TestOutput(unittest.TestCase):
    """Test cases for output functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.test_apis = [
            {
                "name": "GitHub API",
                "description": "GitHub API for accessing repositories, users, and more",
                "auth": "OAuth",
                "https": "Yes",
                "cors": "Yes",
                "category": "Development"
            },
            {
                "name": "Twitter API",
                "description": "Twitter API for accessing tweets, users, and more",
                "auth": "OAuth",
                "https": "Yes",
                "cors": "Yes",
                "category": "Social"
            }
        ]
        
        # Save original stdout
        self.original_stdout = sys.stdout
    
    def tearDown(self):
        """Restore original stdout"""
        sys.stdout = self.original_stdout
    
    def test_output_json(self):
        """Test JSON output format"""
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # Call output_results with JSON format
        cli.output_results(self.test_apis, "json")
        
        # Get the captured output
        output = captured_output.getvalue()
        
        # Verify output is valid JSON
        try:
            json_data = json.loads(output)
            self.assertIsInstance(json_data, list)
            self.assertEqual(len(json_data), 2)
            self.assertEqual(json_data[0]["name"], "GitHub API")
            self.assertEqual(json_data[1]["name"], "Twitter API")
        except json.JSONDecodeError:
            self.fail("Output is not valid JSON")
    
    def test_output_table(self):
        """Test table output format"""
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # Call output_results with table format
        cli.output_results(self.test_apis, "table")
        
        # Get the captured output
        output = captured_output.getvalue()
        
        # Verify output contains table headers and data
        self.assertIn("Name", output)
        self.assertIn("Description", output)
        self.assertIn("Auth", output)
        self.assertIn("HTTPS", output)
        self.assertIn("CORS", output)
        self.assertIn("GitHub API", output)
        self.assertIn("Twitter API", output)
        self.assertIn("OAuth", output)
        self.assertIn("Yes", output)

if __name__ == "__main__":
    unittest.main()
