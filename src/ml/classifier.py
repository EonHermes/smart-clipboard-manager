"""Content classification using ML."""

import numpy as np
from typing import List, Dict, Optional
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer


class ContentClassifier:
    """Classifies clipboard content into categories."""
    
    # Predefined categories with keywords
    CATEGORIES = {
        "code": ["function", "def ", "class ", "import", "const", "let", "var", "fn"],
        "url": ["http://", "https://", "www.", ".com", ".org", ".io"],
        "email": ["@", ".com", ".org", ".net"],
        "command": ["sudo", "pip", "npm", "cargo", "git", "docker"],
        "text": [],  # Default category
    }
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.kmeans: Optional[KMeans] = None
        self._fitted = False
    
    def _rule_based_classify(self, content: str) -> Optional[str]:
        """Use keyword rules for quick classification."""
        content_lower = content.lower()
        
        for category, keywords in self.CATEGORIES.items():
            if category == "text":
                continue
            if any(kw.lower() in content_lower for kw in keywords):
                return category
        
        return None
    
    def classify(self, content: str) -> Dict[str, any]:
        """Classify content and return prediction with confidence."""
        # Try rule-based first (fast)
        rule_category = self._rule_based_classify(content)
        
        if rule_category:
            return {
                "category": rule_category,
                "confidence": 0.85,
                "method": "rules",
            }
        
        # Fall back to ML clustering if fitted
        if self._fitted and len(content) > 20:
            try:
                tfidf = self.vectorizer.transform([content])
                prediction = self.kmeans.predict(tfidf)[0]
                distances = self.kmeans.transform(tfidf)[0]
                confidence = 1 - (distances[prediction] / np.max(distances))
                
                return {
                    "category": f"cluster_{prediction}",
                    "confidence": float(confidence),
                    "method": "ml",
                }
            except Exception:
                pass
        
        # Default to text
        return {
            "category": "text",
            "confidence": 0.5,
            "method": "default",
        }
    
    def fit(self, samples: List[str]):
        """Fit the classifier on sample data."""
        if len(samples) < 10:
            return
        
        # Vectorize samples
        tfidf_matrix = self.vectorizer.fit_transform(samples)
        
        # Determine optimal clusters (simple heuristic)
        n_clusters = min(5, len(samples) // 5)
        if n_clusters >= 2:
            self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            self.kmeans.fit(tfidf_matrix)
            self._fitted = True
    
    def suggest_category(self, content: str, existing_categories: List[str]) -> Optional[str]:
        """Suggest a category based on similar existing clips."""
        classification = self.classify(content)
        
        # If rule-based or high confidence ML, use it
        if classification["confidence"] > 0.7:
            return classification["category"]
        
        # Otherwise suggest from existing categories
        if existing_categories:
            return existing_categories[0]  # Most common
        
        return None
