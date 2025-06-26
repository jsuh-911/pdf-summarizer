import nltk
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
from collections import Counter
import re
from config import Config

class TextCategorizer:
    def __init__(self):
        self.download_nltk_data()
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
    def download_nltk_data(self):
        """Download required NLTK data"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
        except Exception as e:
            print(f"Warning: Could not download NLTK data: {e}")
    
    def extract_keywords_tfidf(self, text: str, num_keywords: int = 15) -> List[str]:
        """Extract keywords using TF-IDF"""
        try:
            # Preprocess text
            text = self.preprocess_text(text)
            
            # Fit TF-IDF
            tfidf_matrix = self.vectorizer.fit_transform([text])
            feature_names = self.vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()[0]
            
            # Get top keywords
            keyword_scores = list(zip(feature_names, tfidf_scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            return [kw[0] for kw in keyword_scores[:num_keywords] if kw[1] > 0]
        except Exception as e:
            print(f"Error in TF-IDF keyword extraction: {e}")
            return self.extract_keywords_frequency(text, num_keywords)
    
    def extract_keywords_frequency(self, text: str, num_keywords: int = 15) -> List[str]:
        """Fallback keyword extraction using word frequency"""
        # Clean and tokenize
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'been', 'be', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'not', 'no', 'yes', 'all', 'any', 'some', 'each', 'every', 'other', 'another', 'such', 'more', 'most', 'much', 'many', 'few', 'less', 'least', 'than', 'as', 'so', 'very', 'too', 'also', 'just', 'only', 'even', 'now', 'then', 'here', 'there', 'where', 'when', 'why', 'how', 'what', 'who', 'which', 'whose', 'whom'}
        
        words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Count frequency
        word_freq = Counter(words)
        return [word for word, freq in word_freq.most_common(num_keywords)]
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Keep only alphanumeric and spaces
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        return text.strip()
    
    def categorize_by_keywords(self, keywords: List[str]) -> Dict[str, float]:
        """Categorize content based on keyword matching"""
        scores = {category: 0.0 for category in Config.CATEGORIES.keys()}
        
        # Calculate scores based on keyword matches
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for category, category_words in Config.CATEGORIES.items():
                for cat_word in category_words:
                    # Exact match
                    if cat_word.lower() == keyword_lower:
                        scores[category] += 1.0
                    # Partial match
                    elif cat_word.lower() in keyword_lower or keyword_lower in cat_word.lower():
                        scores[category] += 0.5
        
        # Normalize scores
        max_score = max(scores.values()) if any(scores.values()) else 1
        normalized_scores = {k: v / max_score for k, v in scores.items()}
        
        return normalized_scores
    
    def categorize_by_similarity(self, text: str) -> Dict[str, float]:
        """Categorize content using cosine similarity with research category descriptions"""
        category_descriptions = {
            'clinical_trial': 'clinical trial randomized controlled trial RCT human participants intervention treatment placebo double blind efficacy safety therapeutic',
            'preclinical_models': 'animal model mouse rat transgenic knockout in vivo preclinical experimental disease model behavioral pharmacokinetics toxicity',
            'cellular_studies': 'cell culture in vitro cell line primary cells stem cells organoid tissue culture gene expression protein western blot flow cytometry',
            'meta_analysis': 'meta analysis systematic review pooled analysis forest plot heterogeneity odds ratio risk ratio confidence interval cochrane prisma',
            'review_article': 'review literature review narrative review perspective commentary overview state of the art current understanding recent advances future directions'
        }
        
        try:
            # Prepare texts
            texts = [text] + list(category_descriptions.values())
            
            # Calculate TF-IDF
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Calculate similarities
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            # Create scores dictionary
            scores = {}
            for i, category in enumerate(category_descriptions.keys()):
                scores[category] = float(similarities[i])
            
            return scores
            
        except Exception as e:
            print(f"Error in similarity categorization: {e}")
            return {category: 0.0 for category in Config.CATEGORIES.keys()}
    
    def get_primary_category(self, scores: Dict[str, float], threshold: float = 0.3) -> str:
        """Get the primary category based on scores"""
        if not scores or max(scores.values()) < threshold:
            return 'uncategorized'
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def get_category_summary(self, scores: Dict[str, float]) -> List[Tuple[str, float]]:
        """Get sorted list of categories with their scores"""
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)