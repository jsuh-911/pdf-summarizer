import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.progress import track
from rich.table import Table

from pdf_extractor import PDFExtractor
from ollama_client import OllamaClient
from categorizer import TextCategorizer
from config import Config

class PDFSummarizer:
    def __init__(self, model: str = None):
        self.console = Console()
        self.pdf_extractor = PDFExtractor()
        self.ollama_client = OllamaClient(model=model)
        self.categorizer = TextCategorizer()
        self.output_dir = Path(Config.OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)
        
    def check_ollama_connection(self) -> bool:
        """Check if Ollama is running and model is available"""
        if not self.ollama_client.is_model_available():
            self.console.print(f"[red]Error: Model '{self.ollama_client.model}' not available[/red]")
            self.console.print("Make sure Ollama is running and the model is installed:")
            self.console.print(f"ollama pull {self.ollama_client.model}")
            return False
        return True
    
    def process_single_pdf(self, pdf_path: str, use_llm_keywords: bool = True) -> Dict:
        """Process a single PDF file"""
        self.console.print(f"[blue]Processing:[/blue] {Path(pdf_path).name}")
        
        # Extract text and metadata
        try:
            pdf_data = self.pdf_extractor.process_pdf(pdf_path)
        except Exception as e:
            self.console.print(f"[red]Error extracting PDF:[/red] {e}")
            return None
        
        text = pdf_data['text']
        metadata = pdf_data['metadata']
        
        # Generate summary
        self.console.print("[yellow]Generating structured summary...[/yellow]")
        summary_result = self.ollama_client.generate_summary(text, "structured")
        
        if "error" in summary_result:
            self.console.print(f"[red]Failed to generate summary: {summary_result['error']}[/red]")
            # Fallback to raw response if available
            summary = summary_result.get("raw_response", "Failed to generate summary")
        else:
            summary = summary_result
        
        # Extract keywords
        self.console.print("[yellow]Extracting keywords...[/yellow]")
        if use_llm_keywords:
            llm_keywords = self.ollama_client.extract_keywords(text)
            tfidf_keywords = self.categorizer.extract_keywords_tfidf(text)
            # Combine and deduplicate
            all_keywords = list(set(llm_keywords + tfidf_keywords))
        else:
            all_keywords = self.categorizer.extract_keywords_tfidf(text)
        
        # Categorize content
        self.console.print("[yellow]Categorizing content...[/yellow]")
        if use_llm_keywords and llm_keywords:
            llm_categories = self.ollama_client.categorize_content(text, llm_keywords)
        else:
            llm_categories = {}
        
        keyword_categories = self.categorizer.categorize_by_keywords(all_keywords)
        similarity_categories = self.categorizer.categorize_by_similarity(text)
        
        # Combine categorization scores
        final_categories = {}
        for category in Config.CATEGORIES.keys():
            scores = [
                llm_categories.get(category, 0) * 0.4,
                keyword_categories.get(category, 0) * 0.3,
                similarity_categories.get(category, 0) * 0.3
            ]
            final_categories[category] = sum(scores)
        
        primary_category = self.categorizer.get_primary_category(final_categories)
        
        # Create result
        result = {
            'metadata': metadata,
            'summary': summary,
            'keywords': all_keywords,
            'categories': final_categories,
            'primary_category': primary_category,
            'word_count': pdf_data['word_count'],
            'processed_at': datetime.now().isoformat()
        }
        
        # Always save the result to JSON file
        self.save_result(result, pdf_path)
        
        return result
    
    def process_multiple_pdfs(self, pdf_paths: List[str], use_llm_keywords: bool = True) -> List[Dict]:
        """Process multiple PDF files"""
        results = []
        
        for pdf_path in track(pdf_paths, description="Processing PDFs..."):
            result = self.process_single_pdf(pdf_path, use_llm_keywords)
            if result:
                results.append(result)
                self.save_result(result, pdf_path)
        
        return results
    
    def save_result(self, result: Dict, original_path: str):
        """Save processing result to JSON file"""
        # Ensure summaries directory exists
        self.output_dir.mkdir(exist_ok=True)
        
        # Create filename based on original PDF
        filename = Path(original_path).stem + "_summary.json"
        output_path = self.output_dir / filename
        
        # Create a clean output structure
        output_data = {
            "source_file": str(Path(original_path).name),
            "processed_at": result['processed_at'],
            "pdf_metadata": result['metadata'],
            "structured_summary": result['summary'],
            "extracted_keywords": result['keywords'],
            "categorization": {
                "primary_category": result['primary_category'],
                "category_scores": result['categories']
            },
            "document_stats": {
                "word_count": result['word_count'],
                "processing_timestamp": result['processed_at']
            }
        }
        
        # Save with proper formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        self.console.print(f"[green]JSON Summary Saved:[/green] {output_path}")
        
        # Also create a simplified version matching the examples format
        if isinstance(result['summary'], dict):
            simple_output = result['summary'].copy()
            simple_filename = Path(original_path).stem + "_simple.json"
            simple_path = self.output_dir / simple_filename
            
            with open(simple_path, 'w', encoding='utf-8') as f:
                json.dump(simple_output, f, indent=2, ensure_ascii=False)
            
            self.console.print(f"[green]Simple Format Saved:[/green] {simple_path}")
    
    def display_results(self, results: List[Dict]):
        """Display results in a formatted table"""
        if not results:
            self.console.print("[red]No results to display[/red]")
            return
        
        table = Table(title="PDF Processing Results")
        table.add_column("File", style="cyan")
        table.add_column("Primary Category", style="magenta")
        table.add_column("Word Count", justify="right", style="green")
        table.add_column("Top Keywords", style="yellow")
        
        for result in results:
            filename = result['metadata']['filename']
            primary_cat = result['primary_category']
            word_count = str(result['word_count'])
            top_keywords = ', '.join(result['keywords'][:5])
            
            table.add_row(filename, primary_cat, word_count, top_keywords)
        
        self.console.print(table)
        
        # Category distribution
        self.console.print("\n[bold]Category Distribution:[/bold]")
        all_categories = {}
        for result in results:
            primary = result['primary_category']
            all_categories[primary] = all_categories.get(primary, 0) + 1
        
        for category, count in sorted(all_categories.items(), key=lambda x: x[1], reverse=True):
            self.console.print(f"  {category}: {count}")
    
    def create_category_report(self, results: List[Dict]) -> str:
        """Create a markdown report of categorized summaries"""
        if not results:
            return ""
        
        # Group by category
        by_category = {}
        for result in results:
            category = result['primary_category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(result)
        
        # Create markdown report
        report = f"# PDF Summary Report\n\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"Total PDFs processed: {len(results)}\n\n"
        
        for category in sorted(by_category.keys()):
            pdfs = by_category[category]
            report += f"## {category.title()} ({len(pdfs)} PDFs)\n\n"
            
            for result in pdfs:
                title = result['metadata'].get('title') or result['metadata']['filename']
                report += f"### {title}\n\n"
                report += f"**Keywords:** {', '.join(result['keywords'][:8])}\n\n"
                
                summary = result['summary']
                if isinstance(summary, dict):
                    # Format structured summary
                    if 'Title' in summary:
                        report += f"**Title:** {summary['Title']}\n\n"
                    if 'Author(s)' in summary:
                        report += f"**Author(s):** {summary['Author(s)']}\n\n"
                    if 'Year Published' in summary:
                        report += f"**Year:** {summary['Year Published']}\n\n"
                    if 'Journal' in summary:
                        report += f"**Journal:** {summary['Journal']}\n\n"
                    if 'BibTeX Citation' in summary:
                        report += f"**BibTeX Citation:**\n```\n{summary['BibTeX Citation']}\n```\n\n"
                    if 'Type' in summary:
                        report += f"**Type:** {summary['Type']}\n\n"
                    if 'Method' in summary:
                        report += f"**Method:** {summary['Method']}\n\n"
                    if 'Key Findings' in summary:
                        report += f"**Key Findings:**\n"
                        for finding, description in summary['Key Findings'].items():
                            report += f"- {finding}: {description}\n"
                        report += "\n"
                    if 'Key Takeaways' in summary:
                        report += f"**Key Takeaways:** {summary['Key Takeaways']}\n\n"
                else:
                    # Fallback to text summary
                    report += f"{summary}\n\n"
                
                report += "---\n\n"
        
        # Save report
        report_path = self.output_dir / f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.console.print(f"[green]Report saved:[/green] {report_path}")
        return str(report_path)