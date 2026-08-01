import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# output 
class RouterOutput(BaseModel):

    intent: str = Field(description="hanya boleh berisi: lapor_darurat, tanya_info, atau lainnya")
    disaster_type: str = Field(description="jenis bencana: banjir, gempa, longsor, kebakaran, tsunami, angin, kriminalitas, kecelakaan, spam, lainnya")
    confidence: float = Field(description="nilai keyakinan 0 sampai 1")
    alasan: str = Field(description="alasan klasifikasi")

# router agent
def route_message(
        user_message: str,
        chat_history: str = ""
):

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0
    )

    structured_llm = llm.with_structured_output(
        RouterOutput
    )

    system_prompt = """
        Kamu adalah Router Agent pada sistem koordinasi bencana BPBD.
        Tugasmu HANYA mengklasifikasikan pesan warga.

        [INTENT]
        Hanya boleh memilih SATU:
        1. lapor_darurat
        2. tanya_info
        3. lainnya

        [ATURAN LAPOR_DARURAT]
        Pilih "lapor_darurat" HANYA jika warga melaporkan kejadian BANJIR.
        Contoh:
        - rumah kebanjiran
        - air masuk rumah
        - genangan tinggi
        - sungai meluap
        - tanggul jebol
        - banjir besar
        - terjebak banjir
        - butuh evakuasi banjir

        [ATURAN TANYA_INFO]
        Jika warga bertanya mengenai:
        - SOP banjir
        - evakuasi banjir
        - nomor darurat
        - lokasi posko
        - bantuan banjir
        - langkah menghadapi banjir

        [LAINNYA]
        SEMUA kondisi berikut WAJIB memilih "lainnya":
        - gempa
        - tsunami
        - longsor
        - kebakaran
        - angin puting beliung
        - pohon tumbang
        - kriminalitas
        - kecelakaan
        - kehilangan
        - spam
        - candaan
        - salam
        - percakapan biasa

        [DISASTER TYPE]
        Pilih salah satu:
        banjir
        gempa
        tsunami
        longsor
        kebakaran
        angin
        kriminalitas
        kecelakaan
        spam
        lainnya

        [SANGAT PENTING]
        Jika pesan membahas GEMPA,
        MAKA:
        intent = lainnya
        disaster_type = gempa

        JANGAN PERNAH memilih lapor_darurat.

        Hal yang sama berlaku untuk kebakaran,
        longsor,
        tsunami,
        dan bencana selain banjir.

        Jangan pernah berhalusinasi.

        Jawab sesuai schema.
        """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Riwayat sebelumnya:\n{chat_history}\n\nPesan warga saat ini: {user_message}")
    ])

    chain = prompt | structured_llm

    result = chain.invoke({
        "user_message": user_message,
        "chat_history": chat_history
    })

    return result


if __name__ == "__main__":

    tests = [
        "Rumah saya kebanjiran.",
        "Ada gempa bumi besar.",
        "Posko dimana?",
        "Halo",
        "Tolong air sudah masuk rumah saya.",
        "Terjadi kebakaran."
    ]

    for t in tests:

        print("\n====================================")
        print(t)

        hasil = route_message(t)
        print(hasil.model_dump())