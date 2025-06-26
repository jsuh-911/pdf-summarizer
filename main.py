#!/usr/bin/env python3
import click
import os
from pathlib import Path
from typing import List
from rich.console import Console

from summarizer import PDFSummarizer
from config import Config

console = Console()

@click.group()
def cli():
    """PDF Summarizer with Ollama - Create Blinkist-style summaries and categorize PDFs"""
    pass

@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--model', '-m', default=None, help='Ollama model to use')
@click.option('--no-llm-keywords', is_flag=True, help='Skip LLM keyword extraction')
def process(pdf_path: str, model: str, no_llm_keywords: bool):
    """Process a single PDF file"""
    summarizer = PDFSummarizer(model=model)
    
    if not summarizer.check_ollama_connection():
        return
    
    result = summarizer.process_single_pdf(pdf_path, use_llm_keywords=not no_llm_keywords)
    
    if result:
        summarizer.display_results([result])
        summary = result['summary']
        if isinstance(summary, dict):
            console.print(f"\n[bold green]Structured Summary:[/bold green]")
            for key, value in summary.items():
                if key != "error":
                    if key == "BibTeX Citation":
                        console.print(f"\n[cyan]{key}:[/cyan]")
                        console.print(f"[dim]{value}[/dim]")
                    elif isinstance(value, dict):
                        console.print(f"\n[cyan]{key}:[/cyan]")
                        for sub_key, sub_value in value.items():
                            console.print(f"  • {sub_key}: {sub_value}")
                    elif isinstance(value, list):
                        console.print(f"\n[cyan]{key}:[/cyan] {', '.join(map(str, value))}")
                    else:
                        console.print(f"\n[cyan]{key}:[/cyan] {value}")
        else:
            console.print(f"\n[bold green]Summary:[/bold green]\n{summary}")
    else:
        console.print("[red]Failed to process PDF[/red]")

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--model', '-m', default=None, help='Ollama model to use')
@click.option('--no-llm-keywords', is_flag=True, help='Skip LLM keyword extraction')
@click.option('--report', '-r', is_flag=True, help='Generate markdown report')
def batch(directory: str, model: str, no_llm_keywords: bool, report: bool):
    """Process all PDF files in a directory"""
    pdf_files = list(Path(directory).glob('*.pdf'))
    
    if not pdf_files:
        console.print(f"[red]No PDF files found in {directory}[/red]")
        return
    
    console.print(f"Found {len(pdf_files)} PDF files")
    
    summarizer = PDFSummarizer(model=model)
    
    if not summarizer.check_ollama_connection():
        return
    
    results = summarizer.process_multiple_pdfs(
        [str(p) for p in pdf_files], 
        use_llm_keywords=not no_llm_keywords
    )
    
    if results:
        summarizer.display_results(results)
        
        if report:
            report_path = summarizer.create_category_report(results)
            console.print(f"[blue]Report created:[/blue] {report_path}")
    else:
        console.print("[red]No PDFs were successfully processed[/red]")

@cli.command()
def setup():
    """Setup the environment and check dependencies"""
    console.print("[bold]PDF Summarizer Setup[/bold]")
    
    # Check Ollama installation
    console.print("\n[blue]Checking Ollama...[/blue]")
    if os.system("ollama --version > /dev/null 2>&1") == 0:
        console.print("[green]✓[/green] Ollama is installed")
    else:
        console.print("[red]✗[/red] Ollama not found. Install from: https://ollama.ai")
        return
    
    # Check if Ollama is running
    if os.system("ollama list > /dev/null 2>&1") == 0:
        console.print("[green]✓[/green] Ollama is running")
    else:
        console.print("[red]✗[/red] Ollama is not running. Start with: ollama serve")
        return
    
    # Check for default model
    summarizer = PDFSummarizer()
    if summarizer.check_ollama_connection():
        console.print(f"[green]✓[/green] Model '{Config.OLLAMA_MODEL}' is available")
    else:
        console.print(f"[yellow]![/yellow] Model '{Config.OLLAMA_MODEL}' not found")
        console.print(f"Install with: ollama pull {Config.OLLAMA_MODEL}")
    
    # Check output directory
    if Path(Config.OUTPUT_DIR).exists():
        console.print(f"[green]✓[/green] Output directory: {Config.OUTPUT_DIR}")
    else:
        console.print(f"[yellow]![/yellow] Creating output directory: {Config.OUTPUT_DIR}")
        Path(Config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    console.print("\n[bold green]Setup complete![/bold green]")
    console.print("\nExample usage:")
    console.print("  python main.py process document.pdf")
    console.print("  python main.py batch ./pdfs --report")

@cli.command()
def models():
    """List available Ollama models"""
    console.print("[bold]Available Ollama Models:[/bold]")
    
    try:
        from ollama import Client
        client = Client()
        models = client.list()
        
        if not models['models']:
            console.print("[yellow]No models installed[/yellow]")
            console.print("Install a model: ollama pull llama2")
            return
        
        for model in models['models']:
            name = model['name']
            size = model.get('size', 0) / (1024**3)  # Convert to GB
            console.print(f"  {name} ({size:.1f}GB)")
            
    except Exception as e:
        console.print(f"[red]Error listing models:[/red] {e}")

@cli.command()
def test_filenames():
    """Test filename generation with different author/year combinations"""
    from summarizer import PDFSummarizer
    
    summarizer = PDFSummarizer()
    
    test_cases = [
        {
            "name": "Single author with year",
            "result": {"summary": {"Author(s)": "David A. Loeffler", "Year Published": 2019}},
            "original_path": "/test/document.pdf"
        },
        {
            "name": "Two authors with year", 
            "result": {"summary": {"Author(s)": "David A. Loeffler and Jan O. Aasly", "Year Published": 2019}},
            "original_path": "/test/document.pdf"
        },
        {
            "name": "Multiple authors with year",
            "result": {"summary": {"Author(s)": "Livia H. Morais, Joseph C. Boktor, Siamak MahmoudianDehkordi", "Year Published": 2024}},
            "original_path": "/test/document.pdf"
        },
        {
            "name": "Single author no year",
            "result": {"summary": {"Author(s)": "Kimberly C. Paul", "Year Published": ""}},
            "original_path": "/test/document.pdf"
        },
        {
            "name": "No author info",
            "result": {"summary": {"Author(s)": "Not specified", "Year Published": 2023}},
            "original_path": "/test/research_paper.pdf"
        },
        {
            "name": "Comma-separated format",
            "result": {"summary": {"Author(s)": "Smith, John A., Jones, Mary B.", "Year Published": 2023}},
            "original_path": "/test/document.pdf"
        }
    ]
    
    console.print("[bold]Testing filename generation rules:[/bold]\n")
    
    for test in test_cases:
        filename = summarizer._generate_filename(test["result"], test["original_path"])
        console.print(f"[cyan]{test['name']}:[/cyan]")
        console.print(f"  Input: {test['result']['summary'].get('Author(s)', 'N/A')} ({test['result']['summary'].get('Year Published', 'N/A')})")
        console.print(f"  Output: [green]{filename}[/green]")
        console.print()

@cli.command()
def test_json():
    """Create a test JSON file to verify output format"""
    from datetime import datetime
    import json
    from pathlib import Path
    
    # Create test data matching our output format
    test_data = {
        "source_file": "test_document.pdf",
        "processed_at": datetime.now().isoformat(),
        "pdf_metadata": {
            "title": "Test Document",
            "author": "Test Author",
            "filename": "test_document.pdf",
            "pages": 10
        },
        "structured_summary": {
            "Title": "Sample Research Paper on PDF Processing",
            "Author(s)": "David A. Loeffler and Jan O. Aasly",
            "Year Published": 2024,
            "Journal": "Journal of Document Processing",
            "BibTeX Citation": "@article{Author2024,\n  title={Sample Research Paper on PDF Processing},\n  author={Test Author and Co-Author},\n  journal={Journal of Document Processing},\n  year={2024},\n  note={Extracted from PDF}\n}",
            "Type": "research paper",
            "Categories": ["preclinical_models", "cellular_studies"],
            "Sample Size": "100 documents",
            "Method": "Automated text extraction and LLM processing",
            "Key Findings": {
                "Finding 1": "PDF processing accuracy ↑ 95% with structured prompts",
                "Finding 2": "Processing time ↓ 60% with optimized chunking", 
                "Finding 3": "JSON output → improved data usability"
            },
            "Prediction Model": "no",
            "Key Takeaways": "This study demonstrates effective PDF-to-JSON conversion using local LLMs. The structured approach significantly improves accuracy and processing speed while maintaining comprehensive data extraction. Results show promise for large-scale document processing applications."
        },
        "extracted_keywords": ["pdf", "processing", "llm", "json", "extraction"],
        "categorization": {
            "primary_category": "preclinical_models",
            "category_scores": {
                "preclinical_models": 0.9,
                "cellular_studies": 0.3,
                "clinical_trial": 0.1,
                "meta_analysis": 0.0,
                "review_article": 0.0
            }
        },
        "document_stats": {
            "word_count": 1500,
            "processing_timestamp": datetime.now().isoformat()
        }
    }
    
    # Ensure summaries directory exists
    output_dir = Path("./summaries")
    output_dir.mkdir(exist_ok=True)
    
    # Use the smart filename generation
    from summarizer import PDFSummarizer
    summarizer = PDFSummarizer()
    filename_base = summarizer._generate_filename({"summary": test_data["structured_summary"]}, "/test/test_document.pdf")
    
    # Save test files
    test_path = output_dir / f"{filename_base}_summary.json"
    simple_path = output_dir / f"{filename_base}_simple.json"
    
    with open(test_path, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    with open(simple_path, 'w', encoding='utf-8') as f:
        json.dump(test_data["structured_summary"], f, indent=2, ensure_ascii=False)
    
    console.print(f"[green]Test JSON files created:[/green]")
    console.print(f"  Full format: {test_path}")
    console.print(f"  Simple format: {simple_path}")

@cli.command()
@click.argument('examples_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
def show_examples(examples_dir: str):
    """Show example JSON structure from examples directory"""
    import json
    from pathlib import Path
    
    example_files = list(Path(examples_dir).glob('*.json'))
    
    if not example_files:
        console.print(f"[red]No JSON files found in {examples_dir}[/red]")
        return
    
    console.print(f"[bold]Found {len(example_files)} example files:[/bold]")
    
    for file_path in example_files[:3]:  # Show first 3 examples
        console.print(f"\n[cyan]File: {file_path.name}[/cyan]")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for key, value in data.items():
                if isinstance(value, dict):
                    console.print(f"[yellow]{key}:[/yellow]")
                    for sub_key, sub_value in list(value.items())[:3]:  # First 3 items
                        console.print(f"  • {sub_key}: {sub_value}")
                    if len(value) > 3:
                        console.print(f"  ... and {len(value) - 3} more")
                elif isinstance(value, list):
                    console.print(f"[yellow]{key}:[/yellow] {', '.join(map(str, value))}")
                else:
                    display_value = str(value)
                    if len(display_value) > 100:
                        display_value = display_value[:100] + "..."
                    console.print(f"[yellow]{key}:[/yellow] {display_value}")
        except Exception as e:
            console.print(f"[red]Error reading {file_path.name}: {e}[/red]")

@cli.command()
def init_db():
    """Initialize the PostgreSQL database"""
    import subprocess
    from pathlib import Path
    from database import DatabaseManager
    
    schema_path = Path("database_schema.sql")
    if not schema_path.exists():
        console.print("[red]database_schema.sql not found[/red]")
        return
    
    console.print("[blue]Initializing PostgreSQL database...[/blue]")
    
    try:
        # Try to connect to check if database exists
        db_manager = DatabaseManager()
        if db_manager.pool:
            console.print("[green]Database connection successful[/green]")
            
            # Execute schema
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            conn = db_manager.get_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute(schema)
                conn.commit()
                db_manager.return_connection(conn)
                
                console.print("[green]Database schema created successfully[/green]")
            else:
                console.print("[red]Could not get database connection[/red]")
        else:
            console.print("[red]Could not connect to database[/red]")
            console.print("Make sure PostgreSQL is running and database 'pdf_summarizer' exists")
            console.print("Create database with: createdb pdf_summarizer")
            
    except Exception as e:
        console.print(f"[red]Database initialization error: {e}[/red]")

@cli.command()
@click.option('--query', '-q', help='Text search query')
@click.option('--category', '-c', help='Filter by category')
@click.option('--year-from', type=int, help='Filter by year from')
@click.option('--year-to', type=int, help='Filter by year to')
@click.option('--author', '-a', help='Filter by author')
@click.option('--journal', '-j', help='Filter by journal')
@click.option('--limit', '-l', type=int, default=10, help='Number of results')
def search(query: str, category: str, year_from: int, year_to: int, 
           author: str, journal: str, limit: int):
    """Search documents in the database"""
    from database import DatabaseManager
    
    db_manager = DatabaseManager()
    if not db_manager.pool:
        console.print("[red]Database not connected[/red]")
        return
    
    results = db_manager.search_documents(
        query=query,
        category=category,
        year_from=year_from,
        year_to=year_to,
        author=author,
        journal=journal,
        limit=limit
    )
    
    if not results:
        console.print("[yellow]No documents found[/yellow]")
        return
    
    console.print(f"[green]Found {len(results)} documents:[/green]\n")
    
    for doc in results:
        console.print(f"[cyan]ID: {doc['id']}[/cyan] - [bold]{doc['title'] or 'No Title'}[/bold]")
        console.print(f"  Authors: {doc['authors'] or 'Unknown'}")
        console.print(f"  Year: {doc['year_published'] or 'Unknown'}")
        console.print(f"  Journal: {doc['journal'] or 'Unknown'}")
        console.print(f"  Category: {doc['primary_category']}")
        console.print(f"  Keywords: {', '.join(doc['keywords']) if doc['keywords'] and doc['keywords'][0] else 'None'}")
        console.print()

@cli.command()
def stats():
    """Show database statistics"""
    from database import DatabaseManager
    
    db_manager = DatabaseManager()
    if not db_manager.pool:
        console.print("[red]Database not connected[/red]")
        return
    
    stats = db_manager.get_statistics()
    
    console.print("[bold]Database Statistics[/bold]\n")
    console.print(f"Total Documents: [green]{stats['total_documents']}[/green]\n")
    
    if stats['by_category']:
        console.print("[bold]By Category:[/bold]")
        for category, count in stats['by_category'].items():
            console.print(f"  {category}: {count}")
        console.print()
    
    if stats['by_year']:
        console.print("[bold]By Year (Top 10):[/bold]")
        for year, count in stats['by_year'].items():
            console.print(f"  {year}: {count}")
        console.print()
    
    if stats['top_journals']:
        console.print("[bold]Top Journals:[/bold]")
        for journal, count in stats['top_journals'].items():
            console.print(f"  {journal}: {count}")

@cli.command()
@click.option('--summaries-dir', default='./summaries', help='Summaries directory path')
def sync_db(summaries_dir: str):
    """Sync JSON files from summaries folder to database (no duplicates)"""
    from database import DatabaseManager
    from pathlib import Path
    
    db_manager = DatabaseManager()
    if not db_manager.pool:
        console.print("[red]Database not connected[/red]")
        console.print("Make sure PostgreSQL is running and database is initialized:")
        console.print("  createdb pdf_summarizer")
        console.print("  pixi run init-db")
        return
    
    summaries_path = Path(summaries_dir)
    if not summaries_path.exists():
        console.print(f"[red]Summaries directory not found: {summaries_dir}[/red]")
        return
    
    console.print(f"[blue]Syncing summaries from: {summaries_path.absolute()}[/blue]")
    stats = db_manager.sync_from_summaries_folder(summaries_dir)
    
    if stats["added"] > 0:
        console.print(f"\n[green]Successfully added {stats['added']} new documents to database![/green]")

@cli.command()
@click.argument('doc_id', type=int)
def show(doc_id: int):
    """Show detailed document information"""
    from database import DatabaseManager
    
    db_manager = DatabaseManager()
    if not db_manager.pool:
        console.print("[red]Database not connected[/red]")
        return
    
    doc = db_manager.get_document_by_id(doc_id)
    if not doc:
        console.print(f"[red]Document with ID {doc_id} not found[/red]")
        return
    
    console.print(f"[bold]{doc['title'] or 'No Title'}[/bold]\n")
    console.print(f"[cyan]ID:[/cyan] {doc['id']}")
    console.print(f"[cyan]Authors:[/cyan] {doc['authors'] or 'Unknown'}")
    console.print(f"[cyan]Year:[/cyan] {doc['year_published'] or 'Unknown'}")
    console.print(f"[cyan]Journal:[/cyan] {doc['journal'] or 'Unknown'}")
    console.print(f"[cyan]Category:[/cyan] {doc['primary_category']}")
    console.print(f"[cyan]Sample Size:[/cyan] {doc['sample_size'] or 'Not specified'}")
    console.print(f"[cyan]Method:[/cyan] {doc['method'] or 'Not specified'}")
    
    if doc['keywords'] and doc['keywords'][0]:
        console.print(f"[cyan]Keywords:[/cyan] {', '.join(doc['keywords'])}")
    
    if doc['key_takeaways']:
        console.print(f"\n[bold]Key Takeaways:[/bold]\n{doc['key_takeaways']}")
    
    if doc['key_findings']:
        console.print(f"\n[bold]Key Findings:[/bold]")
        for finding in doc['key_findings']:
            if finding['name']:
                console.print(f"  • [yellow]{finding['name']}:[/yellow] {finding['description']}")

@cli.command()
@click.option('--key', required=True, help='Configuration key')
@click.option('--value', required=True, help='Configuration value')
def config(key: str, value: str):
    """Set configuration values"""
    env_file = Path('.env')
    
    # Read existing .env file
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    env_vars[k] = v
    
    # Update value
    env_vars[key.upper()] = value
    
    # Write back to .env
    with open(env_file, 'w') as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")
    
    console.print(f"[green]Set {key}={value}[/green]")

if __name__ == '__main__':
    cli()