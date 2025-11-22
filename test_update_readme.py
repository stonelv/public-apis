#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify the README update functionality.
"""

import json
import os
import tempfile
import shutil

# Create a temporary directory for testing
test_dir = tempfile.mkdtemp()
print(f"Created test directory: {test_dir}")

try:
    # Create a test README.md with some API entries
    test_readme_content = '''# Test APIs

## Index
* [Animals](#animals)

### Animals
API | Description | Auth | HTTPS | CORS 
|:---|:---|:---|:---|:---|
| [AdoptAPet](https://www.adoptapet.com/public/apis/pet_list.html) | Resource to help get pets adopted | `apiKey` | Yes | Yes |
| [Axolotl](https://theaxolotlapi.netlify.app/) | Collection of axolotl pictures and facts | No | Yes | No |
| [Cat Facts](https://alexwohlbruck.github.io/cat-facts/) | Daily cat facts | No | Yes | No |
'''

    test_readme_path = os.path.join(test_dir, 'README.md')
    with open(test_readme_path, 'w', encoding='utf-8') as f:
        f.write(test_readme_content)

    # Import the update_readme function
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
    from validate_and_report import update_readme

    # Create test API data with one unstable API
    test_apis = [
        {
            'name': 'AdoptAPet',
            'description': 'Resource to help get pets adopted',
            'auth': 'api_key',
            'https': True,
            'cors': True,
            'category': 'Animals',
            'url': 'https://www.adoptapet.com/public/apis/pet_list.html',
            'slug': 'adoptapet-adoptapet.com',
            'domain': 'adoptapet.com',
            'status': 'ok',
            'last_checked': '2025-11-18T13:30:22.050583',
            'reliability_score': 1.0
        },
        {
            'name': 'Axolotl',
            'description': 'Collection of axolotl pictures and facts',
            'auth': 'no',
            'https': True,
            'cors': False,
            'category': 'Animals',
            'url': 'https://theaxolotlapi.netlify.app/',
            'slug': 'axolotl-theaxolotlapi.netlify.app',
            'domain': 'theaxolotlapi.netlify.app',
            'status': 'failed',
            'last_checked': '2025-11-18T13:30:22.050583',
            'reliability_score': 0.0  # This API is unstable
        },
        {
            'name': 'Cat Facts',
            'description': 'Daily cat facts',
            'auth': 'no',
            'https': True,
            'cors': False,
            'category': 'Animals',
            'url': 'https://alexwohlbruck.github.io/cat-facts/',
            'slug': 'cat-facts-alexwohlbruck.github.io',
            'domain': 'alexwohlbruck.github.io',
            'status': 'ok',
            'last_checked': '2025-11-18T13:30:22.050583',
            'reliability_score': 1.0
        }
    ]

    # Run update_readme
    print("Running update_readme...")
    update_readme(test_readme_path, test_apis)

    # Read the updated README and print it
    print("\nUpdated README.md:")
    with open(test_readme_path, 'r', encoding='utf-8') as f:
        updated_content = f.read()
        print(updated_content)

    # Check if the unstable API was marked correctly
    if '⚠️ Unstable' in updated_content and 'Axolotl' in updated_content:
        print("✓ Test passed: Unstable API was correctly marked")
    else:
        print("✗ Test failed: Unstable API was not marked correctly")

finally:
    # Clean up
    shutil.rmtree(test_dir)
    print(f"\nCleaned up test directory: {test_dir}")