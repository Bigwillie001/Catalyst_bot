import os
from core.llm import ask_claude # This helper uses the same API key
from llama_index.core import Settings

# We no longer re-initialize Settings.llm here because 
# main.py sets it globally for the whole application.

SUPPORTED_LANGUAGES = [
    "python", "rust", "kotlin", "go", "c++", "c#", "c",
    "html", "css", "javascript", "sql", "swift", "typescript", "java"
]

ERROR_KEYWORDS = [
    "error", "exception", "traceback", "failed", "undefined",
    "null", "segfault", "panic", "syntax error", "cannot find",
    "importerror", "typeerror", "valueerror", "nameerror",
    "indexerror", "keyerror", "attributeerror", "runtimeerror",
    "nullpointerexception", "segmentation fault", "unresolved",
    "line ", "at line", "errno", "exit code", "crashed", "❌"
]

CODE_KEYWORDS = [
    "write", "create", "build", "generate", "make", "code",
    "implement", "develop", "function", "class", "api", "script",
    "program", "app", "fix", "refactor", "optimize", "convert",
    "show me", "give me", "how to", "example of"
]

def detect_language(request: str) -> str:
    request_lower = request.lower()
    for lang in SUPPORTED_LANGUAGES:
        if lang in request_lower:
            return lang

    # Use the helper to determine language if not obvious
    prompt = f"""Given this coding request, return ONLY the single best programming language.
Supported: {', '.join(SUPPORTED_LANGUAGES)}
Request: "{request}"
Reply with ONLY the language name in lowercase."""
    
    try:
        result = ask_claude(prompt).strip().lower()
        return result if result in SUPPORTED_LANGUAGES else "python"
    except:
        return "python"

def classify_request(text: str) -> str:
    text_lower = text.lower()
    if any(kw in text_lower for kw in ERROR_KEYWORDS):
        return "error"
    if any(kw in text_lower for kw in CODE_KEYWORDS):
        return "code"
    return "question"