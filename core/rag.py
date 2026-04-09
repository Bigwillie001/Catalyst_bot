import os
import chromadb
from llama_index.core import VectorStoreIndex, PromptTemplate, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from config import CHROMA_PATH

# 1. ENFORCED STRICT TEMPLATE
STRICT_QA_PROMPT = PromptTemplate(
    "### [GROUND TRUTH CONTEXT]\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Using ONLY the context above, answer the query.\n"
    "If the answer is not in the context, strictly reply: "
    "'DATA INSUFFICIENT — Query falls outside ingested parameters.'\n\n"
    "QUERY: {query_str}\n"
    "EXECUTION: "
)

def query_docs(query: str, top_k: int = 5) -> str:
    """
    RAG Synthesis Engine: Executes retrieval and synthesis using 
    globally defined Settings (Groq + HuggingFace).
    """
    try:
        # Access Persistent Store
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection("codex_docs")

        count = collection.count()
        if count == 0:
            return "VECTOR STORE EMPTY, Please ingest documents."

        # Architecture: Chroma Vector Store -> VectorStoreIndex
        vector_store = ChromaVectorStore(chroma_collection=collection)
        index = VectorStoreIndex.from_vector_store(vector_store)

        # Build Query Engine with strict synthesis parameters
        # Note: Settings.llm and Settings.embed_model must be set in config.py or main.py
        query_engine = index.as_query_engine(
            similarity_top_k=min(top_k, count),
            response_mode="compact",        # Forces LlamaIndex to merge context and stop generic filler
            text_qa_template=STRICT_QA_PROMPT
        )

        # Execute Synthesis
        response = query_engine.query(query)
        return str(response)

    except Exception as e:
        return f"⚡ RAG ERROR: {str(e)}"