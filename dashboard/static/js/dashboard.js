console.log("Dashboard Loaded");

const searchInput = document.getElementById("searchInput");
const statusFilter = document.getElementById("statusFilter");
const kategoriFilter = document.getElementById("kategoriFilter");

function filterTable() {
    
    const keyword = searchInput.value.toLowerCase();
    const status = statusFilter.value.toLowerCase();
    const kategori = kategoriFilter.value.toLowerCase();

    const rows = document.querySelectorAll(".laporan-row");

    rows.forEach(row => {
        const id = row.dataset.id;
        const pesan = row.dataset.pesan;
        const st = row.dataset.status;
        const kat = row.dataset.kategori;

        const lolosPencarian = checkSearchMatch(id, pesan, st, kat, keyword);
        
        const lolosFilter = checkFilterMatch(st, kat, status, kategori);

        if (lolosPencarian && lolosFilter) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });

    if (typeof filterMarkers === "function") {
        filterMarkers();
    }
}

searchInput.addEventListener("keyup", filterTable);
statusFilter.addEventListener("change", filterTable);
kategoriFilter.addEventListener("change", filterTable);