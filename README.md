# PDF Summarizer with Ollama

A Python application that uses local LLMs through Ollama to create Blinkist-style summaries of PDF documents and categorize them by keywords.

## Features

- **PDF Text Extraction**: Extract text from PDFs using PyPDF2 and pdfplumber
- **Structured JSON Summaries**: Generate scientific paper-style structured summaries with key findings, methodology, and takeaways
- **Keyword Extraction**: Extract keywords using both LLM and TF-IDF methods
- **Content Categorization**: Automatically categorize PDFs into topics (business, technology, self-help, etc.)
- **Batch Processing**: Process multiple PDFs in a directory
- **Rich Console Output**: Beautiful terminal interface with progress tracking
- **Report Generation**: Create markdown reports organized by category

## Prerequisites

**Option 1: Pixi (Recommended)**
- **Pixi** - Install from [https://pixi.sh](https://pixi.sh)
- **Note**: Uses conda-forge only for Python runtime, all packages from PyPI

**Option 2: Pure Python/PyPI (Enterprise-friendly)**
- **Python 3.8+** 
- **No conda dependencies** - Uses only PyPI packages

## Installation

### Option 1: Using Pixi (Recommended)

1. Clone the repository:
```bash
cd pdf_summarizer
```

2. Install all dependencies and set up Ollama:
```bash
# Install Python dependencies
pixi install

# Complete development setup (installs Ollama, pulls model, starts service)
pixi run dev-setup
```

3. Set up PostgreSQL database (optional but recommended):
```bash
# Create database (if PostgreSQL is already installed)
createdb pdf_summarizer

# Initialize database schema
pixi run init-db

# Verify database setup
pixi run db-stats
```

### Option 2: Pure Python Setup (No conda-forge)

1. Clone the repository:
```bash
cd pdf_summarizer
```

2. Run the setup script:
```bash
# Automated setup
./setup.sh

# Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ollama pull mistral:latest
```

3. Set up PostgreSQL database (optional but recommended):
```bash
# Create database (if PostgreSQL is already installed)
createdb pdf_summarizer

# Initialize database schema (activate venv first)
source venv/bin/activate
python main.py init-db

# Verify database setup
python main.py stats
```

### Manual Ollama Setup (if needed)
```bash
# Install Ollama only
pixi run install-ollama

# Pull a language model
pixi run pull-model

# Start Ollama service
pixi run start-ollama

# Verify setup
pixi run setup
```

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Available configuration options:
- `OLLAMA_MODEL`: Model to use (default: llama2)
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)
- `OUTPUT_DIR`: Directory for output files (default: ./summaries)
- `MAX_CHUNK_SIZE`: Maximum text chunk size for processing

## Usage

### Process a single PDF
```bash
pixi run python main.py process document.pdf
# Or use the task shortcut
pixi run process document.pdf
```

### Process all PDFs in a directory
```bash
pixi run python main.py batch ./pdfs
# Or use the task shortcut
pixi run batch ./pdfs --report
```

### Generate a categorized report
```bash
pixi run python main.py batch ./pdfs --report
```

### Use a specific model
```bash
pixi run python main.py process document.pdf --model mistral
```

### Skip LLM keyword extraction (faster)
```bash
pixi run python main.py process document.pdf --no-llm-keywords
```

### List available models
```bash
pixi run python main.py models
# Or use the task shortcut
pixi run models
```

### Set configuration
```bash
pixi run python main.py config --key OLLAMA_MODEL --value mistral
```

### View example output format
```bash
pixi run python main.py show-examples /path/to/examples
```

### Test JSON output format
```bash
pixi run python main.py test-json
```

### Test filename generation rules
```bash
pixi run python main.py test-filenames
```

### Database Operations
```bash
# Initialize PostgreSQL database
pixi run init-db

# Search documents
pixi run python main.py search --query "metabolomics" --category "clinical_trial"

# Show database statistics  
pixi run db-stats

# View specific document
pixi run python main.py show 1
```

## PostgreSQL Database Integration

The application includes full PostgreSQL database integration for organizing and searching processed documents.

### Database Setup

1. **PostgreSQL Installation** (if not already installed):
   ```bash
   # macOS with Homebrew
   brew install postgresql
   brew services start postgresql
   
   # Ubuntu/Debian
   sudo apt install postgresql postgresql-contrib
   sudo systemctl start postgresql
   ```

2. **Create the PDF Summarizer Database**:
   ```bash
   # Create a new database specifically for this app
   createdb pdf_summarizer
   ```
   This creates an empty database named `pdf_summarizer`. PostgreSQL can have multiple databases - this creates one just for our application.

3. **Initialize Database Schema**:
   ```bash
   # Create tables, indexes, and schema structure
   pixi run init-db
   ```
   This creates all the tables (`documents`, `keywords`, `key_findings`, `category_scores`), indexes for fast searching, and database views.

4. **Verify Setup**:
   ```bash
   # Check that everything is working
   pixi run db-stats
   ```
   Should show "Total Documents: 0" confirming the database is ready.

**Troubleshooting Setup**:
```bash
# Check if PostgreSQL is running
pg_isready

# List all databases (should include pdf_summarizer after step 2)
psql -l

# Check if tables exist (should show tables after step 3)
psql -d pdf_summarizer -c "\dt"
```

### Database Schema

The database stores documents across multiple related tables:

- **`documents`**: Main document information (title, authors, year, journal, etc.)
- **`keywords`**: Extracted keywords (many-to-many with documents)
- **`key_findings`**: Research findings (one-to-many with documents)  
- **`category_scores`**: Categorization scores (one-to-many with documents)

### Search and Query Features

**Text Search**:
```bash
pixi run python main.py search --query "Parkinson's disease"
```

**Filter by Category**:
```bash
pixi run python main.py search --category "clinical_trial"
```

**Filter by Year Range**:
```bash
pixi run python main.py search --year-from 2020 --year-to 2024
```

**Filter by Author**:
```bash
pixi run python main.py search --author "Loeffler"
```

**Filter by Journal**:
```bash
pixi run python main.py search --journal "Nature"
```

**Combined Filters**:
```bash
pixi run python main.py search \
  --query "metabolomics biomarkers" \
  --category "preclinical_models" \
  --year-from 2022 \
  --limit 20
```

### Database Statistics

View comprehensive statistics:
```bash
pixi run db-stats
```

Shows:
- Total documents count
- Distribution by research category
- Distribution by publication year
- Top journals by document count

### Document Management

**View Detailed Document**:
```bash
pixi run python main.py show 5
```

Displays complete document information including:
- Metadata (title, authors, year, journal)
- Research categorization
- Keywords and key findings
- Full key takeaways text

### Configuration

Database settings in `.env`:
```bash
DATABASE_URL=postgresql://localhost/pdf_summarizer
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pdf_summarizer
DB_USER=postgres
DB_PASSWORD=your_password
```

## Categories

The application automatically categorizes research content into these study types:

- **Clinical Trial**: Human clinical trials, RCTs, therapeutic interventions, patient studies
- **Preclinical Models**: Animal studies, in vivo experiments, disease models, pharmacokinetics
- **Cellular Studies**: In vitro studies, cell culture, molecular biology, gene expression
- **Meta Analysis**: Systematic reviews, pooled analyses, evidence synthesis
- **Review Article**: Literature reviews, perspectives, commentaries, overviews

## Output

For each processed PDF, the application creates:

1. **Full JSON Summary File** (`{filename}_summary.json`): Complete processing results with metadata, categorization, and document stats
2. **Simple JSON File** (`{filename}_simple.json`): Clean format matching research paper examples (Title, Author, BibTeX, Key Findings, etc.)
3. **Console Display**: Formatted table with key information
4. **Markdown Report** (optional): Organized by category

All JSON files are automatically saved to the `./summaries/` directory.

### Example Output Structure

```json
{
  "metadata": {
    "title": "Document Title",
    "author": "Author Name", 
    "filename": "document.pdf",
    "pages": 250
  },
  "summary": {
    "Title": "Document title or main topic",
    "Author(s)": "Primary author(s)",
    "Year Published": 2024,
    "Journal": "Journal or publication venue",
    "BibTeX Citation": "@article{AuthorYear,\n  title={Title},\n  author={Author Name},\n  journal={Journal Name},\n  year={2024},\n  note={Extracted from PDF}\n}",
    "Type": "research paper",
    "Categories": ["preclinical_models", "cellular_studies"],
    "Sample Size": "Study size if applicable",
    "Method": "Methodology or approach",
    "Key Findings": {
      "Finding 1": "Description with direction ↑/↓",
      "Finding 2": "Description with impact",
      "Finding 3": "Statistical results"
    },
    "Prediction Model": "yes/no",
    "Key Takeaways": "Comprehensive summary covering insights, implications, and significance..."
  },
  "keywords": ["keyword1", "keyword2", ...],
  "categories": {
    "preclinical_models": 0.8,
    "cellular_studies": 0.3,
    "clinical_trial": 0.1,
    "meta_analysis": 0.0,
    "review_article": 0.0
  },
  "primary_category": "preclinical_models",
  "word_count": 15000,
  "processed_at": "2024-01-15T10:30:00"
}
```

## VS Code Integration

For the best development experience:

1. Open the project in VS Code
2. Install the Python extension
3. Select the appropriate Python interpreter
4. Use the integrated terminal for running commands

### Recommended VS Code Extensions
- Python
- Pylance
- Jupyter (if you want to experiment with the code in notebooks)

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
pixi run start-ollama

# Check available models
pixi run models

# Or use ollama directly
ollama list
```

### Model Not Found
```bash
# Pull the required model
pixi run pull-model

# Or pull a specific model
ollama pull llama2:7b
```

### PDF Extraction Issues
- Try using `--no-llm-keywords` for faster processing
- Some PDFs might have OCR issues - consider pre-processing with OCR tools
- Very large PDFs might need chunking - adjust `MAX_CHUNK_SIZE` in config

### Performance Tips
- Use smaller models for faster processing: `llama2:7b` instead of `llama2:13b`
- Skip LLM keywords with `--no-llm-keywords` for 2x speed improvement
- Process PDFs in smaller batches for better memory management

## Examples

```bash
# Quick start - complete setup and process a single PDF
pixi run dev-setup
pixi run process ~/Downloads/book.pdf

# Process all PDFs in Downloads folder with report
pixi run batch ~/Downloads --report

# Use faster model and skip LLM keywords
pixi run python main.py batch ./pdfs --model llama2:7b --no-llm-keywords

# Setup and verify installation
pixi run setup

# Use predefined tasks
pixi run example-single  # Process example.pdf
pixi run example-batch   # Process ./pdfs directory

# Test JSON output functionality
pixi run test-json       # Create sample JSON files
```

## Output Files

Each PDF processed will create two JSON files in the `./summaries/` directory with **intelligent filename generation**:

### Filename Rules:
1. **Single author**: `LastName-YEAR` (e.g., `Loeffler-2019`)
2. **Two authors**: `FirstLast-SecondLast-YEAR` (e.g., `Loeffler-Aasly-2019`)
3. **Multiple authors**: Uses first two authors `First-Second-YEAR`
4. **No year**: Just author names (e.g., `Paul`)
5. **No author**: Falls back to original filename

### File Types:
- `{intelligent_name}_summary.json` - Full format with metadata and categorization
- `{intelligent_name}_simple.json` - Clean format matching research examples

Example directory structure after processing:
```
summaries/
├── Loeffler-2019_summary.json
├── Loeffler-2019_simple.json
├── Morais-Boktor-2024_summary.json
├── Morais-Boktor-2024_simple.json
├── Paul_summary.json
└── Paul_simple.json
```

## Pixi Tasks Reference

- `pixi run dev-setup` - Complete setup (Ollama + model + start service)
- `pixi run setup` - Verify installation
- `pixi run process <file>` - Process single PDF
- `pixi run batch <dir>` - Process directory
- `pixi run models` - List available models
- `pixi run install-ollama` - Install Ollama
- `pixi run pull-model` - Pull default model
- `pixi run start-ollama` - Start Ollama service
- `pixi run example-single` - Run example with single PDF
- `pixi run example-batch` - Run example with batch processing