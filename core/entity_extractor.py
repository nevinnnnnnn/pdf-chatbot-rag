import re

EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
PHONE_REGEX = r"(?:\+?\d{1,3}[\s-]?)?\d{10}"
URL_REGEX = r"(https?://[^\s]+|www\.[^\s]+)"
DATE_REGEX = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
AMOUNT_REGEX = r"(₹\s?\d+(?:,\d+)*(?:\.\d+)?|\$\s?\d+(?:,\d+)*(?:\.\d+)?)"


def extract_entities(text):
    emails = re.findall(EMAIL_REGEX, text)
    phones = re.findall(PHONE_REGEX, text)
    urls = re.findall(URL_REGEX, text)
    dates = re.findall(DATE_REGEX, text)
    amounts = re.findall(AMOUNT_REGEX, text)

    return {
        "emails": list(set(emails)),
        "phones": list(set(phones)),
        "urls": list(set(urls)),
        "dates": list(set(dates)),
        "amounts": list(set(amounts)),
    }
