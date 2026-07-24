// inisialisasi
const map = L.map("map").setView(
    [-6.2088, 106.8456],
    11
);

let markers = [];

// tile
L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        attribution: "&copy; OpenStreetMap Contributors"
    }
).addTo(map);

// pin color
const greenIcon = new L.Icon({
    iconUrl:
        "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",

    shadowUrl:
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",

    iconSize: [25,41],
    iconAnchor:[12,41],
    popupAnchor:[1,-34],
    shadowSize:[41,41]
});

const yellowIcon = new L.Icon({
    iconUrl:
        "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-gold.png",

    shadowUrl:
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",

    iconSize:[25,41],
    iconAnchor:[12,41],
    popupAnchor:[1,-34],
    shadowSize:[41,41]
});

const greyIcon = new L.Icon({
    iconUrl:
        "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png",

    shadowUrl:
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",

    iconSize:[25,41],
    iconAnchor:[12,41],
    popupAnchor:[1,-34],
    shadowSize:[41,41]
});

// get data
async function loadMarkers(){

    const response = await fetch(
        "http://127.0.0.1:8000/api/map"
    );

    const data = await response.json();

    console.log(data);

    data.forEach(item => {
        if(
            item.latitude == null ||
            item.longitude == null
        ){
            return;
        }

        // Tentukan warna marker
        let icon = greyIcon;

        if(item.kategori === "insiden terverifikasi"){
            icon = greenIcon;
        }   
        else if(item.kategori === "perlu tinjauan"){
            icon = yellowIcon;
        }

        const marker = L.marker(
            [
                item.latitude,
                item.longitude
            ],
            {
                icon: icon
            }
        )
        .addTo(map)
        .bindPopup(
            `
            <div style="min-width:240px">

            <h6>
            📍 Laporan #${item.id}
            </h6>
            
            <hr>

            <p style="margin-bottom:8px;">
            💬 ${item.pesan}
            </p>
            
            <table class="table table-sm mb-2">
            
            <tr>
            <td><b>Status</b></td>
            <td>${item.status}</td>
            </tr>

            <tr>
            <td><b>Kategori</b></td>
            <td>${item.kategori}</td>
            </tr>

            <tr>
            <td><b>Waktu</b></td>
            <td>${item.waktu}</td>
            </tr>

            <tr>
            <td><b>Latitude</b></td>
            <td>${item.latitude}</td>
            </tr>

            <tr>
            <td><b>Longitude</b></td>
            <td>${item.longitude}</td>
            </tr>

            </table>

            <div class="d-grid">

            <a
            class="btn btn-primary btn-sm"
            href="http://127.0.0.1:5000/laporan/${item.id}">

            Lihat Detail

            </a>

            </div>

            </div>
            `
        );
        markers.push({
        marker: marker,
        data: item
        });
    });

}

loadMarkers();

// filter
function filterMarkers(){

    const keyword =
    document
    .getElementById("searchInput")
    .value
    .toLowerCase();

    const status =
    document
    .getElementById("statusFilter")
    .value
    .toLowerCase();

    const kategori =
    document
    .getElementById("kategoriFilter")
    .value
    .toLowerCase();

    markers.forEach(item=>{
        const data = item.data;

        let tampil = true;

        if(
            keyword &&
            !(
                data.id.toString().includes(keyword) ||
                data.pesan.toLowerCase().includes(keyword) ||
                data.status.toLowerCase().includes(keyword) ||
                data.kategori.toLowerCase().includes(keyword)
            )
        ){
            tampil = false;
        }

        if(
            status &&
            data.status.toLowerCase() !== status
        ){
            tampil = false;
        }

        if(
            kategori &&
            data.kategori.toLowerCase() !== kategori
        ){
            tampil = false;
        }

        if(tampil){
            if(!map.hasLayer(item.marker)){
                item.marker.addTo(map);
            }

        }else{
            if(map.hasLayer(item.marker)){
                map.removeLayer(item.marker);
            }    
        }
    });

}

// legend
const legend = L.control({
    position: "bottomright"
});

legend.onAdd = function () {

    const div = L.DomUtil.create(
        "div",
        "info legend"
    );

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

        🟢 Insiden Terverifikasi

        <br>

        🟡 Perlu Tinjauan

        <br>

        ⚪ Selesai

        </div>
    `;

    return div;

};

legend.addTo(map);