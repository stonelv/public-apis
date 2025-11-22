#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

# Add scripts directory to path
import sys
sys.path.append('scripts')

from scripts.validate_and_report import parse_readme

readme_path = 'README.md'
print(f"Parsing {readme_path}...")

apis, category_counts = parse_readme(readme_path)
print(f"Total APIs parsed: {len(apis)}")
print(f"Categories: {len(category_counts)}")
print(f"Category counts: {category_counts}")

# Print first 5 APIs
print(f"\nFirst 5 APIs:")
for api in apis[:5]:
    print(f"  {api['name']} ({api['category']}) - {api['url']}")