console.log("Dashboard Loaded");

const searchInput =
document.getElementById("searchInput");

const statusFilter =
document.getElementById("statusFilter");

const kategoriFilter =
document.getElementById("kategoriFilter");

function filterTable(){
    
    const keyword =
    searchInput.value.toLowerCase();

    const status =
    statusFilter.value.toLowerCase();

    const kategori =
    kategoriFilter.value.toLowerCase();

    const rows =
    document.querySelectorAll(".laporan-row");

    rows.forEach(row=>{
        const id=
        row.dataset.id;

        const pesan = 
        row.dataset.pesan;

        const st =
        row.dataset.status;

        const kat = 
        row.dataset.kategori;

        let tampil = true;

        // search
        if(
            keyword &&
            !(
                id.includes(keyword) ||
                pesan.includes(keyword) ||
                st.includes(keyword) ||
                kat.includes(keyword)
            )
        ){
            tampil = false;
        }

        // filter status
        if(
            status &&
            st !== status
        ){
            tampil = false;
        }

        // filter kategori
        if(
            kategori &&
            kat !== kategori
        ){
            tampil = false;
        }

        row.style.display = 
            tampil ? "" : "none";
    })

    if(typeof filterMarkers === "function"){
    filterMarkers();
    }
}

searchInput.addEventListener(
    "keyup",
    filterTable
);

statusFilter.addEventListener(
    "change",
    filterTable
);

kategoriFilter.addEventListener(
    "change",
    filterTable
);
