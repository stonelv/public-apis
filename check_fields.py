#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os

def check_api_fields():
    # Check if apis.json exists
    apis_path = os.path.join('data', 'apis.json')
    if not os.path.exists(apis_path):
        print(f"{apis_path} not found!")
        return

    # Load the JSON data
    with open(apis_path, 'r', encoding='utf-8') as f:
        apis_data = json.load(f)

    print(f"Total APIs: {len(apis_data)}")

    if apis_data:
        # Check the first API entry
        first_api = apis_data[0]
        print(f"\nFirst API: {first_api['name']}")
        print(f"URL: {first_api['url']}")
        print(f"\nAll fields in API entry:")
        for field in sorted(first_api.keys()):
            value = first_api[field]
            # Truncate long values
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"  {field}: {value}")

        # Check specific fields
        print(f"\nChecking specific fields:")
        for field in ['response_time', 'redirect_count', 'reliability_score', 'status']:
            if field in first_api:
                print(f"  ✓ {field} is present")
            else:
                print(f"  ✗ {field} is missing")

        # Check reliability_score calculation
        if 'reliability_score' in first_api:
            print(f"\nReliability score: {first_api['reliability_score']}")

if __name__ == '__main__':
    check_api_fields()