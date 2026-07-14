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

    #interception
    if validation_data:
        status_validasi = validation_data.get("status_validasi", "").lower()
        if "hoax" in status_validasi:
            cuaca = validation_data.get("kondisi_cuaca_aktual", "cerah")
            print("[EKSEKUTOR] Laporan terdeteksi HOAX. Memblokir dari posko BPBD...")
            
            return ExecutorOutput(
                balasan_warga=f"PERINGATAN: Berdasarkan sensor satelit cuaca, lokasi Anda saat ini terpantau {cuaca}. Tidak ada indikasi hujan. Sistem menolak laporan Anda. Mohon jangan mengirimkan laporan palsu ke layanan darurat BPBD.",
                eskalasi_posko=False,
                kategori_laporan="bukan laporan" 
            )

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
    3. JIKA intent = 'lapor_darurat': Beritahu warga bahwa tim posko BPBD segera diberitahu untuk tindakan evakuasi. Berikan instruksi keselamatan pertama dengan ringkas (misal: matikan listrik, evakuasi ke tempat tinggi). Set eskalasi_posko ke True. Set kategori 'insiden terverifikasi'.
    4. JIKA intent = 'tanya_info': Jawab pertanyaan warga berdasarkan 'Konteks SOP'. Set eskalasi_posko ke False. Set kategori 'bukan laporan'.
    5. JIKA intent = 'lainnya': Tolak dengan sopan, ingatkan bahwa ini adalah saluran khusus darurat banjir BPBD. Set eskalasi_posko ke False. Set kategori 'bukan laporan'.
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