from telegram import Update
from telegram.ext import ContextTypes
from database import save_user_prefs

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
        "/ingest [url] — Index a repo\n"
        "/style — Configure my personality 🎛️\n\n" 
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
        "*To set personality:*\n" 
        "Type `/style` to configure how I reply.\n\n"
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

# APPENDED: The new style command logic
async def style_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    user_id = update.message.from_user.id

    if not args:
        # Show the menu if they just type /style
        await update.message.reply_text(
            "🎛️ *Catalyst bot preference configuration*\n\n"
            "How should I reply to you?\n\n"
            "*1. Verbosity:* Surgical, Standard, Comprehensive\n"
            "*2. Tone:* systematically, Colleague, Mentor\n"
            "*3. Format:* one-line sentence brief,Code-First, Step-by-Step, Scientific\n\n"
            "*Usage:* `/style [Verbosity] [Tone] [Format]`\n"
            "Example: `/style Surgical Machine Code-First`\n\n"
            "*Custom Override:* `/style custom [Your instructions]`\n",
            parse_mode="Markdown"
        )
        return

    # Handle custom text rules
    if args[0].lower() == "custom":
        custom_rule = " ".join(args[1:])
        save_user_prefs(user_id, "Standard", "Colleague", "Standard", custom_rule)
        await update.message.reply_text(f"✅ Custom Profile Locked: {custom_rule}")
    
    # Handle standard 3-word configuration
    else:
        v = args[0] if len(args) > 0 else "Standard"
        t = args[1] if len(args) > 1 else "Colleague"
        f = args[2] if len(args) > 2 else "Standard"
        save_user_prefs(user_id, v, t, f, "")
        await update.message.reply_text(f"✅ Profile Locked:\nVerbosity: {v}\nTone: {t}\nFormat: {f}")