from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


# output schema
class RouterOutput(BaseModel):
    intent: str = Field(description="hanya boleh berisi: lapor_darurat, tanya_info, atau lainnya")
    disaster_type: str = Field(description="jenis bencana: banjir, gempa, longsor, kebakaran, tsunami, angin, kriminalitas, kecelakaan, spam, lainnya")
    confidence: float = Field(description="nilai keyakinan 0 sampai 1")
    alasan: str = Field(description="alasan klasifikasi")


# agent function
def route_message(user_message: str, chat_history: str = "") -> RouterOutput:
    # inisialisasi model
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0
    )
    
    structured_llm = llm.with_structured_output(RouterOutput)

    system_prompt = """
        Kamu adalah Router Agent pada sistem koordinasi bencana BPBD.
        Tugasmu HANYA mengklasifikasikan pesan warga.

        [INTENT]
        Hanya boleh memilih SATU: 1. lapor_darurat, 2. tanya_info, 3. lainnya

        [ATURAN LAPOR_DARURAT]
        Pilih "lapor_darurat" HANYA jika warga melaporkan kejadian BANJIR.

        [SANGAT PENTING]
        Sistem ini EKSKLUSIF hanya menangani pelaporan darurat untuk BANJIR.
        Jika warga melaporkan BENCANA LAIN (seperti gempa, kebakaran, longsor, tsunami, angin puting beliung, atau kecelakaan), MAKA:
        - intent = lainnya
        - disaster_type = [sesuaikan dengan jenis bencana yang dilaporkan]

        JANGAN PERNAH memilih "lapor_darurat" untuk bencana selain banjir.
        Jangan pernah berhalusinasi. Jawab sesuai schema.
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