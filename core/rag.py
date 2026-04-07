def query_docs(query: str, top_k: int = 5) -> str:
    try:
        import chromadb
        from llama_index.vector_stores.chroma import ChromaVectorStore
        from llama_index.core import VectorStoreIndex, Settings
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        from llama_index.core.llms import MockLLM
        from config import CHROMA_PATH

        # Silence MockLLM warning — LlamaIndex needs something set
        Settings.llm = MockLLM()
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="all-MiniLM-L6-v2"
        )

        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection("codex_docs")

        count = collection.count()
        if count == 0:
            return ""

        actual_k = min(top_k, count)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        index = VectorStoreIndex.from_vector_store(vector_store)
        retriever = index.as_retriever(similarity_top_k=actual_k)
        nodes = retriever.retrieve(query)

        if not nodes:
            return ""

        context_parts = []
        for i, node in enumerate(nodes):
            context_parts.append(f"[Source {i+1}]\n{node.text}")

        return "\n\n---\n\n".join(context_parts)

    except Exception as e:
        print(f"RAG Error: {e}")
        return ""