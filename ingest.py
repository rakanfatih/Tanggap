import os
import glob
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# load environment variables
load_dotenv()

def create_vector_db():
    print ("1. membaca dokumen ...")

    documents = []

    # memuat file pdf 
    print (" memuat file pdf ...")
    pdf_loader = PyPDFDirectoryLoader("data_knowledge/")
    documents.extend(pdf_loader.load())

    # memuat file csv
    print (" memuat file csv ...")
    csv_files = glob.glob("data_knowledge/*csv")
    for file in csv_files:
        # agar simbol kebaca
        csv_loader = CSVLoader(file_path=file, encoding="utf-8")
        documents.extend(csv_loader.load())

    print(f"total halaman/baris data yang dimuat: {len(documents)}" )

    print ("2. chungking ....")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"total chunk yang dibuat: {len(chunks)}")

    print ("3. membuat vector database ...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=OpenAIEmbeddings(),
        persist_directory="./vector_db"    
    )

    print("vector db berhasil diperbarui")

if __name__ == "__main__":
    create_vector_db()
