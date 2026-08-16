from pydantic import BaseModel, Field


class DecisionOutput(BaseModel):
    action: str = Field(description="escalate, respond, atau reject")
    eskalasi_posko: bool = Field(description="true jika laporan diteruskan ke dashboard BPBD")
    kategori_laporan: str = Field(description="insiden terverifikasi, perlu tinjauan, atau bukan laporan")
    reason: str = Field(description="alasan keputusan")


def make_decision(
    intent: str,
    disaster_type: str,
    validation_score: int | None = None,
    flood_detected: bool | None = None,
    vision_confidence: float | None = None,
    possible_fake: bool | None = None,
    severity: str | None = None,
    object_count: int | None = None
) -> DecisionOutput:

    if validation_score is None:
        validation_score = 0

    if vision_confidence is None:
        vision_confidence = 0

    if object_count is None:
        object_count = 0
    
    # bukan laporan
    if intent == "lainnya":
        return DecisionOutput(
            action="reject",
            eskalasi_posko=False,
            kategori_laporan="bukan laporan",
            reason="Pesan berada di luar ruang lingkup sistem."
        )

    # tanya informasi
    if intent == "tanya_info":
        return DecisionOutput(
            action="respond",
            eskalasi_posko=False,
            kategori_laporan="bukan laporan",
            reason="Pesan berupa permintaan informasi."
        )

    # hanya banjir
    if disaster_type != "banjir":
        return DecisionOutput(
            action="reject",
            eskalasi_posko=False,
            kategori_laporan="bukan laporan",
            reason="Sistem hanya menangani laporan banjir."
        )

    # foto terindikasi palsu
    if possible_fake:
        return DecisionOutput(
            action="reject",
            eskalasi_posko=False,
            kategori_laporan="perlu tinjauan",
            reason="Foto terindikasi tidak sesuai dengan kondisi banjir."
        )

    # vision tidak menemukan banjir
    if flood_detected is False:
        return DecisionOutput(
            action="reject",
            eskalasi_posko=False,
            kategori_laporan="bukan laporan",
            reason="Laporan ditolak karena objek banjir sama sekali tidak terdeteksi pada gambar."
        )
    
    # kondisi sangat meyakinkan
    if (
        validation_score >= 60
        and vision_confidence >= 0.90
        and severity in ["Tinggi", "Sedang"]
    ):
        return DecisionOutput(
            action="escalate",
            eskalasi_posko=True,
            kategori_laporan="insiden terverifikasi",
            reason="Validator dan Vision Agent sama-sama menunjukkan banjir dengan tingkat keyakinan tinggi."
        )

    # bypass (skor validasi gagal, tapi visual sangat meyakinkan)
    if vision_confidence >= 0.90 and severity == "Tinggi":
        return DecisionOutput(
            action="escalate",
            eskalasi_posko=True,
            kategori_laporan="perlu tinjauan",
            reason="Eskalasi darurat: Vision Agent mendeteksi banjir tingkat Tinggi dengan keyakinan visual yang sangat kuat, mengabaikan skor validasi."
        )

    # banjir terdeteksi tetapi tidak ada objek referensi  
    if flood_detected is True and object_count == 0:
        return DecisionOutput(
            action="escalate",
            eskalasi_posko=True,
            kategori_laporan="perlu tinjauan",
            reason="Banjir terdeteksi, namun tidak ada objek referensi untuk mengukur kedalaman. Eskalasi paksa ke posko untuk pengecekan manual."
        )   

    # cukup yakin
    if (
        validation_score >= 40
        and vision_confidence >= 0.60
    ):
        return DecisionOutput(
            action="respond",
            eskalasi_posko=True,
            kategori_laporan="perlu tinjauan",
            reason="Laporan cukup meyakinkan namun masih memerlukan verifikasi operator."
        )

    # skor rendah (fallback)
    return DecisionOutput(
        action="reject",
        eskalasi_posko=False,
        kategori_laporan="bukan laporan",
        reason="Data validasi belum cukup untuk melakukan eskalasi otomatis."
    )