"""
Intent Classification Module

Uses scikit-learn to classify natural language queries into command intents.
The model uses TF-IDF vectorization with a Linear SVM classifier.
"""

import pickle
import os
from pathlib import Path
from typing import Tuple, Optional, List
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
import numpy as np

from .training_data import get_training_data, get_intent_list


@dataclass
class ClassificationResult:
    """Result of intent classification."""
    intent: str
    confidence: float
    all_intents: List[Tuple[str, float]]  # Top intents with scores


class IntentClassifier:
    """
    ML-based intent classifier using TF-IDF + SVM.
    
    This classifier:
    - Uses TF-IDF to convert text to numerical features
    - Uses Linear SVM for fast, accurate classification
    - Supports confidence scoring via decision function
    """
    
    MODEL_FILENAME = "intent_model.pkl"
    
    def __init__(self, model_dir: Optional[Path] = None):
        """
        Initialize the classifier.
        
        Args:
            model_dir: Directory to save/load model. Defaults to package directory.
        """
        self.model_dir = model_dir or Path(__file__).parent / "models"
        self.model_path = self.model_dir / self.MODEL_FILENAME
        
        self.pipeline: Optional[Pipeline] = None
        self.intent_labels: List[str] = []
        
        # Try to load existing model, otherwise train new one
        if not self._load_model():
            self.train()
    
    def train(self, save: bool = True) -> dict:
        """
        Train the intent classification model.
        
        Args:
            save: Whether to save the trained model to disk.
            
        Returns:
            Dictionary with training metrics.
        """
        # Get training data
        training_data = get_training_data()
        texts = [t for t, _ in training_data]
        labels = [l for _, l in training_data]
        
        # Store unique labels
        self.intent_labels = sorted(set(labels))
        
        # Create pipeline: TF-IDF + SVM
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 3),  # Use unigrams, bigrams, and trigrams
                max_features=5000,
                sublinear_tf=True,  # Apply sublinear TF scaling
            )),
            ('classifier', LinearSVC(
                C=1.0,
                class_weight='balanced',  # Handle class imbalance
                max_iter=10000,
                dual=True,
            ))
        ])
        
        # Train the model
        self.pipeline.fit(texts, labels)
        
        # Calculate cross-validation score
        cv_scores = cross_val_score(self.pipeline, texts, labels, cv=5)
        
        metrics = {
            "accuracy": float(np.mean(cv_scores)),
            "std": float(np.std(cv_scores)),
            "num_samples": len(texts),
            "num_intents": len(self.intent_labels),
        }
        
        # Save model if requested
        if save:
            self._save_model()
        
        return metrics
    
    def classify(self, text: str, top_k: int = 3) -> ClassificationResult:
        """
        Classify a natural language query into an intent.
        
        Args:
            text: The user's natural language input.
            top_k: Number of top intents to return with scores.
            
        Returns:
            ClassificationResult with intent and confidence.
        """
        if self.pipeline is None:
            raise RuntimeError("Model not trained. Call train() first.")
        
        # Preprocess
        text = text.lower().strip()
        
        # Get prediction
        predicted_intent = self.pipeline.predict([text])[0]
        
        # Get decision function scores for confidence
        decision_scores = self.pipeline.decision_function([text])[0]
        
        # Convert to probabilities using softmax
        exp_scores = np.exp(decision_scores - np.max(decision_scores))
        probabilities = exp_scores / exp_scores.sum()
        
        # Get top-k intents
        top_indices = np.argsort(probabilities)[::-1][:top_k]
        all_intents = [
            (self.intent_labels[i], float(probabilities[i]))
            for i in top_indices
        ]
        
        # Get confidence for predicted intent
        predicted_idx = self.intent_labels.index(predicted_intent)
        confidence = float(probabilities[predicted_idx])
        
        return ClassificationResult(
            intent=predicted_intent,
            confidence=confidence,
            all_intents=all_intents
        )
    
    def _save_model(self):
        """Save the trained model to disk."""
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "pipeline": self.pipeline,
            "intent_labels": self.intent_labels,
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def _load_model(self) -> bool:
        """
        Load a trained model from disk.
        
        Returns:
            True if model was loaded successfully, False otherwise.
        """
        if not self.model_path.exists():
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.pipeline = model_data["pipeline"]
            self.intent_labels = model_data["intent_labels"]
            return True
        except Exception:
            return False
    
    def retrain(self) -> dict:
        """Force retrain the model with latest training data."""
        return self.train(save=True)
    
    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            "model_path": str(self.model_path),
            "model_exists": self.model_path.exists(),
            "num_intents": len(self.intent_labels),
            "intents": self.intent_labels,
        }


# Singleton instance for reuse
_classifier_instance: Optional[IntentClassifier] = None


def get_classifier() -> IntentClassifier:
    """Get or create the singleton classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntentClassifier()
    return _classifier_instance


def classify_intent(text: str) -> ClassificationResult:
    """
    Convenience function to classify intent.
    
    Args:
        text: Natural language query.
        
    Returns:
        ClassificationResult with intent and confidence.
    """
    classifier = get_classifier()
    return classifier.classify(text)

