function checkSearchMatch(id, pesan, status, kategori, keyword) {
    if (!keyword) {
        return true;
    }
    
    return (
        id.includes(keyword) ||
        pesan.includes(keyword) ||
        status.includes(keyword) ||
        kategori.includes(keyword)
    );
}