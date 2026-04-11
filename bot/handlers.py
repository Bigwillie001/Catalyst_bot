import os
import asyncio
import base64
from groq import Groq
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from llama_index.core import Settings
from core.router import classify_request, detect_language
from core.rag import query_docs
from core.llm import ask_claude
from core.error_handler import handle_error
from core.ingestion import ingest_pdf
from bot.formatter import format_response
from database import get_user_prefs, save_user_prefs
from config import UPLOADS_PATH

load_dotenv()


# ============================================================
# UTILITIES
# ============================================================

def encode_image(image_path: str) -> str:
    """Convert image file to base64 string for Vision model."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def keep_typing(chat, stop_event: asyncio.Event):
    """Keep sending typing indicator until stop_event is set."""
    while not stop_event.is_set():
        await chat.send_action("typing")
        await asyncio.sleep(4)


async def send_long_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    Splits response into chunks to bypass Telegram's 4096 char limit.
    Splits on newlines to avoid breaking code blocks where possible.
    """
    max_length = 8500
    chunks = []

    while len(text) > max_length:
        split_index = text.rfind("\n", 0, max_length)
        if split_index == -1:
            split_index = max_length
        chunks.append(text[:split_index])
        text = text[split_index:].lstrip()
    chunks.append(text)

    for chunk in chunks:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=chunk,
                parse_mode="Markdown"
            )
        except Exception:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=chunk
            )


# ============================================================
# USER PREFERENCE HANDLER
# ============================================================

async def set_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Saves user response style preferences.
    Usage: /set_style
    """
    user_id = update.message.from_user.id
    save_user_prefs(user_id, "Surgical", "Machine", "Code-First")
    await update.message.reply_text(
        "✅ *Preferences Locked:* Surgical | Machine | Code-First",
        parse_mode="Markdown"
    )


# ============================================================
# CORE MESSAGE HANDLER
# ============================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main dispatcher — classifies every text message as:
    - error: routes to error handler
    - code: detects language, queries KB, generates code
    - question: queries KB, generates answer
    - DATA INSUFFICIENT: falls back to Tavily web search
    """
    text = update.message.text
    chat = update.message.chat
    user_id = update.message.from_user.id
    stop_event = asyncio.Event()

    # Inject user preferences into LLM system prompt
    prefs = get_user_prefs(user_id)
    if prefs and hasattr(Settings.llm, "system_prompt"):
        Settings.llm.system_prompt = (
            f"You are Catalyst-Nexus. USER PREFERENCES: {prefs}"
        )

    # Keep typing indicator alive during processing
    typing_task = asyncio.create_task(keep_typing(chat, stop_event))

    try:
        request_type = classify_request(text)

        if request_type == "error":
            await update.message.reply_text("🔍 Analyzing your error...")
            response = handle_error(text)

        elif request_type == "code":
            language = detect_language(text)
            await update.message.reply_text(
                f"⚙️ Detected: {language.upper()} — Building now..."
            )
            doc_context = query_docs(f"{language} {text}")

            prompt = f"""Write complete, working {language} code for the following:

{text}

Requirements:
- Code must be fully functional, not pseudocode
- Include all imports and dependencies
- Add clear senior-level comments
- Show how to run or use it"""

            response = ask_claude(prompt, doc_context)
            response = f"🔤 Language: {language.upper()}\n\n{response}"

        else:
            await update.message.reply_text("📚 Consulting knowledge base...")
            doc_context = query_docs(text)
            prompt = f"""Answer this programming question thoroughly:

{text}

If code is needed, write complete working examples."""
            response = ask_claude(prompt, doc_context)

        # ── TAVILY WEB SEARCH FALLBACK ──────────────────────────────
        # Triggered when Catalyst-Nexus flags insufficient data
        if "DATA INSUFFICIENT" in response:
            await update.message.reply_text(
                "🌐 *Knowledge base insufficient — searching the web...*",
                parse_mode="Markdown"
            )
            try:
                from tavily import TavilyClient
                tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
                search_result = tavily.search(
                    query=text,
                    search_depth="advanced"
                )

                # Build web context from Tavily results
                web_context = "\n\n".join([
                    f"[Web Source {i+1}]: {r['content']}"
                    for i, r in enumerate(search_result.get("results", []))
                ])

                
                web_prompt = f"""You previously flagged this query as DATA INSUFFICIENT.
Live web search results have now been retrieved. Use them as TIER-1 GROUND TRUTH.

WEB SEARCH RESULTS:
{web_context}

Now answer this request completely using the web results above:
{text}"""

                response = ask_claude(web_prompt, web_context)
                response = f"🌐 *Source: Live Web Search*\n\n{response}"

            except Exception as web_err:
                response += f"\n\n❌ Web search fallback failed: {str(web_err)}"
        # ── END TAVILY FALLBACK ──────────────────────────────────────

    except Exception as e:
        response = f"❌ Internal error: {str(e)}"

    finally:
        stop_event.set()
        typing_task.cancel()

    await send_long_message(update, context, format_response(response))



# ============================================================
# VISION HANDLER — Image OCR + Code Extraction
# ============================================================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Vision OCR: Extracts code, text, or error messages from images.
    Uses Groq llama-3.2-11b-vision-preview model.
    Extracted text is then passed through the standard ask_claude pipeline.
    """
    user_id = update.message.from_user.id
    status_msg = await update.message.reply_text(
        "👁️ *Scanning image...*",
        parse_mode="Markdown"
    )

    # Download highest-res photo
    photo_file = await update.message.photo[-1].get_file()
    file_path = f"vision_{user_id}.jpg"
    await photo_file.download_to_drive(file_path)

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract all code, information, text, or error messages from this image. "
                                "Output raw text only. No conversational filler."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encode_image(file_path)}"
                            }
                        }
                    ]
                }
            ]
        )

        extracted_text = completion.choices[0].message.content

        await status_msg.edit_text(
            f"👁️ *Extracted Text:*\n```\n{extracted_text[:1000]}\n```\n⚙️ *Processing...*",
            parse_mode="Markdown"
        )

        # Route extracted text through main Catalyst-Nexus pipeline
        doc_context = query_docs(extracted_text)
        response = ask_claude(
            f"Analyze and process this extracted image content:\n\n{extracted_text}",
            doc_context
        )

        await send_long_message(update, context, format_response(response))

    except Exception as e:
        await status_msg.edit_text(f"❌ Image error: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ============================================================
# VOICE HANDLER — Transcription + Auto-Translation
# ============================================================

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Voice Processing: Transcribes audio using Whisper-large-v3.
    Auto-translates foreign input to English before processing.
    Routes transcribed text through the standard ask_claude pipeline.
    """
    user_id = update.message.from_user.id
    status_msg = await update.message.reply_text(
        "🎙️ *Analyzing audio...*",
        parse_mode="Markdown"
    )

    voice_file = await context.bot.get_file(update.message.voice.file_id)
    file_path = f"temp_{user_id}.ogg"
    await voice_file.download_to_drive(file_path)

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3",
                response_format="json"
            )

        user_text = transcription.text

        await status_msg.edit_text(
            f"🎤 *Transcribed:* `{user_text}`\n⚙️ *Processing...*",
            parse_mode="Markdown"
        )

        # Inject user preferences + translation directive
        prefs = get_user_prefs(user_id)
        if hasattr(Settings.llm, "system_prompt"):
            Settings.llm.system_prompt += (
                f"\nUSER PREFS: {prefs}. "
                "TRANSLATION PROTOCOL: Translate foreign input to English first, then answer."
            )

        # Route transcribed text through Catalyst-Nexus pipeline
        doc_context = query_docs(user_text)
        prompt = f"""The user sent a voice message. Transcribed content:

{user_text}

Process and respond to this as a technical coding assistant would."""

        response = ask_claude(prompt, doc_context)
        await send_long_message(update, context, format_response(response))

    except Exception as e:
        await status_msg.edit_text(f"❌ Voice error: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ============================================================
# DOCUMENT HANDLER — PDF Ingestion
# ============================================================

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles PDF uploads and ingests them into the knowledge base."""
    try:
        file = await update.message.document.get_file()
        file_name = update.message.document.file_name

        if not file_name.endswith(".pdf"):
            await update.message.reply_text("❌ Only PDF files are supported.")
            return

        os.makedirs(UPLOADS_PATH, exist_ok=True)
        save_path = f"{UPLOADS_PATH}/{file_name}"
        await file.download_to_drive(save_path)

        await update.message.reply_text(
            f"⏳ Ingesting PDF: *{file_name}*\nThis may take a moment...",
            parse_mode="Markdown"
        )
        result = ingest_pdf(save_path)
        await update.message.reply_text(result, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Document error: {str(e)}")


# ============================================================
# GITHUB HANDLER — Repo Ingestion
# ============================================================

async def handle_github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detects GitHub URLs and ingests the repo into the knowledge base."""
    try:
        text = update.message.text
        words = text.split()
        url = next((w for w in words if "github.com" in w), None)

        if not url:
            await update.message.reply_text("❌ No valid GitHub URL found.")
            return

        await update.message.reply_text(
            f"⏳ Cloning and indexing repo...",
            parse_mode="Markdown"
        )
        from core.ingestion import ingest_github
        result = ingest_github(url)
        await update.message.reply_text(result, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ GitHub error: {str(e)}")