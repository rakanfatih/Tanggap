import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# output
class ExecutorOutput(BaseModel):

    final_response: str = Field(
        description="Pesan akhir yang dikirim kepada warga."
    )

# exeutor agent
def execute_response(
    user_message: str,
    intent: str,
    action: str,
    kategori_laporan: str,
    reason: str,
    context: str = "",
    chat_history: str = ""
):

    print("\n==============================")
    print("[EXECUTOR AGENT]")
    print("==============================")

    print(f"Intent     : {intent}")
    print(f"Action     : {action}")
    print(f"Kategori   : {kategori_laporan}")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2
    )

    structured_llm = llm.with_structured_output(
        ExecutorOutput
    )

    system_prompt = """
        Kamu adalah Executor Agent pada sistem koordinasi bencana BPBD.

        Tugasmu BUKAN mengambil keputusan.

        Keputusan sistem sudah diberikan oleh Decision Agent.

        Tugasmu hanya menyusun balasan akhir yang natural,
        jelas,
        singkat,
        empatik,
        dan mudah dipahami masyarakat.

        ==================================================

        ATURAN

        ==================================================

        1.
        JANGAN mengubah Action.

        2.
        JANGAN mengubah Kategori Laporan.

        3.
        Jika Action = reject

        Jelaskan dengan sopan bahwa aplikasi hanya menangani
        laporan dan informasi mengenai banjir.

        Jangan memberikan SOP.

        ==================================================

        4.
        Jika Action = respond
        dan Intent = tanya_info

        Jawab menggunakan Context.

        Jika Context kosong,
        katakan informasi belum tersedia.

        ==================================================

        5.
        Jika Action = respond
        dan Kategori = perlu tinjauan

        Sampaikan bahwa laporan telah diterima,
        namun masih memerlukan verifikasi operator BPBD.

        Jangan mengatakan laporan telah diteruskan ke Posko.

        ==================================================

        6.
        Jika Action = escalate

        Sampaikan bahwa laporan telah diterima
        dan telah diteruskan kepada Posko BPBD.

        Berikan instruksi keselamatan awal
        berdasarkan Context.

        ==================================================

        7.
        Jangan membuat fakta baru.

        Gunakan HANYA informasi pada Context.

        ==================================================

        8.
        Gunakan bahasa Indonesia yang natural,
        ramah,
        dan profesional.

        Jangan terlalu panjang.
        """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                """
                Riwayat Percakapan Sebelumnya:
                {chat_history}

                Pesan Warga (Saat Ini):
                {user_message}

                Intent:
                {intent}

                Action:
                {action}

                Kategori:
                {kategori_laporan}

                Alasan:
                {reason}

                Context:
                {context}
                """
            )
        ]
    )

    chain = prompt | structured_llm

    hasil = chain.invoke(
        {
            "user_message": user_message,
            "intent": intent,
            "action": action,
            "kategori_laporan": kategori_laporan,
            "reason": reason,
            "context": context
        }
    )

    print("\n===== HASIL EXECUTOR =====")
    print(hasil.final_response)

    return hasil


# test
if __name__ == "__main__":

    hasil = execute_response(
        user_message="Rumah saya kebanjiran.",
        intent="lapor_darurat",
        action="escalate",
        kategori_laporan="insiden terverifikasi",
        reason="validation score tinggi",
        context="""
        Segera menuju tempat yang lebih tinggi.

        Matikan aliran listrik apabila masih aman dilakukan.

        Ikuti arahan petugas BPBD.
        """
    )

    print("\n===== OUTPUT =====")
    print(hasil.model_dump())