# API Badger

API Badger is a tool that parses the Public APIs README.md file, generates badges for each API entry, and exports the results in different formats.

## Features
- Parse API tables from Markdown files
- Generate badges for HTTPS, Auth, and CORS status
- Export results to:
  - Markdown (with badges)
  - HTML (interactive page)
  - CSV (for further analysis)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/public-apis/public-apis.git
   ```

2. Navigate to the api_badger directory:
   ```bash
   cd public-apis/tools/api_badger
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Build All Outputs
Generate Markdown with badges and HTML page:
```bash
python cli.py build
```

### Export to CSV
Export API data to CSV file:
```bash
python cli.py export-csv
```

### Serve HTML Page
Serve the generated HTML page locally:
```bash
python cli.py serve
```

## Command Options

### Build Command
- `--file`: Markdown file to parse (default: `README.md`)
- `--out-dir`: Output directory for HTML files (default: `output`)
- `--skip-invalid`: Skip invalid API entries

Example:
```bash
python cli.py build --file README.md --out-dir docs --skip-invalid
```

### Export CSV Command
- `--file`: Markdown file to parse (default: `README.md`)
- `--out-dir`: Output directory for CSV file (default: `output`)
- `--skip-invalid`: Skip invalid API entries

Example:
```bash
python cli.py export-csv --file README.md --out-dir data
```

### Serve Command
- `--dir`: Directory with generated HTML files (default: `output`)
- `--port`: Port to serve on (default: 8000)
- `--open`: Open the page in a browser

Example:
```bash
python cli.py serve --dir docs --port 8080 --open
```

## Badge Colors
- `yes`: brightgreen
- `no`: lightgrey
- `unknown`: orange
- `empty`: red

## Running Tests

Run the pytest tests:
```bash
pytest tests/ -v
```

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/public-apis/public-apis/blob/master/LICENSE) file for details.
