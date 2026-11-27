"""Modul Database & Transactional Tools untuk DesaWisata Guide."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
import os
from typing import Any, Dict, List, Literal, Optional, Tuple

from dotenv import load_dotenv
from langchain_core.tools import tool

from db.connection import get_db_cursor

NO_PAKET_MARKERS = {"", "none", "null", "tanpa paket", "tidak ada", "-"}
DEFAULT_REFERENCE_DATE = "2026-11-17"

SQL_HOMESTAY_KOSONG = """
SELECT h.kode, h.nama, h.kapasitas, h.jumlah_kamar, h.harga_per_malam, h.fasilitas, h.ramah_anak
FROM homestay h
WHERE h.kapasitas >= %(jumlah_tamu)s
  AND NOT EXISTS (
    SELECT 1 FROM booking b
    WHERE b.homestay_kode = h.kode
      AND b.status = 'booked'
      AND b.tgl_checkin  < %(checkout)s
      AND b.tgl_checkout > %(checkin)s
  )
ORDER BY h.harga_per_malam;
""".strip()

SQL_STATUS_BOOKING = """
SELECT b.kode, b.nama_tamu, h.nama AS homestay, b.tgl_checkin, b.tgl_checkout,
       b.jumlah_tamu, p.nama AS paket, b.status, b.total_harga
FROM booking b
JOIN homestay h ON h.kode = b.homestay_kode
LEFT JOIN paket_wisata p ON p.kode = b.paket_kode
WHERE b.kode = %(kode)s;
""".strip()

SQL_REKAP_BULANAN = """
SELECT status, COUNT(*) AS jumlah_booking, SUM(total_harga) AS total_rupiah
FROM booking
WHERE EXTRACT(YEAR FROM tgl_checkin) = %(tahun)s
  AND EXTRACT(MONTH FROM tgl_checkin) = %(bulan)s
GROUP BY status
ORDER BY status;
""".strip()


def _serialize_value(value: Any) -> Any:
    """Mengubah tipe tanggal, waktu, dan Decimal agar aman diserialisasi ke JSON."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, Decimal):
        return int(value) if value == int(value) else float(value)
    return value


def _serialize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Mengubah satu baris RealDictCursor menjadi dict Python standar."""
    return {key: _serialize_value(val) for key, val in dict(row).items()}


def _parse_date(value: str, field_name: str) -> date:
    """Mem-parsing tanggal format YYYY-MM-DD dan memunculkan pesan error yang jelas."""
    if not value or not isinstance(value, str):
        raise ValueError(f"Parameter '{field_name}' wajib diisi dengan format YYYY-MM-DD.")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(
            f"Format tanggal '{field_name}' tidak valid ('{value}'). Gunakan format YYYY-MM-DD."
        ) from exc


def _is_no_paket(paket: Optional[str]) -> bool:
    """Memeriksa apakah input paket menandakan tamu memesan tanpa paket wisata."""
    if paket is None:
        return True
    return paket.strip().lower() in NO_PAKET_MARKERS


def _get_reference_date() -> date:
    """Mengambil REFERENCE_DATE dari environment / .env (default 2026-11-17)."""
    load_dotenv()
    raw = os.getenv("REFERENCE_DATE", DEFAULT_REFERENCE_DATE).strip()
    return date.fromisoformat(raw)


def _lookup_entity(
    cur: Any,
    table_name: Literal["homestay", "paket_wisata"],
    columns: str,
    identifier: str,
    entity_label: str,
) -> Dict[str, Any]:
    """Mencari baris homestay atau paket_wisata berdasarkan kode atau nama secara parameterized."""
    cleaned = (identifier or "").strip()
    if not cleaned:
        raise ValueError(f"Nama atau kode {entity_label} tidak boleh kosong.")

    exact_sql = f"""
        SELECT {columns}
        FROM {table_name}
        WHERE UPPER(kode) = UPPER(%(q)s)
           OR LOWER(nama) = LOWER(%(q)s)
        LIMIT 1;
    """
    cur.execute(exact_sql, {"q": cleaned})
    row = cur.fetchone()
    if row:
        return dict(row)

    partial_sql = f"""
        SELECT {columns}
        FROM {table_name}
        WHERE nama ILIKE %(pattern)s
        ORDER BY kode;
    """
    cur.execute(partial_sql, {"pattern": f"%{cleaned}%"})
    matches = cur.fetchall()
    if len(matches) == 1:
        return dict(matches[0])
    if len(matches) > 1:
        names = ", ".join(m["nama"] for m in matches)
        raise ValueError(
            f"Input {entity_label} '{cleaned}' ambigu; cocok dengan: {names}."
        )
    raise ValueError(f"{entity_label.capitalize()} '{cleaned}' tidak ditemukan.")


def _resolve_homestay(cur: Any, identifier: str) -> Dict[str, Any]:
    """Mengambil detail homestay berdasarkan kode (HS01) atau nama."""
    return _lookup_entity(
        cur=cur,
        table_name="homestay",
        columns="kode, nama, kapasitas, jumlah_kamar, harga_per_malam, fasilitas, ramah_anak",
        identifier=identifier,
        entity_label="homestay",
    )


def _resolve_paket(cur: Any, identifier: str) -> Dict[str, Any]:
    """Mengambil detail paket_wisata berdasarkan kode (PK01) atau nama."""
    return _lookup_entity(
        cur=cur,
        table_name="paket_wisata",
        columns="kode, nama, harga_per_orang, durasi_jam, usia_min, jam_mulai, jam_selesai, luar_ruang",
        identifier=identifier,
        entity_label="paket wisata",
    )


def hitung_total_harga_murni(
    jumlah_malam: int,
    harga_per_malam: int,
    harga_per_orang: int = 0,
    jumlah_tamu: int = 0,
) -> int:
    """
    Fungsi murni untuk menghitung total harga penginapan dan paket wisata secara deterministik.

    Rumus: total_harga = (jumlah_malam * harga_per_malam) + (harga_per_orang * jumlah_tamu)
    """
    if jumlah_malam < 1:
        raise ValueError("jumlah_malam minimal 1 malam.")
    if jumlah_tamu < 0:
        raise ValueError("jumlah_tamu tidak boleh negatif.")
    if harga_per_malam < 0 or harga_per_orang < 0:
        raise ValueError("Tarif harga tidak boleh negatif.")
    return (jumlah_malam * harga_per_malam) + (harga_per_orang * jumlah_tamu)


def hitung_persen_pengembalian_dp(
    tgl_checkin: date,
    reference_date: Optional[date] = None,
) -> Tuple[int, int]:
    """
    Menghitung selisih hari dari reference_date ke tgl_checkin dan persentase pengembalian DP.

    Aturan:
      - >= 7 hari sebelum check-in -> 100%
      - 3–6 hari sebelum check-in  -> 50%
      - < 3 hari sebelum check-in  -> 0%
    """
    ref_date = reference_date or _get_reference_date()
    selisih_hari = (tgl_checkin - ref_date).days
    if selisih_hari >= 7:
        persen = 100
    elif 3 <= selisih_hari <= 6:
        persen = 50
    else:
        persen = 0
    return selisih_hari, persen


def get_paket_info(paket_kode_atau_nama: str) -> Optional[Dict[str, Any]]:
    """
    Helper untuk mengambil informasi paket wisata (khususnya jam_mulai, jam_selesai, luar_ruang)
    dari tabel paket_wisata untuk kebutuhan modul prakiraan cuaca.
    """
    if _is_no_paket(paket_kode_atau_nama):
        return None
    try:
        with get_db_cursor() as cur:
            row = _resolve_paket(cur, paket_kode_atau_nama)
            return _serialize_row(row)
    except ValueError:
        return None


def run_query_data(
    jenis_query: Literal["homestay_kosong", "status_booking", "rekap_bulanan"],
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    jumlah_tamu: Optional[int] = None,
    kode: Optional[str] = None,
    tahun: Optional[int] = None,
    bulan: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Menjalankan salah satu dari 3 parameterized query dari contoh_query.sql:
    - homestay_kosong (butuh checkin, checkout, jumlah_tamu)
    - status_booking (butuh kode)
    - rekap_bulanan (butuh tahun, bulan)
    """
    try:
        with get_db_cursor() as cur:
            if jenis_query == "homestay_kosong":
                ci_date = _parse_date(checkin or "", "checkin")
                co_date = _parse_date(checkout or "", "checkout")
                if co_date <= ci_date:
                    raise ValueError("Tanggal checkout harus lebih besar dari tanggal checkin.")
                if jumlah_tamu is None or int(jumlah_tamu) < 1:
                    raise ValueError("Parameter 'jumlah_tamu' wajib diisi minimal 1.")
                tamu_int = int(jumlah_tamu)

                cur.execute(
                    SQL_HOMESTAY_KOSONG,
                    {
                        "jumlah_tamu": tamu_int,
                        "checkin": ci_date,
                        "checkout": co_date,
                    },
                )
                rows = [_serialize_row(r) for r in cur.fetchall()]
                return {
                    "status": "success",
                    "jenis_query": jenis_query,
                    "parameter": {
                        "checkin": ci_date.isoformat(),
                        "checkout": co_date.isoformat(),
                        "jumlah_tamu": tamu_int,
                    },
                    "jumlah_hasil": len(rows),
                    "data": rows,
                }

            if jenis_query == "status_booking":
                kode_norm = (kode or "").strip().upper()
                if not kode_norm:
                    raise ValueError("Parameter 'kode' booking wajib diisi (contoh: BK-094).")
                cur.execute(SQL_STATUS_BOOKING, {"kode": kode_norm})
                row = cur.fetchone()
                if not row:
                    return {
                        "status": "not_found",
                        "jenis_query": jenis_query,
                        "parameter": {"kode": kode_norm},
                        "data": None,
                        "message": f"Booking dengan kode '{kode_norm}' tidak ditemukan.",
                    }
                return {
                    "status": "success",
                    "jenis_query": jenis_query,
                    "parameter": {"kode": kode_norm},
                    "data": _serialize_row(row),
                }

            if jenis_query == "rekap_bulanan":
                if tahun is None or bulan is None:
                    raise ValueError("Parameter 'tahun' dan 'bulan' wajib diisi.")
                tahun_int = int(tahun)
                bulan_int = int(bulan)
                if not (1 <= bulan_int <= 12):
                    raise ValueError("Parameter 'bulan' harus antara 1 sampai 12.")
                cur.execute(
                    SQL_REKAP_BULANAN,
                    {"tahun": tahun_int, "bulan": bulan_int},
                )
                rows = [_serialize_row(r) for r in cur.fetchall()]
                return {
                    "status": "success",
                    "jenis_query": jenis_query,
                    "parameter": {"tahun": tahun_int, "bulan": bulan_int},
                    "data": rows,
                }

            raise ValueError(
                "jenis_query harus salah satu dari: 'homestay_kosong', 'status_booking', 'rekap_bulanan'."
            )
    except ValueError as err:
        return {"status": "error", "jenis_query": jenis_query, "message": str(err)}


def run_hitung_harga(
    homestay: str,
    jumlah_tamu: int,
    jumlah_malam: Optional[int] = None,
    tgl_checkin: Optional[str] = None,
    tgl_checkout: Optional[str] = None,
    paket: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Menghitung rincian dan total harga menginap + paket wisata secara deterministik
    berdasarkan tarif di database PostgreSQL.
    """
    try:
        tamu_int = int(jumlah_tamu)
        if tamu_int < 1:
            raise ValueError("Parameter 'jumlah_tamu' minimal 1 orang.")

        malam_dari_tanggal: Optional[int] = None
        if tgl_checkin or tgl_checkout:
            ci_date = _parse_date(tgl_checkin or "", "tgl_checkin")
            co_date = _parse_date(tgl_checkout or "", "tgl_checkout")
            malam_dari_tanggal = (co_date - ci_date).days
            if malam_dari_tanggal < 1:
                raise ValueError("tgl_checkout harus minimal 1 hari setelah tgl_checkin.")

        if jumlah_malam is not None:
            malam_int = int(jumlah_malam)
            if malam_int < 1:
                raise ValueError("jumlah_malam minimal 1 malam.")
            if malam_dari_tanggal is not None and malam_dari_tanggal != malam_int:
                raise ValueError(
                    f"jumlah_malam ({malam_int}) tidak cocok dengan rentang tanggal ({malam_dari_tanggal} malam)."
                )
        elif malam_dari_tanggal is not None:
            malam_int = malam_dari_tanggal
        else:
            raise ValueError(
                "Sediakan 'jumlah_malam' atau pasangan 'tgl_checkin' dan 'tgl_checkout'."
            )

        with get_db_cursor() as cur:
            hs = _resolve_homestay(cur, homestay)
            pk = None if _is_no_paket(paket) else _resolve_paket(cur, paket or "")

        harga_per_malam = int(hs["harga_per_malam"])
        harga_per_orang = int(pk["harga_per_orang"]) if pk else 0
        biaya_homestay = malam_int * harga_per_malam
        biaya_paket = harga_per_orang * tamu_int
        total_harga = hitung_total_harga_murni(
            jumlah_malam=malam_int,
            harga_per_malam=harga_per_malam,
            harga_per_orang=harga_per_orang,
            jumlah_tamu=tamu_int,
        )

        result: Dict[str, Any] = {
            "status": "success",
            "homestay_kode": hs["kode"],
            "homestay_nama": hs["nama"],
            "kapasitas_homestay": int(hs["kapasitas"]),
            "harga_per_malam": harga_per_malam,
            "paket_kode": pk["kode"] if pk else None,
            "paket_nama": pk["nama"] if pk else None,
            "harga_per_orang": harga_per_orang,
            "jumlah_malam": malam_int,
            "jumlah_tamu": tamu_int,
            "biaya_homestay": biaya_homestay,
            "biaya_paket": biaya_paket,
            "total_harga": total_harga,
        }
        if tamu_int > int(hs["kapasitas"]):
            result["catatan"] = (
                f"Peringatan: jumlah_tamu ({tamu_int}) melebihi kapasitas {hs['nama']} ({hs['kapasitas']} orang)."
            )
        return result
    except ValueError as err:
        return {"status": "error", "message": str(err)}


def run_booking(
    mode: Literal["create", "cancel"],
    homestay: Optional[str] = None,
    nama_tamu: Optional[str] = None,
    tgl_checkin: Optional[str] = None,
    tgl_checkout: Optional[str] = None,
    jumlah_tamu: Optional[int] = None,
    paket: Optional[str] = None,
    kode: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Membuat booking baru (mode='create') atau membatalkan booking (mode='cancel')
    secara transaksional di PostgreSQL.
    """
    try:
        if mode == "create":
            return _create_booking(
                homestay=homestay,
                nama_tamu=nama_tamu,
                tgl_checkin=tgl_checkin,
                tgl_checkout=tgl_checkout,
                jumlah_tamu=jumlah_tamu,
                paket=paket,
            )
        if mode == "cancel":
            return _cancel_booking(kode=kode)
        raise ValueError("Parameter 'mode' harus 'create' atau 'cancel'.")
    except ValueError as err:
        return {"status": "error", "mode": mode, "message": str(err)}


def _create_booking(
    homestay: Optional[str],
    nama_tamu: Optional[str],
    tgl_checkin: Optional[str],
    tgl_checkout: Optional[str],
    jumlah_tamu: Optional[int],
    paket: Optional[str] = None,
) -> Dict[str, Any]:
    """Implementasi transaksional pembuatan booking baru berstatus 'booked'."""
    nama_clean = (nama_tamu or "").strip()
    if not nama_clean:
        raise ValueError("Parameter 'nama_tamu' wajib diisi.")
    if not homestay:
        raise ValueError("Parameter 'homestay' wajib diisi.")
    if jumlah_tamu is None or int(jumlah_tamu) < 1:
        raise ValueError("Parameter 'jumlah_tamu' wajib diisi minimal 1.")
    tamu_int = int(jumlah_tamu)

    ci_date = _parse_date(tgl_checkin or "", "tgl_checkin")
    co_date = _parse_date(tgl_checkout or "", "tgl_checkout")
    jumlah_malam = (co_date - ci_date).days
    if jumlah_malam < 1:
        raise ValueError("tgl_checkout harus minimal 1 hari setelah tgl_checkin.")

    with get_db_cursor(commit=True) as cur:
        hs = _resolve_homestay(cur, homestay)
        if tamu_int > int(hs["kapasitas"]):
            raise ValueError(
                f"Jumlah tamu ({tamu_int}) melebihi kapasitas maksimal {hs['nama']} ({hs['kapasitas']} orang)."
            )

        pk = None if _is_no_paket(paket) else _resolve_paket(cur, paket or "")

        # Cegah race condition saat pengecekan bentrok & pembuatan kode urut BK-xxx
        cur.execute("LOCK TABLE booking IN SHARE ROW EXCLUSIVE MODE;")

        cur.execute(
            """
            SELECT kode, tgl_checkin, tgl_checkout
            FROM booking
            WHERE homestay_kode = %(homestay_kode)s
              AND status = 'booked'
              AND tgl_checkin < %(tgl_checkout)s
              AND tgl_checkout > %(tgl_checkin)s
            ORDER BY tgl_checkin;
            """,
            {
                "homestay_kode": hs["kode"],
                "tgl_checkin": ci_date,
                "tgl_checkout": co_date,
            },
        )
        conflicts = cur.fetchall()
        if conflicts:
            conflict_list = ", ".join(
                f"{c['kode']} ({c['tgl_checkin']} s.d. {c['tgl_checkout']})"
                for c in conflicts
            )
            raise ValueError(
                f"{hs['nama']} ({hs['kode']}) sudah dibooking pada rentang tanggal tersebut: {conflict_list}."
            )

        cur.execute(
            """
            SELECT COALESCE(MAX(CAST(SUBSTRING(kode FROM 4) AS INT)), 0) AS max_num
            FROM booking
            WHERE kode ~ '^BK-[0-9]+$';
            """
        )
        max_row = cur.fetchone()
        next_num = int(max_row["max_num"]) + 1 if max_row else 101
        new_kode = f"BK-{next_num:03d}"

        harga_per_malam = int(hs["harga_per_malam"])
        harga_per_orang = int(pk["harga_per_orang"]) if pk else 0
        total_harga = hitung_total_harga_murni(
            jumlah_malam=jumlah_malam,
            harga_per_malam=harga_per_malam,
            harga_per_orang=harga_per_orang,
            jumlah_tamu=tamu_int,
        )
        dp_nominal = (total_harga * 30) // 100

        cur.execute(
            """
            INSERT INTO booking (
                kode, homestay_kode, paket_kode, nama_tamu,
                tgl_checkin, tgl_checkout, jumlah_tamu, status, total_harga
            )
            VALUES (
                %(kode)s, %(homestay_kode)s, %(paket_kode)s, %(nama_tamu)s,
                %(tgl_checkin)s, %(tgl_checkout)s, %(jumlah_tamu)s, 'booked', %(total_harga)s
            );
            """,
            {
                "kode": new_kode,
                "homestay_kode": hs["kode"],
                "paket_kode": pk["kode"] if pk else None,
                "nama_tamu": nama_clean,
                "tgl_checkin": ci_date,
                "tgl_checkout": co_date,
                "jumlah_tamu": tamu_int,
                "total_harga": total_harga,
            },
        )

    dp_formatted = f"Rp{dp_nominal:,}".replace(",", ".")
    return {
        "status": "booked",
        "mode": "create",
        "kode": new_kode,
        "nama_tamu": nama_clean,
        "homestay_kode": hs["kode"],
        "homestay_nama": hs["nama"],
        "paket_kode": pk["kode"] if pk else None,
        "paket_nama": pk["nama"] if pk else None,
        "tgl_checkin": ci_date.isoformat(),
        "tgl_checkout": co_date.isoformat(),
        "jumlah_malam": jumlah_malam,
        "jumlah_tamu": tamu_int,
        "total_harga": total_harga,
        "dp_persen": 30,
        "dp_nominal": dp_nominal,
        "batas_pembayaran_jam": 24,
        "pengingat": (
            f"Booking {new_kode} tersimpan dengan status 'booked'. "
            f"Harap melakukan pembayaran DP 30% ({dp_formatted}) maksimal dalam 24 jam."
        ),
    }


def _cancel_booking(kode: Optional[str]) -> Dict[str, Any]:
    """Implementasi transaksional pembatalan booking beserta perhitungan pengembalian DP."""
    kode_norm = (kode or "").strip().upper()
    if not kode_norm:
        raise ValueError("Parameter 'kode' booking wajib diisi untuk pembatalan.")

    ref_date = _get_reference_date()
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            """
            SELECT b.kode, b.homestay_kode, h.nama AS homestay_nama,
                   b.paket_kode, p.nama AS paket_nama, b.nama_tamu,
                   b.tgl_checkin, b.tgl_checkout, b.jumlah_tamu, b.status, b.total_harga
            FROM booking b
            JOIN homestay h ON h.kode = b.homestay_kode
            LEFT JOIN paket_wisata p ON p.kode = b.paket_kode
            WHERE b.kode = %(kode)s
            FOR UPDATE OF b;
            """,
            {"kode": kode_norm},
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Booking dengan kode '{kode_norm}' tidak ditemukan.")
        if row["status"] != "booked":
            raise ValueError(
                f"Booking '{kode_norm}' tidak dapat dibatalkan karena statusnya sudah '{row['status']}'."
            )

        selisih_hari, persen_dp = hitung_persen_pengembalian_dp(
            tgl_checkin=row["tgl_checkin"],
            reference_date=ref_date,
        )

        cur.execute(
            "UPDATE booking SET status = 'cancelled' WHERE kode = %(kode)s;",
            {"kode": kode_norm},
        )

    return {
        "status": "cancelled",
        "mode": "cancel",
        "kode": row["kode"],
        "nama_tamu": row["nama_tamu"],
        "homestay_kode": row["homestay_kode"],
        "homestay_nama": row["homestay_nama"],
        "paket_kode": row["paket_kode"],
        "paket_nama": row["paket_nama"],
        "tgl_checkin": row["tgl_checkin"].isoformat(),
        "tgl_checkout": row["tgl_checkout"].isoformat(),
        "jumlah_tamu": int(row["jumlah_tamu"]),
        "total_harga": int(row["total_harga"]),
        "reference_date": ref_date.isoformat(),
        "selisih_hari": selisih_hari,
        "persen_pengembalian_dp": persen_dp,
        "pesan": (
            f"Status booking {row['kode']} berubah menjadi 'cancelled'. "
            f"Pembatalan dilakukan {selisih_hari} hari sebelum check-in (referensi {ref_date.isoformat()}), "
            f"sehingga DP dikembalikan {persen_dp}%."
        ),
    }


@tool
def query_data(
    jenis_query: Literal["homestay_kosong", "status_booking", "rekap_bulanan"],
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    jumlah_tamu: Optional[int] = None,
    kode: Optional[str] = None,
    tahun: Optional[int] = None,
    bulan: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Menjalankan query read-only terparameter ke PostgreSQL Desa Wisata Lembah Asri.

    Pilihan jenis_query:
    - 'homestay_kosong': cek homestay tersedia (butuh checkin, checkout format YYYY-MM-DD, dan jumlah_tamu).
    - 'status_booking': cek detail satu booking (butuh kode, contoh 'BK-094').
    - 'rekap_bulanan': rekap jumlah & nominal booking per status dalam bulan check-in (butuh tahun dan bulan).
    """
    return run_query_data(
        jenis_query=jenis_query,
        checkin=checkin,
        checkout=checkout,
        jumlah_tamu=jumlah_tamu,
        kode=kode,
        tahun=tahun,
        bulan=bulan,
    )


@tool
def hitung_harga(
    homestay: str,
    jumlah_tamu: int,
    jumlah_malam: Optional[int] = None,
    tgl_checkin: Optional[str] = None,
    tgl_checkout: Optional[str] = None,
    paket: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Menghitung total harga menginap homestay dan paket wisata secara deterministik:
    total_harga = (jumlah_malam * harga_per_malam) + (harga_per_orang * jumlah_tamu).

    Args:
        homestay: Kode (mis. 'HS05') atau nama homestay (mis. 'Homestay Dahlia').
        jumlah_tamu: Jumlah tamu/peserta.
        jumlah_malam: Jumlah malam menginap (opsional jika tgl_checkin & tgl_checkout diisi).
        tgl_checkin: Tanggal check-in format YYYY-MM-DD (opsional jika jumlah_malam diisi).
        tgl_checkout: Tanggal check-out format YYYY-MM-DD (opsional jika jumlah_malam diisi).
        paket: Kode (mis. 'PK02') atau nama paket wisata (mis. 'Belajar Membatik'), kosongkan jika tanpa paket.
    """
    return run_hitung_harga(
        homestay=homestay,
        jumlah_tamu=jumlah_tamu,
        jumlah_malam=jumlah_malam,
        tgl_checkin=tgl_checkin,
        tgl_checkout=tgl_checkout,
        paket=paket,
    )


@tool
def booking(
    mode: Literal["create", "cancel"],
    homestay: Optional[str] = None,
    nama_tamu: Optional[str] = None,
    tgl_checkin: Optional[str] = None,
    tgl_checkout: Optional[str] = None,
    jumlah_tamu: Optional[int] = None,
    paket: Optional[str] = None,
    kode: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Membuat atau membatalkan booking homestay di PostgreSQL.

    Args:
        mode: 'create' untuk membuat booking baru, atau 'cancel' untuk membatalkan booking.
        homestay: Kode/nama homestay (wajib untuk mode='create').
        nama_tamu: Nama pemesan (wajib untuk mode='create').
        tgl_checkin: Tanggal check-in YYYY-MM-DD (wajib untuk mode='create').
        tgl_checkout: Tanggal check-out YYYY-MM-DD (wajib untuk mode='create').
        jumlah_tamu: Jumlah tamu (wajib untuk mode='create').
        paket: Kode/nama paket wisata (opsional untuk mode='create', None jika tanpa paket).
        kode: Kode booking seperti 'BK-101' (wajib untuk mode='cancel').
    """
    return run_booking(
        mode=mode,
        homestay=homestay,
        nama_tamu=nama_tamu,
        tgl_checkin=tgl_checkin,
        tgl_checkout=tgl_checkout,
        jumlah_tamu=jumlah_tamu,
        paket=paket,
        kode=kode,
    )


def get_db_tools() -> List[Any]:
    """Mengembalikan daftar LangChain tools untuk modul Database & Transactional."""
    return [query_data, hitung_harga, booking]
