import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral:latest')
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './summaries')
    MAX_CHUNK_SIZE = int(os.getenv('MAX_CHUNK_SIZE', 4000))
    
    # Categorization keywords
    CATEGORIES = {
        'business': ['business', 'management', 'leadership', 'strategy', 'marketing', 'sales', 'entrepreneurship'],
        'technology': ['technology', 'programming', 'software', 'ai', 'machine learning', 'data science', 'coding'],
        'self_help': ['self-help', 'productivity', 'habits', 'mindset', 'personal development', 'motivation'],
        'science': ['science', 'research', 'biology', 'physics', 'chemistry', 'neuroscience', 'psychology'],
        'finance': ['finance', 'investing', 'money', 'economics', 'trading', 'wealth', 'financial'],
        'health': ['health', 'fitness', 'nutrition', 'wellness', 'medicine', 'exercise', 'diet'],
        'history': ['history', 'historical', 'war', 'politics', 'government', 'society', 'culture'],
        'philosophy': ['philosophy', 'ethics', 'morality', 'thinking', 'wisdom', 'meaning', 'purpose']
    }