import json

# Load the API data
with open('data/apis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check the first 5 APIs for auth type
print('First 5 APIs - Auth type:')
for api in data[:5]:
    print(f"{api['name']} - Auth: {api['auth']}")

# Count auth types
auth_counts = {}
for api in data:
    auth = api['auth']
    auth_counts[auth] = auth_counts.get(auth, 0) + 1

print('\nAuth type counts:')
for auth_type, count in auth_counts.items():
    print(f'{auth_type}: {count}')