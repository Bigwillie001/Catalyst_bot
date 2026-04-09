import os
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder, MessageHandler,
    CommandHandler, filters
)
from bot.handlers import handle_message, handle_document, handle_github
from bot.commands import start_command, help_command, ingest_command, test_command, style_command
from config import TELEGRAM_TOKEN
from database import init_db

# Global LlamaIndex Settings
from llama_index.core import Settings
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# STEP 1 — Load environment
load_dotenv()

# STEP 2 — Define THE BRAIN globally (Groq LLM)
# APPENDED: The strict base rules for Catalyst Core
CATALYST_SYSTEM_PROMPT = r"""You are CatalystBot. You operate under STRICT RAG LIMITATIONS.
1. Never fully use internal knowledge to answer.
2. Use ONLY the provided context.
3. If the context is missing info, respond ONLY with: 'DATA INSUFFICIENT'.
4. No conversational filler, no greetings, no 'Sure, I can help'.
5. LATEX MANDATE: Use ONLY $$ for display math and $ for inline math. Never use \[, \], \(, or \)."""

Settings.llm = Groq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.0,
    max_tokens=9992,system_prompt=CATALYST_SYSTEM_PROMPT
)

Settings.embed_model = HuggingFaceEmbedding(
    model_name="all-MiniLM-L6-v2"
)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

print("✅ Catalyst + Embeddings initialized.")

def main():
    init_db()
    print("✅ User Vault DB Verified.")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("ingest", ingest_command))
    app.add_handler(CommandHandler("style", style_command))

    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r'https://github\.com'),
        handle_github
    ))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    print("🤖 Catalyst Bot is live and running...")
    app.run_polling()

if __name__ == "__main__":
    main()