#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os

def check_json_files():
    base_path = 'data'
    
    # Check apis.json
    apis_path = os.path.join(base_path, 'apis.json')
    if os.path.exists(apis_path):
        with open(apis_path, 'r', encoding='utf-8') as f:
            apis_data = json.load(f)
        print(f"Total APIs in apis.json: {len(apis_data)}")
    else:
        print(f"apis.json not found at {apis_path}")
    
    # Check report.json
    report_path = os.path.join(base_path, 'report.json')
    if os.path.exists(report_path):
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        print(f"Total APIs in report: {report_data['summary']['total_apis']}")
        print(f"Categories: {report_data['summary']['categories']}")
        print(f"OK APIs: {report_data['summary']['ok_apis']}")
        print(f"Failed APIs: {report_data['summary']['failed_apis']}")
    else:
        print(f"report.json not found at {report_path}")
    
    # Check anomalies.json
    anomalies_path = os.path.join(base_path, 'anomalies.json')
    if os.path.exists(anomalies_path):
        with open(anomalies_path, 'r', encoding='utf-8') as f:
            anomalies_data = json.load(f)
        print(f"Total anomalies: {len(anomalies_data)}")
    else:
        print(f"anomalies.json not found at {anomalies_path}")

if __name__ == '__main__':
    check_json_files()