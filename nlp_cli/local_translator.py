"""
Local NLP Translator Module

This is the main translation engine that combines:
1. Intent Classification (ML-based)
2. Entity Extraction (Rule-based)
3. Command Generation (Template-based)

No external LLM dependencies - runs 100% locally!
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple

from .intent_classifier import IntentClassifier, ClassificationResult, get_classifier
from .entity_extractor import EntityExtractor, ExtractedEntities, get_extractor
from .command_templates import get_command_for_intent, get_all_intents
from .system_info import SystemContext, get_system_context


@dataclass
class TranslationResult:
    """Result of natural language to command translation."""
    command: str
    success: bool
    intent: str
    confidence: float
    description: str
    is_dangerous: bool
    entities: ExtractedEntities
    alternative_intents: List[Tuple[str, float]]
    error_message: Optional[str] = None
    
    @property
    def model_used(self) -> str:
        """Return model name for compatibility with old interface."""
        return "LocalNLP (TF-IDF + SVM)"


class LocalTranslator:
    """
    Local NLP-based command translator.
    
    This translator uses:
    - TF-IDF + SVM for intent classification
    - Regex patterns for entity extraction
    - Template-based command generation
    
    No internet or external LLM required!
    """
    
    def __init__(self):
        """Initialize the translator components."""
        self.classifier = get_classifier()
        self.extractor = get_extractor()
        self.system_context = get_system_context()
        self.last_entities: Optional[ExtractedEntities] = None
    
    def translate(self, query: str) -> List[TranslationResult]:
        """
        Translate natural language to shell command(s).
        Handles multi-step commands joined by 'and', 'then'.
        
        Args:
            query: Natural language query from the user.
            
        Returns:
            List of TranslationResult objects.
        """
        # Split query by delimiters
        delimiters = [" and ", " then ", " & ", " && "]
        parts = [query]
        
        for delimiter in delimiters:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(delimiter))
            parts = new_parts
            
        results = []
        for part in parts:
            if not part.strip():
                continue
            result = self._translate_single(part.strip())
            results.append(result)
            
        return results

    def _translate_single(self, query: str) -> TranslationResult:
        """Process a single atomic command."""
        try:
            # Step 1: Classify intent
            classification = self.classifier.classify(query)
            
            # Step 2: Extract entities
            entities = self.extractor.extract(query)
            
            # Step 3: Resolve Context (The "Magic" Step)
            if self.last_entities:
                # If current command has "it" or missing filename, use previous
                if entities.raw_entities.get('context_ref') == 'it':
                    if not entities.filename and self.last_entities.filename:
                        entities.filename = self.last_entities.filename
                    if not entities.directory and self.last_entities.directory:
                        entities.directory = self.last_entities.directory
            
            # Update session state
            if entities.has_target():
                self.last_entities = entities
            
            # Step 4: Generate command from template
            command, description, is_dangerous = get_command_for_intent(
                intent=classification.intent,
                entities=entities,
                context=self.system_context
            )
            
            return TranslationResult(
                command=command,
                success=True,
                intent=classification.intent,
                confidence=classification.confidence,
                description=description,
                is_dangerous=is_dangerous,
                entities=entities,
                alternative_intents=classification.all_intents[1:],  # Skip first (it's the main intent)
            )
            
        except Exception as e:
            return TranslationResult(
                command="",
                success=False,
                intent="unknown",
                confidence=0.0,
                description="Translation failed",
                is_dangerous=False,
                entities=ExtractedEntities(),
                alternative_intents=[],
                error_message=str(e),
            )
    
    def explain_command(self, command: str) -> str:
        """
        Provide a simple explanation of a command.
        
        Since we're not using an LLM, we provide template-based explanations.
        
        Args:
            command: The shell command to explain.
            
        Returns:
            Human-readable explanation.
        """
        explanations = {
            "ls": "Lists files and directories in the current location.",
            "dir": "Lists files and directories in the current location (Windows).",
            "cd": "Changes the current directory.",
            "pwd": "Prints the current working directory path.",
            "mkdir": "Creates a new directory.",
            "rm": "Removes/deletes files. Use with caution!",
            "del": "Deletes files (Windows). Use with caution!",
            "cp": "Copies files from source to destination.",
            "copy": "Copies files (Windows).",
            "mv": "Moves or renames files.",
            "move": "Moves files (Windows).",
            "cat": "Displays the contents of a file.",
            "type": "Displays file contents (Windows).",
            "grep": "Searches for text patterns in files.",
            "find": "Finds files matching criteria.",
            "ps": "Shows running processes.",
            "kill": "Terminates a running process.",
            "ping": "Tests network connectivity to a host.",
            "chmod": "Changes file permissions (Unix).",
            "df": "Shows disk space usage.",
            "du": "Shows directory size.",
        }
        
        # Try to find a matching explanation
        cmd_lower = command.lower()
        for key, explanation in explanations.items():
            if key in cmd_lower:
                return explanation
        
        return "This command will be executed in your shell."
    
    def get_model_info(self) -> dict:
        """Get information about the NLP model."""
        classifier_info = self.classifier.get_model_info()
        return {
            "name": "LocalNLP (TF-IDF + SVM)",
            "type": "Local ML Model",
            "num_intents": classifier_info["num_intents"],
            "intents": classifier_info["intents"],
            "requires_internet": False,
        }
    
    def retrain(self) -> dict:
        """Retrain the intent classifier."""
        return self.classifier.retrain()
    
    def get_supported_intents(self) -> List[str]:
        """Get list of all supported command intents."""
        return get_all_intents()


# Singleton instance
_translator_instance: Optional[LocalTranslator] = None


def get_translator() -> LocalTranslator:
    """Get or create the singleton translator instance."""
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = LocalTranslator()
    return _translator_instance


def create_translator() -> LocalTranslator:
    """
    Factory function to create a translator.
    
    Returns:
        LocalTranslator instance.
    """
    return get_translator()


def translate(query: str) -> List[TranslationResult]:
    """
    Convenience function to translate a query.
    
    Args:
        query: Natural language query.
        
    Returns:
        List of TranslationResult objects with generated command.
    """
    translator = get_translator()
    return translator.translate(query)

