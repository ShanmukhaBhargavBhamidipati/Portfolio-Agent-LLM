import re

URL_PATTERN = re.compile(r'https?://[^\s,]+')

def extract_urls(text: str) -> list[str]:
    if not text:
        return []
    
    urls = URL_PATTERN.findall(text)
    
    cleaned = []
    
    for url in urls:
        cleaned.append(url.rstrip(").,]}>\"'"))
    
    return list(dict.fromkeys(cleaned))