"""Unit & integration tests untuk modul Database & Transactional Tools (DesaWisata Guide)."""

import csv
from datetime import date
from pathlib import Path
import re
import unittest

from app.db_tools import (
    booking,
    get_paket_info,
    hitung_harga,
    hitung_persen_pengembalian_dp,
    hitung_total_harga_murni,
    query_data,
)
from db.connection import check_db_health, get_db_cursor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_SQL_PATH = PROJECT_ROOT / "data" / "seed.sql"
QA_EVAL_PATH = PROJECT_ROOT / "eval" / "qa_eval.csv"


def _load_qa_eval() -> dict[str, dict[str, str]]:
    """Membaca eval/qa_eval.csv jika tersedia untuk memverifikasi kecocokan kunci evaluasi."""
    if not QA_EVAL_PATH.exists():
        return {}
    with QA_EVAL_PATH.open("r", encoding="utf-8", newline="") as f:
        return {row["id"]: row for row in csv.DictReader(f)}


def _parse_seed_bookings() -> list[dict]:
    """Mem-parsing baris INSERT INTO booking dari data/seed.sql jika file tersedia."""
    if not SEED_SQL_PATH.exists():
        return []
    content = SEED_SQL_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        r"INSERT INTO booking VALUES \('([^']+)', '([^']+)', (NULL|'[^']+'), "
        r"'([^']+)', '([^']+)', '([^']+)', (\d+), '([^']+)', (\d+)\);"
    )
    rows = []
    for match in pattern.findall(content):
        kode, homestay_kode, paket_raw, nama_tamu, ci, co, tamu, status, total = match
        rows.append(
            {
                "kode": kode,
                "homestay_kode": homestay_kode,
                "paket_kode": None if paket_raw == "NULL" else paket_raw.strip("'"),
                "nama_tamu": nama_tamu,
                "tgl_checkin": ci,
                "tgl_checkout": co,
                "jumlah_tamu": int(tamu),
                "status": status,
                "total_harga": int(total),
            }
        )
    return rows


class TestDatabaseAndTools(unittest.TestCase):
    """Pengujian koneksi database, query_data, hitung_harga (NFR-04), dan booking (Q06–Q12)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.qa_eval = _load_qa_eval()

    def _cleanup_bk101(self) -> None:
        with get_db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM booking WHERE kode = %s;", ("BK-101",))

    def test_01_db_health_and_seed_counts(self) -> None:
        """Memastikan koneksi PostgreSQL sehat dan data seed (8 homestay, 5 paket, 100 booking) ada."""
        self.assertTrue(check_db_health(), "Koneksi database PostgreSQL gagal atau tidak sehat.")
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM homestay;")
            self.assertEqual(cur.fetchone()["cnt"], 8)
            cur.execute("SELECT COUNT(*) AS cnt FROM paket_wisata;")
            self.assertEqual(cur.fetchone()["cnt"], 5)
            cur.execute("SELECT COUNT(*) AS cnt FROM booking;")
            self.assertEqual(cur.fetchone()["cnt"], 100)

    def test_02_nfr04_hitung_harga_matches_100_seed_rows(self) -> None:
        """NFR-04: hitung_harga harus cocok 100% (selisih Rp0) dengan seluruh 100 baris seed.sql."""
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT kode, homestay_kode, paket_kode, tgl_checkin, tgl_checkout,
                       jumlah_tamu, total_harga
                FROM booking
                WHERE kode <= 'BK-100'
                ORDER BY kode;
                """
            )
            db_rows = cur.fetchall()

        self.assertEqual(len(db_rows), 100, "Jumlah baris seed booking harus tepat 100.")

        seed_rows = _parse_seed_bookings()
        if seed_rows:
            self.assertEqual(len(seed_rows), 100)
            seed_map = {r["kode"]: r for r in seed_rows}
        else:
            seed_map = {}

        for row in db_rows:
            res = hitung_harga.invoke(
                {
                    "homestay": row["homestay_kode"],
                    "jumlah_tamu": int(row["jumlah_tamu"]),
                    "tgl_checkin": row["tgl_checkin"].isoformat(),
                    "tgl_checkout": row["tgl_checkout"].isoformat(),
                    "paket": row["paket_kode"],
                }
            )
            self.assertEqual(res["status"], "success", f"Gagal pada {row['kode']}: {res}")
            diff = abs(res["total_harga"] - int(row["total_harga"]))
            self.assertEqual(
                diff,
                0,
                f"Selisih harga pada {row['kode']}: hitung={res['total_harga']} vs db={row['total_harga']}",
            )
            if row["kode"] in seed_map:
                self.assertEqual(res["total_harga"], seed_map[row["kode"]]["total_harga"])

    def test_03_get_paket_info_helper(self) -> None:
        """Memastikan helper get_paket_info mengambil jam_mulai, jam_selesai, dan luar_ruang."""
        tubing_by_name = get_paket_info("Susur Sungai (Tubing)")
        self.assertIsNotNone(tubing_by_name)
        assert tubing_by_name is not None
        self.assertEqual(tubing_by_name["kode"], "PK05")
        self.assertEqual(tubing_by_name["jam_mulai"], "13:00")
        self.assertEqual(tubing_by_name["jam_selesai"], "15:00")
        self.assertTrue(tubing_by_name["luar_ruang"])

        batik_by_code = get_paket_info("PK02")
        self.assertIsNotNone(batik_by_code)
        assert batik_by_code is not None
        self.assertEqual(batik_by_code["jam_mulai"], "09:00")
        self.assertEqual(batik_by_code["jam_selesai"], "11:00")
        self.assertFalse(batik_by_code["luar_ruang"])

    def test_04_q06_homestay_kosong(self) -> None:
        """Skenario Q06: Homestay kosong 20–21 Des 2026 untuk 5 orang."""
        res = query_data.invoke(
            {
                "jenis_query": "homestay_kosong",
                "checkin": "2026-12-20",
                "checkout": "2026-12-21",
                "jumlah_tamu": 5,
            }
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["jumlah_hasil"], 3)
        names_and_prices = [(item["nama"], item["harga_per_malam"]) for item in res["data"]]
        self.assertEqual(
            names_and_prices,
            [
                ("Homestay Sedap Malam", 350000),
                ("Homestay Dahlia", 375000),
                ("Homestay Kenanga", 400000),
            ],
        )
        if "Q06" in self.qa_eval:
            for item in res["data"]:
                self.assertIn(item["nama"], self.qa_eval["Q06"]["jawaban_benar"])

    def test_05_q07_status_booking_bk094(self) -> None:
        """Skenario Q07: Detail status booking BK-094."""
        res = query_data.invoke({"jenis_query": "status_booking", "kode": "BK-094"})
        self.assertEqual(res["status"], "success")
        data = res["data"]
        self.assertEqual(data["kode"], "BK-094")
        self.assertEqual(data["status"], "booked")
        self.assertEqual(data["nama_tamu"], "Rina Lestari")
        self.assertEqual(data["homestay"], "Homestay Melati")
        self.assertEqual(data["tgl_checkin"], "2026-12-20")
        self.assertEqual(data["tgl_checkout"], "2026-12-21")
        self.assertEqual(data["jumlah_tamu"], 4)
        self.assertIsNone(data["paket"])
        self.assertEqual(data["total_harga"], 300000)

    def test_06_q08_rekap_bulanan_oktober_2026(self) -> None:
        """Skenario Q08: Rekap booking dengan check-in Oktober 2026."""
        res = query_data.invoke({"jenis_query": "rekap_bulanan", "tahun": 2026, "bulan": 10})
        self.assertEqual(res["status"], "success")
        by_status = {row["status"]: row for row in res["data"]}
        self.assertEqual(by_status["booked"]["jumlah_booking"], 4)
        self.assertEqual(by_status["booked"]["total_rupiah"], 3715000)
        self.assertEqual(by_status["cancelled"]["jumlah_booking"], 5)

    def test_07_q09_hitung_harga_dahlia_membatik(self) -> None:
        """Skenario Q09: 2 malam di Homestay Dahlia untuk 4 orang + Belajar Membatik."""
        res = hitung_harga.invoke(
            {
                "homestay": "Homestay Dahlia",
                "jumlah_tamu": 4,
                "jumlah_malam": 2,
                "paket": "Belajar Membatik",
            }
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["biaya_homestay"], 750000)
        self.assertEqual(res["biaya_paket"], 480000)
        self.assertEqual(res["total_harga"], 1230000)

    def test_08_dp_refund_rules_and_pure_math(self) -> None:
        """Memverifikasi fungsi murni perhitungan harga dan aturan pengembalian DP H-n."""
        self.assertEqual(hitung_total_harga_murni(2, 375000, 120000, 4), 1230000)
        ref = date(2026, 11, 17)
        self.assertEqual(hitung_persen_pengembalian_dp(date(2026, 11, 24), ref), (7, 100))
        self.assertEqual(hitung_persen_pengembalian_dp(date(2026, 11, 23), ref), (6, 50))
        self.assertEqual(hitung_persen_pengembalian_dp(date(2026, 11, 20), ref), (3, 50))
        self.assertEqual(hitung_persen_pengembalian_dp(date(2026, 11, 19), ref), (2, 0))

    def test_09_q11_and_q12_booking_create_cancel_and_cleanup(self) -> None:
        """Skenario Q11 (create BK-101) dan Q12 (cancel BK-101), lalu hapus BK-101 agar bersih 100 baris."""
        self._cleanup_bk101()
        try:
            # Validasi kapasitas melebihi batas (HS07 max 5 tamu)
            over_cap = booking.invoke(
                {
                    "mode": "create",
                    "homestay": "Homestay Sedap Malam",
                    "nama_tamu": "Andi",
                    "tgl_checkin": "2026-12-20",
                    "tgl_checkout": "2026-12-21",
                    "jumlah_tamu": 6,
                }
            )
            self.assertEqual(over_cap["status"], "error")

            # Validasi anti bentrok tanggal 'booked' (HS08 sudah dibooking BK-095 pada 20–22 Des 2026)
            conflict = booking.invoke(
                {
                    "mode": "create",
                    "homestay": "HS08",
                    "nama_tamu": "Andi",
                    "tgl_checkin": "2026-12-20",
                    "tgl_checkout": "2026-12-21",
                    "jumlah_tamu": 4,
                }
            )
            self.assertEqual(conflict["status"], "error")

            # Q11: Create BK-101 untuk Homestay Sedap Malam (paling murah dari Q06)
            created = booking.invoke(
                {
                    "mode": "create",
                    "homestay": "Homestay Sedap Malam",
                    "nama_tamu": "Andi",
                    "tgl_checkin": "2026-12-20",
                    "tgl_checkout": "2026-12-21",
                    "jumlah_tamu": 5,
                    "paket": None,
                }
            )
            self.assertEqual(created["status"], "booked")
            self.assertEqual(created["kode"], "BK-101")
            self.assertEqual(created["homestay_kode"], "HS07")
            self.assertEqual(created["homestay_nama"], "Homestay Sedap Malam")
            self.assertEqual(created["nama_tamu"], "Andi")
            self.assertEqual(created["jumlah_tamu"], 5)
            self.assertIsNone(created["paket_kode"])
            self.assertEqual(created["total_harga"], 350000)
            self.assertEqual(created["dp_persen"], 30)
            self.assertEqual(created["dp_nominal"], 105000)
            self.assertEqual(created["batas_pembayaran_jam"], 24)
            self.assertIn("30%", created["pengingat"])
            self.assertIn("24 jam", created["pengingat"])

            # Pastikan tidak bisa di-double-book setelah BK-101 tercipta
            double_book = booking.invoke(
                {
                    "mode": "create",
                    "homestay": "HS07",
                    "nama_tamu": "Budi",
                    "tgl_checkin": "2026-12-20",
                    "tgl_checkout": "2026-12-21",
                    "jumlah_tamu": 2,
                }
            )
            self.assertEqual(double_book["status"], "error")

            # Q12: Cancel BK-101 (2026-12-20 vs REFERENCE_DATE=2026-11-17 -> 33 hari -> DP 100%)
            cancelled = booking.invoke({"mode": "cancel", "kode": "BK-101"})
            self.assertEqual(cancelled["status"], "cancelled")
            self.assertEqual(cancelled["kode"], "BK-101")
            self.assertEqual(cancelled["selisih_hari"], 33)
            self.assertEqual(cancelled["persen_pengembalian_dp"], 100)

            # Pastikan cancel ulang ditolak
            cancel_again = booking.invoke({"mode": "cancel", "kode": "BK-101"})
            self.assertEqual(cancel_again["status"], "error")

            # Pastikan status di DB benar-benar 'cancelled'
            check_db = query_data.invoke({"jenis_query": "status_booking", "kode": "BK-101"})
            self.assertEqual(check_db["status"], "success")
            self.assertEqual(check_db["data"]["status"], "cancelled")
        finally:
            self._cleanup_bk101()

        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM booking;")
            self.assertEqual(cur.fetchone()["cnt"], 100, "Database harus kembali bersih tepat 100 baris.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
