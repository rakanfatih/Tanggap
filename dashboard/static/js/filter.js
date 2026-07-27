function checkFilterMatch(rowStatus, rowKategori, filterStatus, filterKategori) {
    let matchStatus = true;
    let matchKategori = true;

    // Cek kecocokan status (jika filter aktif)
    if (filterStatus && rowStatus !== filterStatus) {
        matchStatus = false;
    }

    // Cek kecocokan kategori (jika filter aktif)
    if (filterKategori && rowKategori !== filterKategori) {
        matchKategori = false;
    }

    // Harus lolos kedua filter untuk bisa ditampilkan
    return matchStatus && matchKategori;
}