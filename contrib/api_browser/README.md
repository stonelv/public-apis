# API Browser CLI Tool

A simple Python CLI tool to browse and filter APIs from the public-apis repository.

## Features

- **Parse API List**: Reads and parses API information from the repository's README.md
- **Filter APIs**: Search by keyword or filter by category
- **Output Formats**: Support for table and JSON output
- **Local Cache**: Caches API data for 24 hours to improve performance
- **Force Refresh**: Option to force refresh the cache

## Installation

1. Clone the repository:
```bash
git clone https://github.com/public-apis/public-apis.git
cd public-apis/contrib/api_browser
```

2. Install any required dependencies (none for basic functionality)

## Usage

### Basic Usage

```bash
python api_browser.py
```

### Filter by Query

```bash
python api_browser.py --query "weather"
```

### Filter by Category

```bash
python api_browser.py --category "Animals"
```

### Filter by Both Query and Category

```bash
python api_browser.py --query "facts" --category "Animals"
```

### JSON Output

```bash
python api_browser.py --output json
```

### Force Cache Refresh

```bash
python api_browser.py --cache-refresh
```

### Specify Custom README Path

```bash
python api_browser.py --file /path/to/README.md
```

## Examples

1. Search for weather APIs:
```bash
python api_browser.py -q weather
```

2. List all APIs in the Animals category:
```bash
python api_browser.py -c Animals
```

## Testing

Run the unit tests using pytest:

```bash
pytest
```

## License

MIT
