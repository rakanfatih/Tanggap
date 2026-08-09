import os
import glob
import re
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VECTOR_DB_PATH = BASE_DIR / "vector_db"

load_dotenv()

# data cleaning
def clean_text(text: str) -> str:
    text = re.sub(r'http\S+|www.\S+', '', text)    
    text = re.sub(r'\b(Halaman|Hal|Page)\s*\d+\b', '', text, flags=re.IGNORECASE)    
    text = text.encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def create_vector_db():
    print("memulai proses ingestion dokumen...")
    documents = []

    # load pdf
    pdf_loader = PyPDFDirectoryLoader("data_knowledge/")
    pdf_docs = pdf_loader.load()
    documents.extend(pdf_docs)
    print(f"berhasil memuat {len(pdf_docs)} halaman PDF.")

    # load csv
    csv_files = glob.glob("data_knowledge/*.csv")
    csv_total = 0
    for file in csv_files:
        csv_loader = CSVLoader(file_path=file, encoding="utf-8")
        rows = csv_loader.load()
        csv_total += len(rows)
        documents.extend(rows)
        
    print(f"berhasil memuat {csv_total} baris CSV.")

    if not documents:
        print("tidak ada dokumen yang ditemukan di folder 'data_knowledge/'.")
        return

    # text cleaning
    for doc in documents:
        doc.page_content = clean_text(doc.page_content)

    # text splitting
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    print(f"dokumen dipecah menjadi {len(chunks)} chunks.")

    # embedding and saving to vector database
    print("membuat embedding dan menyimpan ke vectorDB (Chroma)...")
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTOR_DB_PATH)    
    )

    print(f"vectordb berhasil dibuat di: {VECTOR_DB_PATH}")

if __name__ == "__main__":
    create_vector_db()