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
        
        # Generate intelligent filename based on author and year
        filename_base = self._generate_filename(result, original_path)
        filename = filename_base + "_summary.json"
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
            simple_filename = filename_base + "_simple.json"
            simple_path = self.output_dir / simple_filename
            
            with open(simple_path, 'w', encoding='utf-8') as f:
                json.dump(simple_output, f, indent=2, ensure_ascii=False)
            
            self.console.print(f"[green]Simple Format Saved:[/green] {simple_path}")
    
    def _generate_filename(self, result: Dict, original_path: str) -> str:
        """Generate intelligent filename based on author and year"""
        try:
            summary = result.get('summary', {})
            if not isinstance(summary, dict):
                # Fallback to original filename
                return Path(original_path).stem
            
            # Extract author(s) and year
            authors_str = summary.get('Author(s)', '')
            year = summary.get('Year Published', '')
            
            # Clean and parse authors
            if not authors_str or authors_str in ['Not specified', 'not specified', '']:
                # No author info, use original filename
                return Path(original_path).stem
            
            # Parse authors - handle various formats
            authors = self._parse_authors(authors_str)
            
            if not authors:
                return Path(original_path).stem
            
            # Generate filename based on rules
            if len(authors) == 1:
                # Rule 1: Last name of first author
                filename_base = authors[0]
                if year and str(year) not in ['null', 'None', '']:
                    filename_base += f"-{year}"
            elif len(authors) >= 2:
                # Rule 2: First and second author last names
                filename_base = f"{authors[0]}-{authors[1]}"
                if year and str(year) not in ['null', 'None', '']:
                    filename_base += f"-{year}"
            else:
                # Fallback
                filename_base = authors[0]
                if year and str(year) not in ['null', 'None', '']:
                    filename_base += f"-{year}"
            
            # Clean filename - remove invalid characters
            filename_base = self._clean_filename(filename_base)
            
            return filename_base
            
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not generate smart filename: {e}[/yellow]")
            return Path(original_path).stem
    
    def _parse_authors(self, authors_str: str) -> List[str]:
        """Parse author string and extract last names"""
        try:
            # Handle common separators
            if ' and ' in authors_str:
                parts = authors_str.split(' and ')
            elif ', ' in authors_str and ' et al' not in authors_str:
                # Handle "Last, First, Last2, First2" format
                parts = authors_str.split(', ')
                # Group pairs for "Last, First" format
                if len(parts) >= 2:
                    grouped_parts = []
                    i = 0
                    while i < len(parts):
                        if i + 1 < len(parts) and not any(title in parts[i+1].lower() for title in ['dr', 'prof', 'phd']):
                            # Check if next part looks like a first name (no last name indicators)
                            next_words = parts[i+1].split()
                            if len(next_words) == 1 or (len(next_words) == 2 and '.' in next_words[1]):
                                # Likely "Last, First" format
                                grouped_parts.append(f"{parts[i]}, {parts[i+1]}")
                                i += 2
                            else:
                                grouped_parts.append(parts[i])
                                i += 1
                        else:
                            grouped_parts.append(parts[i])
                            i += 1
                    parts = grouped_parts
            elif '; ' in authors_str:
                parts = authors_str.split('; ')
            else:
                parts = [authors_str]
            
            last_names = []
            for part in parts[:2]:  # Only take first 2 authors
                part = part.strip()
                if not part or 'et al' in part.lower():
                    continue
                
                # Extract last name (assume it's the last word)
                words = part.split()
                if words:
                    # Handle formats like "Smith, John" or "John Smith"
                    if ',' in part:
                        last_name = words[0].replace(',', '')
                    else:
                        last_name = words[-1]
                    
                    # Clean the last name
                    last_name = last_name.strip('.,;')
                    if last_name and len(last_name) > 1:
                        last_names.append(last_name)
            
            return last_names
            
        except Exception:
            return []
    
    def _clean_filename(self, filename: str) -> str:
        """Clean filename by removing invalid characters"""
        import re
        # Remove or replace invalid filename characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\s+', '_', filename)  # Replace spaces with underscores
        filename = filename.strip('._-')  # Remove leading/trailing dots, underscores, hyphens
        
        # Ensure it's not empty and not too long
        if not filename:
            filename = "unknown"
        if len(filename) > 50:
            filename = filename[:50]
        
        return filename
    
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