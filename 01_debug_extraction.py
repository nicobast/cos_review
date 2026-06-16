# 01_debug_extraction.py
import json
from pathlib import Path

def analyze_extraction_results():
    """Analyze the extraction results to identify problems."""
    INPUT_FILE = Path("cos_review/outputs/00_pdf_text.jsonl")
    
    if not INPUT_FILE.exists():
        print("No extraction results found!")
        return
    
    empty_count = 0
    error_count = 0
    total_count = 0
    
    with open(INPUT_FILE, 'r') as f:
        for line in f:
            total_count += 1
            record = json.loads(line)
            status = record.get('status', '')
            if status == 'empty':
                empty_count += 1
                print(f"Empty text: {record['filename']}")
            elif status == 'error':
                error_count += 1
                print(f"Error: {record['filename']} - {record.get('error', 'Unknown error')}")
    
    print(f"\nSummary:")
    print(f"Total PDFs: {total_count}")
    print(f"Empty text: {empty_count}")
    print(f"Errors: {error_count}")
    print(f"Success rate: {(total_count - empty_count - error_count) / total_count * 100:.1f}%")

if __name__ == "__main__":
    analyze_extraction_results()