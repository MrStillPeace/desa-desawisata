from typing import Any, Dict, List, Optional
from langchain_core.tools import tool
from app.weather import get_weather_forecast


@tool
def cari_dokumen(query: str) -> str:
    """
    Mencari informasi dokumen/brosur resmi Desa Wisata Lembah Asri menggunakan RAG (ChromaDB).
    
    Args:
        query: Pertanyaan atau kata kunci pencarian seputar fasilitas, aturan, dan info desa wisata.
        
    Returns:
        Kutipan konteks relevan dari dokumen resmi.
    """
    # TODO: Diimplementasikan oleh anggota tim RAG (query ke ChromaDB collection)
    return f"[Stub cari_dokumen] Hasil pencarian untuk query: '{query}'"


@tool
def query_data(sql_query: str) -> str:
    """
    Menjalankan query SQL read-only ke database PostgreSQL Desa Wisata Lembah Asri.
    
    Args:
        sql_query: Pernyataan SQL SELECT untuk mengambil data paket, ketersediaan, atau riwayat.
        
    Returns:
        Hasil data dalam format string/JSON.
    """
    # TODO: Diimplementasikan oleh anggota tim Database/SQL (eksekusi via psycopg/engine)
    return f"[Stub query_data] Hasil query: '{sql_query}'"


@tool
def hitung_harga(paket: str, jumlah_orang: int, tanggal: Optional[str] = None) -> Dict[str, Any]:
    """
    Menghitung estimasi total harga kunjungan atau paket wisata berdasarkan jumlah peserta dan tanggal kunjungan.
    
    Args:
        paket: Nama atau kode paket wisata (contoh: 'family', 'outbound', 'camping').
        jumlah_orang: Jumlah peserta/pengunjung.
        tanggal: Tanggal rencana kunjungan (format YYYY-MM-DD, opsional).
        
    Returns:
        Rincian perhitungan harga (harga dasar, diskon jika ada, dan total biaya).
    """
    # TODO: Diimplementasikan oleh anggota tim Logic/Tools
    return {
        "status": "stub",
        "paket": paket,
        "jumlah_orang": jumlah_orang,
        "tanggal": tanggal,
        "estimasi_harga": 0,
        "catatan": "Logika kalkulasi harga akan diimplementasikan oleh tim."
    }


@tool
def cek_cuaca(hari: str = "hari_ini") -> Dict[str, Any]:
    """
    Mengecek perkiraan cuaca di kawasan Desa Wisata Lembah Asri (-6.83, 107.62) menggunakan Open-Meteo API.
    
    Args:
        hari: Pilihan hari perkiraan ('hari_ini', 'besok', atau 'mingguan').
        
    Returns:
        Informasi suhu, kelembaban, dan potensi hujan pada lokasi desa wisata.
    """
    # Menggunakan modul app.weather
    return get_weather_forecast(days=1 if hari == "hari_ini" else 3)


@tool
def booking(nama: str, paket: str, jumlah_orang: int, tanggal: str, kontak: str) -> Dict[str, Any]:
    """
    Melakukan reservasi / booking kunjungan wisata dan mencatatnya ke sistem database.
    
    Args:
        nama: Nama lengkap pemesan.
        paket: Nama paket wisata yang dipesan.
        jumlah_orang: Jumlah peserta kunjungan.
        tanggal: Tanggal kunjungan (format YYYY-MM-DD).
        kontak: Nomor WhatsApp atau email pemesan.
        
    Returns:
        Status reservasi beserta kode booking atau konfirmasi.
    """
    # TODO: Diimplementasikan oleh anggota tim Database/Booking
    return {
        "status": "stub",
        "booking_id": "STUB-BOOKING-001",
        "nama": nama,
        "paket": paket,
        "jumlah_orang": jumlah_orang,
        "tanggal": tanggal,
        "kontak": kontak,
        "pesan": "Booking stub berhasil dicatat. Logika persistence ke PostgreSQL akan diimplementasikan oleh tim."
    }


def get_all_tools() -> List[Any]:
    """Mengembalikan daftar semua tools yang tersedia untuk di-bind ke model LangGraph."""
    return [cari_dokumen, query_data, hitung_harga, cek_cuaca, booking]
