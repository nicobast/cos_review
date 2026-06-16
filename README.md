COS Review Project
This project automates the extraction and analysis of scientific papers related to autism spectrum disorder (ASD) and related neurodevelopmental conditions. It extracts text from PDFs, processes them through an LLM to extract structured data, and saves the results.

# Setup Instructions
1. Clone Repository

<pre lang="md"><code>```bash
git clone <repository-url>
cd cos_review
```</code></pre>

2. Create Virtual Environment

<pre lang="md"><code>```bash
python -m venv venv
venv\Scripts\activate  # Windows
```</code></pre>

3. Install Dependencies

<pre lang="md"><code>```bash
pip install -r requirements.txt
```</code></pre>

4. Set Up Environment Variables

- Set your LLM API key as a Windows environment variable.
- run in CMD with admin rights:

<pre lang="md"><code>```cmd
setx LLM_API_KEY "your_actual_api_key_here"
```</code></pre>

# Project Structure

cos_review/
├── 00_extract_pdfs.py          # Extract text from PDF files
├── 01_debug_extraction.py      # Debug and analyze extraction results
├── 02_llm_database.py          # Process extracted text with LLM to extract structured data
├── llm_config.json             # LLM configuration settings
├── test_connection.py          # Test OpenAI API connection
├── README.md                   # This file
├── requirements.txt            # Python dependencies
└── rayyan downloads/           # Input directory for PDF files
└── outputs/                    # Output directory for extracted data

# Usage Workflow

1. Place PDF files in the rayyan downloads directory
2. Run PDF extraction:

<pre lang="md"><code>```bash
python 00_extract_pdfs.py
```</code></pre>

3. Debug extraction results:

<pre lang="md"><code>```bash
python 01_debug_extraction.py
```</code></pre>

4. Process with LLM:

<pre lang="md"><code>```bash
python 02_llm_database.py
```</code></pre>

- generates an extracted_table.csv in outputs/02_pdf_runs/union

# Requirements

Dependencies are listed in requirements.txt:

- pypdf
- pdfplumber (optional but recommended)
- openai
- python-dotenv (for .env support)

Install with:

<pre lang="md"><code>```bash
pip install -r requirements.txt
```</code></pre>

# Security Notes

- Never commit API keys to version control
- Use environment variables or .env files
- Add .env and llm_config.json to .gitignore
- The project is designed to read API keys from environment variables only

# Troubleshooting

Common Issues:

- UnicodeDecodeError: Usually caused by PDF encoding issues. The scripts include robust error handling.
- Missing API Key: Ensure LLM_API_KEY is set in environment variables.
- No PDF Files: Place PDFs in the rayyan downloads directory.
- Connection Errors: Verify network connectivity and API endpoint URL.

<pre lang="md"><code>```bash
# Check if API key is accessible
python -c "import os; print(os.environ.get('LLM_API_KEY'))"
# Test LLM connection
python test_connection.py
# View extraction results
python 01_debug_extraction.py
```</code></pre>