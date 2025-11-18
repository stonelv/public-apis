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
    
    # Handle multiple auth types
    if ' or ' in auth:
        auth = auth.split(' or ')[0].strip()
    
    # Remove backticks
    auth = auth.replace('`', '')
    
    # Normalize
    normalized = AUTH_MAPPING.get(auth, 'custom' if auth else 'unknown')
    if normalized == 'custom' and auth not in ['custom']:
        normalized = 'unknown'  # Set to unknown if not explicitly 'custom'
    
    return auth, normalized

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
    if api.auth_normalized == 'unknown':
        problems.append('unknown_auth')
    
    api.problems = problems
    return api

def parse_readme(readme_path: str, limit: int = None, category_filter: str = None) -> List[APIEntry]:
    """Parse README.md and extract API entries"""
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    current_category = None
    apis = []
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        
        # Check if this is a category line
        category_match = CATEGORY_PATTERN.match(line)
        if category_match:
            current_category = category_match.group(1).strip()
            continue
        
        # Check if this is a table row
        if current_category and line.startswith('|') and '](' in line:
            # Skip header separator lines
            if line.startswith('|:-'):
                continue
            
            # Match API row pattern
            match = API_ROW_PATTERN.match(line)
            if match:
                name = match.group(1).strip()
                url = match.group(2).strip()
                description = match.group(3).strip()
                auth_str = match.group(4).strip()
                https_str = match.group(5).strip()
                cors_str = match.group(6).strip() if match.group(6) else 'Unknown'
                
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
                cors = CORS_MAPPING.get(cors_str, None)
                
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
                
                # Apply limit
                if limit and len(apis) >= limit:
                    return apis
    
    return apis

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
                    if api.category == category:
                        api.problems.append('domain_cluster')
    
    # Detect cross-category domains (same domain in multiple categories)
    for domain, categories in domain_category_map.items():
        if len(categories) > 1:
            for api in domain_api_map[domain]:
                api.problems.append('cross_category_domain')

def generate_problems_summary(apis: List[APIEntry]) -> Dict:
    """Generate problems summary"""
    problem_counts = defaultdict(int)
    problem_examples = defaultdict(list)
    
    # Count problems and collect examples
    for api in apis:
        for problem in api.problems:
            problem_counts[problem] += 1
            
            # Collect up to 5 examples
            if len(problem_examples[problem]) < 5:
                example = {
                    'name': api.name,
                    'category': api.category,
                    'url': api.url,
                    'line_no': api.line_no
                }
                problem_examples[problem].append(example)
    
    # Generate summary
    summary = {
        'problems': {},
        'stats': {
            'total_apis': len(apis),
            'apis_with_problems': sum(1 for api in apis if api.problems),
            'total_problems': sum(problem_counts.values())
        }
    }
    
    for problem, count in sorted(problem_counts.items()):
        summary['problems'][problem] = {
            'count': count,
            'examples': problem_examples[problem]
        }
    
    return summary

def main():
    parser = argparse.ArgumentParser(description='API Extraction Tool')
    parser.add_argument('--limit', type=int, help='Limit the number of APIs to extract')
    parser.add_argument('--category', type=str, help='Filter by category')
    parser.add_argument('--report', action='store_true', help='Generate problems summary')
    parser.add_argument('--strict', action='store_true', help='Exit with error if problems found')
    args = parser.parse_args()
    
    # Parse README
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')
    apis = parse_readme(readme_path, args.limit, args.category)
    
    # Detect advanced problems
    detect_advanced_problems(apis)
    
    # Convert to dict and sort
    api_dicts = [asdict(api) for api in apis]
    api_dicts.sort(key=lambda x: (x['category'].lower(), x['name'].lower()))
    
    # Export to data/apis.json
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'apis.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(api_dicts, f, indent=2, ensure_ascii=False)
    
    print(f"Extracted {len(apis)} APIs to data/apis.json")
    
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