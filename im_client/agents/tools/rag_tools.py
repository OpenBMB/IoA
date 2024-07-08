import os

PERSIST_DIR = os.environ.get("PERSIST_DIR")

if PERSIST_DIR:
    from llama_index.core.retrievers import VectorIndexRetriever
    from llama_index.llms.openai import OpenAI
    from llama_index.core import VectorStoreIndex
    from llama_index.core.retrievers import VectorIndexRetriever
    from llama_index.core import (
        VectorStoreIndex,
        SimpleDirectoryReader,
        StorageContext,
        load_index_from_storage,
        Settings,
    )

    if not os.path.exists(PERSIST_DIR):
        from llama_index.core.node_parser import SentenceSplitter

        # Local settings
        Settings.chunk_size = int(os.environ.get("CHUNK_SIZE"))  # default 512
        documents = SimpleDirectoryReader(os.environ.get("RAG_DATA")).load_data()
        index = VectorStoreIndex.from_documents(
            documents,
            transformations=[SentenceSplitter(chunk_size=int(os.environ.get("CHUNK_SIZE")))],
            llm=OpenAI(
                temperature=float(os.environ.get("RAG_LLM_TEMPERATURE")),
            ),  # default 0.1 gpt-3.5-turbo
        )
        index = VectorStoreIndex.from_documents(documents)

        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)


def rag_query(query: str):
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=int(os.environ.get("SIMILARITY_TOP_K")),  # default 2
    )
    response = retriever.retrieve(query)
    ret = [item.get_text() for item in response]
    ret = "\n".join(ret)

    return "according to the query and documents, the answers retrieved by rag are \n\n" + ret + "."
