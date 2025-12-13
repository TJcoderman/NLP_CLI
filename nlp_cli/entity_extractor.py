"""
Entity Extraction Module

Extracts relevant entities from natural language queries using
regex patterns and rule-based extraction.

Entities include:
- File names and patterns (*.txt, file.py)
- Directory names
- Paths (absolute and relative)
- URLs
- Process names
- IP addresses/hostnames
- Text strings (in quotes)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ExtractedEntities:
    """Container for all extracted entities from a query."""
    
    # File-related
    filename: Optional[str] = None
    file_pattern: Optional[str] = None  # e.g., *.txt, *.py
    file_extension: Optional[str] = None
    
    # Directory-related
    directory: Optional[str] = None
    destination: Optional[str] = None
    source: Optional[str] = None
    
    # Path-related
    path: Optional[str] = None
    
    # Text/content
    search_text: Optional[str] = None  # Text to search for
    new_name: Optional[str] = None  # For rename operations
    
    # Network
    url: Optional[str] = None
    hostname: Optional[str] = None
    
    # Process
    process_name: Optional[str] = None
    
    # Misc
    count: Optional[int] = None
    raw_entities: Dict[str, Any] = field(default_factory=dict)
    
    def has_target(self) -> bool:
        """Check if we have any target (file, directory, or pattern)."""
        return any([
            self.filename,
            self.file_pattern,
            self.directory,
            self.path,
        ])


class EntityExtractor:
    """
    Rule-based entity extractor using regex patterns.
    
    This extracts structured information from natural language
    queries to help build accurate shell commands.
    """
    
    # Common file extensions
    FILE_EXTENSIONS = [
        'txt', 'py', 'js', 'ts', 'json', 'xml', 'html', 'css', 'md',
        'log', 'csv', 'yml', 'yaml', 'toml', 'ini', 'cfg', 'conf',
        'sh', 'bat', 'ps1', 'exe', 'dll', 'so', 'zip', 'tar', 'gz',
        'jpg', 'jpeg', 'png', 'gif', 'svg', 'pdf', 'doc', 'docx',
        'xls', 'xlsx', 'ppt', 'pptx', 'mp3', 'mp4', 'wav', 'avi',
    ]
    
    def __init__(self):
        """Initialize the entity extractor with compiled regex patterns."""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile all regex patterns for efficiency."""
        
        # Quoted strings: "text" or 'text'
        self.quoted_pattern = re.compile(r'["\']([^"\']+)["\']')
        
        # File patterns: *.txt, *.py, etc.
        ext_group = '|'.join(self.FILE_EXTENSIONS)
        self.file_pattern_regex = re.compile(
            rf'\*\.({ext_group})\b', re.IGNORECASE
        )
        
        # File with extension: file.txt, my_script.py
        self.filename_pattern = re.compile(
            rf'\b([\w\-\.]+\.({ext_group}))\b', re.IGNORECASE
        )
        
        # URL pattern
        self.url_pattern = re.compile(
            r'https?://[^\s<>"\']+|www\.[^\s<>"\']+', re.IGNORECASE
        )
        
        # Path patterns (Unix and Windows)
        self.unix_path_pattern = re.compile(
            r'(?:^|[\s"])(/(?:[\w\-\.]+/)*[\w\-\.]*)', re.IGNORECASE
        )
        self.windows_path_pattern = re.compile(
            r'([A-Za-z]:\\(?:[\w\-\. ]+\\)*[\w\-\. ]*)', re.IGNORECASE
        )
        
        # Directory/folder name after keywords
        self.named_pattern = re.compile(
            r'\b(?:named?|called?|folder|directory)\s+["\']?(\w[\w\-\. ]*)["\']?',
            re.IGNORECASE
        )
        
        # "to X" pattern for destinations
        self.to_pattern = re.compile(
            r'\bto\s+["\']?([\w\-\./\\]+)["\']?', re.IGNORECASE
        )
        
        # "from X" pattern for sources
        self.from_pattern = re.compile(
            r'\bfrom\s+["\']?([\w\-\./\\]+)["\']?', re.IGNORECASE
        )
        
        # IP address pattern
        self.ip_pattern = re.compile(
            r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        )
        
        # Hostname pattern (domain-like)
        self.hostname_pattern = re.compile(
            r'\b((?:[\w\-]+\.)+[a-zA-Z]{2,})\b'
        )
        
        # Number pattern
        self.number_pattern = re.compile(r'\b(\d+)\b')
        
        # Extension mentions: "txt files", "python files", "py files"
        self.extension_mention = re.compile(
            rf'\b({ext_group})\s+files?\b', re.IGNORECASE
        )
        
        # Language-to-extension mapping for natural language
        self.language_extensions = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'java': 'java',
            'rust': 'rs',
            'ruby': 'rb',
            'go': 'go',
            'c++': 'cpp',
            'csharp': 'cs',
            'text': 'txt',
            'markdown': 'md',
            'config': 'cfg',
        }
        
        # Language mentions: "python files", "javascript files"
        lang_group = '|'.join(self.language_extensions.keys())
        self.language_mention = re.compile(
            rf'\b({lang_group})\s+files?\b', re.IGNORECASE
        )
        
        # Alternative extension mentions: "all .txt", "the .py files"
        self.dot_extension = re.compile(
            rf'\.({ext_group})\b', re.IGNORECASE
        )
    
    def extract(self, text: str) -> ExtractedEntities:
        """
        Extract all entities from a natural language query.
        
        Args:
            text: The user's natural language input.
            
        Returns:
            ExtractedEntities object with all found entities.
        """
        entities = ExtractedEntities()
        text_lower = text.lower()
        
        # Extract quoted strings first (highest priority for search text)
        quoted = self.quoted_pattern.findall(text)
        if quoted:
            # First quoted string is usually the most important
            entities.search_text = quoted[0]
            entities.raw_entities['quoted'] = quoted
            
            # Handle "write 'text' to file" or "write 'text' in file"
            if 'write' in text_lower or 'save' in text_lower or 'create file' in text_lower:
                if len(quoted) >= 1:
                    entities.search_text = quoted[0] # The content
        
        # Extract file patterns (*.txt)
        file_patterns = self.file_pattern_regex.findall(text_lower)
        if file_patterns:
            entities.file_pattern = f"*.{file_patterns[0]}"
            entities.file_extension = file_patterns[0]
        
        # Extract specific filenames
        filenames = self.filename_pattern.findall(text)
        if filenames:
            entities.filename = filenames[0][0]
            entities.file_extension = filenames[0][1]
        
        # Extract extension mentions (txt files, py files)
        ext_mentions = self.extension_mention.findall(text_lower)
        if ext_mentions and not entities.file_pattern:
            entities.file_pattern = f"*.{ext_mentions[0]}"
            entities.file_extension = ext_mentions[0]
        
        # Extract language mentions (python files, javascript files)
        lang_mentions = self.language_mention.findall(text_lower)
        if lang_mentions and not entities.file_pattern:
            lang = lang_mentions[0]
            ext = self.language_extensions.get(lang, lang)
            entities.file_pattern = f"*.{ext}"
            entities.file_extension = ext
        
        # Extract dot extensions
        dot_exts = self.dot_extension.findall(text_lower)
        if dot_exts and not entities.file_pattern:
            entities.file_pattern = f"*.{dot_exts[0]}"
            entities.file_extension = dot_exts[0]
        
        # Extract URLs
        urls = self.url_pattern.findall(text)
        if urls:
            entities.url = urls[0]
        
        # Extract paths
        unix_paths = self.unix_path_pattern.findall(text)
        if unix_paths:
            entities.path = unix_paths[0]
        
        windows_paths = self.windows_path_pattern.findall(text)
        if windows_paths:
            entities.path = windows_paths[0]
        
        # Extract named entities (folder named X)
        named = self.named_pattern.findall(text)
        if named:
            entities.directory = named[0].strip()
            entities.new_name = named[0].strip()
        
        # Extract destinations (to X)
        to_matches = self.to_pattern.findall(text)
        if to_matches:
            entities.destination = to_matches[0]
        
        # Extract sources (from X)
        from_matches = self.from_pattern.findall(text)
        if from_matches:
            entities.source = from_matches[0]
        
        # Extract IPs
        ips = self.ip_pattern.findall(text)
        if ips:
            entities.hostname = ips[0]
        
        # Extract hostnames (fallback)
        if not entities.hostname:
            hostnames = self.hostname_pattern.findall(text)
            if hostnames:
                entities.hostname = hostnames[0]
        
        # Extract numbers
        numbers = self.number_pattern.findall(text)
        if numbers:
            entities.count = int(numbers[0])
        
        # Special case: "go back" or "parent"
        if 'go back' in text_lower or 'parent' in text_lower or 'go up' in text_lower:
            entities.directory = '..'
        
        # Special case: "go home" or "home directory"
        if 'go home' in text_lower or 'home directory' in text_lower:
            entities.directory = '~'
            
        # Special case: "in it" (context resolution placeholder)
        if 'in it' in text_lower or 'into it' in text_lower:
            entities.raw_entities['context_ref'] = 'it'
        
        return entities


# Singleton instance
_extractor_instance: Optional[EntityExtractor] = None


def get_extractor() -> EntityExtractor:
    """Get or create the singleton extractor instance."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = EntityExtractor()
    return _extractor_instance


def extract_entities(text: str) -> ExtractedEntities:
    """
    Convenience function to extract entities.
    
    Args:
        text: Natural language query.
        
    Returns:
        ExtractedEntities with all found entities.
    """
    extractor = get_extractor()
    return extractor.extract(text)

