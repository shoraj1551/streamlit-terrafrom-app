"""
Log Export Functionality

Export logs to CSV and JSON formats.
"""

import csv
import json
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path


class LogExporter:
    """Export logs to various formats"""
    
    def __init__(self, export_dir: Path = None):
        self.export_dir = export_dir or Path("./exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_csv(self, logs: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Export logs to CSV file
        
        Args:
            logs: List of log dictionaries
            filename: Output filename (optional)
            
        Returns:
            Path to exported file
        """
        if not logs:
            raise ValueError("No logs to export")
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logs_export_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        # Get all unique keys from logs
        fieldnames = set()
        for log in logs:
            fieldnames.update(log.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(logs)
        
        return str(filepath)
    
    def export_to_json(self, logs: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Export logs to JSON file
        
        Args:
            logs: List of log dictionaries
            filename: Output filename (optional)
            
        Returns:
            Path to exported file
        """
        if not logs:
            raise ValueError("No logs to export")
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logs_export_{timestamp}.json"
        
        filepath = self.export_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(logs, jsonfile, indent=2)
        
        return str(filepath)
    
    def export_to_jsonl(self, logs: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Export logs to JSON Lines format
        
        Args:
            logs: List of log dictionaries
            filename: Output filename (optional)
            
        Returns:
            Path to exported file
        """
        if not logs:
            raise ValueError("No logs to export")
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logs_export_{timestamp}.jsonl"
        
        filepath = self.export_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as jsonlfile:
            for log in logs:
                jsonlfile.write(json.dumps(log) + '\n')
        
        return str(filepath)
