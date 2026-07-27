def create_user_response(action):

    if action == "escalate":

        return (
            "Laporan berhasil diverifikasi.\n"
            "Tim BPBD sedang menuju lokasi."
        )

    elif action == "respond":

        return (
            "Laporan diterima dan akan ditinjau operator."
        )

    return (
        "Laporan ditolak karena tidak memenuhi syarat."
    )