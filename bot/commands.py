from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to Catalyst Bot!*\n\n"
        "I'm your personal AI coding assistant.\n\n"
        "*What I can do:*\n"
        "🔤 Write code in 12 languages\n"
        "🐛 Debug and fix errors\n"
        "📄 Learn from your PDFs\n"
        "🐙 Index your GitHub repos\n\n"
        "*Commands:*\n"
        "/start — This message\n"
        "/help — Full guide\n"
        "/ingest [github_url] — Index a repo\n\n"
        "Just *send me any message* to get started!",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Catalyst Bot Help*\n\n"
        "*To write code:*\n"
        "Just describe what you want. e.g:\n"
        "`Build a REST API in Go`\n\n"
        "*To debug an error:*\n"
        "Paste your error directly. e.g:\n"
        "`TypeError: NoneType has no attribute...`\n\n"
        "*To add docs:*\n"
        "Send a PDF file directly\n"
        "Or: `/ingest https://github.com/user/repo`\n\n"
        "*Supported Languages:*\n"
        "Python, Rust, Kotlin, Go, C++, C#, C,\n"
        "HTML/CSS, JavaScript, SQL, Swift,\n"
        "TypeScript, Java",
        parse_mode="Markdown"
    )

async def ingest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Please provide a GitHub URL.\n"
            "Usage: `/ingest https://github.com/user/repo`",
            parse_mode="Markdown"
        )
        return
    url = args[0]
    await update.message.reply_text(
        f"⏳ Cloning and indexing `{url}`...",
        parse_mode="Markdown"
    )
    from core.ingestion import ingest_github
    result = ingest_github(url)
    await update.message.reply_text(result)
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from core.rag import query_docs
    import chromadb
    from config import CHROMA_PATH

    try:
        db = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = db.get_or_create_collection("codex_docs")
        count = collection.count()

        # Test retrieval
        sample = query_docs("function example code")
        preview = sample[:300] if sample else "Nothing retrieved yet."

        await update.message.reply_text(
            f"🧠 Knowledge Base Status:\n\n"
            f"📦 Total chunks stored: {count}\n\n"
            f"🔍 Sample retrieval:\n{preview}...",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Test failed: {str(e)}")