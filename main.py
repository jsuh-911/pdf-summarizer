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
                    if isinstance(value, dict):
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