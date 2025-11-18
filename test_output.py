#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys

# Add scripts directory to path
sys.path.append('scripts')

from scripts.validate_and_report import parse_readme, validate_apis, generate_report, detect_anomalies

# Test parsing
readme_path = 'README.md'
apis = parse_readme(readme_path)
print(f"Total APIs parsed: {len(apis)}")

# Test validation
print("Validating APIs...")
validated_apis = validate_apis(apis[:5], 5, 5, True)  # Test with 5 APIs in dry-run mode
print(f"Validated APIs: {len(validated_apis)}")

# Check slug generation
print(f"\nSlug check:")
for api in validated_apis:
    print(f"  {api['name']} -> {api['slug']}")

# Test output generation
print(f"\nTesting output generation...")

# Create data directory if needed
os.makedirs('data', exist_ok=True)

# Write test data
apis_json_path = os.path.join('data', 'apis.json')
print(f"Writing to {apis_json_path}...")

# Test with full API list
print(f"Full API list: {len(apis)}")

# Run validation in dry-run mode for all APIs
print("Validating all APIs (dry-run)...")
validated_all = validate_apis(apis, 5, 5, True)
print(f"Validated all APIs: {len(validated_all)}")

print(f"First API: {validated_all[0]}")

# Check if slug is properly generated
print(f"First API slug: {validated_all[0]['slug']}")
print(f"Last API slug: {validated_all[-1]['slug']}")