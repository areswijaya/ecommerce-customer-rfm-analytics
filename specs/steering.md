# SPECIFICATION: Project Steering, Guardrails & Interview Defensibility

**Project:** E-Commerce Customer Segmentation & RFM Analytics Dashboard  
**Status:** Approved & Active  
**Version:** 2.0.0  
**North Star Reference:** `PROJECT_CONTEXT.md`

---

## 1. Kompas Strategis & Positioning Portofolio

Proyek ini diposisikan secara tegas dan terukur sebagai **Customer Analytics & Commercial Intelligence Showcase**:
- **Bukan Duplikasi Proyek 1:** Proyek 1 berfokus pada efisiensi operasional, durasi pengiriman logistik, korelasi rating pesanan terlambat, dan analisis Pareto kategori produk.
- **Fokus Inti Proyek 2:** Berpusat pada **Pelanggan (Customer-Centric Analytics)**: bagaimana pelanggan berbelanja (*behavioral lifecycle*), segmentasi RFM empiris, dinamika pembiayaan cicilan, dan monetisasi retensi pelanggan.
- **Pesan untuk Rekruter:** Menunjukkan kedewasaan analitis bahwa strategi pertumbuhan marketplace tidak hanya bergantung pada akuisisi pelanggan baru, melainkan pada **proteksi segmen bernilai tinggi (*At Risk*)** dan **konversi pembeli bernilai besar (*Potential Loyalists*)**.

---

## 2. Prinsip Anti-Drift (North Star Guardrails)

1. **Guardrail 1 — Integritas Identitas Konsumen:**
   Dilarang keras menggunakan `customer_id` untuk menghitung perilaku berulang pelanggan. Seluruh logika RFM wajib mengacu pada `customer_unique_id`. Pelanggaran terhadap prinsip ini akan mengacaukan perhitungan frekuensi retensi.
2. **Guardrail 2 — Konsistensi Definisi Pendapatan:**
   Definisi nilai pesanan (`order_value` / `total_monetary`) harus selalu konsisten dengan omset komersial (`price + freight_value`).
3. **Guardrail 3 — Larangan Naive Qcut pada Frekuensi:**
   Dilarang memaksakan kuintil kontinu pada metrik dengan skewness ekstrem ($97\%$ bernilai 1). Pemetaan diskrit yang dirancang pada `rfm_analysis.py` adalah batasan metodologi yang wajib dipertahankan.
4. **Guardrail 4 — Integritas Performa Antarmuka:**
   Membaca file 93.358 baris (`rfm_data.csv`) tidak boleh menghambat render awal dashboard. Pemuatan data granular wajib di-cache dengan `@st.cache_data`.

---

## 3. Matriks Risiko & Mitigasi Teknis

| Kode | Risiko Teridentifikasi | Tingkat | Rencana Mitigasi |
|---|---|---|---|
| **RSK-01** | Beban memori saat memuat `rfm_data.csv` (6,7 MB) di Streamlit Cloud. | Sedang | Gunakan `@st.cache_data(show_spinner=False)`, batasi kolom yang di-load hanya kolom esensial, dan gunakan lazy inspection. |
| **RSK-02** | Inkonsistensi filter antar-file agregasi CSV. | Rendah | Jelaskan cakupan filter secara transparan pada sidebar dan sediakan fallback aman jika filter menghasilkan baris kosong. |
| **RSK-03** | Konflik warna grafik Plotly pada tema peramban yang berbeda. | Tinggi | Kunci tema permanen via `.streamlit/config.toml` dan helper `apply_plot_theme()` dengan background transparan. |
| **RSK-04** | Regresi kode saat pengujian otomatis dijalankan lintas platform (Windows/Linux). | Sedang | Gunakan `Path(__file__).resolve()` untuk seluruh penanganan path berkas. |

---

## 4. Panduan Pertanggungjawaban Wawancara (*Interview Defensibility Guide*)

Berikut adalah skenario pertanyaan teknis/bisnis yang siap dipertanggungjawabkan oleh kandidat:

### Pertanyaan 1: "Mengapa Anda menggunakan pemetaan diskrit untuk Frequency, bukan 5 kuintil standar seperti Recency dan Monetary?"
> **Jawaban Kandidat:**  
> "Pada dataset marketplace Olist, setelah memfilter pesanan berstatus *delivered*, terdapat 93.358 pelanggan unik, di mana **97,0% (90.557 pelanggan) hanya pernah berbelanja 1 kali**, dan hanya **3,0% yang bertransaksi $\ge 2$ kali**.  
> Jika kita memaksakan fungsi `pd.qcut(df['frequency'], q=5)`, algoritma akan melempar *ValueError: Bin edges must be unique* karena batas persentil ke-20 hingga ke-80 semuanya bernilai 1.  
> Oleh karena itu, saya merancang pemetaan diskrit berbasis realitas bisnis: pelanggan bertransaksi 1x diberi skor 1, pelanggan bertransaksi 2x diberi skor 3, dan pelanggan dengan transaksi $\ge 3$ kali diberi skor 5. Pendekatan ini mempertahankan validitas statistik sekaligus merefleksikan karakteristik produk Olist yang didominasi *durable goods* (perabot, elektronik, kasur)."

### Pertanyaan 2: "Mengapa segmen *Potential Loyalists* dan *At Risk* menjadi sorotan utama Anda dibandingkan *Champions*?"
> **Jawaban Kandidat:**  
> "Meskipun segmen *Champions* memiliki loyalitas dan frekuensi tertinggi, jumlah mereka di marketplace ini relatif kecil ($1.134$ pelanggan atau $1,21\%$, menyumbang $2,49\%$ pendapatan).  
> Sebaliknya, temuan analitik saya mengungkap bahwa **dua segmen terbesar yang mengendalikan lebih dari $57,6\%$ total pendapatan** adalah:
> 1. **Potential Loyalists ($28,31\%$ omset / $14.454$ pelanggan):** Mereka baru berbelanja ($R \ge 4$) dengan keranjang belanja bernilai tinggi ($M \ge 4$). Peluang terbesar marketplace adalah mengonversi mereka menjadi repeat buyers melalui voucher pesanan kedua dalam 30 hari.
> 2. **At Risk ($29,30\%$ omset / $14.723$ pelanggan):** Mereka adalah pelanggan bernilai tinggi di masa lalu yang sudah tidak bertransaksi selama lebih dari 1 tahun ($R \le 2$). Kehilangan segmen ini berarti kehilangan hampir sepertiga basis omset historis, sehingga program *win-back* terfokus menjadi prioritas mutlak."

### Pertanyaan 3: "Mengapa Anda mengonversi dashboard dari Matplotlib/Seaborn ke Plotly?"
> **Jawaban Kandidat:**  
> "Dalam konteks produk data analitik, Matplotlib menghasilkan kanvas statis berbasis piksel yang tidak ramah pengguna pada perangkat web modern: teks sumbu UUID penjual 32 karakter bertumpuk tidak terbaca, dan pengguna tidak dapat melihat angka pasti tanpa tooltip.  
> Dengan memigrasikan seluruh visualisasi ke Plotly Express dan Graph Objects, dasbor memiliki:
> 1. Interaktivitas penuh (*hover tooltips*, seleksi data, dan *zoom*).
> 2. Kerapian visual dengan memotong UUID penjual di sumbu grafik namun tetap menampilkan hash lengkap pada tooltip.
> 3. Integrasi sempurna dengan CSS Glassmorphism dan tema gelap WCAG AAA, menghadirkan standar produk BI modern."
