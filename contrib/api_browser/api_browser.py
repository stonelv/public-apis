#!/usr/bin/env python3
"""API Browser CLI tool for public-apis repository"""

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Any

CACHE_DIR = Path.home() / ".api-browser"
CACHE_FILE = CACHE_DIR / "apis_cache.json"
CACHE_EXPIRY = 24 * 60 * 60  # 24 hours in seconds


def create_cache_dir() -> None:
    """Create cache directory if it doesn't exist"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def is_cache_valid() -> bool:
    """Check if cache file exists and is not expired"""
    if not CACHE_FILE.exists():
        return False
    try:
        cache_time = CACHE_FILE.stat().st_mtime
        return time.time() - cache_time < CACHE_EXPIRY
    except Exception:
        return False


def load_cache() -> List[Dict[str, Any]]:
    """Load APIs from cache file"""
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_cache(apis: List[Dict[str, Any]]) -> None:
    """Save APIs to cache file"""
    create_cache_dir()
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(apis, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def parse_readme(file_path: str) -> List[Dict[str, Any]]:
    """Parse README.md file to extract API information"""
    apis = []
    current_category = None

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check for category heading (### Category Name)
        if line.startswith("### "):
            current_category = line[4:].strip()
            i += 1
            continue

        # Check for API table header
        if line == "API | Description | Auth | HTTPS | CORS":
            # Skip the separator line
            i += 2
            continue

        # Check for API table row
        if " | " in line and current_category:
            parts = [part.strip() for part in line.split(" | ")]
            if len(parts) >= 5:
                # Extract API name and URL from markdown link
                api_match = re.match(r"\[(.*?)\]\((.*?)\)", parts[0])
                if api_match:
                    api_name = api_match.group(1)
                    api_url = api_match.group(2)
                else:
                    api_name = parts[0]
                    api_url = ""

                api = {
                    "name": api_name,
                    "url": api_url,
                    "description": parts[1],
                    "auth": parts[2],
                    "https": parts[3] == "Yes",
                    "cors": parts[4],
                    "category": current_category
                }
                apis.append(api)

        i += 1

    return apis


def filter_apis(apis: List[Dict[str, Any]], query: str = None, category: str = None) -> List[Dict[str, Any]]:
    """Filter APIs by query and/or category"""
    filtered = apis.copy()

    if query:
        query_lower = query.lower()
        filtered = [
            api for api in filtered
            if query_lower in api["name"].lower() or
               query_lower in api["description"].lower() or
               query_lower in api["category"].lower()
        ]

    if category:
        category_lower = category.lower()
        filtered = [
            api for api in filtered
            if category_lower == api["category"].lower()
        ]

    return filtered


def print_table(apis: List[Dict[str, Any]]) -> None:
    """Print APIs in table format"""
    if not apis:
        print("No APIs found")
        return

    # Calculate column widths
    max_name = max(len(api["name"]) for api in apis) + 2
    max_desc = max(len(api["description"]) for api in apis) + 2
    max_auth = max(len(api["auth"]) for api in apis) + 2
    max_https = 8  # "HTTPS" + 2
    max_cors = max(len(api["cors"]) for api in apis) + 2
    max_cat = max(len(api["category"]) for api in apis) + 2

    # Print header
    print(f"{'Name':<{max_name}}{'Description':<{max_desc}}{'Auth':<{max_auth}}{'HTTPS':<{max_https}}{'CORS':<{max_cors}}{'Category':<{max_cat}}")
    print("-" * (max_name + max_desc + max_auth + max_https + max_cors + max_cat))

    # Print rows
    for api in apis:
        https_str = "Yes" if api["https"] else "No"
        print(f"{api['name']:<{max_name}}{api['description']:<{max_desc}}{api['auth']:<{max_auth}}{https_str:<{max_https}}{api['cors']:<{max_cors}}{api['category']:<{max_cat}}")


def print_json(apis: List[Dict[str, Any]]) -> None:
    """Print APIs in JSON format"""
    print(json.dumps(apis, indent=2, ensure_ascii=False))


def main() -> None:
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="API Browser for public-apis repository")
    parser.add_argument("--query", "-q", type=str, help="Search query to filter APIs")
    parser.add_argument("--category", "-c", type=str, help="Filter APIs by category")
    parser.add_argument("--output", "-o", type=str, choices=["table", "json"], default="table",
                        help="Output format (default: table)")
    parser.add_argument("--cache-refresh", action="store_true", help="Force refresh of cache")
    parser.add_argument("--file", "-f", type=str, default="../../README.md",
                        help="Path to README.md file (default: ../../README.md)")

    args = parser.parse_args()

    # Load APIs from cache or parse README
    if not args.cache_refresh and is_cache_valid():
        apis = load_cache()
    else:
        apis = parse_readme(args.file)
        save_cache(apis)

    # Filter APIs
    filtered_apis = filter_apis(apis, args.query, args.category)

    # Output results
    if args.output == "json":
        print_json(filtered_apis)
    else:
        print_table(filtered_apis)


if __name__ == "__main__":
    main()
