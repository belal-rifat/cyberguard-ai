import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "faiss_index")


def load_vectorstore():
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    vectorstore = FAISS.load_local(
        INDEX_DIR,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    return vectorstore


def test_retrieval(query, k=3):
    vectorstore = load_vectorstore()
    results = vectorstore.similarity_search(query, k=k)

    print(f"\nQuery: {query}")
    print(f"Top {k} matching chunks:\n")
    for i, doc in enumerate(results, start=1):
        source = doc.metadata.get("source", "unknown")
        print(f"--- Result {i} (source: {source}) ---")
        print(doc.page_content[:300])
        print()


if __name__ == "__main__":
    test_retrieval("someone is asking for my password urgently over email")
