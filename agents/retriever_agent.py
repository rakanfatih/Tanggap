import os

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from pathlib import Path
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DB_PATH = BASE_DIR / "vector_db"

load_dotenv()


# agent function
def retrieve_sop_info(query: str, k: int = 5): 
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

    try:
        vectorstore = Chroma(persist_directory=str(VECTOR_DB_PATH), embedding_function=embeddings)
    except Exception as e:
        print(f"gagal membuka vectordb: {e}")
        return {"context": "", "total_references": 0}

    try:
        documents = vectorstore.similarity_search(query, k=k)
    except Exception as e:
        print(f"gagal melakukan similarity search: {e}")
        return {"context": "", "total_references": 0}

    if not documents:
        return {"context": "", "total_references": 0}

    context = ""

    for i, doc in enumerate(documents):
        context += (
            f"[Referensi {i+1}]\n"
            f"{doc.page_content}\n\n"
        )
        
    return {"context": context, "total_references": len(documents)}