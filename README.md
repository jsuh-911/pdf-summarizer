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

## Categories

The application automatically categorizes content into these categories:

- **Business**: Management, leadership, strategy, marketing
- **Technology**: Programming, AI, data science, software
- **Self-help**: Productivity, habits, personal development
- **Science**: Research, biology, physics, psychology
- **Finance**: Investing, economics, trading, wealth
- **Health**: Fitness, nutrition, wellness, medicine
- **History**: Historical events, politics, society
- **Philosophy**: Ethics, thinking, wisdom, meaning

## Output

For each processed PDF, the application creates:

1. **JSON Summary File**: Complete processing results with metadata
2. **Console Display**: Formatted table with key information
3. **Markdown Report** (optional): Organized by category

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
    "Type": "research paper",
    "Categories": ["category1", "category2"],
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
    "business": 0.8,
    "technology": 0.3,
    ...
  },
  "primary_category": "business",
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