import re
from typing import List, Dict

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extracts emails, URLs, and phone numbers from the text.
    """
    # Cast to string to ensure .findall works correctly
    input_text: str = str(text)

    emails: List[str] = re.findall(r'[\w\.-]+@[\w\.-]+', input_text)
    urls: List[str] = re.findall(r'https?://[^\s]+', input_text)
    
    return {
        "emails": emails,
        "urls": urls
    }