#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Extraction Tool
This script parses API tables from README.md and exports to data/apis.json.
"""

import re
import json
import os
import argparse
import urllib.parse
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

# Regex patterns
CATEGORY_PATTERN = re.compile(r'###\s+([\w\s&]+)')
API_ROW_PATTERN = re.compile(r'\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*')

# Normalization mappings
AUTH_MAPPING = {
    'No': 'none',
    'apiKey': 'apikey',
    'OAuth': 'oauth',
    'X-Mashape-Key': 'x-mashape-key',
    'User-Agent': 'user-agent',
    'Unknown': 'unknown',
    '`apiKey`': 'apikey',
    '`OAuth`': 'oauth',
    'api_key': 'apikey',
    'apikey': 'apikey',
    'OAuth2': 'oauth',
    'oauth2': 'oauth',
    'oauth 2.0': 'oauth',
    'api key': 'apikey',
    '': 'none'
}

HTTPS_MAPPING = {
    'Yes': True,
    'No': False
}

CORS_MAPPING = {
    'Yes': True,
    'No': False,
    'Unknown': None
}

@dataclass
class APIEntry:
    """API entry data class"""
    name: str
    description: str
    auth_original: str
    auth_normalized: str
    https: bool
    cors: Optional[bool]
    category: str
    url: str
    domain: str
    slug: str
    line_no: int
    problems: List[str]

def generate_slug(name: str, domain: str) -> str:
    """Generate slug from name and domain"""
    # Convert to lowercase
    name_part = name.lower()
    domain_part = domain.lower()
    
    # Remove backticks
    name_part = name_part.replace('`', '')
    
    # Replace non-alphanumeric characters in name with - and compress
    name_slug = re.sub(r'[^a-z0-9]+', '-', name_part)
    name_slug = name_slug.strip('-')
    
    # Keep domain as is but remove any spaces or special characters except dots
    domain_slug = re.sub(r'[^a-z0-9.]+', '-', domain_part)
    domain_slug = domain_slug.strip('-')
    
    # Combine and ensure no double dashes between name and domain
    slug = f"{name_slug}-{domain_slug}" if name_slug and domain_slug else name_slug or domain_slug
    
    return slug

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc:
            # Handle URLs without scheme
            if '://' in url:
                domain = url.split('://', 1)[1].split('/', 1)[0]
            else:
                domain = url.split('/', 1)[0]
        else:
            domain = parsed.netloc
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain.lower()
    except Exception:
        return url

def normalize_auth(auth_str: str) -> Tuple[str, str]:
    """Normalize authentication type"""
    auth = auth_str.strip()
    original_auth = auth
    
    # Handle multiple auth types
    if ' or ' in auth:
        auth = auth.split(' or ')[0].strip()
    
    # Remove backticks
    auth = auth.replace('`', '')
    
    # Normalize according to rules
    if auth in AUTH_MAPPING:
        normalized = AUTH_MAPPING[auth]
    elif not auth:
        normalized = 'unknown_auth'
    else:
        normalized = 'custom'
    
    return original_auth, normalized

def validate_api(api: APIEntry) -> APIEntry:
    """Validate API entry and add problems"""
    problems = []
    
    # Check short description
    if len(api.description.strip()) < 8:
        problems.append('short_description')
    
    # Check illegal URL
    try:
        parsed = urllib.parse.urlparse(api.url)
        if not parsed.scheme and not api.url.startswith('//'):
            problems.append('illegal_url')
    except Exception:
        problems.append('illegal_url')
    
    # Check unknown auth
    if api.auth_normalized == 'unknown_auth':
        problems.append('unknown_auth')
    
    # Remove duplicates and update
    api.problems = list(dict.fromkeys(problems))
    return api

def parse_readme(readme_path: str, limit_categories: int = None, category_filter: str = None) -> Tuple[List[APIEntry], bool]:
    """Parse README.md and extract API entries"""
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    current_category = None
    apis = []
    categories_processed = set()
    format_anomalies_found = False
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        
        # Check if this is a category line
        category_match = CATEGORY_PATTERN.match(line)
        if category_match:
            current_category = category_match.group(1).strip()
            categories_processed.add(current_category)
            
            # Apply category limit
            if limit_categories and len(categories_processed) > limit_categories:
                break
            continue
        
        # Check if this is a table row
        if current_category and line.startswith('|'):
            # Skip header separator lines
            if line.startswith('|:-') or line.startswith('|:---'):
                continue
            
            # Match API row pattern
            match = API_ROW_PATTERN.match(line)
            if match:
                name = match.group(1).strip()
                url = match.group(2).strip()
                description = match.group(3).strip()
                auth_str = match.group(4).strip()
                https_str = match.group(5).strip()
                cors_str = match.group(6).strip() if len(match.groups()) > 6 else 'Unknown' if len(match.groups()) > 5 else None
                
                # Apply category filter
                if category_filter and current_category.lower() != category_filter.lower():
                    continue
                
                # Extract domain
                domain = extract_domain(url)
                
                # Generate slug
                slug = generate_slug(name, domain)
                
                # Normalize values
                auth_original, auth_normalized = normalize_auth(auth_str)
                https = HTTPS_MAPPING.get(https_str, False)
                cors = CORS_MAPPING.get(cors_str, None) if cors_str else None
                
                # Create API entry
                api_entry = APIEntry(
                    name=name,
                    description=description,
                    auth_original=auth_str,
                    auth_normalized=auth_normalized,
                    https=https,
                    cors=cors,
                    category=current_category,
                    url=url,
                    domain=domain,
                    slug=slug,
                    line_no=line_num + 1,  # Convert to 1-based
                    problems=[]
                )
                
                # Validate API entry
                api_entry = validate_api(api_entry)
                
                apis.append(api_entry)
            else:
                # Check if this line looks like an API row but didn't match regex
                if '](' in line and len(line.split('|')) >= 4:  # At least 4 columns (name, desc, auth, https)
                    format_anomalies_found = True
                    
                    # Try to extract as much as possible
                    columns = [col.strip() for col in line.split('|') if col.strip()]
                    if len(columns) >= 2:
                        name_url = columns[0]
                        if '](' in name_url:
                            name = name_url.split('](')[0][1:]
                            url = name_url.split('](')[1][:-1]
                        else:
                            name = name_url
                            url = ""
                        
                        description = columns[1] if len(columns) > 1 else ""
                        auth_str = columns[2] if len(columns) > 2 else ""
                        https_str = columns[3] if len(columns) > 3 else ""
                        cors_str = columns[4] if len(columns) > 4 else None
                        
                        # Extract domain
                        domain = extract_domain(url)
                        
                        # Generate slug
                        slug = generate_slug(name, domain)
                        
                        # Normalize values
                        auth_original, auth_normalized = normalize_auth(auth_str)
                        https = HTTPS_MAPPING.get(https_str, False)
                        cors = CORS_MAPPING.get(cors_str, None) if cors_str else None
                        
                        # Create API entry
                        api_entry = APIEntry(
                            name=name,
                            description=description,
                            auth_original=auth_str,
                            auth_normalized=auth_normalized,
                            https=https,
                            cors=cors,
                            category=current_category,
                            url=url,
                            domain=domain,
                            slug=slug,
                            line_no=line_num + 1,  # Convert to 1-based
                            problems=['format_anomaly']
                        )
                        
                        # Validate API entry
                        api_entry = validate_api(api_entry)
                        
                        apis.append(api_entry)
    
    return apis, format_anomalies_found

def detect_advanced_problems(apis: List[APIEntry]) -> None:
    """Detect advanced problems like domain clusters and cross-category domains"""
    # Group APIs by domain and category
    domain_category_map = defaultdict(set)
    domain_api_map = defaultdict(list)
    category_domain_count = defaultdict(Counter)
    
    for api in apis:
        domain = api.domain
        category = api.category
        domain_category_map[domain].add(category)
        domain_api_map[domain].append(api)
        category_domain_count[category][domain] += 1
    
    # Detect domain clusters in the same category (same domain > 3 times)
    for category, domain_counts in category_domain_count.items():
        for domain, count in domain_counts.items():
            if count > 3:
                for api in domain_api_map[domain]:
                    if api.category == category and 'domain_cluster' not in api.problems:
                        api.problems.append('domain_cluster')
    
    # Detect cross-category domains (same domain in multiple categories)
    for domain, categories in domain_category_map.items():
        if len(categories) > 1:
            for api in domain_api_map[domain]:
                if 'cross_category_domain' not in api.problems:
                    api.problems.append('cross_category_domain')

def generate_problems_summary(apis: List[APIEntry]) -> Dict:
    """Generate summary of problems"""
    summary = {
        "problems": {
            "short_description": [],
            "illegal_url": [],
            "unknown_auth": [],
            "domain_cluster": [],
            "cross_category_domain": [],
            "format_anomaly": []
        },
        "stats": {
            "total_apis": len(apis),
            "apis_with_problems": 0,
            "total_problems": 0,
            "unique_domains": 0,
            "unknown_auth_count": 0,
            "cross_category_domain_count": 0
        }
    }
    
    apis_with_problems_count = 0
    total_problems_count = 0
    unique_domains = set()
    unknown_auth_count = 0
    cross_category_domain_count = 0
    cross_category_domains = set()
    
    for api in apis:
        # Collect unique domains
        if api.domain:
            unique_domains.add(api.domain)
        
        # Count unknown_auth
        if api.auth_normalized == 'unknown_auth':
            unknown_auth_count += 1
        
        if api.problems:
            # Remove duplicate problems
            api.problems = list(dict.fromkeys(api.problems))
            
            apis_with_problems_count += 1
            total_problems_count += len(api.problems)
            
            for problem in api.problems:
                if problem in summary["problems"]:
                    summary["problems"][problem].append(api.slug)
                    
                # Track cross category domains
                if problem == 'cross_category_domain':
                    if api.domain and api.domain not in cross_category_domains:
                        cross_category_domains.add(api.domain)
                        cross_category_domain_count += 1
    
    # Update stats
    summary["stats"]["apis_with_problems"] = apis_with_problems_count
    summary["stats"]["total_problems"] = total_problems_count
    summary["stats"]["unique_domains"] = len(unique_domains)
    summary["stats"]["unknown_auth_count"] = unknown_auth_count
    summary["stats"]["cross_category_domain_count"] = cross_category_domain_count
    
    # Limit examples to 5 for each problem type
    for problem_type, slugs in summary["problems"].items():
        summary["problems"][problem_type] = slugs[:5]
    
    return summary

def main():
    parser = argparse.ArgumentParser(description='API Extraction Tool')
    parser.add_argument('--limit', type=int, help='Limit the number of categories to extract')
    parser.add_argument('--category', type=str, help='Filter by category')
    parser.add_argument('--report', action='store_true', help='Generate problems summary')
    parser.add_argument('--strict', action='store_true', help='Exit with error on format anomalies (not quality problems)')
    parser.add_argument('readme_path', nargs='?', help='Path to README.md file', default=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md'))
    args = parser.parse_args()
    
    # Parse README
    readme_path = args.readme_path
    apis, format_anomalies_found = parse_readme(readme_path, args.limit, args.category)
    
    # Detect advanced problems
    detect_advanced_problems(apis)
    
    # Convert to dict and sort
    api_dicts = [asdict(api) for api in apis]
    
    # Sort based on category filter
    if args.category:
        api_dicts.sort(key=lambda x: x['name'].lower())
    else:
        api_dicts.sort(key=lambda x: (x['category'].lower(), x['name'].lower()))
    
    # Export to appropriate JSON file
    base_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    if args.category:
        category_slug = generate_slug(args.category, "")
        output_path = os.path.join(base_data_dir, f'apis_{category_slug}.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(api_dicts, f, indent=2, ensure_ascii=False)
        print(f"Extracted {len(apis)} APIs from category '{args.category}' to {output_path}")
    else:
        output_path = os.path.join(base_data_dir, 'apis.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(api_dicts, f, indent=2, ensure_ascii=False)
        print(f"Extracted {len(apis)} APIs to {output_path}")
    
    # Generate problems summary if requested
    if args.report:
        problems_summary = generate_problems_summary(apis)
        problems_path = os.path.join(base_data_dir, 'problems_summary.json')
        with open(problems_path, 'w', encoding='utf-8') as f:
            json.dump(problems_summary, f, indent=2, ensure_ascii=False)
        print(f"Generated problems summary to {problems_path}")
    
    # Check for strict mode
    if args.strict and format_anomalies_found:
        print("ERROR: Found format anomalies in strict mode. Exiting.")
        sys.exit(1)
    
    # Generate problems summary if requested
    if args.report:
        summary = generate_problems_summary(apis)
        summary_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'problems_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"Generated problems summary to data/problems_summary.json")
        
        # Print summary
        print(f"\nStats:")
        print(f"Total APIs: {summary['stats']['total_apis']}")
        print(f"APIs with problems: {summary['stats']['apis_with_problems']}")
        print(f"Total problems: {summary['stats']['total_problems']}")
        
        if summary['problems']:
            print(f"\nProblems:")
            for problem, data in summary['problems'].items():
                print(f"- {problem}: {data['count']} occurrences")
    
    # Exit with error if strict mode and problems found
    if args.strict:
        has_problems = any(api.problems for api in apis)
        if has_problems:
            print(f"\nStrict mode enabled: Exiting with error due to problems")
            exit(1)

if __name__ == '__main__':
    main()