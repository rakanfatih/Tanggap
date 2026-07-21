from pydantic import BaseModel, Field

#
class DecisionOutput(BaseModel):

    action: str = Field(
        description="escalate, respond, atau reject"
    )

    eskalasi_posko: bool = Field(
        description="true jika laporan harus diteruskan ke dashboard posko."
    )

    kategori_laporan: str = Field(
        description="insiden terverifikasi, perlu tinjauan, atau bukan laporan"
    )

    reason: str = Field(
        description="alasan keputusan."
    )

#decision agent
def make_decision(
    intent: str,
    disaster_type: str,
    validation_score: int | None = None
):

    print("\n==============================")
    print("[DECISION AGENT]")
    print("==============================")

    print(f"Intent            : {intent}")
    print(f"Disaster Type     : {disaster_type}")
    print(f"Validation Score  : {validation_score}")

    # jika lainnya
    if intent == "lainnya":
        hasil = DecisionOutput(
            action="reject",
            eskalasi_posko=False,
            kategori_laporan="bukan laporan",
            reason="pesan berada di luar ruang lingkup sistem."
        )
        print(hasil)
        return hasil

    # jika tanya info
    if intent == "tanya_info":
        hasil = DecisionOutput(
            action="respond",
            eskalasi_posko=False,
            kategori_laporan="bukan laporan",
            reason="pesan berupa permintaan informasi."
        )
        print(hasil)
        return hasil

    # jika lapor darurat
    if intent == "lapor_darurat":

        if disaster_type != "banjir":
            hasil = DecisionOutput(
                action="reject",
                eskalasi_posko=False,
                kategori_laporan="bukan laporan",
                reason="jenis bencana berada di luar ruang lingkup sistem."
            )
            print(hasil)
            return hasil

        if validation_score is None:
            validation_score = 0
        
        # terverifikasi
        if validation_score >= 80:
            hasil = DecisionOutput(
                action="escalate",
                eskalasi_posko=True,
                kategori_laporan="insiden terverifikasi",
                reason="laporan banjir memiliki skor validasi tinggi."
            )
            print(hasil)
            return hasil

        # perlu tinjauan
        hasil = DecisionOutput(
            action="respond",
            eskalasi_posko=False,
            kategori_laporan="perlu tinjauan",
            reason="hasil validasi belum cukup untuk memverifikasi laporan sehingga memerlukan tinjauan operator."
        )
        print(hasil)
        return hasil

    #fallback 
    hasil = DecisionOutput(
        action="reject",
        eskalasi_posko=False,
        kategori_laporan="bukan laporan",
        reason="keputusan tidak dapat ditentukan."
    )
    print(hasil)
    return hasil

# test
if __name__ == "__main__":

    tests = [
        ("lapor_darurat", "banjir", 100),
        ("lapor_darurat", "banjir", 60),
        ("tanya_info", "banjir", None),
        ("lainnya", "gempa", None)
    ]

    for t in tests:

        print("\n====================================")

        hasil = make_decision(
            intent=t[0],
            disaster_type=t[1],
            validation_score=t[2]
        )

        print(hasil.model_dump())