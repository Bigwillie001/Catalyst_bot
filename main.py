import os
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder, MessageHandler,
    CommandHandler, filters
)
from bot.handlers import handle_message, handle_document, handle_github
from bot.commands import start_command, help_command, ingest_command, test_command
from config import TELEGRAM_TOKEN

# LlamaIndex Embedding Setup only — LLM is handled by Groq in core/llm.py
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.llms import MockLLM

# STEP 1 — Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# STEP 2 — Set embeddings globally for RAG
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# STEP 3 — Silence LlamaIndex LLM requirement (Groq handles all LLM calls)
Settings.llm = MockLLM()

# STEP 4 — Silence tokenizer warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

print("✅ Embeddings initialized.")

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