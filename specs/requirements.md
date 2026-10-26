# SPECIFICATION: Requirements & Business Logic

**Project:** E-Commerce Customer Segmentation & RFM Analytics Dashboard  
**Status:** Approved & Verified (100%)  
**Version:** 2.0.0 (Audited & Synchronized)  
**North Star Reference:** `PROJECT_CONTEXT.md`

---

## 1. Pendahuluan
Dokumen ini mendefinisikan kebutuhan fungsional (FR), non-fungsional (NFR), formula komputasi RFM, dan kriteria penerimaan (Acceptance Criteria) untuk portofolio analitik data pelanggan (*Customer Intelligence*). Seluruh spesifikasi dirancang untuk membuktikan ketajaman analitis, pemahaman perilaku konsumen pasar e-commerce (*durable goods*), dan keahlian rekayasa dashboard interaktif modern.

---

## 2. Target Pengguna & Konteks Wawancara Kerja
- **Kandidat (Author):** Ilfa Antaries Yusuf Wijaya — Data Analyst dengan spesialisasi *Commercial & Customer Analytics*.
- **Interviewer / Stakeholder:** Head of Marketing/Growth, Lead Data Analyst, atau Product Manager yang mengevaluasi:
  1. **Pemahaman Karakteristik Data:** Menyadari perbedaan mendasar antara `customer_id` (transaksional) dan `customer_unique_id` (identitas unik konsumen).
  2. **Metodologi Segmentasi Tangguh:** Tidak menerapkan kuantil naif pada frekuensi saat data didominasi 97% pembelian tunggal, melainkan merancang sistem skor diskrit yang realistis.
  3. **Impact Bisnis Nyata:** Mampu memetakan bahwa 57,6% pendapatan tertumpu pada dua kelompok kritis (*Potential Loyalists* & *At Risk*) dan menyusun strategi retensi spesifik.
  4. **Eksekusi Teknis Modern:** Mengembangkan antarmuka interaktif Plotly dengan arsitektur modular, penanganan error defensif, dan pengujian unit otomatis.

---

## 3. Spesifikasi Kebutuhan Fungsional (Functional Requirements)

### FR-01: Komputasi Metrik RFM Granular (Level Pelanggan Unik)
- **FR-01.1:** Menyaring hanya pesanan berstatus `delivered` (96.478 pesanan) dari `orders_dataset.csv`.
- **FR-01.2:** Menautkan data pesanan dengan `customers_dataset.csv` berbasis `customer_id` untuk mengekstrak `customer_unique_id` (menghasilkan 93.358 pelanggan unik).
- **FR-01.3:** Menghitung total nilai pesanan dari `order_items_dataset.csv`:
  $$\text{order\_value} = \sum (\text{price} + \text{freight\_value})$$
  Nilai ini konsisten dengan definisi *Net Revenue* di seluruh analisis komersial.
- **FR-01.4:** Menetapkan tanggal referensi (*snapshot date*): 1 hari setelah pesanan delivered terakhir (`2018-08-30 15:00:37`).
- **FR-01.5:** Menghitung tiga metrik inti per `customer_unique_id`:
  - **Recency ($R$):** Selisih hari antara `snapshot_date` dan transaksi pembelian terakhir pelanggan:
    $$R = \lfloor (\text{snapshot\_date} - \max(\text{order\_purchase\_timestamp})) / 86400 \rfloor$$
  - **Frequency ($F$):** Jumlah pesanan unik (`nunique(order_id)`) yang dilakukan pelanggan.
  - **Monetary ($M$):** Total akumulasi pembelanjaan pelanggan ($\sum \text{order\_value}$).

### FR-02: Sistem Pembobotan & Segmentasi 7 Kelompok Perilaku
- **FR-02.1:** **Recency Score ($r\_score$):** Dibagi menjadi 5 kuintil (`pd.qcut`, skor 1 s.d. 5, di mana 5 = paling baru belanja).
- **FR-02.2:** **Monetary Score ($m\_score$):** Dibagi menjadi 5 kuintil (`pd.qcut`, skor 1 s.d. 5, di mana 5 = nilai belanja terbesar).
- **FR-02.3:** **Frequency Score ($f\_score$):** Karena 97,0% pelanggan memiliki $F=1$, pembagian kuintil naif akan gagal (duplicate edges). Digunakan pemetaan diskrit:
  $$f\_score = \begin{cases} 5, & \text{jika } F \ge 3 \\ 3, & \text{jika } F = 2 \\ 1, & \text{jika } F = 1 \end{cases}$$
- **FR-02.4:** Klasifikasi 7 Segmen Bisnis:
  1. **Champions:** $F \ge 2$, $R \ge 4$, $M \ge 3$ (Pelanggan loyal teraktif dengan nilai belanja tinggi).
  2. **Loyal Customers:** $F \ge 2$, $R \ge 3$ (Pelanggan berulang dengan frekuensi transaksi stabil).
  3. **Potential Loyalists:** $F = 1$, $R \ge 4$, $M \ge 4$ (Pelanggan baru belanja besar, 28,3% revenue!).
  4. **New Customers:** $F = 1$, $R \ge 4$, $M < 4$ (Pelanggan baru belanja standar/rendah).
  5. **Need Attention:** $F = 1$, $R = 3$ (Pelanggan moderat ~7 bulan lalu, berisiko churn).
  6. **At Risk:** ($M \ge 4$ atau $F \ge 2$) dan $R \le 2$ (Pelanggan belanja besar lama tak aktif, 29,3% revenue!).
  7. **Hibernating:** $F = 1$, $R \le 2$, $M < 4$ (Pelanggan lama dorman bernilai rendah).

### FR-03: Kinerja Kategori Produk & Tren Penjualan Bulanan
- **FR-03.1:** Agregasi omset penjualan dan volume transaksi per kategori produk dari `sales_by_category.csv`.
- **FR-03.2:** Evaluasi tren 18 bulan dari `monthly_sales.csv` untuk memantau fluktuasi order dan lonjakan penjualan musiman (*Black Friday November 2017*).

### FR-04: Analisis Kinerja Penjual & Korelasi Kepuasan
- **FR-04.1:** Evaluasi performa penjual teratas dari `seller_summary.csv` berdasarkan omset dan volume pesanan.
- **FR-04.2:** Pemotongan identitas penjual (*truncated ID* 8 karakter) dengan tampilan hash UUID lengkap pada tooltip interaktif.
- **FR-04.3:** Kalkulasi koefisien korelasi non-parametrik Spearman ($\rho$) antara volume pesanan dan skor ulasan rata-rata untuk memvalidasi stabilitas kualitas layanan.

### FR-05: Metode Pembayaran & Struktur Cicilan
- **FR-05.1:** Analisis distribusi nilai pembayaran per instrumen (*credit card*, *boleto*, *voucher*, *debit card*) dari `payment_summary.csv`.
- **FR-05.2:** Analisis proporsi jumlah transaksi berdasarkan termin cicilan (*1x s.d. 24x installments*) dari `installment_summary.csv`.

### FR-06: Antarmuka Interaktif Dashboard Modern (`dashboard.py`)
- **FR-06.1:** Executive KPI Ribbon (4 Kartu Utama: Total Revenue, Total Orders, Average Review Score, Top Category).
- **FR-06.2:** Migrasi 100% visualisasi ke **Plotly** interaktif dengan tema gelap elegan (`apply_plot_theme`).
- **FR-06.3:** Format angka standar Indonesia `fmt_id()` pada seluruh metrik dan label sumbu.
- **FR-06.4:** Fitur interaktif *RFM Segment Explorer & Customer Lookup* yang memungkinkan pencarian identitas pelanggan unik dan inspeksi skor RFM.
- **FR-06.5:** Penanganan kondisi kosong (*defensive state*) jika pengguna mengosongkan filter pilihan.

---

## 4. Kebutuhan Non-Fungsional (Non-Functional Requirements)

- **NFR-01 (Kualitas UI/UX & Dark Mode):** Kontras warna mematuhi standar WCAG AAA, tampilan responsif di layar desktop dan tablet, serta tidak ada teks putih di atas latar terang.
- **NFR-02 (Performa & Caching):** Dashboard memanfaatkan `@st.cache_data` sehingga transisi filter berlangsung instan ($<500\text{ ms}$).
- **NFR-03 (Keandalan Pengujian):** Seluruh logika matematis RFM dan skenario interaksi UI wajib lulus pengujian otomatis `pytest` ($100\%$ Pass Rate).
- **NFR-04 (Separation of Concerns):** Seluruh styling estetika dipisahkan ke dalam `dashboard/style.css` dan konfigurasi tema di `.streamlit/config.toml`.
