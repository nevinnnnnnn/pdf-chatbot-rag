import re
from typing import Dict, List


# -----------------------------
# Regex Patterns
# -----------------------------

EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

PHONE_REGEX = r"""
(?:\+?\d{1,3}[\s-]?)?      # country code
(?:\(?\d{3}\)?[\s-]?)?    # area code
\d{3}[\s-]?\d{4}          # local number
"""

URL_REGEX = r"(https?://[^\s]+|www\.[^\s]+)"

DATE_REGEX = r"""
\b(
    \d{1,2}[/-]\d{1,2}[/-]\d{2,4} |
    \d{4}[/-]\d{1,2}[/-]\d{1,2}
)\b
"""

AMOUNT_REGEX = r"""
(?:₹|\$|€|£)\s?\d+(?:,\d{3})*(?:\.\d+)?
"""


# -----------------------------
# Entity Extraction
# -----------------------------

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extracts structured entities from text.
    Returns unique values only.
    """

    if not text or not isinstance(text, str):
        return {
            "emails": [],
            "phones": [],
            "urls": [],
            "dates": [],
            "amounts": [],
        }

    emails = re.findall(EMAIL_REGEX, text)
    phones = re.findall(PHONE_REGEX, text, flags=re.VERBOSE)
    urls = re.findall(URL_REGEX, text)
    dates = re.findall(DATE_REGEX, text, flags=re.VERBOSE)
    amounts = re.findall(AMOUNT_REGEX, text, flags=re.VERBOSE)

    # Normalize results
    return {
        "emails": sorted(set(emails)),
        "phones": sorted(set(p.strip() for p in phones if p.strip())),
        "urls": sorted(set(urls)),
        "dates": sorted(set(dates)),
        "amounts": sorted(set(amounts)),
    }
