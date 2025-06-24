import PyPDF2
import pdfplumber
from typing import List, Dict
import re
from pathlib import Path

class PDFExtractor:
    def __init__(self):
        pass
    
    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2 (faster but less accurate)"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting text with PyPDF2: {e}")
        return text
    
    def extract_text_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber (more accurate but slower)"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error extracting text with pdfplumber: {e}")
        return text
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers and headers/footers patterns
        text = re.sub(r'\n\d+\n', '\n', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\']', ' ', text)
        return text.strip()
    
    def extract_metadata(self, pdf_path: str) -> Dict:
        """Extract PDF metadata"""
        metadata = {}
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                info = reader.metadata
                if info:
                    metadata = {
                        'title': info.get('/Title', ''),
                        'author': info.get('/Author', ''),
                        'subject': info.get('/Subject', ''),
                        'creator': info.get('/Creator', ''),
                        'pages': len(reader.pages)
                    }
        except Exception as e:
            print(f"Error extracting metadata: {e}")
        
        # Add file info
        path_obj = Path(pdf_path)
        metadata['filename'] = path_obj.name
        metadata['filepath'] = str(path_obj.absolute())
        
        return metadata
    
    def chunk_text(self, text: str, max_chunk_size: int = 4000) -> List[str]:
        """Split text into chunks for processing"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def process_pdf(self, pdf_path: str, use_pdfplumber: bool = True) -> Dict:
        """Main method to process a PDF file"""
        if use_pdfplumber:
            text = self.extract_text_pdfplumber(pdf_path)
        else:
            text = self.extract_text_pypdf2(pdf_path)
        
        if not text.strip():
            raise ValueError(f"No text could be extracted from {pdf_path}")
        
        cleaned_text = self.clean_text(text)
        metadata = self.extract_metadata(pdf_path)
        
        return {
            'text': cleaned_text,
            'metadata': metadata,
            'word_count': len(cleaned_text.split())
        }