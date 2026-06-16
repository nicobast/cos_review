# Updated 00_extract_pdfs.py
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
except ImportError:
    print("Warning: pdfplumber not installed. Install with `pip install pdfplumber` for better text extraction.")

ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT.parent / "rayyan downloads"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "00_pdf_text.jsonl"

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Improved text extraction with fallback methods."""
    try:
        # Try basic pypdf extraction first
        reader = PdfReader(str(pdf_path))
        pages = []
        
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                pages.append(page_text)
            else:
                # Try alternative extraction methods
                try:
                    with PDF.open(pdf_path) as pdf:
                        page_text = pdf.pages[page_num-1].extract_text()
                        if page_text and page_text.strip():
                            pages.append(page_text)
                except:
                    pages.append("")
        
        result = "\n\n".join(pages).strip()
        
        # If still empty, try extracting text from all pages together
        if not result:
            try:
                with PDF.open(pdf_path) as pdf:
                    full_text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
                    result = full_text.strip()
            except:
                pass
                
        return result if result else ""
        
    except PdfReadError as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""
    except Exception as e:
        print(f"Unexpected error with {pdf_path}: {e}")
        return ""

def process_pdfs(input_dir: Path, output_file: Path) -> None:
    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {input_dir}")

    with output_file.open("w", encoding="utf-8") as out_f:
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
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    process_pdfs(INPUT_DIR, OUTPUT_FILE)
    print(f"Saved extracted PDF text to {OUTPUT_FILE}")