from groq import Groq
from dotenv import load_dotenv
import os
import time

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Rotation — if one hits limit, falls to next
MODELS = [
    "llama-3.3-70b-versatile",   # Best quality
    "llama-3.3-70b-versatile",      # Fast fallback
    "qwen3-32b",              # Last resort
]

SYSTEM_PROMPT = """You are Catalyst Bot — an elite, professional AI coding assistant.

STRICT RULES:
1. When asked to write/create/build code → ALWAYS output complete, working, production-grade code. No excuses.
2. When given an error → ALWAYS diagnose and output the exact fix with corrected code.
3. NEVER say "I can't", "I won't", or "here's a simplified version."
4. ALWAYS include all imports and dependencies.
5. ALWAYS add clear comments explaining each part.
6. ALWAYS structure your response with clear sections.
7. If context/docs are provided → study them and use them to inform your output.

You support these languages fluently:
Python, Rust, Kotlin, Go, C++, C#, C, HTML/CSS, JavaScript, SQL, Swift, TypeScript, Java.

Output format for CODE requests:
- Brief explanation of approach
- Full working code block with comments
- How to run it

Output format for ERROR requests:
- Error Type
- Root Cause
- Fixed Code
- Prevention tip"""


def ask_claude(prompt: str, context: str = "") -> str:
    if context and len(context.strip()) > 50:
        full_prompt = f"""{SYSTEM_PROMPT}

--- RELEVANT DOCS/CONTEXT FROM YOUR KNOWLEDGE BASE ---
{context}
--- END OF CONTEXT ---

Using the context above where relevant, now fulfill this request completely:
{prompt}"""
    else:
        full_prompt = f"""{SYSTEM_PROMPT}

Request: {prompt}"""

    for model in MODELS:
        for attempt in range(3):
            try:
                print(f"🤖 Using {model}...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=4096,
                    temperature=0.3
                )
                result = response.choices[0].message.content
                print(f"✅ Response received from {model}")
                return result

            except Exception as e:
                error = str(e)
                if "429" in error or "rate" in error.lower():
                    if attempt < 2:
                        wait = (attempt + 1) * 5
                        print(f"⏳ {model} rate limited. Waiting {wait}s...")
                        time.sleep(wait)
                        continue
                    else:
                        print(f"❌ {model} exhausted. Trying next...")
                        break
                else:
                    print(f"❌ {model} error: {error}")
                    break

    return "❌ All models unavailable right now. Please try again in 1 minute."