from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

retriever = Chroma(
    collection_name="rag-chroma",
    persist_directory="./.chroma_db",
    embedding_function=OpenAIEmbeddings(),
).as_retriever()


if __name__ == "__main__":
    from langchain_text_splitters import CharacterTextSplitter
    from langchain_community.document_loaders import WebBaseLoader

    urls = [
        "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
        "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
        "https://lilianweng.github.io/posts/2024-07-07-hallucination/",
    ]

    docs = [WebBaseLoader(url).load() for url in urls]
    docs_list = [item for sublist in docs for item in sublist]
    text_splitter = CharacterTextSplitter(chunk_size=250, chunk_overlap=0)
    doc_splits = text_splitter.split_documents(docs_list)

    Chroma.from_documents(
        documents=doc_splits,
        collection_name="rag-chroma",
        embedding=OpenAIEmbeddings(),
        persist_directory="./.chroma_db",
    )
    print(f"Ingested {len(doc_splits)} document chunks into ChromaDB.")
