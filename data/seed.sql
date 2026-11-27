-- DesaWisata Guide: skema + data
-- AI Engineering Study Group - Big Data Lab
-- Cara pakai: psql -d desawisata -f seed.sql

DROP TABLE IF EXISTS booking, paket_wisata, homestay CASCADE;

CREATE TABLE homestay (
  kode            VARCHAR(4) PRIMARY KEY,
  nama            TEXT NOT NULL,
  kapasitas       INT  NOT NULL,          -- maksimal tamu per unit
  jumlah_kamar    INT  NOT NULL,
  harga_per_malam INT  NOT NULL,          -- Rupiah per unit (tarif satuan)
  fasilitas       TEXT NOT NULL,          -- dipisah koma
  ramah_anak      BOOLEAN NOT NULL
);

CREATE TABLE paket_wisata (
  kode            VARCHAR(4) PRIMARY KEY,
  nama            TEXT NOT NULL,
  harga_per_orang INT  NOT NULL,          -- Rupiah
  durasi_jam      INT  NOT NULL,
  usia_min        INT  NOT NULL,
  jam_mulai       TIME NOT NULL,          -- WIB
  jam_selesai     TIME NOT NULL,          -- WIB
  luar_ruang      BOOLEAN NOT NULL        -- TRUE = dipengaruhi cuaca
);

CREATE TABLE booking (
  kode          VARCHAR(6) PRIMARY KEY,                       -- BK-001
  homestay_kode VARCHAR(4) NOT NULL REFERENCES homestay(kode),
  paket_kode    VARCHAR(4) REFERENCES paket_wisata(kode),     -- NULL = hanya menginap
  nama_tamu     TEXT NOT NULL,
  tgl_checkin   DATE NOT NULL,
  tgl_checkout  DATE NOT NULL,
  jumlah_tamu   INT  NOT NULL,
  status        TEXT NOT NULL CHECK (status IN ('booked','cancelled')),
  total_harga   INT  NOT NULL                                 -- malam x harga homestay + harga paket x jumlah tamu
);

INSERT INTO homestay VALUES ('HS01', 'Homestay Melati', 4, 2, 300000, 'WiFi, kamar mandi dalam, sarapan', TRUE);
INSERT INTO homestay VALUES ('HS02', 'Homestay Kenanga', 6, 3, 400000, 'WiFi, sarapan, dapur bersama, area parkir', TRUE);
INSERT INTO homestay VALUES ('HS03', 'Homestay Anggrek', 2, 1, 250000, 'Sarapan, kipas angin', FALSE);
INSERT INTO homestay VALUES ('HS04', 'Homestay Teratai', 8, 4, 550000, 'WiFi, air panas, dapur bersama, halaman bermain, sarapan', TRUE);
INSERT INTO homestay VALUES ('HS05', 'Homestay Dahlia', 5, 3, 375000, 'WiFi, sarapan, view sawah', TRUE);
INSERT INTO homestay VALUES ('HS06', 'Homestay Mawar', 3, 2, 275000, 'Sarapan, air panas', FALSE);
INSERT INTO homestay VALUES ('HS07', 'Homestay Sedap Malam', 5, 2, 350000, 'Sarapan, dapur bersama, halaman bermain', TRUE);
INSERT INTO homestay VALUES ('HS08', 'Homestay Flamboyan', 6, 3, 450000, 'WiFi, air panas, sarapan, view bukit', TRUE);

INSERT INTO paket_wisata VALUES ('PK01', 'Jelajah Sawah', 150000, 3, 4, '07:00', '10:00', TRUE);
INSERT INTO paket_wisata VALUES ('PK02', 'Belajar Membatik', 120000, 2, 6, '09:00', '11:00', FALSE);
INSERT INTO paket_wisata VALUES ('PK03', 'Trekking Curug Lembah', 175000, 4, 10, '07:00', '11:00', TRUE);
INSERT INTO paket_wisata VALUES ('PK04', 'Kelas Masak Kuliner Desa', 130000, 3, 5, '10:00', '13:00', FALSE);
INSERT INTO paket_wisata VALUES ('PK05', 'Susur Sungai (Tubing)', 200000, 2, 12, '13:00', '15:00', TRUE);

INSERT INTO booking VALUES ('BK-001', 'HS08', 'PK04', 'Andi Lestari', '2026-01-03', '2026-01-04', 5, 'cancelled', 1100000);
INSERT INTO booking VALUES ('BK-002', 'HS08', 'PK05', 'Wulan Santoso', '2026-01-13', '2026-01-15', 6, 'booked', 2100000);
INSERT INTO booking VALUES ('BK-003', 'HS02', 'PK01', 'Dimas Utami', '2026-01-25', '2026-01-26', 4, 'booked', 1000000);
INSERT INTO booking VALUES ('BK-004', 'HS05', NULL, 'Laras Permana', '2026-02-05', '2026-02-08', 3, 'booked', 1125000);
INSERT INTO booking VALUES ('BK-005', 'HS04', NULL, 'Agus Santoso', '2026-02-06', '2026-02-08', 4, 'booked', 1100000);
INSERT INTO booking VALUES ('BK-006', 'HS05', 'PK04', 'Citra Nugroho', '2026-02-15', '2026-02-17', 3, 'booked', 1140000);
INSERT INTO booking VALUES ('BK-007', 'HS07', NULL, 'Anisa Hidayat', '2026-02-16', '2026-02-19', 2, 'booked', 1050000);
INSERT INTO booking VALUES ('BK-008', 'HS04', NULL, 'Agus Wijaya', '2026-02-18', '2026-02-21', 4, 'booked', 1650000);
INSERT INTO booking VALUES ('BK-009', 'HS03', NULL, 'Agus Kusuma', '2026-02-27', '2026-03-01', 2, 'booked', 500000);
INSERT INTO booking VALUES ('BK-010', 'HS04', 'PK04', 'Citra Gunawan', '2026-03-02', '2026-03-04', 4, 'booked', 1620000);
INSERT INTO booking VALUES ('BK-011', 'HS04', NULL, 'Dimas Utami', '2026-03-13', '2026-03-14', 2, 'booked', 550000);
INSERT INTO booking VALUES ('BK-012', 'HS08', NULL, 'Wulan Siregar', '2026-03-13', '2026-03-16', 5, 'booked', 1350000);
INSERT INTO booking VALUES ('BK-013', 'HS08', 'PK04', 'Reza Permana', '2026-03-17', '2026-03-18', 3, 'cancelled', 840000);
INSERT INTO booking VALUES ('BK-014', 'HS04', 'PK01', 'Agus Siregar', '2026-03-19', '2026-03-21', 8, 'cancelled', 2300000);
INSERT INTO booking VALUES ('BK-015', 'HS01', 'PK02', 'Dimas Hidayat', '2026-04-06', '2026-04-07', 2, 'booked', 540000);
INSERT INTO booking VALUES ('BK-016', 'HS01', 'PK01', 'Agus Nugroho', '2026-04-07', '2026-04-09', 3, 'booked', 1050000);
INSERT INTO booking VALUES ('BK-017', 'HS04', NULL, 'Citra Siregar', '2026-04-08', '2026-04-10', 2, 'booked', 1100000);
INSERT INTO booking VALUES ('BK-018', 'HS04', 'PK04', 'Nadia Setiawan', '2026-04-16', '2026-04-18', 3, 'cancelled', 1490000);
INSERT INTO booking VALUES ('BK-019', 'HS04', 'PK03', 'Yoga Hidayat', '2026-04-20', '2026-04-21', 2, 'booked', 900000);
INSERT INTO booking VALUES ('BK-020', 'HS06', 'PK01', 'Laras Utami', '2026-04-24', '2026-04-25', 3, 'booked', 725000);
INSERT INTO booking VALUES ('BK-021', 'HS04', 'PK02', 'Rina Saputra', '2026-04-28', '2026-04-29', 6, 'booked', 1270000);
INSERT INTO booking VALUES ('BK-022', 'HS06', 'PK01', 'Nadia Nugroho', '2026-05-02', '2026-05-03', 2, 'booked', 575000);
INSERT INTO booking VALUES ('BK-023', 'HS02', NULL, 'Bayu Gunawan', '2026-05-04', '2026-05-05', 3, 'cancelled', 400000);
INSERT INTO booking VALUES ('BK-024', 'HS07', NULL, 'Galih Nugroho', '2026-05-06', '2026-05-07', 2, 'booked', 350000);
INSERT INTO booking VALUES ('BK-025', 'HS01', 'PK01', 'Intan Utami', '2026-05-09', '2026-05-10', 3, 'booked', 750000);
INSERT INTO booking VALUES ('BK-026', 'HS04', 'PK02', 'Wulan Utami', '2026-05-09', '2026-05-11', 4, 'booked', 1580000);
INSERT INTO booking VALUES ('BK-027', 'HS01', NULL, 'Fajar Lestari', '2026-05-14', '2026-05-16', 4, 'booked', 600000);
INSERT INTO booking VALUES ('BK-028', 'HS04', 'PK03', 'Fajar Setiawan', '2026-05-17', '2026-05-18', 4, 'booked', 1250000);
INSERT INTO booking VALUES ('BK-029', 'HS04', 'PK04', 'Reza Nugroho', '2026-05-19', '2026-05-21', 3, 'booked', 1490000);
INSERT INTO booking VALUES ('BK-030', 'HS01', 'PK03', 'Rizky Gunawan', '2026-05-23', '2026-05-25', 4, 'booked', 1300000);
INSERT INTO booking VALUES ('BK-031', 'HS02', NULL, 'Yoga Permana', '2026-05-27', '2026-05-30', 4, 'cancelled', 1200000);
INSERT INTO booking VALUES ('BK-032', 'HS05', 'PK05', 'Dewi Rahmawati', '2026-06-04', '2026-06-07', 3, 'booked', 1725000);
INSERT INTO booking VALUES ('BK-033', 'HS07', 'PK02', 'Fajar Lestari', '2026-06-04', '2026-06-05', 2, 'booked', 590000);
INSERT INTO booking VALUES ('BK-034', 'HS04', 'PK04', 'Fitri Santoso', '2026-06-06', '2026-06-09', 3, 'booked', 2040000);
INSERT INTO booking VALUES ('BK-035', 'HS01', 'PK03', 'Intan Siregar', '2026-06-08', '2026-06-11', 4, 'booked', 1600000);
INSERT INTO booking VALUES ('BK-036', 'HS05', NULL, 'Budi Pratama', '2026-06-17', '2026-06-18', 5, 'booked', 375000);
INSERT INTO booking VALUES ('BK-037', 'HS08', 'PK04', 'Wulan Pratama', '2026-06-18', '2026-06-20', 4, 'booked', 1420000);
INSERT INTO booking VALUES ('BK-038', 'HS03', 'PK05', 'Anisa Santoso', '2026-06-19', '2026-06-20', 2, 'booked', 650000);
INSERT INTO booking VALUES ('BK-039', 'HS07', 'PK03', 'Intan Hidayat', '2026-06-22', '2026-06-24', 2, 'booked', 1050000);
INSERT INTO booking VALUES ('BK-040', 'HS01', 'PK01', 'Arif Hidayat', '2026-07-03', '2026-07-04', 3, 'booked', 750000);
INSERT INTO booking VALUES ('BK-041', 'HS08', 'PK01', 'Reza Utami', '2026-07-04', '2026-07-05', 5, 'booked', 1200000);
INSERT INTO booking VALUES ('BK-042', 'HS01', NULL, 'Arif Siregar', '2026-07-10', '2026-07-12', 3, 'cancelled', 600000);
INSERT INTO booking VALUES ('BK-043', 'HS04', 'PK05', 'Maya Lestari', '2026-07-10', '2026-07-12', 4, 'booked', 1900000);
INSERT INTO booking VALUES ('BK-044', 'HS08', 'PK05', 'Galih Utami', '2026-07-10', '2026-07-12', 5, 'booked', 1900000);
INSERT INTO booking VALUES ('BK-045', 'HS02', 'PK03', 'Laras Gunawan', '2026-07-11', '2026-07-12', 4, 'booked', 1100000);
INSERT INTO booking VALUES ('BK-046', 'HS07', NULL, 'Sari Siregar', '2026-07-12', '2026-07-14', 4, 'cancelled', 700000);
INSERT INTO booking VALUES ('BK-047', 'HS08', NULL, 'Reza Kusuma', '2026-07-15', '2026-07-16', 6, 'cancelled', 450000);
INSERT INTO booking VALUES ('BK-048', 'HS06', 'PK02', 'Yoga Rahmawati', '2026-07-23', '2026-07-24', 2, 'booked', 515000);
INSERT INTO booking VALUES ('BK-049', 'HS04', 'PK01', 'Citra Utami', '2026-07-27', '2026-07-30', 6, 'booked', 2550000);
INSERT INTO booking VALUES ('BK-050', 'HS05', NULL, 'Arif Pratama', '2026-07-28', '2026-07-29', 4, 'booked', 375000);
INSERT INTO booking VALUES ('BK-051', 'HS07', 'PK03', 'Bayu Siregar', '2026-08-02', '2026-08-03', 4, 'booked', 1050000);
INSERT INTO booking VALUES ('BK-052', 'HS05', NULL, 'Agus Utami', '2026-08-04', '2026-08-06', 3, 'booked', 750000);
INSERT INTO booking VALUES ('BK-053', 'HS07', 'PK02', 'Galih Pratama', '2026-08-08', '2026-08-09', 5, 'booked', 950000);
INSERT INTO booking VALUES ('BK-054', 'HS03', 'PK02', 'Budi Setiawan', '2026-08-13', '2026-08-16', 2, 'booked', 990000);
INSERT INTO booking VALUES ('BK-055', 'HS04', 'PK04', 'Eko Rahmawati', '2026-08-14', '2026-08-16', 6, 'cancelled', 1880000);
INSERT INTO booking VALUES ('BK-056', 'HS04', 'PK01', 'Maya Wijaya', '2026-08-17', '2026-08-18', 8, 'booked', 1750000);
INSERT INTO booking VALUES ('BK-057', 'HS05', 'PK05', 'Agus Nugroho', '2026-08-17', '2026-08-19', 3, 'booked', 1350000);
INSERT INTO booking VALUES ('BK-058', 'HS01', 'PK02', 'Putri Permana', '2026-08-22', '2026-08-24', 4, 'booked', 1080000);
INSERT INTO booking VALUES ('BK-059', 'HS07', NULL, 'Agus Kusuma', '2026-08-22', '2026-08-25', 2, 'cancelled', 1050000);
INSERT INTO booking VALUES ('BK-060', 'HS05', 'PK03', 'Fajar Permana', '2026-08-26', '2026-08-27', 5, 'booked', 1250000);
INSERT INTO booking VALUES ('BK-061', 'HS04', 'PK03', 'Tania Santoso', '2026-08-27', '2026-08-28', 2, 'booked', 900000);
INSERT INTO booking VALUES ('BK-062', 'HS04', 'PK03', 'Fajar Nugroho', '2026-08-28', '2026-08-29', 6, 'cancelled', 1600000);
INSERT INTO booking VALUES ('BK-063', 'HS07', NULL, 'Anisa Kusuma', '2026-09-01', '2026-09-04', 5, 'booked', 1050000);
INSERT INTO booking VALUES ('BK-064', 'HS02', 'PK05', 'Eko Gunawan', '2026-09-11', '2026-09-13', 4, 'booked', 1600000);
INSERT INTO booking VALUES ('BK-065', 'HS02', NULL, 'Eko Nugroho', '2026-09-14', '2026-09-15', 3, 'booked', 400000);
INSERT INTO booking VALUES ('BK-066', 'HS08', 'PK02', 'Nadia Lestari', '2026-09-16', '2026-09-18', 2, 'booked', 1140000);
INSERT INTO booking VALUES ('BK-067', 'HS04', 'PK05', 'Arif Rahmawati', '2026-09-17', '2026-09-18', 4, 'booked', 1350000);
INSERT INTO booking VALUES ('BK-068', 'HS07', 'PK04', 'Arif Wijaya', '2026-09-19', '2026-09-22', 3, 'cancelled', 1440000);
INSERT INTO booking VALUES ('BK-069', 'HS04', 'PK03', 'Putri Kusuma', '2026-09-22', '2026-09-23', 6, 'booked', 1600000);
INSERT INTO booking VALUES ('BK-070', 'HS07', 'PK02', 'Hendra Rahmawati', '2026-10-01', '2026-10-02', 3, 'cancelled', 710000);
INSERT INTO booking VALUES ('BK-071', 'HS07', 'PK03', 'Rizky Wijaya', '2026-10-04', '2026-10-05', 5, 'cancelled', 1225000);
INSERT INTO booking VALUES ('BK-072', 'HS08', 'PK02', 'Citra Permana', '2026-10-09', '2026-10-10', 2, 'booked', 690000);
INSERT INTO booking VALUES ('BK-073', 'HS06', 'PK01', 'Sari Kusuma', '2026-10-10', '2026-10-11', 3, 'cancelled', 725000);
INSERT INTO booking VALUES ('BK-074', 'HS04', NULL, 'Arif Rahmawati', '2026-10-15', '2026-10-17', 3, 'booked', 1100000);
INSERT INTO booking VALUES ('BK-075', 'HS03', 'PK03', 'Rina Gunawan', '2026-10-21', '2026-10-23', 2, 'booked', 850000);
INSERT INTO booking VALUES ('BK-076', 'HS01', 'PK02', 'Galih Kusuma', '2026-10-23', '2026-10-24', 4, 'cancelled', 780000);
INSERT INTO booking VALUES ('BK-077', 'HS02', 'PK05', 'Hendra Pratama', '2026-10-24', '2026-10-26', 2, 'cancelled', 1200000);
INSERT INTO booking VALUES ('BK-078', 'HS05', 'PK03', 'Tania Gunawan', '2026-10-27', '2026-10-28', 4, 'booked', 1075000);
INSERT INTO booking VALUES ('BK-079', 'HS07', 'PK02', 'Rizky Gunawan', '2026-11-02', '2026-11-03', 2, 'booked', 590000);
INSERT INTO booking VALUES ('BK-080', 'HS01', 'PK03', 'Reza Hidayat', '2026-11-04', '2026-11-05', 2, 'booked', 650000);
INSERT INTO booking VALUES ('BK-081', 'HS08', NULL, 'Nadia Hidayat', '2026-11-04', '2026-11-05', 4, 'booked', 450000);
INSERT INTO booking VALUES ('BK-082', 'HS04', 'PK02', 'Fitri Utami', '2026-11-13', '2026-11-14', 6, 'booked', 1270000);
INSERT INTO booking VALUES ('BK-083', 'HS06', 'PK02', 'Maya Utami', '2026-11-13', '2026-11-14', 2, 'booked', 515000);
INSERT INTO booking VALUES ('BK-084', 'HS02', NULL, 'Agus Setiawan', '2026-11-14', '2026-11-15', 5, 'cancelled', 400000);
INSERT INTO booking VALUES ('BK-085', 'HS08', 'PK05', 'Dewi Nugroho', '2026-11-20', '2026-11-21', 4, 'booked', 1250000);
INSERT INTO booking VALUES ('BK-086', 'HS08', 'PK04', 'Tania Siregar', '2026-11-23', '2026-11-24', 5, 'booked', 1100000);
INSERT INTO booking VALUES ('BK-087', 'HS02', 'PK05', 'Agus Saputra', '2026-12-01', '2026-12-02', 6, 'booked', 1600000);
INSERT INTO booking VALUES ('BK-088', 'HS07', NULL, 'Citra Siregar', '2026-12-04', '2026-12-05', 5, 'booked', 350000);
INSERT INTO booking VALUES ('BK-089', 'HS04', 'PK02', 'Putri Setiawan', '2026-12-05', '2026-12-06', 8, 'booked', 1510000);
INSERT INTO booking VALUES ('BK-090', 'HS04', 'PK05', 'Budi Nugroho', '2026-12-06', '2026-12-07', 2, 'booked', 950000);
INSERT INTO booking VALUES ('BK-091', 'HS02', 'PK02', 'Andi Setiawan', '2026-12-14', '2026-12-16', 3, 'booked', 1160000);
INSERT INTO booking VALUES ('BK-092', 'HS01', 'PK02', 'Reza Saputra', '2026-12-19', '2026-12-20', 2, 'booked', 540000);
INSERT INTO booking VALUES ('BK-093', 'HS04', 'PK01', 'Arif Pratama', '2026-12-19', '2026-12-22', 7, 'booked', 2700000);
INSERT INTO booking VALUES ('BK-094', 'HS01', NULL, 'Rina Lestari', '2026-12-20', '2026-12-21', 4, 'booked', 300000);
INSERT INTO booking VALUES ('BK-095', 'HS08', 'PK02', 'Reza Utami', '2026-12-20', '2026-12-22', 5, 'booked', 1500000);
INSERT INTO booking VALUES ('BK-096', 'HS06', 'PK02', 'Maya Lestari', '2026-12-22', '2026-12-23', 2, 'cancelled', 515000);
INSERT INTO booking VALUES ('BK-097', 'HS02', 'PK04', 'Hendra Wijaya', '2026-12-24', '2026-12-26', 6, 'booked', 1580000);
INSERT INTO booking VALUES ('BK-098', 'HS05', 'PK04', 'Fitri Santoso', '2026-12-27', '2026-12-29', 2, 'booked', 1010000);
INSERT INTO booking VALUES ('BK-099', 'HS08', 'PK01', 'Putri Permana', '2026-12-27', '2026-12-28', 5, 'booked', 1200000);
INSERT INTO booking VALUES ('BK-100', 'HS08', NULL, 'Rina Nugroho', '2026-12-28', '2026-12-30', 4, 'booked', 900000);
