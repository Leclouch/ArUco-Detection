#!/usr/bin/env python3
"""
generate_markers.py
===================
Men-generate gambar marker ArUco (default: dictionary DICT_4X4_50) untuk ID 0-4,
masing-masing disimpan sebagai file PNG di folder `markers/`.

Marker ini dipakai sebagai referensi visual statis di lapangan: robot membaca
marker lewat kamera untuk tahu posisi/objek referensi, tanpa perlu komunikasi
wireless antar robot.

Setelah menyimpan, script langsung mencoba MEMBACA BALIK tiap file yang dibuat
(round-trip test). Kalau marker tidak terbaca oleh detector-nya sendiri, hampir
pasti file itu juga tidak akan terbaca kamera.

Contoh pemakaian:
    python generate_markers.py                     # ID 0-4, ukuran default
    python generate_markers.py --size 1200         # lebih besar (buat print)
    python generate_markers.py --ids 0 1 2         # cuma ID tertentu
    python generate_markers.py --plain             # tanpa label teks
    python generate_markers.py --sheet             # + 1 lembar berisi semua marker
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Konfigurasi skema ID
# ---------------------------------------------------------------------------
# Tiap ID ArUco mewakili satu peran/state robot.
# CATATAN: tabel ini juga ada di detect_markers.py. Kalau diubah di sini,
# ubah juga di sana supaya label yang tampil di kamera tetap sinkron.
MARKER_ROLES: dict[int, str] = {
    0: "Standby",
    1: "Ambil",
    2: "Lepas",
    3: "Putar CW",
    4: "Putar CCW",
}

DEFAULT_DICT_NAME = "DICT_4X4_50"


# ---------------------------------------------------------------------------
# Lapisan kompatibilitas OpenCV
# ---------------------------------------------------------------------------
# Nama fungsi ArUco berubah di OpenCV 4.7:
#   OpenCV <4.7 : cv2.aruco.Dictionary_get() / cv2.aruco.drawMarker()
#   OpenCV >=4.7: cv2.aruco.getPredefinedDictionary() / generateImageMarker()
# Fungsi lama sudah DIHAPUS di OpenCV 4.9+ (dan tetap hilang di 5.x), jadi kode
# ini memilih otomatis supaya jalan di versi lama maupun baru.

def load_dictionary(dict_name: str):
    """Ambil objek dictionary ArUco dari namanya (string).

    Kenapa lewat getattr, bukan hardcode cv2.aruco.DICT_4X4_50?
    Supaya nama dictionary bisa diganti lewat argumen CLI (--dict) tanpa
    mengubah kode, sekaligus bisa kita validasi dengan pesan error yang jelas.
    """
    dict_id = getattr(cv2.aruco, dict_name, None)

    if not isinstance(dict_id, int):
        # Kumpulkan semua nama DICT_* yang tersedia untuk ditampilkan ke user.
        available = sorted(n for n in dir(cv2.aruco) if n.startswith("DICT_"))
        raise ValueError(
            f"Dictionary '{dict_name}' tidak dikenal di OpenCV {cv2.__version__}.\n"
            f"Pilihan yang tersedia: {', '.join(available)}"
        )

    if hasattr(cv2.aruco, "getPredefinedDictionary"):
        return cv2.aruco.getPredefinedDictionary(dict_id)      # OpenCV >= 4.7
    return cv2.aruco.Dictionary_get(dict_id)                   # OpenCV <  4.7


def dictionary_capacity(dictionary) -> int:
    """Jumlah marker unik yang muat di dictionary ini (DICT_4X4_50 -> 50).

    Dipakai untuk memvalidasi ID sebelum generate: minta ID 60 dari DICT_4X4_50
    akan bikin OpenCV melempar error mentah, lebih baik kita cegat duluan.
    """
    return int(dictionary.bytesList.shape[0])


def render_marker(dictionary, marker_id: int, side_px: int, border_bits: int = 1) -> np.ndarray:
    """Gambar satu marker jadi array grayscale berukuran side_px x side_px.

    border_bits = tebal bingkai hitam marker dalam satuan "modul" (kotak kecil).
    Standarnya 1 dan sebaiknya tidak diubah: bingkai hitam inilah yang dipakai
    detector untuk menemukan kandidat marker di gambar.
    """
    if hasattr(cv2.aruco, "generateImageMarker"):
        return cv2.aruco.generateImageMarker(dictionary, marker_id, side_px, None, border_bits)
    return cv2.aruco.drawMarker(dictionary, marker_id, side_px, None, border_bits)


def build_detector(dictionary):
    """Buat detector ArUco (dipakai untuk verifikasi round-trip di file ini).

    OpenCV >=4.7 memakai objek cv2.aruco.ArucoDetector; versi lama memakai
    fungsi lepas cv2.aruco.detectMarkers(). Kita bungkus keduanya jadi satu
    callable dengan bentuk hasil yang sama: (corners, ids, rejected).
    """
    if hasattr(cv2.aruco, "ArucoDetector"):
        params = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(dictionary, params)
        return detector.detectMarkers                          # OpenCV >= 4.7

    params = cv2.aruco.DetectorParameters_create()             # OpenCV <  4.7
    return lambda image: cv2.aruco.detectMarkers(image, dictionary, parameters=params)


# ---------------------------------------------------------------------------
# Pengolahan gambar marker
# ---------------------------------------------------------------------------

def add_quiet_zone(marker: np.ndarray, margin_ratio: float) -> np.ndarray:
    """Tambahkan margin putih ("quiet zone") di sekeliling marker.

    Ini BUKAN hiasan. Algoritma deteksi mencari kontur segi empat gelap; kalau
    marker mepet ke tepi gambar atau menempel objek gelap, konturnya tidak
    tertutup dan marker gagal terdeteksi. Rekomendasi umum: quiet zone minimal
    selebar 1 modul. Default 20% dari sisi marker sudah jauh di atas itu.
    """
    margin = max(1, int(round(marker.shape[0] * margin_ratio)))
    return cv2.copyMakeBorder(
        marker,
        margin, margin, margin, margin,
        cv2.BORDER_CONSTANT,
        value=255,  # 255 = putih pada citra grayscale
    )


def add_label(image: np.ndarray, text: str) -> np.ndarray:
    """Tempel pita putih berisi teks di bawah marker (mis. "ID 1 - Ambil").

    Teks sengaja ditaruh DI LUAR area marker + quiet zone, jadi tidak
    mengganggu deteksi, tapi sangat membantu waktu marker sudah diprint dan
    tercecer di meja lab.
    """
    width = image.shape[1]
    band_height = max(28, int(width * 0.13))

    # Pita putih polos sebagai alas teks.
    band = np.full((band_height, width), 255, dtype=np.uint8)

    font = cv2.FONT_HERSHEY_SIMPLEX
    # Skala font dihitung dari lebar gambar supaya proporsional di semua --size.
    scale = width / 520.0
    thickness = max(1, int(round(scale * 2)))

    (text_w, text_h), _ = cv2.getTextSize(text, font, scale, thickness)
    origin = ((width - text_w) // 2, (band_height + text_h) // 2)  # rata tengah
    cv2.putText(band, text, origin, font, scale, 0, thickness, cv2.LINE_AA)

    return np.vstack([image, band])


def verify_marker(image: np.ndarray, detect, expected_id: int) -> bool:
    """Round-trip test: baca balik gambar yang baru dibuat, cocokkan ID-nya.

    Kalau ini gagal berarti ada yang salah (dictionary beda, gambar kekecilan,
    quiet zone kurang) dan lebih baik ketahuan sekarang daripada waktu demo.
    """
    _corners, ids, _rejected = detect(image)
    if ids is None:
        return False
    return expected_id in ids.flatten().tolist()


# ---------------------------------------------------------------------------
# Lembar gabungan (opsional)
# ---------------------------------------------------------------------------

def build_contact_sheet(images: list[np.ndarray], columns: int = 3, gap_ratio: float = 0.08) -> np.ndarray:
    """Susun semua marker jadi satu gambar grid, untuk diprint sekali jalan.

    Berguna untuk menguji syarat "banyak marker dalam satu frame": cukup print
    satu lembar ini, arahkan kamera, semua ID langsung terbaca bersamaan.
    """
    cell_h = max(img.shape[0] for img in images)
    cell_w = max(img.shape[1] for img in images)
    gap = max(8, int(cell_w * gap_ratio))

    rows = (len(images) + columns - 1) // columns
    sheet_h = rows * cell_h + (rows + 1) * gap
    sheet_w = columns * cell_w + (columns + 1) * gap
    sheet = np.full((sheet_h, sheet_w), 255, dtype=np.uint8)

    for index, img in enumerate(images):
        r, c = divmod(index, columns)
        y = gap + r * (cell_h + gap)
        x = gap + c * (cell_w + gap)
        # Marker ditaruh rata tengah di dalam selnya kalau ukurannya beda.
        y += (cell_h - img.shape[0]) // 2
        x += (cell_w - img.shape[1]) // 2
        sheet[y:y + img.shape[0], x:x + img.shape[1]] = img

    return sheet


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate marker ArUco untuk skema ID robot (0=Standby .. 4=Putar CCW).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dict", dest="dict_name", default=DEFAULT_DICT_NAME,
                        help="Nama dictionary ArUco.")
    parser.add_argument("--ids", type=int, nargs="+", default=sorted(MARKER_ROLES),
                        help="Daftar ID yang ingin di-generate.")
    parser.add_argument("--size", type=int, default=700,
                        help="Sisi marker dalam piksel (belum termasuk quiet zone).")
    parser.add_argument("--margin", type=float, default=0.20,
                        help="Lebar quiet zone sebagai rasio terhadap sisi marker.")
    parser.add_argument("--output", type=Path, default=Path("markers"),
                        help="Folder tujuan file PNG.")
    parser.add_argument("--plain", action="store_true",
                        help="Jangan tempelkan label teks di bawah marker.")
    parser.add_argument("--sheet", action="store_true",
                        help="Buat juga satu file berisi semua marker dalam grid.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # --- Validasi argumen sebelum kerja apa pun -----------------------------
    if args.size < 50:
        print(f"[ERROR] --size {args.size} terlalu kecil. Pakai minimal 50 piksel.", file=sys.stderr)
        return 1
    if args.margin < 0:
        print(f"[ERROR] --margin tidak boleh negatif (diberi {args.margin}).", file=sys.stderr)
        return 1

    try:
        dictionary = load_dictionary(args.dict_name)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    capacity = dictionary_capacity(dictionary)
    invalid = [i for i in args.ids if i < 0 or i >= capacity]
    if invalid:
        print(f"[ERROR] ID {invalid} di luar jangkauan {args.dict_name} "
              f"(hanya menerima 0..{capacity - 1}).", file=sys.stderr)
        return 1

    try:
        args.output.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"[ERROR] Gagal membuat folder '{args.output}': {exc}", file=sys.stderr)
        return 1

    detect = build_detector(dictionary)

    print(f"OpenCV {cv2.__version__} | dictionary {args.dict_name} (kapasitas {capacity} marker)")
    print(f"Menyimpan ke: {args.output.resolve()}\n")

    generated: list[np.ndarray] = []
    failures = 0

    for marker_id in args.ids:
        role = MARKER_ROLES.get(marker_id, "(tanpa peran)")

        image = render_marker(dictionary, marker_id, args.size)
        image = add_quiet_zone(image, args.margin)

        # Verifikasi dilakukan SEBELUM label ditempel, supaya yang diuji benar-
        # benar marker + quiet zone-nya, bukan kebetulan tertolong elemen lain.
        ok = verify_marker(image, detect, marker_id)

        if not args.plain:
            image = add_label(image, f"ID {marker_id} - {role}")

        slug = role.lower().replace(" ", "_").replace("(", "").replace(")", "")
        filename = args.output / f"marker_{marker_id}_{slug}.png"
        if not cv2.imwrite(str(filename), image):
            print(f"[ERROR] Gagal menulis {filename}", file=sys.stderr)
            failures += 1
            continue

        generated.append(image)
        status = "OK   " if ok else "GAGAL"
        if not ok:
            failures += 1
        print(f"  [{status}] ID {marker_id:>2} - {role:<10} -> {filename.name} "
              f"({image.shape[1]}x{image.shape[0]} px)")

    # --- Lembar gabungan opsional ------------------------------------------
    if args.sheet and generated:
        sheet = build_contact_sheet(generated)
        sheet_path = args.output / "all_markers_sheet.png"
        if cv2.imwrite(str(sheet_path), sheet):
            print(f"\n  Lembar gabungan -> {sheet_path.name} "
                  f"({sheet.shape[1]}x{sheet.shape[0]} px)")

    print()
    if failures:
        print(f"[SELESAI DENGAN MASALAH] {failures} marker bermasalah.", file=sys.stderr)
        return 1

    print(f"[SELESAI] {len(generated)} marker dibuat, semuanya lolos uji baca balik.")
    print("Tips print: skala gambar sampai sisi HITAM marker = 10 cm agar cocok "
          "dengan asumsi ukuran di detect_markers.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
