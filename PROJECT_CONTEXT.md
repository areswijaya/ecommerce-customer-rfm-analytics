# PROJECT_CONTEXT.md — E-Commerce Customer Segmentation & RFM Analytics Dashboard

## 1. Ringkasan Proyek & Positioning
- **Nama Proyek:** E-Commerce Customer Segmentation & RFM Analytics Dashboard
- **GitHub Repository Slug:** `ecommerce-customer-rfm-analytics`
- **Domain:** Customer & Commercial Intelligence (Brazilian Olist Marketplace)
- **Positioning Portofolio:** Membedakan diri secara tegas dari Proyek 1 (yang berfokus pada Operasional, Logistik, dan Pertumbuhan MoM). Proyek 2 berfokus pada **Customer Analytics, Behavioral RFM Segmentation, Seller Economics, dan Retensi Pendapatan** untuk menjawab tantangan strategis pemasaran, pencegahan churn, dan maksimalisasi nilai seumur hidup pelanggan (*Customer Lifetime Value*).
- **Tujuan Utama:** Menganalisis perilaku belanja 93.358 pelanggan unik menggunakan **segmentasi RFM (Recency, Frequency, Monetary)** ke dalam 7 kelompok perilaku, membuktikan konsentrasi 57,6% pendapatan pada *Potential Loyalists* (28,3%) dan *At Risk* (29,3%), mengevaluasi dinamika pembiayaan cicilan dan korelasi performa penjual, serta memvisualisasikannya dalam dashboard Streamlit modern berbasis Plotly interaktif.
- **Pengembang:** Ilfa Antaries Yusuf Wijaya (Data Analyst & Commercial Intelligence Portfolio)
- **Deployment URL:** https://ecommerce-insights-dashboard-areswidjaja.streamlit.app/

---

## 2. Struktur Proyek & File Konsistensi
```
PROJECT 2 (CUSTOMER SEGMENTATION AND RFM ANALYTICS)/
├── .streamlit/
│   └── config.toml                # Konfigurasi Dark Theme Slate (#0F172A)
├── dashboard/
│   ├── dashboard.py               # Aplikasi Streamlit interaktif (100% Plotly)
│   ├── style.css                  # Desain modern Glassmorphism & kartu KPI
│   ├── sales_by_category.csv      # Data agregat penjualan per kategori (12 bulan)
│   ├── seller_summary.csv         # Data agregat performa penjual (6 bulan)
│   ├── payment_summary.csv        # Data agregat metode pembayaran (12 bulan)
│   ├── installment_summary.csv    # Data agregat cicilan pembayaran (12 bulan)
│   ├── review_summary.csv         # Data agregat ulasan pelanggan (12 bulan)
│   ├── monthly_sales.csv          # Data tren penjualan bulanan (18 bulan)
│   ├── rfm_summary.csv            # Data agregat segmen RFM pelanggan
│   └── rfm_data.csv               # Data granular RFM per customer_unique_id (93k baris)
├── data/                          # Raw datasets (Olist Brazilian E-commerce)
│   ├── customers_dataset.csv
│   ├── geolocation_dataset.csv
│   ├── orders_dataset.csv
│   ├── order_items_dataset.csv
│   ├── order_payments_dataset.csv
│   ├── order_reviews_dataset.csv
│   ├── products_dataset.csv
│   ├── product_category_name_translation.csv
│   └── sellers_dataset.csv
├── specs/                         # Spesifikasi formal (Spec-Driven Development)
│   ├── requirements.md            # Kebutuhan fungsional, non-fungsional & formula RFM
│   ├── design.md                  # Arsitektur sistem, palet desain & ADR
│   ├── steering.md                # Guardrails anti-drift & interview defensibility
│   └── tasks.md                   # Checklist tugas implementasi & status verifikasi
├── tests/                         # Pengujian otomatis (pytest AAA pattern)
│   ├── conftest.py
│   ├── test_rfm_analysis.py       # Unit tests logika komputasi & segmentasi RFM
│   ├── test_dashboard_integration.py # Integration testing dasar (AppTest)
│   └── test_dashboard_scenarios.py   # Scenario testing (filter & edge cases)
├── laporan_evaluasi_dan_audit_proyek.md # Laporan audit komprehensif
├── rencana_perbaikan_dashboard.md       # Rencana aksi perbaikan bertahap
├── notebook.ipynb                 # Notebook analisis data (EDA & visualisasi)
├── rfm_analysis.py                # Modul komputasi vektor RFM mandiri
├── PROJECT_CONTEXT.md             # Living context file & single source of truth
├── README.md                      # Dokumentasi komprehensif proyek
├── requirements.txt               # Daftar dependensi Python (Plotly, Scipy, dsb.)
├── runtime.txt                    # Konfigurasi Python runtime
└── url.txt                        # Tautan deployment aktual
```

---

## 3. Metodologi Analisis RFM (Recency, Frequency, Monetary)

### A. Karakteristik Data & Data Integrity
1. **Customer Identifier**: Menggunakan `customer_unique_id` dari `customers_dataset.csv`. Kolom `customer_id` pada `orders_dataset.csv` bersifat per transaksi (99.441 order ID = 99.441 customer ID unik). Menggunakan `customer_unique_id` adalah standar mutlak agar pelanggan berulang (*repeat customers*) terhitung akurat.
2. **Order Validity**: Hanya memperhitungkan pesanan berstatus `delivered` (96.478 pesanan, mewakili 93.358 pelanggan unik).
3. **Periode Analisis**: Seluruh riwayat transaksi pesanan delivered (September 2016 - Agustus 2018).
4. **Snapshot Date**: `2018-08-30 15:00:37` (1 hari setelah pesanan delivered terakhir).

### B. Definisi Metrik
- **Recency ($R$)**: Jumlah hari sejak tanggal pesanan terakhir pelanggan hingga `snapshot_date`. Nilai lebih kecil menandakan transaksi yang lebih baru (lebih baik).
- **Frequency ($F$)**: Jumlah pesanan unik (`nunique(order_id)`) per `customer_unique_id`.
- **Monetary ($M$)**: Total pengeluaran pelanggan (`sum(price + freight_value)`), konsisten dengan definisi revenue pada analisis komersial.

### C. Karakteristik Khusus Olist & Pendekatan Segmentasi
- **Empirical Reality**: Pada marketplace Olist, 97,0% pelanggan hanya melakukan 1 kali transaksi, dan 3,0% melakukan $\ge 2$ transaksi karena mayoritas kategori produk merupakan durable goods (furnitur, elektronik, kasur, jam tangan).
- **Handling**: Naive `pd.qcut` pada Frequency akan gagal dengan error *duplicate bin edges*. Oleh karena itu:
  - Recency diskor menjadi 5 kuintil (`r_score` 1-5, di mana 5 = paling baru).
  - Monetary diskor menjadi 5 kuintil (`m_score` 1-5, di mana 5 = belanja terbesar).
  - Frequency diskor secara diskrit ($F=1 \rightarrow 1, F=2 \rightarrow 3, F \ge 3 \rightarrow 5$).
- **7 Segmen Bisnis Actionable**:
  1. **Champions**: Repeat buyers ($F \ge 2$) yang baru saja berbelanja ($R \ge 4$) dan bernilai transaksi tinggi/menengah ($M \ge 3$). (Strategi: Loyalty reward, VIP perks).
  2. **Loyal Customers**: Repeat buyers ($F \ge 2$) yang aktif ($R \ge 3$) dengan pembelian konsisten. (Strategi: Program referral, cross-sell).
  3. **Potential Loyalists**: Pembeli baru ($R \ge 4$) bernilai transaksi tinggi ($M \ge 4$, $F=1$). Kontributor revenue terbesar (28,3%)! (Strategi: Next-order voucher 30 hari).
  4. **New Customers**: Pembeli baru ($R \ge 4$) dengan keranjang belanja standar/rendah ($M < 4$, $F=1$). (Strategi: Onboarding email, welcome discount).
  5. **Need Attention**: Pembeli moderat ($R=3$, ~7 bulan lalu) yang mendekati risiko churn. (Strategi: Kampanye reaktivasi limited-time offer).
  6. **At Risk**: Pelanggan belanja besar di masa lalu ($M \ge 4$ atau $F \ge 2$) yang sudah lama tidak aktif ($R \le 2$, >1 tahun). Menyumbang 29,3% historical revenue! (Strategi: Win-back campaign agresif).
  7. **Hibernating**: Pelanggan lama belanja kecil yang sudah dorman ($R \le 2, M < 4, F=1$). (Strategi: Low-cost automated newsletter).

---

## 4. Standar Kode, Antarmuka & Pengujian
- **Desain Streamlit**: 100% menggunakan Plotly Express dan Graph Objects dengan helper `apply_plot_theme()` berlatar transparan, diselaraskan dengan stylesheet `dashboard/style.css` dan konfigurasi `.streamlit/config.toml`.
- **Formatting**: Menerapkan standardisasi angka Indonesia `fmt_id()` (titik ribuan, koma desimal, dan prefiks `R$`).
- **Defensive Filtering**: Dilengkapi penanganan kondisi kosong dan slider dinamis untuk mencegah `StreamlitInvalidMinMaxError`.
- **Pengujian Otomatis**: 13 unit test otomatis (`pytest`) lulus 100% mencakup logika RFM, integritas data agregat, dan interaksi skenario UI dashboard.
