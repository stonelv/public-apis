import json

# Load the API data
with open('data/apis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Count auth types
auth_counts = {}
for api in data:
    auth = api['auth']
    auth_counts[auth] = auth_counts.get(auth, 0) + 1

# Print results
print('Auth Type Counts:')
for auth_type, count in sorted(auth_counts.items()):
    print(f'{auth_type}: {count}')

# Check if any 'unknown' auth types exist
if 'unknown' in auth_counts:
    print(f'\nWARNING: Found {auth_counts['unknown']} APIs with unknown auth type!')
    print('Sample APIs with unknown auth:')
    sample_count = 0
    for api in data:
        if api['auth'] == 'unknown':
            print(f"- {api['name']} (Category: {api['category']}, Auth: {api['original_auth'] if 'original_auth' in api else 'N/A'})")
            sample_count += 1
            if sample_count >= 10:
                break