import os
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder, MessageHandler,
    CommandHandler, filters
)
from bot.handlers import handle_message, handle_document, handle_github
from bot.commands import start_command, help_command, ingest_command, test_command
from config import TELEGRAM_TOKEN

# LlamaIndex Imports
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# 1. LOAD ENVIRONMENT FIRST
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


Settings.llm = GoogleGenAI(
    model="models/gemini-2.0-flash",
    api_key=api_key
)

# 3. GLOBAL EMBEDDING SETUP (The "Learning" engine)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Silence tokenizer warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

print("✅ LLM and Embeddings initialized. MockLLM is now disabled.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handlers
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