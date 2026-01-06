import re
from typing import List, Dict

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extracts emails, URLs, and phone numbers from the text.
    
    Args:
        text: Text to extract entities from
    
    Returns:
        Dictionary containing lists of extracted entities
    """
    input_text: str = str(text)

    # Extract emails
    emails: List[str] = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', input_text)
    
    # Extract URLs
    urls: List[str] = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', input_text)
    
    # Extract phone numbers (various formats)
    phones: List[str] = re.findall(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', input_text)
    
    return {
        "emails": list(set(emails)),  # Remove duplicates
        "urls": list(set(urls)),
        "phones": list(set(phones))
    }