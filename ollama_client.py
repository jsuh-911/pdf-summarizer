import ollama
import json
from typing import List, Dict
from config import Config

class OllamaClient:
    def __init__(self, model: str = None, host: str = None):
        self.model = model or Config.OLLAMA_MODEL
        self.host = host or Config.OLLAMA_HOST
        self.client = ollama.Client(host=self.host)
    
    def is_model_available(self) -> bool:
        """Check if the specified model is available"""
        try:
            models = self.client.list()
            
            # Handle different response structures
            if hasattr(models, 'models'):
                model_list = models.models
            elif 'models' in models:
                model_list = models['models']
            else:
                model_list = models
            
            # Extract model names - handle both dict and object formats
            available_models = []
            for model in model_list:
                if hasattr(model, 'model'):
                    available_models.append(model.model)
                elif 'model' in model:
                    available_models.append(model['model'])
                elif hasattr(model, 'name'):
                    available_models.append(model.name)
                elif 'name' in model:
                    available_models.append(model['name'])
            
            # Check for exact match or partial match
            return any(self.model == model or self.model in model for model in available_models)
        except Exception as e:
            print(f"Error checking model availability: {e}")
            return False
    
    def generate_summary(self, text: str, summary_type: str = "blinkist") -> str:
        """Generate a summary using Ollama"""
        if summary_type == "blinkist":
            prompt = self._create_blinkist_prompt(text)
        else:
            prompt = self._create_standard_prompt(text)
        
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 1000
                }
            )
            return response['response'].strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return ""
    
    def _create_blinkist_prompt(self, text: str) -> str:
        """Create a Blinkist-style summary prompt"""
        return f"""
Create a Blinkist-style summary of the following text. Your summary should:

1. Start with a brief "What's in it for me?" section (2-3 sentences)
2. Extract 5-7 key insights or "blinks" from the content
3. Each blink should be:
   - A clear, actionable insight
   - 2-3 sentences long
   - Include the main idea and why it matters
4. End with a "Final Summary" paragraph

Format your response as:

**What's in it for me?**
[Brief overview of main benefits]

**Key Insights:**

**Insight 1: [Title]**
[Description and importance]

**Insight 2: [Title]**
[Description and importance]

[Continue for 5-7 insights]

**Final Summary:**
[Concluding thoughts and main takeaway]

Text to summarize:
{text[:3000]}...
"""
    
    def _create_standard_prompt(self, text: str) -> str:
        """Create a standard summary prompt"""
        return f"""
Summarize the following text in a clear, concise manner. Focus on:
- Main arguments and key points
- Important conclusions
- Actionable insights
- Critical information

Keep the summary between 200-400 words.

Text to summarize:
{text[:3000]}...
"""
    
    def extract_keywords(self, text: str, num_keywords: int = 10) -> List[str]:
        """Extract keywords using LLM"""
        prompt = f"""
Extract {num_keywords} most important keywords or key phrases from the following text. 
Return only the keywords, separated by commas, without any additional text or explanation.
Focus on topics, concepts, and main themes.

Text:
{text[:2000]}...
"""
        
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={'temperature': 0.3}
            )
            keywords_text = response['response'].strip()
            # Clean and split keywords
            keywords = [kw.strip().lower() for kw in keywords_text.split(',')]
            return [kw for kw in keywords if kw and len(kw) > 2][:num_keywords]
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []
    
    def categorize_content(self, text: str, keywords: List[str]) -> Dict[str, float]:
        """Categorize content based on predefined categories"""
        categories_text = ", ".join(Config.CATEGORIES.keys())
        
        prompt = f"""
Based on the following text and keywords, assign relevance scores (0-1) for each category.
Return your response as a JSON object with category names as keys and scores as values.

Categories: {categories_text}
Keywords: {', '.join(keywords)}

Text sample:
{text[:1500]}...

Return only the JSON object, no additional text.
"""
        
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={'temperature': 0.2}
            )
            
            # Try to parse JSON response
            response_text = response['response'].strip()
            # Extract JSON from response if it contains other text
            if '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_text = response_text[start:end]
                return json.loads(json_text)
            else:
                return self._fallback_categorization(keywords)
                
        except Exception as e:
            print(f"Error in LLM categorization: {e}")
            return self._fallback_categorization(keywords)
    
    def _fallback_categorization(self, keywords: List[str]) -> Dict[str, float]:
        """Fallback categorization using keyword matching"""
        scores = {category: 0.0 for category in Config.CATEGORIES.keys()}
        
        for keyword in keywords:
            for category, category_words in Config.CATEGORIES.items():
                for cat_word in category_words:
                    if cat_word.lower() in keyword.lower() or keyword.lower() in cat_word.lower():
                        scores[category] += 0.1
        
        # Normalize scores
        max_score = max(scores.values()) if scores.values() else 1
        if max_score > 0:
            scores = {k: min(v / max_score, 1.0) for k, v in scores.items()}
        
        return scores