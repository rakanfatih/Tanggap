import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

#output akhir
class ExecutorOutput(BaseModel):
    balasan_warga: str = Field(description="pesan balasan dalam bahasa Indonesia yang natural, ringkas, dan mudah dipahami warga. berikan instruksi yang jelas.")
    eskalasi_posko: bool = Field(description="true jika ini laporan darurat yang butuh penanganan fisik tim posko, false jika ini hanya pertanyaan info atau spam.")
    kategori_laporan: str = Field(description="pilih salah satu: 'insiden terverifikasi', 'perlu tinjauan', atau 'bukan laporan'")

def execute_response(intent: str, user_message: str, context_data: str = "", validation_data: dict = None):
    print("agen Eksekutor sedang merumuskan keputusan akhir...")

    #inisialisasi llm
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
    structured_llm = llm.with_structured_output(ExecutorOutput)

    #prompt
    system_prompt = """
    kamu adalah agen eksekutor pusat di sistem penanggulangan banjir BPBD Jakarta.
    tugasmu adalah memberikan balasan akhir kepada warga berdasarkan data yang dikumpulkan agen lain.
    
    ATURAN SANGAT KETAT:
    1. JANGAN berhalusinasi. Jika ada referensi SOP yang diberikan, rumuskan balasan HANYA berdasarkan SOP tersebut.
    2. Gunakan bahasa yang ringkas, menenangkan, dan tidak membuat panik.
    3. JIKA intent = 'lapor_darurat': Perhatikan 'Data Validasi'. Jika validitas tinggi, beritahu warga bahwa tim posko segera diberitahu, dan berikan instruksi keselamatan pertama (misal: evakuasi mandiri, matikan listrik). Set eskalasi_posko ke True.
    4. JIKA intent = 'tanya_info': Jawab pertanyaan warga berdasarkan 'Konteks SOP'. Set eskalasi_posko ke False.
    5. JIKA intent = 'lainnya': Tolak dengan sopan, ingatkan bahwa ini adalah saluran khusus darurat banjir BPBD. Set eskalasi_posko ke False.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Intent: {intent}\nPesan Warga: {user_message}\nKonteks SOP: {context_data}\nData Validasi: {validation_data}")
    ])

    #rangkai prompt dan eksekusi
    chain = prompt | structured_llm
    
    result = chain.invoke({
        "intent": intent,
        "user_message": user_message,
        "context_data": context_data,
        "validation_data": validation_data if validation_data else "Tidak ada data validasi"
    })
    
    return result

#uji lokal
if __name__ == "__main__":
    print("=== SKENARIO 1: LAPORAN DARURAT ===")
    intent_masuk = "lapor_darurat"
    pesan_masuk = "Tolong, air sudah masuk rumah saya!"
    # simulasi data dari validator_agent.py
    data_detektif = {
        "koordinat_gps": "-6.1601, 106.7416",
        "kondisi_cuaca_aktual": "Hujan Lebat, Suhu: 25°C",
        "status_validasi": "Tinggi (Cuaca Mendukung)"
    }
    
    keputusan_1 = execute_response(
        intent=intent_masuk, 
        user_message=pesan_masuk, 
        validation_data=data_detektif
    )
    
    print(f"\nbalasan untuk warga:\n{keputusan_1.balasan_warga}")
    print(f"\nkirim ke dashboard admin?: {keputusan_1.eskalasi_posko}")
    print(f"status: {keputusan_1.kategori_laporan}")
    
    print("\n" + "="*40 + "\n")
    
    print("=== SKENARIO 2: TANYA INFORMASI (RAG) ===")
    intent_masuk_2 = "tanya_info"
    pesan_masuk_2 = "kalau air masuk, apa yang harus dimatikan?"
    #simulasi data dari retriever_agent.py
    teks_sop = "[Referensi 1]: Segera matikan meteran listrik dan cabut selang gas saat air mulai memasuki area rumah."
    
    keputusan_2 = execute_response(
        intent=intent_masuk_2,
        user_message=pesan_masuk_2,
        context_data=teks_sop
    )
    
    print(f"\nBalasan untuk Warga:\n{keputusan_2.balasan_warga}")
    print(f"\nKirim ke Dashboard Admin?: {keputusan_2.eskalasi_posko}")
    print(f"Status: {keputusan_2.kategori_laporan}")