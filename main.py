import os
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder, MessageHandler,
    CommandHandler, filters
)
from bot.handlers import handle_message, handle_document, handle_github
from bot.commands import start_command, help_command, ingest_command, test_command
from config import TELEGRAM_TOKEN

# Global LlamaIndex Settings
from llama_index.core import Settings
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# STEP 1 — Load environment
load_dotenv()

# STEP 2 — Define THE BRAIN globally (Groq LLM)
Settings.llm = Groq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.0,
    max_tokens=9992
)

# STEP 3 — Define THE MEMORY globally (Embeddings)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="all-MiniLM-L6-v2"
)

# STEP 4 — Silence tokenizer warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

print("✅ Catalyst + Embeddings initialized.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("ingest", ingest_command))

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