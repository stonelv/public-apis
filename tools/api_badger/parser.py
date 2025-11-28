# -*- coding: utf-8 -*-

import re
from typing import List, Dict, Optional

# Regex patterns
ANCHOR_PATTERN = re.compile(r'^###\s+(.+)')
TABLE_ROW_PATTERN = re.compile(r'^\|.*\|$')
TABLE_HEADER_PATTERN = re.compile(r'^\|:?---')
LINK_PATTERN = re.compile(r'\[(.+?)\]\((http[s]?://.+?)\)')

# Badge color mapping
COLOR_MAPPING = {
    'yes': 'brightgreen',
    'no': 'lightgrey',
    'unknown': 'orange',
    'empty': 'red'
}

class APIParser:
    def __init__(self, skip_invalid: bool = False):
        self.skip_invalid = skip_invalid
        self.categories: Dict[str, List[Dict]] = {}
        self.current_category: Optional[str] = None
    
    def parse_md_file(self, file_path: str) -> None:
        """Parse a Markdown file containing API tables organized by categories."""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.rstrip() for line in f]
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Check for category headers (### Category Name)
            if line.startswith('###'):
                category_match = ANCHOR_PATTERN.match(line)
                if category_match:
                    self.current_category = category_match.group(1)
                    self.categories[self.current_category] = []
                continue
            
            # Skip empty lines and lines that are not table rows
            if not line or not line.startswith('|') or line.startswith('|---'):
                continue
            
            # Process table rows only if we're inside a category
            if self.current_category:
                api_data = self._parse_table_row(line, line_num + 1)
                if api_data:
                    self.categories[self.current_category].append(api_data)
    
    def _parse_table_row(self, line: str, line_num: int) -> Optional[Dict]:
        """Parse a single table row and extract API data."""
        # Split the line by | and remove empty segments
        segments = [seg.strip() for seg in line.split('|') if seg.strip()]
        
        # API table should have 5 columns: Name/Link, Description, Auth, HTTPS, CORS
        if len(segments) < 5:
            if not self.skip_invalid:
                print(f"Warning: Invalid API entry on line {line_num} (insufficient columns)")
            return None
        
        # Extract link and name from the first column
        link_match = LINK_PATTERN.match(segments[0])
        if link_match:
            name = link_match.group(1)
            link = link_match.group(2)
        else:
            if not self.skip_invalid:
                print(f"Warning: Invalid link format on line {line_num}")
            return None
        
        # Extract other fields (use 'empty' if field is missing or empty)
        description = segments[1] if segments[1] else 'empty'
        auth = segments[2].lower() if segments[2] else 'empty'
        https = segments[3].lower() if segments[3] else 'empty'
        cors = segments[4].lower() if segments[4] else 'empty'
        
        return {
            'name': name,
            'description': description,
            'auth': auth,
            'https': https,
            'cors': cors,
            'link': link,
            'category': self.current_category
        }
    
    def generate_badges(self, api_data: Dict) -> Dict:
        """Generate badge URLs for HTTPS, Auth, and CORS fields."""
        badges = {
            'https': self._create_badge('HTTPS', api_data['https']),
            'auth': self._create_badge('Auth', api_data['auth']),
            'cors': self._create_badge('CORS', api_data['cors'])
        }
        return badges
    
    def _create_badge(self, label: str, value: str) -> str:
        """Create a badge URL using the shields.io format."""
        value = value.lower()
        color = COLOR_MAPPING.get(value, COLOR_MAPPING['empty'])
        label_encoded = label.replace(' ', '%20')
        value_encoded = value.replace(' ', '%20')
        return f"https://img.shields.io/badge/{label_encoded}-{value_encoded}-{color}"


def parse_apis(file_path: str, skip_invalid: bool = False) -> Dict[str, List[Dict]]:
    """Convenience function to parse APIs from a Markdown file."""
    parser = APIParser(skip_invalid)
    parser.parse_md_file(file_path)
    return parser.categories


def generate_api_badges(api_data: Dict) -> Dict:
    """Convenience function to generate badges for a single API entry."""
    parser = APIParser()
    return parser.generate_badges(api_data)


def generate_all_badges(categories: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """Generate badges for all API entries in all categories."""
    parser = APIParser()
    for category, apis in categories.items():
        for api in apis:
            api['badges'] = parser.generate_badges(api)
    return categories
