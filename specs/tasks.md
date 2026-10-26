# SPECIFICATION: Implementation Tasks & Verification Checklist

**Project:** E-Commerce Customer Segmentation & RFM Analytics Dashboard  
**Status:** Completed & Verified (100% Pass)  
**Version:** 2.0.0  
**North Star Reference:** `PROJECT_CONTEXT.md`

---

## 1. Daftar Tugas Implementasi

### Kelompok 100: Baseline & Perbaikan Jalur Uji
- [x] **TASK-101:** Audit menyeluruh proyek dan penyusunan `laporan_evaluasi_dan_audit_proyek.md`.
- [x] **TASK-102:** Penyusunan dokumen rencana aksi `rencana_perbaikan_dashboard.md`.
- [x] **TASK-103:** Perbaiki bug path relatif pada `tests/test_rfm_analysis.py` baris 137.
- [x] **TASK-104:** Perbarui dan rapikan file `requirements.txt` (tambahkan Plotly & Scipy).

### Kelompok 200: Pembangunan Paket Spesifikasi (`specs/`)
- [x] **TASK-201:** Buat dokumen spesifikasi kebutuhan fungsional `specs/requirements.md`.
- [x] **TASK-202:** Buat dokumen arsitektur dan desain antarmuka `specs/design.md`.
- [x] **TASK-203:** Buat dokumen batas ruang lingkup dan wawancara `specs/steering.md`.
- [x] **TASK-204:** Buat pelacak tugas eksekusi `specs/tasks.md`.

### Kelompok 300: Fondasi Gaya UI/UX & Tema
- [x] **TASK-301:** Buat file `.streamlit/config.toml` dengan palet Slate Dark Theme.
- [x] **TASK-302:** Buat file `dashboard/style.css` (Glassmorphism, KPI Ribbon, Badge, Expander styling).

### Kelompok 400: Refactoring Visualisasi & Dashboard (`dashboard/dashboard.py`)
- [x] **TASK-401:** Buat helper `fmt_id()` untuk format angka standar Indonesia.
- [x] **TASK-402:** Buat helper `apply_plot_theme()` untuk keseragaman figur Plotly berlatar transparan.
- [x] **TASK-403:** Bangun ulang Executive KPI Ribbon dengan kontainer kartu elegan.
- [x] **TASK-404:** Migrasi Seksi 1 (Kategori Produk) ke Plotly Horizontal Bar.
- [x] **TASK-405:** Migrasi Seksi 2 (Kinerja Penjual) ke Plotly Bar (ID terpotong 8 karakter) + Scatterplot regresi dengan nilai Spearman $\rho$.
- [x] **TASK-406:** Migrasi Seksi 3 (Metode Pembayaran) ke Plotly Donut & Bar Cicilan.
- [x] **TASK-407:** Migrasi Seksi 4 (Kepuasan Pelanggan) ke Plotly Diverging/Horizontal Bar.
- [x] **TASK-408:** Migrasi Seksi 5 (Tren Penjualan Bulanan) ke Plotly Dual-Axis Line Subplot.
- [x] **TASK-409:** Migrasi Seksi 6 (Segmentasi RFM) ke Plotly Distribution Bar, Profile Bar, dan Tabel Aksi Bisnis terformat.
- [x] **TASK-410:** Tambahkan fitur interaktif *RFM Segment Explorer & Customer Lookup* dari `rfm_data.csv`.

### Kelompok 500: Pengujian Otomatis & Keandalan Sistem
- [x] **TASK-501:** Bangun modul pengujian skenario antarmuka `tests/test_dashboard_scenarios.py` (AppTest).
- [x] **TASK-502:** Jalankan `pytest tests/ -v` dan pastikan 100% tes berhasil (13 dari 13 lolos).

### Kelompok 600: Dokumentasi & Sinkronisasi Final
- [ ] **TASK-601:** Perbarui `PROJECT_CONTEXT.md` sesuai arsitektur terbaru.
- [ ] **TASK-602:** Perbarui `README.md` (penyempurnaan jalur lokal, tech stack, dan visual showcase).
