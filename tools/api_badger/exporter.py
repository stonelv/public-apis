# -*- coding: utf-8 -*-

import os
import csv
from typing import Dict, List

class APIExporter:
    def __init__(self, out_dir: str = 'output'):
        self.out_dir = out_dir
        self._create_output_directory()
    
    def _create_output_directory(self) -> None:
        """Create the output directory if it doesn't exist."""
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
    
    def export_md_with_badges(self, categories: Dict[str, List[Dict]], output_file: str = 'README_BADGES.md') -> None:
        """Export APIs to a Markdown file with badges."""
        md_content = "# Public APIs with Badges\n\n"
        
        for category, apis in categories.items():
            md_content += f"## {category}\n\n"
            md_content += "| API | Description | Auth | HTTPS | CORS |\n"
            md_content += "|:---|:---|:---|:---|:---|\n"
            
            for api in apis:
                # Create badge images for each API
                auth_badge = f"![{api['auth']}]({api['badges']['auth']})"
                https_badge = f"![{api['https']}]({api['badges']['https']})"
                cors_badge = f"![{api['cors']}]({api['badges']['cors']})"
                
                # Format the table row
                md_content += f"| [{api['name']}]({api['link']}) | {api['description']} | {auth_badge} | {https_badge} | {cors_badge} |\n"
            
            md_content += "\n**[⬆ Back to Top](#public-apis-with-badges)**\n\n\n"
        
        # Write the Markdown content to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def export_html(self, categories: Dict[str, List[Dict]], output_file: str = 'index.html') -> None:
        """Export APIs to an HTML file with badges."""
        html_path = os.path.join(self.out_dir, output_file)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Public APIs</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        .api-card {{ background-color: #f9f9f9; border: 1px solid #eee; border-radius: 4px; padding: 15px; margin-bottom: 15px; transition: box-shadow 0.3s ease; }}
        .api-card:hover {{ box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .api-name {{ font-size: 1.2em; font-weight: bold; margin-bottom: 5px; }}
        .api-name a {{ color: #007bff; text-decoration: none; }}
        .api-name a:hover {{ text-decoration: underline; }}
        .api-description {{ color: #666; margin-bottom: 10px; line-height: 1.4; }}
        .badges {{ margin-top: 10px; }}
        .badges img {{ margin-right: 5px; vertical-align: middle; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Public APIs</h1>"""
        
        for category, apis in categories.items():
            html_content += f"\n        <h2>{category}</h2>\n"
            
            for api in apis:
                html_content += f"""        <div class="api-card">
            <div class="api-name"><a href="{api['link']}" target="_blank">{api['name']}</a></div>
            <div class="api-description">{api['description']}</div>
            <div class="badges">
                <img src="{api['badges']['https']}" alt="HTTPS: {api['https']}" title="HTTPS: {api['https']}">
                <img src="{api['badges']['auth']}" alt="Auth: {api['auth']}" title="Auth: {api['auth']}">
                <img src="{api['badges']['cors']}" alt="CORS: {api['cors']}" title="CORS: {api['cors']}">
            </div>
        </div>"""
        
        html_content += """
    </div>
</body>
</html>"""
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def export_csv(self, categories: Dict[str, List[Dict]], output_file: str = 'apis.csv') -> None:
        """Export APIs to a CSV file."""
        csv_path = os.path.join(self.out_dir, output_file)
        
        fieldnames = ['name', 'description', 'auth', 'https', 'cors', 'link', 'category']
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for category, apis in categories.items():
                for api in apis:
                    # Create a copy of the API data without badges
                    api_copy = {k: v for k, v in api.items() if k != 'badges'}
                    writer.writerow(api_copy)



def export_md_badges(categories: Dict[str, List[Dict]], output_file: str = 'README_BADGES.md') -> None:
    """Convenience function to export Markdown with badges."""
    exporter = APIExporter()
    exporter.export_md_with_badges(categories, output_file)


def export_html_page(categories: Dict[str, List[Dict]], out_dir: str = 'output', output_file: str = 'index.html') -> None:
    """Convenience function to export HTML page."""
    exporter = APIExporter(out_dir)
    exporter.export_html(categories, output_file)


def export_to_csv(categories: Dict[str, List[Dict]], out_dir: str = 'output', output_file: str = 'apis.csv') -> None:
    """Convenience function to export to CSV."""
    exporter = APIExporter(out_dir)
    exporter.export_csv(categories, output_file)
