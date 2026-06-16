# 00_extract_pdfs.py - Final corrected version
import json
from pathlib import Path
from typing import Optional

try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
except ImportError as exc:
    raise ImportError(
        "Missing dependency: install pypdf with `pip install pypdf`"
    ) from exc

try:
    from pdfplumber import PDF
    HAS_PDFPLUMBER = True
except ImportError:
    print("Warning: pdfplumber not installed. Install with `pip install pdfplumber` for better text extraction.")
    HAS_PDFPLUMBER = False

ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT.parent / "rayyan downloads"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "00_pdf_text.jsonl"

def clean_text_for_encoding(text: str) -> str:
    """Clean text to remove problematic characters that cause encoding errors."""
    if not isinstance(text, str):
        return ""
    
    # Remove null bytes and other problematic characters
    cleaned = text.replace('\x00', '').replace('\x01', '').replace('\x02', '')
    # Keep only printable ASCII characters and common punctuation
    cleaned = ''.join(char for char in cleaned if ord(char) < 128 or char.isspace() or char in '.,!?;:-()[]{}"\'')
    return cleaned.strip()

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Improved text extraction with robust encoding handling."""
    print(f"Processing: {pdf_path.name}")
    
    try:
        # Method 1: Try basic pypdf extraction first
        reader = PdfReader(str(pdf_path))
        pages = []
        
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text:
                    # Clean the text to handle encoding issues
                    cleaned_text = clean_text_for_encoding(page_text)
                    if cleaned_text:
                        pages.append(cleaned_text)
                else:
                    pages.append("")
            except Exception as e:
                print(f"  Page {page_num} extraction failed: {e}")
                pages.append("")
        
        result = "\n\n".join(pages).strip()
        
        # If still empty and pdfplumber is available, try alternative method
        if not result and HAS_PDFPLUMBER:
            try:
                with PDF.open(pdf_path) as pdf:
                    full_text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            # Clean the text
                            cleaned_text = clean_text_for_encoding(page_text)
                            full_text += cleaned_text + "\n"
                    result = full_text.strip()
            except Exception as e:
                print(f"  pdfplumber extraction failed: {e}")
        
        # If still empty, return empty string instead of placeholder
        if not result:
            print(f"  Warning: No text extracted from {pdf_path.name}")
            return ""
            
        return result
        
    except PdfReadError as e:
        print(f"Error reading PDF {pdf_path.name}: {e}")
        return ""
    except Exception as e:
        print(f"Unexpected error with {pdf_path.name}: {e}")
        return ""

def process_pdfs(input_dir: Path, output_file: Path) -> None:
    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {input_dir}")

    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Handle encoding issues by using utf-8 with error replacement
    try:
        with output_file.open("w", encoding="utf-8", errors="replace") as out_f:
            for pdf_path in pdf_files:
                print(f"Processing {pdf_path.name}")
                try:
                    text = extract_text_from_pdf(pdf_path)
                    record = {
                        "filename": pdf_path.name,
                        "filepath": str(pdf_path.resolve()),
                        "num_pages": len(PdfReader(str(pdf_path)).pages),
                        "text": text,
                        "status": "ok" if text else "empty",
                    }
                except Exception as exc:
                    record = {
                        "filename": pdf_path.name,
                        "filepath": str(pdf_path.resolve()),
                        "num_pages": 0,
                        "text": "",
                        "status": "error",
                        "error": str(exc),
                    }
                # Write with proper encoding handling
                out_f.write(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + "\n")
                print(f"  Saved record for {pdf_path.name}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        # Fallback to latin-1 encoding
        try:
            with output_file.open("w", encoding="latin-1", errors="replace") as out_f:
                for pdf_path in pdf_files:
                    print(f"Processing {pdf_path.name}")
                    try:
                        text = extract_text_from_pdf(pdf_path)
                        record = {
                            "filename": pdf_path.name,
                            "filepath": str(pdf_path.resolve()),
                            "num_pages": len(PdfReader(str(pdf_path)).pages),
                            "text": text,
                            "status": "ok" if text else "empty",
                        }
                    except Exception as exc:
                        record = {
                            "filename": pdf_path.name,
                            "filepath": str(pdf_path.resolve()),
                            "num_pages": 0,
                            "text": "",
                            "status": "error",
                            "error": str(exc),
                        }
                    out_f.write(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + "\n")
                    print(f"  Saved record for {pdf_path.name}")
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
            raise

if __name__ == "__main__":
    try:
        process_pdfs(INPUT_DIR, OUTPUT_FILE)
        print(f"Saved extracted PDF text to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)