import re

def format_response(text: str) -> str:
    # Convert **bold** to *bold* for Telegram
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    
    # Remove unsupported markdown
    text = re.sub(r'#{1,6}\s', '', text)
    
    # Fix code blocks
    text = re.sub(r'```(\w+)?\n', r'```\n', text)

    # Escape special characters outside code blocks
    # Split by code blocks first
    parts = re.split(r'(```[\s\S]*?```)', text)
    cleaned = []
    for part in parts:
        if part.startswith('```'):
            cleaned.append(part)
        else:
            part = re.sub(r'(?<![\*`])[_](?![\*`])', r'\\_', part)
            cleaned.append(part)
    
    text = ''.join(cleaned)

    if len(text) > 4000:
        text = text[:3990] + "\n\n_...truncated_"
    
    return text