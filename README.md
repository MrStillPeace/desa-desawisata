# DesaWisata Guide

AI Assistant Bot Telegram untuk **Desa Wisata Lembah Asri**.

> **Status Proyek Saat Ini**: Baru modul **Database & Transactional Tools** yang sudah diimplementasikan lengkap beserta konfigurasi PostgreSQL dan unit test-nya. Modul lain (RAG dokumen PDF, integrasi cuaca Open-Meteo, agent LangGraph, runner FastAPI/Telegram Bot, dan `Dockerfile`) masih berupa kerangka/stub atau belum diimplementasikan.

## Status Modul

| Modul | File Terkait | Status |
| --- | --- | --- |
| Database & Seed PostgreSQL | `docker-compose.yml`, `data/seed.sql` | Selesai |
| Koneksi Database | `db/__init__.py`, `db/connection.py` | Selesai |
| Transactional & DB Tools | `app/db_tools.py` | Selesai |
| Unit & Integration Tests (DB) | `tests/test_db_tools.py` | Selesai |
| RAG + Cuaca & Tools Lain | `app/rag_weather.py`, `app/weather.py`, `app/ingest.py`, `app/tools.py` | Belum selesai (stub/kosong) |
| Agent Graph, Bot & API | `app/graph.py`, `app/bot.py`, `app/main.py`, `Dockerfile` | Belum selesai (kerangka/kosong) |

## Fitur Modul Database & Transactional Tools

1. **Koneksi PostgreSQL (`db/connection.py`)**
   - `get_db_cursor(commit=False)`: context manager koneksi `psycopg2` dengan `RealDictCursor` menggunakan `DATABASE_URL` dari `.env` (otomatis `commit` saat `commit=True`, `rollback` saat read-only atau terjadi exception).
   - `check_db_health() -> bool`: pengecekan koneksi ke PostgreSQL melalui query `SELECT 1 AS ok;`.

2. **Helper & Tools (`app/db_tools.py`)**
   - `get_paket_info(paket_kode_atau_nama: str)`: helper parameterized untuk mengambil detail paket wisata (termasuk `jam_mulai`, `jam_selesai`, dan `luar_ruang`) guna kebutuhan modul prakiraan cuaca.
   - `query_data` (`@tool`) & `run_query_data`: menjalankan 3 parameterized query read-only:
     - `homestay_kosong`: mencari homestay tersedia berdasarkan `checkin`, `checkout`, dan `jumlah_tamu` (mengabaikan booking berstatus `'cancelled'`, diurutkan dari `harga_per_malam` termurah).
     - `status_booking`: melihat detail booking berdasarkan `kode` (mis. `BK-094`).
     - `rekap_bulanan`: rekap jumlah booking dan total rupiah per status berdasarkan `tahun` dan `bulan` check-in.
   - `hitung_harga` (`@tool`), `run_hitung_harga` & `hitung_total_harga_murni`: menghitung biaya secara deterministik dengan rumus:
     `total_harga = (jumlah_malam * harga_per_malam) + (harga_per_orang * jumlah_tamu)`
     Mendukung input `jumlah_malam` langsung maupun pasangan `tgl_checkin` + `tgl_checkout`, serta pencarian homestay/paket berdasarkan kode (`HS05`, `PK02`) atau nama.
   - `booking` (`@tool`), `run_booking` & `hitung_persen_pengembalian_dp`:
     - **Mode `create`**: validasi `jumlah_tamu <= kapasitas`, anti bentrok tanggal pada booking berstatus `'booked'`, penguncian tabel saat transaksi, pembuatan kode urut baru (`BK-101`, `BK-102`, ...), penyimpanan status `'booked'`, serta pengingat DP 30% maksimal dalam 24 jam.
     - **Mode `cancel`**: validasi booking berstatus `'booked'`, mengubah status menjadi `'cancelled'`, dan menghitung pengembalian DP terhadap `REFERENCE_DATE` (`2026-11-17`):
       - `>= 7` hari sebelum check-in: **100%**
       - `3–6` hari sebelum check-in: **50%**
       - `< 3` hari sebelum check-in: **0%**
   - `get_db_tools()`: mengembalikan daftar LangChain tools `[query_data, hitung_harga, booking]`.

## Struktur Direktori Saat Ini

```text
desawisata-guide/
├── app/
│   ├── __init__.py
│   ├── bot.py             # Kerangka bot Telegram (tim lain)
│   ├── db_tools.py        # Helper & LangChain tools database/transaksi
│   ├── graph.py           # Kerangka LangGraph (tim lain)
│   ├── ingest.py          # Kerangka ingestion PDF ke ChromaDB (tim lain)
│   ├── main.py            # Kerangka FastAPI runner (tim lain)
│   ├── rag_weather.py     # Kosong (tim lain)
│   ├── tools.py           # Stub tools awal (tim lain)
│   └── weather.py         # Kerangka Open-Meteo API (tim lain)
├── data/
│   └── seed.sql           # Skema & seed awal PostgreSQL (8 homestay, 5 paket, 100 booking)
├── db/
│   ├── __init__.py
│   └── connection.py      # Context manager psycopg2 & health check
├── docs/                  # Tempat dokumen PDF resmi desa wisata
├── eval/                  # Tempat dataset evaluasi qa_eval.csv
├── tests/
│   └── test_db_tools.py   # Pengujian koneksi DB, NFR-04, dan skenario Q06–Q12
├── .env.example
├── .gitignore
├── docker-compose.yml     # Service PostgreSQL 16 Alpine
├── Dockerfile             # Kosong (tim lain)
├── README.md
└── requirements.txt
```

## Cara Menjalankan & Menguji Modul Database

### 1. Siapkan Environment Variable

Salin `.env.example` menjadi `.env`:

```bash
cp .env.example .env
```

Nilai default untuk database lokal pada `.env`:

```env
POSTGRES_USER=app
POSTGRES_PASSWORD=app
POSTGRES_DB=desawisata
DATABASE_URL=postgresql://app:app@localhost:5432/desawisata
REFERENCE_DATE=2026-11-17
```

### 2. Instal Dependensi Python

Disarankan menggunakan virtual environment:

```bash
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
```

### 3. Jalankan PostgreSQL dengan Docker Compose

Pastikan Docker Desktop sudah aktif, lalu jalankan service `postgres` (container akan otomatis mengimpor `data/seed.sql` saat volume masih baru):

```bash
docker compose up -d postgres
```

### 4. Jalankan Unit & Integration Tests

```bash
python -m tests.test_db_tools
```

Pengujian pada `tests/test_db_tools.py` mencakup:
- Koneksi database sehat (`check_db_health()`) dan jumlah data awal (`8` homestay, `5` paket wisata, `100` booking).
- **NFR-04**: akurasi `hitung_harga` cocok 100% (selisih Rp0) dengan seluruh 100 baris booking di `data/seed.sql`.
- Helper `get_paket_info` untuk integrasi modul cuaca.
- Skenario evaluasi query dan transaksi (`Q06`, `Q07`, `Q08`, `Q09`, `Q11` pembuatan `BK-101`, dan `Q12` pembatalan `BK-101`) beserta pembersihan `BK-101` di akhir tes agar database kembali 100 baris.

## Contoh Pemakaian untuk Rekan Tim

```python
from db.connection import check_db_health, get_db_cursor
from app.db_tools import get_paket_info, get_db_tools

# Cek koneksi database
assert check_db_health() is True

# Ambil jam kegiatan & status luar_ruang untuk modul cuaca
paket = get_paket_info("Susur Sungai (Tubing)")
# -> {'kode': 'PK05', 'jam_mulai': '13:00', 'jam_selesai': '15:00', 'luar_ruang': True, ...}

# Bind tools DB ke LLM / LangGraph
db_tools = get_db_tools()  # [query_data, hitung_harga, booking]
```
