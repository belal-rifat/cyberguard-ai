import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "faiss_index")


def load_documents():
    loader = DirectoryLoader(DATA_DIR, glob="*.txt", loader_cls=TextLoader)
    documents = loader.load()
    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(documents)
    return chunks


def build_and_save_index(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(INDEX_DIR)
    return vectorstore


if __name__ == "__main__":
    documents = load_documents()
    print(f"Loaded {len(documents)} documents from {DATA_DIR}")

    chunks = split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    build_and_save_index(chunks)
    print(f"FAISS index saved to {INDEX_DIR}")
