from core.llm import ask_claude
from core.rag import query_docs

def handle_error(error_text: str) -> str:
    context = query_docs(error_text)

    prompt = f"""You are debugging this error. Be extremely precise and thorough.

ERROR TO DEBUG:
{error_text}

You MUST respond with ALL of these sections:

🔍 ERROR TYPE:
[Identify the exact type of error]

🧠 ROOT CAUSE:
[Explain exactly why this error occurred, line by line if needed]

🔧 FIXED CODE:
[Write the complete corrected code — not a snippet, the full fix]

💡 PREVENTION:
[How to never encounter this error again]

📚 TECHNICAL NOTE:
[Brief explanation of the underlying concept]

Do NOT skip any section. Do NOT be vague."""

    return ask_claude(prompt, context)