"""Section extraction utilities"""
import re
from typing import List, Pattern

# Compile patterns once for efficiency
ABSTRACT_PATTERNS: List[Pattern] = [
    re.compile(r'(?i)abstract\s*\n(.*?)(?=\n\s*(?:introduction|keywords|background|methods|results))', re.DOTALL),
    re.compile(r'(?i)abstract[:\s]+(.*?)(?=\n\s*(?:introduction|keywords|background|methods|results))', re.DOTALL),
]

METHODS_PATTERNS: List[Pattern] = [
    re.compile(pattern, re.DOTALL) for pattern in [
        r'(?i)(?:materials\s+and\s+methods|methods|methodology|experimental\s+procedure)[:\s]*(.*?)(?=\n\s*(?:results|discussion|conclusion))',
        r'(?i)(?:materials\s+and\s+methods|methods|methodology|experimental\s+procedure)\s*\n(.*?)(?=\n\s*(?:results|discussion|conclusion))',
    ]
]

def extract_sections(text: str, max_length: int = 4000) -> str:
    """Extract abstract and methods sections from text"""
    relevant_text = ""
    
    # Extract abstract
    abstract_text = extract_section(text, ABSTRACT_PATTERNS)
    if abstract_text:
        relevant_text += "ABSTRACT:\n" + abstract_text + "\n\n"
    
    # Extract methods
    methods_text = extract_section(text, METHODS_PATTERNS)
    if methods_text:
        relevant_text += "METHODS AND STUDY DETAILS:\n" + methods_text
    
    # Fallback to truncated text if no sections found
    if not relevant_text:
        return text[:max_length]
    
    return relevant_text

def extract_section(text: str, patterns: List[Pattern]) -> str:
    """Extract text using a list of patterns"""
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return "" 