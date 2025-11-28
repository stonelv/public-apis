#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

from parser import parse_apis, generate_all_badges
from exporter import export_md_badges, export_html_page, export_to_csv


def main():
    parser = argparse.ArgumentParser(description='API Badger - Generate badges for Public APIs')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build all output files (markdown and html)')
    build_parser.add_argument('--file', type=str, default='README.md', help='Markdown file to parse')
    build_parser.add_argument('--out-dir', type=str, default='output', help='Output directory for HTML files')
    build_parser.add_argument('--skip-invalid', action='store_true', help='Skip invalid API entries')
    
    # Export CSV command
    csv_parser = subparsers.add_parser('export-csv', help='Export APIs to CSV file')
    csv_parser.add_argument('--file', type=str, default='README.md', help='Markdown file to parse')
    csv_parser.add_argument('--out-dir', type=str, default='output', help='Output directory for CSV file')
    csv_parser.add_argument('--skip-invalid', action='store_true', help='Skip invalid API entries')
    
    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Serve the generated HTML page')
    serve_parser.add_argument('--dir', type=str, default='output', help='Directory with generated HTML files')
    serve_parser.add_argument('--port', type=int, default=8000, help='Port to serve on')
    serve_parser.add_argument('--open', action='store_true', help='Open the page in a browser')
    
    args = parser.parse_args()
    
    if args.command == 'build':
        print(f'Parsing API data from {args.file}...')
        categories = parse_apis(args.file, args.skip_invalid)
        print(f'Found {sum(len(apis) for apis in categories.values())} APIs across {len(categories)} categories')
        
        print('Generating badges...')
        categories_with_badges = generate_all_badges(categories)
        
        print('Exporting Markdown with badges...')
        export_md_badges(categories_with_badges)
        
        print(f'Exporting HTML to {args.out_dir}...')
        export_html_page(categories_with_badges, args.out_dir)
        
        print('Done!')
        
    elif args.command == 'export-csv':
        print(f'Parsing API data from {args.file}...')
        categories = parse_apis(args.file, args.skip_invalid)
        print(f'Found {sum(len(apis) for apis in categories.values())} APIs across {len(categories)} categories')
        
        print(f'Exporting CSV to {args.out_dir}...')
        export_to_csv(categories, args.out_dir)
        
        print('Done!')
        
    elif args.command == 'serve':
        # Change to the output directory
        os.chdir(args.dir)
        
        # Set up the HTTP server
        server_address = ('', args.port)
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        
        print(f'Serving HTTP on port {args.port} from directory {args.dir}...')
        print(f'Open http://localhost:{args.port} in your browser')
        
        if args.open:
            webbrowser.open(f'http://localhost:{args.port}')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nServer stopped')
            sys.exit(0)


if __name__ == '__main__':
    main()
