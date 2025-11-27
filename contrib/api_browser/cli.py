#!/usr/bin/env python3
"""
API Browser CLI Tool

This tool allows users to browse and filter the public APIs list from the repository.
"""

import argparse
import json
import os
from typing import List, Dict

# Use relative imports first, fall back to absolute imports for compatibility
try:
    from . import parser as apiparser
    from . import filter as apifilter
    from . import cache as apicache
except ImportError:
    import parser as apiparser
    import filter as apifilter
    import cache as apicache

def main():
    """Main entry point for the API Browser CLI tool."""
    # Parse command line arguments
    args = parse_args()
    
    # Initialize cache
    cache_manager = apicache.CacheManager()
    
    # Load APIs data
    if args.cache_refresh or not cache_manager.is_valid():
        # Parse from specified source file if cache is invalid or refresh is requested
        apis = apiparser.parse_apis_from_readme(args.source_file)
        # Save to cache
        cache_manager.save(apis)
    else:
        # Load from cache
        apis = cache_manager.load()
    
    # Filter APIs
    filtered_apis = apifilter.filter_apis(apis, args.query, args.category)
    
    # Apply limit if specified
    if args.limit is not None and args.limit > 0:
        filtered_apis = filtered_apis[:args.limit]
    
    # Output results
    output_results(filtered_apis, args.output)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    arg_parser = argparse.ArgumentParser(description="Browse and filter public APIs")
    
    # Source file option
    default_readme = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../README.md"))
    arg_parser.add_argument(
        "--source-file", 
        type=str, 
        default=default_readme, 
        help=f"Path to the README.md file to parse (default: {default_readme})"
    )
    
    # Filter options
    arg_parser.add_argument(
        "-q", "--query", 
        type=str, 
        help="Filter APIs by keyword in name or description"
    )
    arg_parser.add_argument(
        "-c", "--category", 
        type=str, 
        help="Filter APIs by category"
    )
    
    # Output options
    arg_parser.add_argument(
        "-o", "--output", 
        type=str, 
        choices=["json", "table"], 
        default="table", 
        help="Output format (default: table)"
    )
    arg_parser.add_argument(
        "-n", "--limit", 
        type=int, 
        help="Limit the number of results to output"
    )
    
    # Cache options
    arg_parser.add_argument(
        "--cache-refresh", 
        action="store_true", 
        help="Force refresh the local cache"
    )
    
    return arg_parser.parse_args()

def output_results(apis: List[Dict], format: str) -> None:
    """Output the filtered APIs in the specified format."""
    if format == "json":
        print(json.dumps(apis, indent=2, ensure_ascii=False))
    else:
        # Output as table
        print("{:<50} {:<100} {:<20} {:<10} {:<10}".format(
            "Name", "Description", "Auth", "HTTPS", "CORS"
        ))
        print("=" * 200)
        for api in apis:
            print("{:<50} {:<100} {:<20} {:<10} {:<10}".format(
                api["name"],
                api["description"][:97] + "..." if len(api["description"]) > 100 else api["description"],
                api["auth"],
                api["https"],
                api["cors"]
            ))

if __name__ == "__main__":
    main()
