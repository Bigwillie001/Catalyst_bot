from telegram import Update
from telegram.ext import ContextTypes
from core.router import classify_request, detect_language
from core.rag import query_docs
from core.llm import ask_claude
from core.error_handler import handle_error
from core.ingestion import ingest_pdf
from bot.formatter import format_response
import os
import asyncio
from config import UPLOADS_PATH


async def keep_typing(chat, stop_event):
    """Keep sending typing indicator until stop_event is set."""
    while not stop_event.is_set():
        await chat.send_action("typing")
        await asyncio.sleep(4)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat = update.message.chat
    stop_event = asyncio.Event()

    # Start typing indicator in background
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
- Include all imports/dependencies
- Add clear comments
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

    except Exception as e:
        response = f"❌ Internal error: {str(e)}"

    finally:
        stop_event.set()
        typing_task.cancel()

    try:
        await update.message.reply_text(
            format_response(response),
            parse_mode="Markdown"
        )
    except Exception:
        try:
            await update.message.reply_text(format_response(response))
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to send: {str(e)}")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            f"⏳ Ingesting PDF: {file_name}\nThis may take a moment..."
        )
        result = ingest_pdf(save_path)
        await update.message.reply_text(result)

    except Exception as e:
        await update.message.reply_text(f"❌ Document error: {str(e)}")


async def handle_github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        words = text.split()
        url = next((w for w in words if "github.com" in w), None)

        if not url:
            await update.message.reply_text("❌ No valid GitHub URL found.")
            return

        await update.message.reply_text(f"⏳ Cloning and indexing repo...\n{url}")
        from core.ingestion import ingest_github
        result = ingest_github(url)
        await update.message.reply_text(result)

    except Exception as e:
        await update.message.reply_text(f"❌ GitHub error: {str(e)}")