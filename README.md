# ArUco Marker Detection + Pose Estimation

**Tugas Onboarding Divisi Vision — GMRT / ABU Robocon 2027**

Proyek ini membangun sistem pengenalan **ArUco marker** (fiducial marker) memakai Python + OpenCV, sebagai dasar *localization* visual untuk robot kompetisi. Robot perlu tahu posisi dirinya dan objek referensi di lapangan tanpa bergantung pada komunikasi wireless antar robot — solusinya, kita tempel marker sebagai **referensi visual statis** yang bisa dibaca kamera robot. Setiap marker punya ID unik yang kita petakan ke satu peran/state (Standby, Ambil, Lepas, Putar CW, Putar CCW), sehingga sekali kamera membaca marker, robot langsung tahu konteks posisi tersebut. Sebagai nilai tambah, proyek ini juga menghitung **pose** (jarak dan orientasi) marker terhadap kamera.

---

## 📋 Untuk Member Baru: Tugasnya Apa?

Kalau kamu baru masuk dan ditugaskan mengerjakan ini, berikut ringkasan lengkapnya.

### Yang harus dibuat

**Wajib:**

1. **`generate_markers.py`** — men-generate gambar marker ArUco ID 0–4 (dictionary `DICT_4X4_50`), disimpan sebagai PNG per ID, siap diprint atau ditampilkan di layar HP.
2. **`detect_markers.py`** — membuka webcam real-time dan:
   - mendeteksi marker ArUco yang tertangkap kamera,
   - menggambar bounding box di sekeliling marker,
   - menampilkan **label peran** (bukan cuma angka ID), contoh: `ID 1 - Ambil`,
   - tidak crash saat **tidak ada** marker terdeteksi,
   - menangani **lebih dari satu** marker dalam frame yang sama.

**Bonus (nilai tambah):**

3. **Pose estimation** — hitung jarak (*translation vector*) dan orientasi (*rotation vector*) tiap marker terhadap kamera, dengan asumsi ukuran fisik marker 10 cm × 10 cm, memakai file kalibrasi kamera di folder `calibration/`.
4. **Axis 3D** — gambar sumbu X/Y/Z di atas tiap marker yang berhasil di-pose-estimate.
5. **Info di layar** — tampilkan jarak (cm) dan sudut orientasi sebagai teks di samping tiap marker.

### Yang dikumpulkan

| # | Deliverable | Keterangan |
|---|---|---|
| 1 | **Link repo GitHub** | Hasil fork. Pastikan repo publik, atau mentor sudah di-invite sebagai collaborator. |
| 2 | **Link video YouTube** | Boleh *unlisted*. Durasi singkat, menunjukkan minimal **3 ID berbeda** terdeteksi dengan label peran yang benar. Kalau mengerjakan bonus, tunjukkan juga axis 3D + jarak/orientasi. |
| 3 | **Dokumentasi** | Cukup `README.md` di repo yang sama — tidak perlu file terpisah. |

> ⚠️ Video harus menunjukkan **kode benar-benar jalan**, bukan screenshot statis.

### Checklist evaluasi mentor

- [ ] Repo bisa di-clone dan `pip install -r requirements.txt` jalan tanpa error
- [ ] `generate_markers.py` menghasilkan marker ID 0–4 yang valid dan bisa dideteksi balik
- [ ] `detect_markers.py` mendeteksi marker real-time dari webcam dengan label peran yang benar
- [ ] Program tidak crash saat tidak ada marker / banyak marker di frame
- [ ] README lengkap
- [ ] Video menunjukkan kode benar-benar jalan
- [ ] *(Bonus)* Pose estimation + axis 3D berfungsi dan keterbatasannya dijelaskan di README

---

## 🏷️ Skema ID Marker

Dictionary yang dipakai: **`DICT_4X4_50`** (matriks 4×4 bit, kapasitas 50 ID unik).

| ID | Peran | Arti |
|:--:|-------|------|
| 0 | **Standby** | Robot diam menunggu instruksi |
| 1 | **Ambil** | Titik pengambilan objek |
| 2 | **Lepas** | Titik pelepasan objek |
| 3 | **Putar CW** | Rotasi searah jarum jam |
| 4 | **Putar CCW** | Rotasi berlawanan jarum jam |

> **Catatan konteks:** label "peran" di sini murni untuk memperjelas maksud tiap ID. Implementasinya adalah **pembacaan marker statis (localization)** — bukan sinyal real-time antar robot. Komunikasi antar robot adalah topik terpisah.

Tabel ini didefinisikan sebagai `MARKER_ROLES` di `generate_markers.py` **dan** `detect_markers.py`. Kedua script sengaja dibuat berdiri sendiri supaya gampang dibaca/dicopy satu-satu — konsekuensinya, **kalau mengubah tabel, ubah di kedua file** agar label tetap sinkron.

---

## 📁 Struktur Repo

```
penugasan_Vision_heroes/
├── generate_markers.py           # Generate marker PNG ID 0-4
├── detect_markers.py             # Deteksi real-time dari webcam  (BELUM DIBUAT)
├── requirements.txt              # Dependencies
├── calibration/
│   └── camera_calibration.yml    # Matriks kamera + koefisien distorsi  (BELUM DIBUAT)
├── markers/                      # Output generate_markers.py
│   ├── marker_0_standby.png
│   ├── marker_1_ambil.png
│   ├── marker_2_lepas.png
│   ├── marker_3_putar_cw.png
│   ├── marker_4_putar_ccw.png
│   └── all_markers_sheet.png     # Semua marker dalam 1 lembar (opsional)
├── .gitignore
└── README.md
```

---

## ⚙️ Instalasi

**Prasyarat:** Python 3.9 atau lebih baru (proyek ini dikembangkan & diuji pada **Python 3.14 64-bit**).

### 1. Clone repo

```bash
git clone <URL-REPO-KAMU>
cd penugasan_Vision_heroes
```

### 2. Buat virtual environment

Selalu pakai venv — supaya versi OpenCV proyek ini tidak bentrok dengan proyek lain di laptopmu.

**Windows (PowerShell):**
```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Kalau muncul error *"running scripts is disabled on this system"*, jalankan sekali:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Kalau berhasil, prompt terminalmu akan diawali `(.venv)`.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Verifikasi

```bash
python -c "import cv2; print(cv2.__version__, hasattr(cv2, 'aruco'))"
```

Harus mencetak nomor versi dan `True`. Kalau `aruco` bernilai `False` atau `ImportError`, lihat [Troubleshooting](#-troubleshooting).

---

## 🚀 Cara Menjalankan

### `generate_markers.py`

Membuat file PNG marker untuk tiap ID, lalu **langsung menguji baca balik** tiap file yang dibuat.

```bash
python generate_markers.py
```

Output:

```
OpenCV 5.0.0 | dictionary DICT_4X4_50 (kapasitas 50 marker)
Menyimpan ke: ...\markers

  [OK   ] ID  0 - Standby    -> marker_0_standby.png (980x1107 px)
  [OK   ] ID  1 - Ambil      -> marker_1_ambil.png (980x1107 px)
  [OK   ] ID  2 - Lepas      -> marker_2_lepas.png (980x1107 px)
  [OK   ] ID  3 - Putar CW   -> marker_3_putar_cw.png (980x1107 px)
  [OK   ] ID  4 - Putar CCW  -> marker_4_putar_ccw.png (980x1107 px)

[SELESAI] 5 marker dibuat, semuanya lolos uji baca balik.
```

Status `[OK]` berarti marker itu sudah diverifikasi terbaca kembali oleh detector — kalau di sini sudah `GAGAL`, tidak usah lanjut ke webcam, ada yang salah di tahap generate.

**Opsi yang tersedia:**

| Opsi | Default | Fungsi |
|------|:-------:|--------|
| `--ids 0 1 2` | `0 1 2 3 4` | Pilih ID tertentu saja |
| `--size 1200` | `700` | Sisi marker dalam piksel (belum termasuk quiet zone) |
| `--margin 0.25` | `0.20` | Lebar quiet zone, rasio terhadap sisi marker |
| `--output folder` | `markers` | Folder tujuan |
| `--dict DICT_5X5_50` | `DICT_4X4_50` | Ganti dictionary ArUco |
| `--plain` | off | Tanpa label teks di bawah marker |
| `--sheet` | off | Buat juga 1 lembar berisi semua marker dalam grid |

Lihat semua opsi: `python generate_markers.py --help`

**Tips untuk demo video:** pakai `--sheet` untuk menghasilkan `all_markers_sheet.png`. Satu lembar itu berisi kelima marker, jadi requirement *"lebih dari satu marker dalam satu frame"* dan *"minimal 3 ID berbeda"* bisa dibuktikan cukup dengan satu kertas.

### `detect_markers.py`

> 🚧 **Belum dibuat.** Bagian ini akan diisi setelah script-nya selesai.

---

## 🖨️ Cara Print Marker

Ini penting untuk bonus pose estimation: perhitungan jarak mengasumsikan sisi **hitam** marker persis **10 cm**.

| Target DPI print | Pakai `--size` | Hasil sisi hitam |
|:---:|:---:|:---:|
| 150 DPI | `--size 591` | 10 cm |
| 200 DPI | `--size 787` | 10 cm |
| 300 DPI | `--size 1181` | 10 cm |

Atau lebih praktis: print di skala berapa pun, lalu **ukur pakai penggaris** dan sesuaikan angka ukuran marker di `detect_markers.py`. Yang diukur adalah **sisi kotak hitam terluar**, bukan termasuk margin putih dan bukan termasuk pita label.

**Kalau tidak punya printer:** tampilkan PNG-nya di layar HP/tablet dalam mode *fullscreen*, kecerahan tinggi. Deteksi akan tetap jalan. Tapi untuk pose estimation, ukur dulu sisi hitam di layar pakai penggaris dan sesuaikan angkanya — kalau tidak, angka jaraknya akan salah.

**Hal yang bikin deteksi gagal:**
- Marker ditempel di permukaan melengkung atau kertasnya kusut
- Kertas glossy + cahaya langsung → pantulan menutup pola
- Margin putih (*quiet zone*) dipotong habis waktu print
- Marker terlalu kecil / terlalu jauh dari kamera
- Motion blur karena kamera atau marker digerakkan terlalu cepat

---

## 🧠 Catatan Teknis (Wajib Dipahami)

Bagian ini yang paling sering bikin orang stuck. Baca sebelum mulai ngoding.

### 1. API ArUco OpenCV berubah — kebanyakan tutorial di internet sudah usang

Nama fungsi ArUco diganti di **OpenCV 4.7**, dan versi lamanya **dihapus total** di 4.9+. Jadi kalau kamu copy kode dari tutorial YouTube lama, kemungkinan besar kena `AttributeError: module 'cv2.aruco' has no attribute ...`

| Lama (OpenCV < 4.7) | Baru (OpenCV ≥ 4.7) |
|---|---|
| `cv2.aruco.Dictionary_get()` | `cv2.aruco.getPredefinedDictionary()` |
| `cv2.aruco.drawMarker()` | `cv2.aruco.generateImageMarker()` |
| `cv2.aruco.DetectorParameters_create()` | `cv2.aruco.DetectorParameters()` |
| `cv2.aruco.detectMarkers(img, dict, ...)` | `cv2.aruco.ArucoDetector(dict, params).detectMarkers(img)` |
| `cv2.aruco.estimatePoseSingleMarkers()` | `cv2.solvePnP()` dengan flag `SOLVEPNP_IPPE_SQUARE` |
| `cv2.aruco.drawAxis()` | `cv2.drawFrameAxes()` |

Script di repo ini memakai `hasattr()` untuk mendeteksi versi API yang tersedia dan memilih sendiri, jadi **tetap jalan di OpenCV lama maupun baru** — termasuk di laptop mentor yang mungkin versinya beda.

### 2. `opencv-python` vs `opencv-contrib-python`

Dulu modul `cv2.aruco` hanya ada di paket `-contrib`. **Sejak OpenCV 4.7, ArUco sudah pindah ke modul inti (`objdetect`)**, jadi paket `opencv-python` biasa pun sekarang sudah punya `cv2.aruco`. Repo ini tetap memakai `opencv-contrib-python` agar aman di versi lama.

> ❗ **Jangan install keduanya di satu environment.** Dua-duanya menyediakan modul `cv2` dan akan saling menimpa — gejalanya error import yang aneh dan susah dilacak. Kalau terlanjur: `pip uninstall opencv-python opencv-contrib-python`, lalu install ulang salah satu saja.

### 3. Quiet zone bukan hiasan

Detector mencari **kontur segi empat gelap yang tertutup**. Kalau marker mepet tepi gambar atau menempel objek gelap, konturnya tidak tertutup dan marker **tidak terdeteksi sama sekali**. Karena itu `generate_markers.py` otomatis menambah margin putih 20% dari sisi marker (rekomendasi minimum sebenarnya cuma 1 modul — kita lebihkan supaya aman).

### 4. Bingkai hitam marker (`border_bits`)

Kotak hitam tebal di pinggir marker justru bagian yang dicari algoritma deteksi. Nilainya standar `1` dan sebaiknya tidak diubah.

### 5. Label teks ditaruh di luar area marker

Label `ID 1 - Ambil` sengaja ditempel di pita terpisah di bawah marker, di luar quiet zone, supaya membantu identifikasi saat marker sudah diprint tanpa mengganggu deteksi. Pakai `--plain` kalau mau tanpa label.

---

## 📸 Screenshot / Demo

> _(Diisi setelah kode jalan — tempel screenshot atau GIF hasil deteksi di sini.)_

**Video demo YouTube:** _(diisi menyusul)_

---

## ⚠️ Keterbatasan

- **Kalibrasi kamera masih approximate.** File di `calibration/` adalah kalibrasi generik, bukan hasil kalibrasi presisi per-kamera. Akibatnya angka jarak dan orientasi hasil pose estimation **bisa meleset**, terutama di tepi frame dan pada kamera ber-distorsi tinggi (webcam murah, kamera wide-angle). Untuk akurasi sungguhan, lakukan kalibrasi checkerboard sendiri per unit kamera.
- **Akurasi pose bervariasi** tergantung kamera, resolusi, pencahayaan, dan sudut pandang. Marker yang dilihat hampir tegak lurus (*frontal*) rawan **ambiguitas rotasi** — orientasinya bisa "meloncat" bolak-balik antara dua solusi yang sama-sama valid secara matematis.
- **Akurasi jarak bergantung pada ukuran fisik marker yang diinput.** Kalau marker diprint tidak persis 10 cm tapi angka di kode tetap 10 cm, semua jarak akan salah secara proporsional.
- **Pencahayaan sangat berpengaruh.** Cahaya terlalu redup, pantulan pada kertas glossy, atau bayangan yang jatuh di separuh marker bisa menggagalkan deteksi.
- **Deteksi ini stateless per frame** — tidak ada tracking/filtering antar frame, jadi wajar kalau hasilnya sedikit berkedip (*flicker*).
- **Marker statis, bukan komunikasi antar robot.** Sesuai konteks tugas, ini murni localization.

---

## 🔧 Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| `ModuleNotFoundError: No module named 'cv2'` | venv belum aktif, atau `pip install` dijalankan di Python lain. Aktifkan venv lalu install ulang. |
| `AttributeError: module 'cv2.aruco' has no attribute 'Dictionary_get'` | Kamu memakai kode gaya lama di OpenCV baru. Lihat tabel di [Catatan Teknis](#1-api-aruco-opencv-berubah--kebanyakan-tutorial-di-internet-sudah-usang). |
| `hasattr(cv2, 'aruco')` bernilai `False` | Ada bentrok paket. Uninstall `opencv-python` dan `opencv-contrib-python`, lalu install `opencv-contrib-python` saja. |
| Marker terbuat tapi tidak terbaca kamera | Quiet zone terpotong, marker terlalu kecil/jauh, pantulan cahaya, atau motion blur. |
| Script `Activate.ps1` ditolak PowerShell | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

---

## 📊 Status Pengerjaan

- [x] Setup environment (venv + dependencies)
- [x] `generate_markers.py` — marker ID 0–4, lolos uji baca balik
- [ ] `detect_markers.py` — deteksi webcam real-time + label peran
- [ ] *(Bonus)* Kalibrasi kamera + pose estimation
- [ ] *(Bonus)* Axis 3D + info jarak/orientasi di layar
- [ ] Screenshot / GIF demo
- [ ] Video demo YouTube
