import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

def retrieve_sop_info(query: str):
    print(f"agen pemilah sedang mencari informasi untuk: '{query} ...")

    #panggil model embedding
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

    #buka vector db
    try:
        vectorstore = Chroma(
            persist_directory="./vector_db",
            embedding_function=embeddings
        )
    except Exception as e:
        return "error: database vector belum tersedia. jalankan ingest.py terlebih dahulu."
    
    #similarity search
    search_result = vectorstore.similarity_search(query, k=3)

    #if tidak ada hasil
    if not search_result:
        return "maaf, tidak ada informasi terkait SOP atau pedoman tersebut di dalam database."
    
    #gabungkan hasil jadi 1 teks panjang
    context = ""
    for i, doc in enumerate(search_result):
        context += f"[Referensi {i+1}]:\n{doc.page_content}\n\n"

    return context 

#uji lokal
if __name__ == "__main__":
    #sekanrio: uji pertanyaan dari router agent
    pertanyaan_warga = "kalau air mulai naik ke teras, apa yang pertama kali harus dilakukan?"

    print("-" * 40)
    hasil_konteks = retrieve_sop_info(pertanyaan_warga)

    print("\n--- HASIL PENCARIAN DARI BUKU SAKU/SOP ---")
    print(hasil_konteks)
    