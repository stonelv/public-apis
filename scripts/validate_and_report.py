#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Quality and Category Consistency System
This script parses all API tables from README.md, validates APIs, and generates reports.
"""

import re
import json
import os
import time
import argparse
import concurrent.futures
import hashlib
import datetime
from typing import List, Dict, Tuple, Optional
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configuration
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.3
STATUS_FORCELIST = [429, 500, 502, 503, 504]

# Regex patterns
CATEGORY_PATTERN = re.compile(r'###\s+([\w\s&]+)')
API_TABLE_PATTERN = re.compile(r'API \| Description \| Auth \| HTTPS \| CORS\s*\n(\|:---\|:---\|:---\|:---\|:---\|)\s*((?:\|.*?\|\s*)+)', re.DOTALL)
API_ROW_PATTERN = re.compile(r'\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*')

# Normalization mappings
AUTH_MAPPING = {
    'none': 'none',
    'oauth': 'oauth',
    'oauth2': 'oauth',
    'oauth 2.0': 'oauth',
    'oauth 2': 'oauth',
    'api_key': 'apikey',
    'apikey': 'apikey',
    'api key': 'apikey',
    'api-key': 'apikey',
    'api_key': 'apikey',
    'x-mashape-key': 'x-mashape-key',
    'user-agent': 'user-agent',
    'custom': 'custom',
    'unknown': 'unknown',
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

def create_session(timeout: int) -> requests.Session:
    """Create a requests session with retry policy."""
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        read=MAX_RETRIES,
        connect=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=STATUS_FORCELIST
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.timeout = timeout
    return session


def parse_readme(readme_path: str) -> Tuple[List[Dict], Dict[str, int]]:
    """Parse README.md and extract all API entries."""
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    apis = []
    category_counts = {}

    # Use a simpler approach inspired by the existing format.py script
    lines = content.split('\n')

    current_category = None

    for line_num, line in enumerate(lines):
        line = line.strip()

        # Check if this is a category line
        if line.startswith('### '):
            current_category = line[4:].strip()
            category_counts[current_category] = 0
            continue

        # Check if this is a table row
        if current_category and line.startswith('|') and '[' in line and '](' in line:
            # Split the row into columns
            columns = [col.strip() for col in line.split('|') if col.strip()]
            
            # Ensure we have the expected number of columns
            if len(columns) < 5:
                continue

            # Extract API name and URL from the first column
            name_url = columns[0]
            if '](' in name_url:
                name = name_url.split('](')[0][1:]
                url = name_url.split('](')[1][:-1]
            else:
                continue

            description = columns[1]
            auth = columns[2]
            https_str = columns[3]
            cors_str = columns[4] if len(columns) > 4 else 'Unknown'

            # Normalize values
            auth = auth.strip()
            
            # Remove backticks first
            if '`' in auth:
                auth = auth.replace('`', '')
            
            # Convert to lowercase
            auth = auth.lower()
            
            # Check for multiple auth types
            if ' or ' in auth:
                # Use the first auth type for simplicity
                auth = auth.split(' or ')[0].strip()

            normalized_auth = AUTH_MAPPING.get(auth, 'unknown')
            normalized_https = HTTPS_MAPPING.get(https_str, False)
            normalized_cors = CORS_MAPPING.get(cors_str, None)

            # Extract domain
            domain = url.split('://', 1)[-1].split('/', 1)[0].lower()
            # Remove www prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]

            # Generate slug - more user-friendly and deterministic
            slug_base = f"{name.lower().replace(' ', '-').replace('.', '-').replace('_', '-')}-{domain}"
            # Remove duplicate dashes
            slug_base = re.sub(r'-+', '-', slug_base)
            # Remove leading/trailing dashes
            slug_base = slug_base.strip('-')
            # Truncate to reasonable length
            slug = slug_base[:64]

            api_entry = {
                'name': name,
                'description': description,
                'auth': normalized_auth,
                'https': normalized_https,
                'cors': normalized_cors,
                'category': current_category,
                'url': url,
                'slug': slug,
                'domain': domain,
                'status': 'unknown',
                'last_checked': None,
                'reliability_score': 0.0,
                'response_time': None,
                'redirect_count': None
            }

            apis.append(api_entry)
            category_counts[current_category] += 1

    return apis, category_counts


def check_api_status(api: Dict, session: requests.Session, dry_run: bool) -> Dict:
    """Check the status of a single API."""
    result = api.copy()
    result['last_checked'] = datetime.datetime.now().isoformat()

    if dry_run:
        result['status'] = 'ok'
        result['reliability_score'] = 1.0
        result['response_time'] = 0.5  # Simulate fast response
        result['redirect_count'] = 0  # Simulate no redirects
        return result

    try:
        # Try HEAD request first
        start_time = datetime.datetime.now()
        response = session.head(api['url'], allow_redirects=True)
        response_time = (datetime.datetime.now() - start_time).total_seconds()
        status_code = response.status_code
        redirect_count = len(response.history)
    except requests.exceptions.RequestException:
        try:
            # Fall back to GET request with limited response
            start_time = datetime.datetime.now()
            response = session.get(api['url'], allow_redirects=True, timeout=session.timeout, stream=True)
            response_time = (datetime.datetime.now() - start_time).total_seconds()
            status_code = response.status_code
            redirect_count = len(response.history)
            # Close the connection to save resources
            response.close()
        except requests.exceptions.RequestException as e:
            result['status'] = 'failed'
            result['reliability_score'] = 0.0
            result['response_time'] = None
            result['redirect_count'] = None
            return result

    # Determine status and initial reliability score
    if 200 <= status_code < 400:
        result['status'] = 'ok'
        reliability_score = 1.0
    elif status_code == 401 or status_code == 403:
        # Authentication required but API is reachable
        result['status'] = 'ok'
        reliability_score = 0.8
    elif status_code == 429:
        # Rate limited but API is reachable
        result['status'] = 'ok'
        reliability_score = 0.7
    elif 500 <= status_code < 600:
        # Server error
        result['status'] = 'server_error'
        reliability_score = 0.3
    else:
        result['status'] = 'failed'
        reliability_score = 0.0

    # Apply response time penalty (additive up to 0.2)
    if response_time > 2.0:
        response_time_penalty = min(0.2, (response_time - 2.0) / 10.0)
        reliability_score = max(0.0, reliability_score - response_time_penalty)

    # Apply redirect penalty (0.05 per redirect, max 0.2)
    if redirect_count > 0:
        redirect_penalty = min(0.2, redirect_count * 0.05)
        reliability_score = max(0.0, reliability_score - redirect_penalty)

    # Apply specific status code penalties
    if status_code == 202:
        # Accepted - still processing
        reliability_score = max(0.0, reliability_score - 0.1)
    elif status_code == 204:
        # No content - still valid, but less reliable
        reliability_score = max(0.0, reliability_score - 0.1)
    elif status_code == 301:
        # Permanent redirect - good, but slight penalty
        reliability_score = max(0.0, reliability_score - 0.05)
    elif status_code == 302:
        # Temporary redirect - more significant penalty
        reliability_score = max(0.0, reliability_score - 0.15)

    result['reliability_score'] = round(reliability_score, 3)
    result['response_time'] = round(response_time, 3)
    result['redirect_count'] = redirect_count

    return result


def validate_apis(apis: List[Dict], parallel: int, timeout: int, dry_run: bool) -> List[Dict]:
    """Validate all APIs with optional parallel processing."""
    if parallel <= 0:
        parallel = 1

    if dry_run:
        print("Running in dry-run mode - skipping actual API checks")

    session = create_session(timeout)
    validated_apis = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = []
        for api in apis:
            futures.append(executor.submit(check_api_status, api, session, dry_run))

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            validated_apis.append(result)

    return validated_apis


def generate_report(apis: List[Dict], category_counts: Dict[str, int]) -> Dict:
    """Generate a report from validated APIs."""
    total_apis = len(apis)
    ok_apis = sum(1 for api in apis if api['status'] in ['ok', 'server_error'])
    failed_apis = sum(1 for api in apis if api['status'] == 'failed')
    unknown_auth_apis = sum(1 for api in apis if api['auth'] == 'unknown')

    # Calculate category size anomalies (categories with too few or too many APIs)
    category_anomalies = []
    for category, count in category_counts.items():
        if count < 3:
            category_anomalies.append({'category': category, 'type': 'too_few', 'count': count})
        elif count > 120:
            category_anomalies.append({'category': category, 'type': 'too_many', 'count': count})

    # Check for domain conflicts
    domain_counts = {}
    for api in apis:
        domain = api['domain']
        if domain not in domain_counts:
            domain_counts[domain] = []
        domain_counts[domain].append(api)

    domain_conflicts = []
    for domain, api_list in domain_counts.items():
        if len(api_list) > 1:
            conflicting_apis = [{'name': api['name'], 'url': api['url']} for api in api_list]
            domain_conflicts.append({'domain': domain, 'apis': conflicting_apis})

    # Find unknown auth APIs
    unknown_auth_entries = []
    for api in apis:
        if api['auth'] == 'unknown':
            unknown_auth_entries.append({'name': api['name'], 'url': api['url'], 'auth': api['auth']})

    report = {
        'timestamp': datetime.datetime.now().isoformat(),
        'summary': {
            'total_apis': total_apis,
            'ok_apis': ok_apis,
            'failed_apis': failed_apis,
            'unknown_auth_apis': unknown_auth_apis,
            'categories': len(category_counts)
        },
        'category_anomalies': category_anomalies,
        'domain_conflicts': domain_conflicts,
        'unknown_auth_entries': unknown_auth_entries
    }

    return report


def detect_anomalies(apis: List[Dict], report: Dict) -> Dict:
    """Detect anomalies and generate anomalies.json."""
    anomalies = {
        'timestamp': datetime.datetime.now().isoformat(),
        'category_size_anomalies': report['category_anomalies'],
        'domain_conflicts': report['domain_conflicts'],
        'unknown_auth_apis': report['unknown_auth_entries'],
        'failed_apis': [api for api in apis if api['status'] == 'failed']
    }
    return anomalies


def update_readme(readme_path: str, apis: List[Dict]) -> None:
    """Update README.md to mark unstable APIs with ⚠️ Unstable badge."""
    with open(readme_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updated_lines = []
    unstable_apis = {api['slug'] for api in apis if api['reliability_score'] < 0.5}

    for line in lines:
        # Skip non-api lines
        if not line.startswith('|') or '](' not in line:
            updated_lines.append(line)
            continue

        # Extract API information from the line
        columns = [col.strip() for col in line.split('|') if col.strip()]
        if len(columns) < 5:
            updated_lines.append(line)
            continue

        name_url = columns[0]
        if '](' in name_url:
            name = name_url.split('](')[0][1:]
            url = name_url.split('](')[1][:-1]
            description = columns[1]
            auth = columns[2]
            https_str = columns[3]
            cors_str = columns[4] if len(columns) > 4 else 'Unknown'

            # Generate slug to match with api entry
            domain = url.split('://', 1)[-1].split('/', 1)[0].lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            slug_base = f"{name.lower().replace(' ', '-').replace('.', '-').replace('_', '-')}-{domain}"
            slug_base = re.sub(r'-+', '-', slug_base)
            slug_base = slug_base.strip('-')
            slug = slug_base[:64]

            if slug in unstable_apis:
                # Check if the line already has the unstable badge
                if '⚠️ Unstable' not in line:
                    # Append the unstable badge while maintaining table format
                    if line.rstrip()[-1] == '|':
                        # Line ends with |, append before it
                        updated_line = line.rstrip().rstrip('|') + ' | ⚠️ Unstable |\n'
                    else:
                        # Line doesn't end with |, append at the end
                        updated_line = line.rstrip() + ' ⚠️ Unstable |\n'
                    updated_lines.append(updated_line)
                else:
                    updated_lines.append(line)
            else:
                # Remove unstable badge if present (API is now stable)
                updated_line = line.replace(' ⚠️ Unstable |', ' |')
                updated_line = updated_line.replace(' ⚠️ Unstable', '')
                updated_lines.append(updated_line)
        else:
            updated_lines.append(line)

    # Write back the updated content
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)


def main():
    parser = argparse.ArgumentParser(description='API Quality and Category Consistency System')
    parser.add_argument('--parallel', type=int, default=10, help='Number of parallel requests')
    parser.add_argument('--limit', type=int, default=0, help='Limit the number of APIs to check (0 = all)')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (skip actual API checks)')
    args = parser.parse_args()

    # Set up paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(base_dir, 'README.md')
    data_dir = os.path.join(base_dir, 'data')

    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)

    # Parse README
    print("Parsing README.md...")
    apis, category_counts = parse_readme(readme_path)

    # Apply limit if specified
    if args.limit > 0:
        apis = apis[:args.limit]

    # Validate APIs
    print(f"Validating {len(apis)} APIs... (parallel: {args.parallel})")
    validated_apis = validate_apis(apis, args.parallel, args.timeout, args.dry_run)

    # Generate report
    print("Generating report...")
    report = generate_report(validated_apis, category_counts)

    # Detect anomalies
    print("Detecting anomalies...")
    anomalies = detect_anomalies(validated_apis, report)

    # Write outputs
    print("Writing outputs...")

    # Write apis.json
    apis_json_path = os.path.join(data_dir, 'apis.json')
    with open(apis_json_path, 'w', encoding='utf-8') as f:
        json.dump(validated_apis, f, indent=2, ensure_ascii=False)

    # Write report.json
    report_json_path = os.path.join(data_dir, 'report.json')
    with open(report_json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Write anomalies.json
    anomalies_json_path = os.path.join(data_dir, 'anomalies.json')
    with open(anomalies_json_path, 'w', encoding='utf-8') as f:
        json.dump(anomalies, f, indent=2, ensure_ascii=False)

    # Update README to mark unstable APIs
    update_readme(readme_path, validated_apis)

    print("Done!")
    print(f"APIs data: {apis_json_path}")
    print(f"Report: {report_json_path}")
    print(f"Anomalies: {anomalies_json_path}")


if __name__ == '__main__':
    main()