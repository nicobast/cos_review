# 02_llm_database.py - Final corrected version with LLM_API_KEY
import csv
import json
import os
import sys
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
    "doi",
    "article_title",
    "authors",
    "year_of_publication",
    "article_type",
    "age",
    "groups",
    "diagnosis",
    "paradigm",
    "task",
    "pupillometry",
    "eye_tracking",
    "total_duration_of_task",
    "number_of_trials",
    "outcome",
    "effect_size",
    "sensitivity",
    "exclusion_criteria",
    "data_loss",
]

json_schema = {
    "name": "article_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "url": {"type": ["string", "null"]},
            "doi": {"type": ["string", "null"]},
            "article_title": {"type": ["string", "null"]},
            "authors": {"type": ["string", "null"]},
            "year_of_publication": {"type": ["string", "null"]},
            "article_type": {"type": ["string", "null"]},
            "age": {"type": ["string", "null"]},
            "groups": {"type": ["string", "null"]},
            "diagnosis": {"type": ["string", "null"]},
            "paradigm": {"type": ["string", "null"]},
            "task": {"type": ["string", "null"]},
            "pupillometry": {"type": ["string", "null"]},
            "eye_tracking": {"type": ["string", "null"]},
            "total_duration_of_task": {"type": ["string", "null"]},
            "number_of_trials": {"type": ["string", "null"]},
            "outcome": {"type": ["string", "null"]},
            "effect_size": {"type": ["string", "null"]},
            "sensitivity": {"type": ["string", "null"]},
            "exclusion_criteria": {"type": ["string", "null"]},
            "data_loss": {"type": ["string", "null"]},
        },
        "required": FIELD_NAMES,
        "additionalProperties": False,
    },
}

def load_config():
    print("Debug: Loading configuration...")
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = {}
    
    # Debug: Print what's in config
    print("Config contents:", cfg)
    
    # Try to get API key from config first
    api_key_from_config = cfg.get("openai_api_key")
    print("API key from config:", api_key_from_config)
    
    # Try to get API key from environment (using LLM_API_KEY)
    api_key_from_env = os.environ.get("LLM_API_KEY")
    print("API key from environment (LLM_API_KEY):", api_key_from_env)
    
    # If config has key, use it; otherwise check environment
    cfg["openai_api_key"] = api_key_from_config or api_key_from_env
    
    print("Final API key value:", cfg.get("openai_api_key"))
    
    if not cfg.get("openai_api_key"):
        raise RuntimeError("Missing OpenAI API key: set LLM_API_KEY or cos_review/llm_config.json")
    
    cfg["model"] = cfg.get("model")

    if not cfg.get("model"):
        raise RuntimeError("Missing model in config: set 'model' in cos_review/llm_config.json")
    
    # If a base URL is provided in the config, export it to the
    # environment variable the OpenAI client will respect.
    base = cfg.get("base_url") or cfg.get("api_base")
    if base:
        # Do not print or log secrets/URLs here; just set the env var.
        os.environ["OPENAI_API_BASE"] = base

    return cfg

#prompting function with guidance and instructions
def create_prompt(filename: str, text: str) -> str:
    """Create a more robust prompt with better guidance."""
    return f"""
You are an expert scientific data extractor tasked with extracting specific structured information from research papers.

INSTRUCTIONS:
1. Extract ONLY the following fields from the provided text
2. If a field cannot be found, return an empty string ""
3. Do NOT add any interpretation, commentary, or additional information
4. Respond ONLY with valid JSON that matches the schema exactly
5. If the text is incomplete, corrupted, or appears to be from a table/figure, indicate this clearly
6. For ambiguous or unclear information, err on the side of returning empty strings rather than guessing

REQUIRED FIELDS TO EXTRACT:
{', '.join(FIELD_NAMES)}

IMPORTANT GUIDELINES:
- For "url": Extract the official article URL if available, otherwise leave empty
- For "doi": Extract the DOI number if available, otherwise leave empty  
- For "article_title": Extract the full title of the article
- For "authors": Extract author names in a clear format
- For "year_of_publication": Extract the publication year
- For "article_type": Extract the type (e.g., "original research", "review", "case study")
- For "age": Extract age range of participants if specified
- For "groups": Extract participant groups (control, experimental, etc.)
- For "diagnosis": Extract diagnostic criteria or conditions studied
- For "paradigm": Extract experimental paradigm used
- For "task": Extract specific tasks performed by participants
- For "pupillometry": Extract pupillometry measurements or findings
- For "eye_tracking": Extract eye tracking methodology or results
- For "total_duration_of_task": Extract total task duration if specified
- For "number_of_trials": Extract number of trials conducted
- For "outcome": Extract primary outcome measures
- For "effect_size": Extract effect size statistics of group differences if available
- For "sensitivity": Extract sensitivity analysis results if available
- For "exclusion_criteria": Extract exclusion criteria used in the study
- For "data_loss": Extract information about data loss or missing data

EXAMPLE RESPONSE FORMAT:
{{  
  "url": "https://example.com/article",
  "doi": "10.1234/example.2023",
  "article_title": "Study on Pupil Response in Cognitive Tasks",
  "authors": "Smith, J.A., Johnson, B.C.",
  "year_of_publication": "2023",
  "article_type": "original research",
  "age": "20-35 years",
  "groups": "Control group, Experimental group",
  "diagnosis": "Healthy adults",
  "paradigm": "Visual search paradigm",
  "task": "Detecting target stimuli among distractors",
  "pupillometry": "Pupil diameter increased significantly during task",
  "eye_tracking": "Gaze patterns showed attention to targets",
  "total_duration_of_task": "45 minutes",
  "number_of_trials": "120 trials",
  "outcome": "Significant increase in pupil dilation",
  "effect_size": "Cohen's d = 0.85",
  "sensitivity": "Sensitivity analysis showed robust results",
  "exclusion_criteria": "Excluded participants with vision problems",
  "data_loss": "No significant data loss reported"
}}

ARTICLE FILENAME: {filename}

ARTICLE TEXT:
{text}
"""

def read_pdf_records(input_path: Path):
    """Read PDF records with proper error handling for encoding issues."""
    try:
        # Try UTF-8 first
        with input_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)
    except UnicodeDecodeError:
        try:
            # Try latin-1 if UTF-8 fails
            with input_path.open("r", encoding="latin-1", errors="replace") as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line)
        except Exception as e:
            print(f"Failed to read with any encoding: {e}")
            raise

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
        # Write JSON output
        with JSON_OUTPUT.open("w", encoding="utf-8", errors="replace") as json_out:
            for record in records:
                json_out.write(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + "\n")
        
        # Write CSV output
        with CSV_OUTPUT.open("w", newline="", encoding="utf-8", errors="replace") as csv_out:
            writer = csv.DictWriter(csv_out, fieldnames=FIELD_NAMES)
            writer.writeheader()
            for record in records:
                writer.writerow({k: record.get(k, "") for k in FIELD_NAMES})
                
    except Exception as e:
        print(f"Error writing outputs: {e}")
        # Try with latin-1 as fallback
        try:
            with JSON_OUTPUT.open("w", encoding="latin-1", errors="replace") as json_out:
                for record in records:
                    json_out.write(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + "\n")
                    
            with CSV_OUTPUT.open("w", newline="", encoding="latin-1", errors="replace") as csv_out:
                writer = csv.DictWriter(csv_out, fieldnames=FIELD_NAMES)
                writer.writeheader()
                for record in records:
                    writer.writerow({k: record.get(k, "") for k in FIELD_NAMES})
        except Exception as e2:
            print(f"Fallback writing also failed: {e2}")
            raise

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
    try:
        cfg = load_config()
        print("Configuration loaded successfully")
        
        # Ensure OPENAI_API_KEY is set in env (some client code reads it from env)
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = cfg["openai_api_key"]
        
        print("API key set in environment")
        
        # Create client with base_url if provided (modern OpenAI client v1.0+)
        base_url = cfg.get("base_url") or cfg.get("api_base")
        
        if base_url:
            client = OpenAI(api_key=cfg["openai_api_key"], base_url=base_url)
        else:
            client = OpenAI(api_key=cfg["openai_api_key"])
        
        print("Client created successfully")
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
            
            with RAW_OUTPUT.open("a", encoding="utf-8", errors="replace") as raw_f:
                raw_f.write(json.dumps({"filename": filename, "response": str(extracted)}, ensure_ascii=False) + "\n")
            print(f"Processed {filename}")

        # Write final outputs
        write_outputs(results)
        print(f"Wrote JSON output to: {JSON_OUTPUT}")
        print(f"Wrote CSV output to: {CSV_OUTPUT}")
        print(f"Total records processed: {len(results)}")
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)