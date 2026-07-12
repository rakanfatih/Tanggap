import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

#output yang diharapkan
class RouterOutput(BaseModel):
    intent: str =  Field(description="Pilih satu secara persis: 'lapor_darurat','tanya_info', atau 'lainnya'")
    alasan: str = Field(description="Alasan mengapa memilih intent tersebut")

def route_message(user_message: str):
    print("analisis pesan user ...")

    #inisialisasi model
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    #paksa mengikuti instruksi
    structured_llm = llm.with_structured_output(RouterOutput)

    #template prompt
    system_prompt = """
    kamu adalah  agen pemilah di sistem penanggulangan banjir BPBD Jakarta. tugasmu HANYA membaca pesan warga dan mengklasifikasikan intent mereka.
    
    Kategori Aturan:
    - 'lapor_darurat': jika berisikan kepanikan, air naik, terjebak banjir, butuh evakuasi, atau minta bantuan medis.
    - 'tanya_info': jika pesan berisikan pertanyaan tentang cara evakuasi, lokasi posko, SOP, atau nomor darurat.
    - 'lainnya': jika pesan tidak termasuk dua kategori di atas, seperti curhat, saran, atau hal yang tidak relevan.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Pesan user: {user_message}")
    ])

    #hubungkan prompt ke AI
    chain = prompt | structured_llm

    result = chain.invoke({"user_message": user_message})
    return result

#uji lokal
if __name__ == "__main__":
    #sekanrio 1, laporan darurat
    pesan_1 = "Tolong, air sudah masuk rumah saya, saya terjebak di lantai 2, butuh bantuan evakuasi!"
    print(f"\nPesan: {pesan_1}")
    hasil_1 = route_message(pesan_1)
    print(f"Hasil: {hasil_1}\n")
    print("-" * 40)

    #sekanrio 2, tanya informasi
    pesan_2 = "kalau air mulai naik ke teras, apa yang pertama kali harus dilakukan?"
    print(f"\nPesan: {pesan_2}")
    hasil_2 = route_message(pesan_2)
    print(f"Hasil: {hasil_2}\n")