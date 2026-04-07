import os
import fitz
import git
from config import CHROMA_PATH, UPLOADS_PATH


def _index_directory(path: str):
    from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, StorageContext
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    import chromadb

    Settings.embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
    from llama_index.core.llms import MockLLM
    Settings.llm = MockLLM()

    # Load documents
    try:
        documents = SimpleDirectoryReader(
            path,
            recursive=True,
            required_exts=[
                ".py", ".rs", ".go", ".js", ".ts", ".java",
                ".kt", ".cpp", ".c", ".cs", ".swift", ".sql",
                ".html", ".css", ".txt", ".md", ".json"
            ]
        ).load_data()
    except Exception as e:
        raise Exception(f"Failed to read documents: {str(e)}")

    if not documents:
        raise Exception("No readable files found in this path.")

    print(f"📄 Found {len(documents)} documents to index...")

    # Connect to persistent ChromaDB
    db = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = db.get_or_create_collection("codex_docs")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Index and persist
    VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )

    final_count = collection.count()
    print(f"✅ ChromaDB now has {final_count} chunks stored.")


def ingest_pdf(file_path: str) -> str:
    try:
        doc = fitz.open(file_path)
        text = "".join(page.get_text() for page in doc)

        if not text.strip():
            return "❌ PDF appears to be empty or scanned (no extractable text)."

        # Save as .txt for LlamaIndex to read
        txt_path = file_path.replace(".pdf", ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"📄 PDF extracted: {len(text)} characters")
        _index_directory(os.path.dirname(file_path))
        return f"✅ PDF ingested successfully: *{os.path.basename(file_path)}*"

    except Exception as e:
        return f"❌ PDF ingestion failed: `{str(e)}`"


def ingest_github(repo_url: str) -> str:
    try:
        repo_name = repo_url.rstrip("/").split("/")[-1]
        clone_path = f"{UPLOADS_PATH}/{repo_name}"
        os.makedirs(UPLOADS_PATH, exist_ok=True)

        if os.path.exists(clone_path):
            print(f"📁 Repo already cloned at {clone_path}, re-indexing...")
        else:
            print(f"🔽 Cloning {repo_url}...")
            git.Repo.clone_from(repo_url, clone_path)
            print(f"✅ Cloned to {clone_path}")

        _index_directory(clone_path)
        return f"✅ GitHub repo ingested successfully: *{repo_name}*"

    except Exception as e:
        return f"❌ GitHub ingestion failed: `{str(e)}`"