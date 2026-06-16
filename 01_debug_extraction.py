# 01_debug_extraction.py - Fixed version
import json
import sys
from pathlib import Path

def analyze_extraction_results():
    """Analyze the extraction results to identify problems."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    INPUT_FILE = script_dir / "outputs" / "00_pdf_text.jsonl"
    
    print(f"Looking for extraction results at: {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        print("No extraction results found!")
        print("This means either:")
        print("1. PDF extraction hasn't been run yet")
        print("2. PDF extraction failed")
        print("3. The outputs directory doesn't exist")
        
        # Show what directories exist
        print("\nDirectories in cos_review:")
        for item in script_dir.iterdir():
            if item.is_dir():
                print(f"  {item.name}")
                
        # Check if there are any PDF files to process
        pdf_dir = script_dir.parent / "rayyan downloads"
        if pdf_dir.exists():
            pdf_files = list(pdf_dir.glob("*.pdf"))
            print(f"\nFound {len(pdf_files)} PDF files in rayyan downloads/")
            for pdf in pdf_files[:5]:  # Show first 5
                print(f"  {pdf.name}")
            if len(pdf_files) > 5:
                print(f"  ... and {len(pdf_files) - 5} more")
        else:
            print(f"\nNo rayyan downloads directory found at {pdf_dir}")
        
        return
    
    empty_count = 0
    error_count = 0
    total_count = 0
    
    try:
        # Try to read with utf-8 first
        with open(INPUT_FILE, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if line.strip():
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
        print(f"Total PDFs processed: {total_count}")
        print(f"Empty text: {empty_count}")
        print(f"Errors: {error_count}")
        if total_count > 0:
            success_rate = (total_count - empty_count - error_count) / total_count * 100
            print(f"Success rate: {success_rate:.1f}%")
        else:
            print("No data to calculate success rate")
            
    except UnicodeDecodeError as e:
        print(f"Unicode decode error detected: {e}")
        print("Trying to read with latin-1 encoding...")
        try:
            with open(INPUT_FILE, 'r', encoding='latin-1', errors='replace') as f:
                for line in f:
                    if line.strip():
                        total_count += 1
                        record = json.loads(line)
                        status = record.get('status', '')
                        if status == 'empty':
                            empty_count += 1
                            print(f"Empty text: {record['filename']}")
                        elif status == 'error':
                            error_count += 1
                            print(f"Error: {record['filename']} - {record.get('error', 'Unknown error')}")
        except Exception as e2:
            print(f"Still unable to read file with latin-1: {e2}")
            print("Trying with cp1252 encoding (Windows default)...")
            try:
                with open(INPUT_FILE, 'r', encoding='cp1252', errors='replace') as f:
                    for line in f:
                        if line.strip():
                            total_count += 1
                            record = json.loads(line)
                            status = record.get('status', '')
                            if status == 'empty':
                                empty_count += 1
                                print(f"Empty text: {record['filename']}")
                            elif status == 'error':
                                error_count += 1
                                print(f"Error: {record['filename']} - {record.get('error', 'Unknown error')}")
            except Exception as e3:
                print(f"All encoding attempts failed: {e3}")
                print("File may be corrupted or have serious encoding issues")
                return
    except Exception as e:
        print(f"Error reading extraction file: {e}")

if __name__ == "__main__":
    analyze_extraction_results()