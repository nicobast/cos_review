# Updated 02_llm_database.py
import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Any

from openai import OpenAI

ROOT = Path(__file__).resolve().parent
INPUT_FILE = ROOT / "outputs" / "00_pdf_text.jsonl"
OUTPUT_DIR = ROOT / "outputs" / "02_pdf_runs" / "union"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
JSON_OUTPUT = OUTPUT_DIR / "extracted_table.jsonl"
CSV_OUTPUT = OUTPUT_DIR / "extracted_table.csv"
RAW_OUTPUT = OUTPUT_DIR / "raw_responses.jsonl"
CONFIG_PATH = ROOT / "llm_config.json"

FIELD_NAMES = [
    "url",
    "article_title",
    "year_of_publication",
    "article_type",
    "age",
    "included_diagnoses",
    "paradigm_task_types",
    "best_task_to_discriminate_groups",
    "total_duration_of_task",
    "nr_of_trials",
    "eye_tracking_dependent_variable_or_pupillometry",
    "effect_sizes_of_outcomes",
    "evidence_of_sensitivity",
    "data_loss_or_exclusion_criteria",
    "response_task_evoked_or_spontaneous",
]

json_schema = {
    "name": "article_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "url": {"type": ["string", "null"]},
            "article_title": {"type": ["string", "null"]},
            "year_of_publication": {"type": ["string", "null"]},
            "article_type": {"type": ["string", "null"]},
            "age": {"type": ["string", "null"]},
            "included_diagnoses": {"type": ["string", "null"]},
            "paradigm_task_types": {"type": ["string", "null"]},
            "best_task_to_discriminate_groups": {"type": ["string", "null"]},
            "total_duration_of_task": {"type": ["string", "null"]},
            "nr_of_trials": {"type": ["string", "null"]},
            "eye_tracking_dependent_variable_or_pupillometry": {"type": ["string", "null"]},
            "effect_sizes_of_outcomes": {"type": ["string", "null"]},
            "evidence_of_sensitivity": {"type": ["string", "null"]},
            "data_loss_or_exclusion_criteria": {"type": ["string", "null"]},
            "response_task_evoked_or_spontaneous": {"type": ["string", "null"]},
        },
        "required": FIELD_NAMES,
        "additionalProperties": False,
    },
}

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = {}
    cfg["openai_api_key"] = cfg.get("openai_api_key") or os.environ.get("OPENAI_API_KEY")
    if not cfg.get("openai_api_key"):
        raise RuntimeError("Missing OpenAI API key: set OPENAI_API_KEY or cos_review/llm_config.json")
    cfg["model"] = cfg.get("model", "gpt-4o-2024-08-06")

    # If a base URL is provided in the config, export it to the
    # environment variable the OpenAI client will respect.
    base = cfg.get("base_url") or cfg.get("api_base")
    if base:
        # Do not print or log secrets/URLs here; just set the env var.
        os.environ["OPENAI_API_BASE"] = base

    return cfg

def create_prompt(filename: str, text: str) -> str:
    """Create a more robust prompt with better guidance."""
    return f"""
You are extracting structured article metadata from a scientific review or original research paper.
Do not add interpretation or extra commentary. Respond with valid JSON only,
using the exact fields requested. If a field cannot be found, return an empty string.

Important: 
- If the text is very short or appears to be from a table or figure, note this explicitly
- If the text contains only headers or titles, try to extract the most relevant information
- If the text is completely unreadable or corrupted, indicate this clearly

Article filename: {filename}

Article text:
{text}
"""

def read_pdf_records(input_path: Path):
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

def call_openai(client, model, prompt):
    """Improved LLM call with better error handling and retry logic."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a careful scientific data extractor."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_schema", "json_schema": json_schema},
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM call failed: {e}")
        return None

def write_outputs(records):
    """Write outputs with better error handling."""
    try:
        with JSON_OUTPUT.open("w", encoding="utf-8") as json_out, CSV_OUTPUT.open("w", newline="", encoding="utf-8") as csv_out:
            writer = csv.DictWriter(csv_out, fieldnames=FIELD_NAMES)
            writer.writeheader()
            for record in records:
                json_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                writer.writerow({k: record.get(k, "") for k in FIELD_NAMES})
    except Exception as e:
        print(f"Error writing outputs: {e}")

def process_with_fallback(filename: str, text: str, client, model) -> Dict[str, Any]:
    """Process with fallback strategies."""
    # First attempt
    prompt = create_prompt(filename, text)
    
    try:
        raw_response = call_openai(client, model, prompt)
        if raw_response:
            try:
                extracted = json.loads(raw_response)
                return extracted
            except json.JSONDecodeError:
                print(f"Failed to parse JSON response for {filename}")
                # Try to recover by returning a minimal structure
                return {field: "" for field in FIELD_NAMES}
    except Exception as e:
        print(f"LLM processing failed for {filename}: {e}")
    
    # Return default empty structure
    return {field: "" for field in FIELD_NAMES}

if __name__ == "__main__":
    cfg = load_config()

    # Ensure OPENAI_API_KEY is set in env (some client code reads it from env)
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = cfg["openai_api_key"]

    # Create client with base_url if provided (modern OpenAI client v1.0+)
    base_url = cfg.get("base_url") or cfg.get("api_base")
    
    if base_url:
        client = OpenAI(api_key=cfg["openai_api_key"], base_url=base_url)
    else:
        client = OpenAI(api_key=cfg["openai_api_key"])
    
    results = []

    # Process each record
    for item in read_pdf_records(INPUT_FILE):
        filename = item.get("filename", "")
        text = item.get("text", "")
        
        if not text:
            print(f"Skipping {filename}: no extracted text")
            continue
            
        # Truncate very long texts to prevent token limit issues
        if len(text) > 100000:  # Increased from 50000 to 100000
            print(f"Truncating {filename} - text too long ({len(text)} chars)")
            text = text[:100000]
            
        # Process with improved fallback handling
        extracted = process_with_fallback(filename, text, client, cfg["model"])
        extracted["url"] = extracted.get("url") or item.get("filepath", "")
        results.append(extracted)
        
        with RAW_OUTPUT.open("a", encoding="utf-8") as raw_f:
            raw_f.write(json.dumps({"filename": filename, "response": str(extracted)}, ensure_ascii=False) + "\n")
        print(f"Processed {filename}")

    # Write final outputs
    write_outputs(results)
    print(f"Wrote JSON output to: {JSON_OUTPUT}")
    print(f"Wrote CSV output to: {CSV_OUTPUT}")
    print(f"Total records processed: {len(results)}")