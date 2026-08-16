// inisialisasi peta
const map = L.map("map").setView(
    [-6.2088, 106.8456],
    11
);

let markers = [];

// set tile dari openstreetmap
L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        attribution: "&copy; OpenStreetMap Contributors"
    }
).addTo(map);

// konfigurasi warna pin
const greenIcon = new L.Icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const yellowIcon = new L.Icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-gold.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const greyIcon = new L.Icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// fetch data laporan dan buat marker
async function loadMarkers() {
    try {
        const response = await fetch(API_BASE_URL + "/api/map");
        const data = await response.json();

        data.forEach(item => {
            // abaikan data tanpa koordinat
            if (item.latitude == null || item.longitude == null) {
                return;
            }

            // penentuan warna marker
            let icon = greyIcon; // default fallback

            if (item.status === "Selesai") {
                icon = greyIcon;
            } else if (item.kategori === "insiden terverifikasi") {
                icon = greenIcon;
            } else if (item.kategori === "perlu tinjauan") {
                icon = yellowIcon;
            }

            // buat marker
            const marker = L.marker(
                [item.latitude, item.longitude],
                { icon: icon }
            ).addTo(map);
            
            // konten popup
            const popupContent = `
                <div style="min-width: 260px; font-family: 'Poppins', sans-serif;">
                    <!-- header popup -->
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 8px; margin-bottom: 12px;">
                        <h6 style="margin: 0; font-weight: 600; color: #2c3e50;">
                            📍 Laporan #${item.id}
                        </h6>
                        <span class="badge ${item.status === 'Selesai' ? 'bg-secondary' : (item.status === 'Diproses' ? 'bg-primary' : 'bg-warning text-dark')}">${item.status}</span>
                    </div>
                    
                    <!-- pesan warga -->
                    <p style="font-size: 13px; font-style: italic; color: #555; background: #f8f9fc; padding: 8px; border-radius: 5px; border-left: 3px solid #e57e25; margin-bottom: 12px;">
                        "${item.pesan}"
                    </p>

                    <!-- informasi detail -->
                    <div style="font-size: 13px; color: #444; margin-bottom: 15px;">
                        <div style="margin-bottom: 8px;">
                            <i class="fa-regular fa-clock me-2 text-muted"></i> <b>Waktu:</b> ${item.waktu}
                        </div>
                        <div style="display: flex; align-items: flex-start;">
                            <i class="fa-solid fa-map-location-dot me-2 text-muted" style="margin-top: 3px;"></i>
                            <div>
                                <b>Alamat:</b><br>
                                <span style="color: #666; font-size: 11px; line-height: 1.3; display: inline-block; margin-top: 2px;">
                                    ${item.alamat}
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- tombol navigasi -->
                    <div class="d-grid">
                        <a class="btn btn-primary btn-sm rounded-2 shadow-sm fw-bold" href="/laporan/${item.id}">
                            Lihat Detail
                        </a>
                    </div>
                </div>
            `;

            marker.bindPopup(popupContent);

            // simpan marker ke array untuk keperluan filter
            markers.push({
                marker: marker,
                data: item
            });
        });
    } catch (error) {
        console.error("gagal memuat data map:", error);
    }
}

loadMarkers();

// fungsi filter marker
function filterMarkers() {
    const keyword = document.getElementById("searchInput").value.toLowerCase();
    const status = document.getElementById("statusFilter").value.toLowerCase();
    const kategori = document.getElementById("kategoriFilter").value.toLowerCase();

    markers.forEach(item => {
        const data = item.data;
        let tampil = true;

        if (keyword && !(
            data.id.toString().includes(keyword) ||
            data.pesan.toLowerCase().includes(keyword) ||
            data.status.toLowerCase().includes(keyword) ||
            data.kategori.toLowerCase().includes(keyword)
        )) {
            tampil = false;
        }

        if (status && data.status.toLowerCase() !== status) {
            tampil = false;
        }

        if (kategori && data.kategori.toLowerCase() !== kategori) {
            tampil = false;
        }

        if (tampil) {
            if (!map.hasLayer(item.marker)) {
                item.marker.addTo(map);
            }
        } else {
            if (map.hasLayer(item.marker)) {
                map.removeLayer(item.marker);
            }    
        }
    });
}

// tambahkan legenda ke peta
const legend = L.control({ position: "bottomright" });

legend.onAdd = function () {
    const div = L.DomUtil.create("div", "info legend");

    div.innerHTML = `
        <div style="
            background:white;
            padding:10px;
            border-radius:10px;
            box-shadow:0 0 10px rgba(0,0,0,.2);
            font-size:14px;
        ">
        <b>Keterangan</b>
        <hr style="margin:6px 0">
        🟢 Insiden Terverifikasi<br>
        🟡 Perlu Tinjauan<br>
        ⚪ Selesai
        </div>
    `;

    return div;
};

legend.addTo(map);