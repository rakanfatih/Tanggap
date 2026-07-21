import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DB_PATH = BASE_DIR / "vector_db"

load_dotenv()

# retriever agent
def retrieve_sop_info(
    query: str,
    k: int = 5
):

    print("\n==============================")
    print("[RETRIEVER AGENT]")
    print("==============================")

    print(f"Query : {query}")

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3"
    )

    try:

        vectorstore = Chroma(
            persist_directory=str(VECTOR_DB_PATH),
            embedding_function=embeddings
        )

    except Exception as e:

        print(f"[RETRIEVER] Error membuka VectorDB : {e}")

        return {
            "context": "",
            "total_references": 0
        }

    try:

        documents = vectorstore.similarity_search(
            query,
            k=k
        )

    except Exception as e:

        print(f"[RETRIEVER] Error similarity search : {e}")

        return {
            "context": "",
            "total_references": 0
        }

    if not documents:

        print("[RETRIEVER] Tidak ada referensi ditemukan.")

        return {
            "context": "",
            "total_references": 0
        }

    context = ""

    for i, doc in enumerate(documents):

        context += (
            f"[Referensi {i+1}]\n"
            f"{doc.page_content}\n\n"
        )

    print(f"Total Referensi : {len(documents)}")

    return {
        "context": context,
        "total_references": len(documents)
    }


# test
if __name__ == "__main__":

    hasil = retrieve_sop_info(

        "Apa yang harus dilakukan ketika banjir?"

    )

    print("\n===== CONTEXT =====\n")
    print(hasil["context"])
    print(f"\nJumlah Referensi : {hasil['total_references']}")