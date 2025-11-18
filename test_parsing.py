#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scripts.validate_and_report import parse_readme, slugify

readme_path = 'README.md'
print(f"Parsing {readme_path}...")

apis = parse_readme(readme_path)
print(f"Total APIs parsed: {len(apis)}")

if apis:
    first_api = apis[0]
    print(f"First API: {first_api}")
    print(f"Slugified name: {slugify(first_api['name'])}")

# Test slugify function
print(f"\nTesting slugify function:")
print(f"'Axolotl API' -> {slugify('Axolotl API')}")
print(f"'Test API 123' -> {slugify('Test API 123')}")
print(f"'API with many spaces' -> {slugify('API with many spaces')}")
print(f"'API-with-dashes' -> {slugify('API-with-dashes')}")
print(f"'API.with.dots' -> {slugify('API.with.dots')}")
print(f"'API_with_underscores' -> {slugify('API_with_underscores')}")