# ==========================================================
# E-COMMERCE CUSTOMER SEGMENTATION & RFM ANALYTICS DASHBOARD
# Junior Data Analyst Portfolio | Commercial & Customer Intelligence
# Author: Ilfa Antaries Yusuf Wijaya | contact.areswijaya@gmail.com
# ==========================================================

import os
from pathlib import Path
from typing import Optional, Tuple
import warnings

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

warnings.filterwarnings("ignore")

# ----------------------------------------------------------
# PATH & ENVIRONMENT RESOLUTION
# ----------------------------------------------------------
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

def get_file_path(filename: str) -> Path:
    """Find file in current dir, project root, or dashboard subfolder."""
    candidates = [
        CURRENT_DIR / filename,
        PROJECT_ROOT / "dashboard" / filename,
        PROJECT_ROOT / filename,
        PROJECT_ROOT / "data" / filename,
    ]
    for p in candidates:
        if p.exists():
            return p
    return CURRENT_DIR / filename

# ----------------------------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------------------------
st.set_page_config(
    page_title="E-Commerce Customer Segmentation & RFM Analytics",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------
# LOAD CSS STYLING
# ----------------------------------------------------------
css_path = get_file_path("style.css")
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ----------------------------------------------------------
# NUMBER FORMATTING HELPER (STANDARD INDONESIAN FORMAT)
# ----------------------------------------------------------
def fmt_id(val, is_currency: bool = False, decimals: int = 0) -> str:
    """
    Format angka standar Indonesia: pemisah ribuan titik (.), desimal koma (,).
    Contoh: 1234567.89 -> '1.234.568' atau 'R$ 1.234.567,89'
    """
    if val is None or pd.isna(val):
        return "-"
    try:
        val_float = float(val)
    except (ValueError, TypeError):
        return str(val)

    if decimals == 0:
        raw_str = f"{val_float:,.0f}"
    else:
        raw_str = f"{val_float:,.{decimals}f}"

    parts = raw_str.split(".")
    int_part = parts[0].replace(",", ".")
    if len(parts) > 1:
        res = f"{int_part},{parts[1]}"
    else:
        res = int_part

    return f"R$ {res}" if is_currency else res

# ----------------------------------------------------------
# REUSABLE PLOTLY THEME HELPER
# ----------------------------------------------------------
def apply_plot_theme(fig, title: str = "", x_title: str = "", y_title: str = "", margin: Optional[dict] = None) -> go.Figure:
    """Menerapkan layout tema gelap/transparan yang konsisten pada semua figur Plotly."""
    if margin is None:
        margin = dict(l=65, r=30, t=50, b=45)
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>" if title else "", font=dict(size=13, color="#F8FAFC")),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=margin,
        font=dict(color="#F8FAFC", family="Inter, sans-serif"),
        hoverlabel=dict(bgcolor="#1E293B", font_color="#F8FAFC", font_size=12, bordercolor="#3B82F6")
    )
    fig.update_xaxes(title_text=x_title, showgrid=True, gridcolor="rgba(148, 163, 184, 0.12)", automargin=True)
    fig.update_yaxes(title_text=y_title, showgrid=True, gridcolor="rgba(148, 163, 184, 0.12)", automargin=True)
    return fig

# ----------------------------------------------------------
# DATA LOADER (WITH CACHING)
# ----------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_summary_data():
    """Load core aggregate datasets for fast dashboard initial rendering."""
    sales_by_category = pd.read_csv(get_file_path("sales_by_category.csv"))
    seller_summary = pd.read_csv(get_file_path("seller_summary.csv"))
    payment_summary = pd.read_csv(get_file_path("payment_summary.csv"))
    installment_summary = pd.read_csv(get_file_path("installment_summary.csv"))
    review_summary = pd.read_csv(get_file_path("review_summary.csv"))
    monthly_sales = pd.read_csv(get_file_path("monthly_sales.csv"))
    monthly_sales["order_month"] = pd.to_datetime(monthly_sales["order_month"])
    rfm_summary = pd.read_csv(get_file_path("rfm_summary.csv"))

    # Ensure numeric types
    sales_by_category["total_revenue"] = pd.to_numeric(sales_by_category["total_revenue"], errors="coerce").fillna(0)
    sales_by_category["total_transactions"] = pd.to_numeric(sales_by_category["total_transactions"], errors="coerce").fillna(0)
    sales_by_category["aov"] = sales_by_category["total_revenue"] / sales_by_category["total_transactions"].replace(0, 1)

    seller_summary["total_revenue"] = pd.to_numeric(seller_summary["total_revenue"], errors="coerce").fillna(0)
    seller_summary["total_orders"] = pd.to_numeric(seller_summary["total_orders"], errors="coerce").fillna(0)
    seller_summary["avg_review_score"] = pd.to_numeric(seller_summary["avg_review_score"], errors="coerce").fillna(0)

    installment_summary["total_orders"] = pd.to_numeric(installment_summary["total_orders"], errors="coerce").fillna(0)
    installment_summary["total_payment_value"] = pd.to_numeric(installment_summary["total_payment_value"], errors="coerce").fillna(0)
    installment_summary["aov"] = installment_summary["total_payment_value"] / installment_summary["total_orders"].replace(0, 1)

    monthly_sales["total_orders"] = pd.to_numeric(monthly_sales["total_orders"], errors="coerce").fillna(0)
    monthly_sales["total_revenue"] = pd.to_numeric(monthly_sales["total_revenue"], errors="coerce").fillna(0)
    monthly_sales["mom_growth"] = monthly_sales["total_revenue"].pct_change() * 100
    monthly_sales["aov"] = monthly_sales["total_revenue"] / monthly_sales["total_orders"].replace(0, 1)

    return (
        sales_by_category,
        seller_summary,
        payment_summary,
        installment_summary,
        review_summary,
        monthly_sales,
        rfm_summary
    )

@st.cache_data(show_spinner=False)
def load_rfm_granular():
    """Load granular RFM dataset for interactive customer lookup and CRM download."""
    rfm_data_path = get_file_path("rfm_data.csv")
    if rfm_data_path.exists():
        return pd.read_csv(rfm_data_path)
    return pd.DataFrame()

(
    sales_by_category,
    seller_summary,
    payment_summary,
    installment_summary,
    review_summary,
    monthly_sales,
    rfm_summary
) = load_summary_data()

# ----------------------------------------------------------
# HERO HEADER BANNER
# ----------------------------------------------------------
st.markdown("""
<div class="main-banner">
    <h1>🛒 E-Commerce Customer Segmentation & RFM Analytics</h1>
    <p>Marketplace Customer Intelligence, Behavioral RFM Segmentation, Financing Dynamics & Strategic Revenue Retention (Olist Dataset)</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# SIDEBAR GLOBAL FILTERS
# ----------------------------------------------------------
st.sidebar.markdown("### ⚙️ Filter Global & Kontrol")

# 1. Date Range Filter
min_date = monthly_sales["order_month"].min().date()
max_date = monthly_sales["order_month"].max().date()

st.sidebar.markdown("#### 🗓️ Rentang Waktu Penjualan")
date_range = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    help="Menyaring data tren penjualan bulanan (Seksi 5)."
)

# Safe date range resolution
if isinstance(date_range, (tuple, list)):
    if len(date_range) == 2:
        start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered_monthly = monthly_sales[(monthly_sales["order_month"] >= start_d) & (monthly_sales["order_month"] <= end_d)]
    elif len(date_range) == 1:
        start_d = end_d = pd.to_datetime(date_range[0])
        filtered_monthly = monthly_sales[(monthly_sales["order_month"] >= start_d) & (monthly_sales["order_month"] <= end_d)]
        st.sidebar.info("💡 Memilih satu tanggal. Menampilkan data pada periode tersebut.")
    else:
        filtered_monthly = monthly_sales.copy()
else:
    filtered_monthly = monthly_sales.copy()

# 2. Product Category Filter
st.sidebar.markdown("#### 📦 Kategori Produk")
all_categories = sorted(sales_by_category["product_category_name_english"].dropna().unique().tolist())
select_all_cats = st.sidebar.checkbox("Pilih Seluruh Kategori", value=True)

if select_all_cats:
    selected_categories = all_categories
else:
    top_cat_defaults = ["health_beauty", "watches_gifts", "bed_bath_table", "sports_leisure", "computers_accessories"]
    selected_categories = st.sidebar.multiselect(
        "Pilih Kategori Spesifik",
        options=all_categories,
        default=[c for c in top_cat_defaults if c in all_categories]
    )

filtered_sales = (
    sales_by_category[sales_by_category["product_category_name_english"].isin(selected_categories)]
    if selected_categories else pd.DataFrame()
)

# 3. Payment Method Filter
st.sidebar.markdown("#### 💳 Metode Pembayaran")
all_payments = sorted(payment_summary["payment_type"].dropna().unique().tolist())
select_all_pay = st.sidebar.checkbox("Pilih Semua Metode Pembayaran", value=True)

if select_all_pay:
    selected_payments = all_payments
else:
    selected_payments = st.sidebar.multiselect(
        "Pilih Metode Pembayaran",
        options=all_payments,
        default=all_payments[:2]
    )

filtered_payment = (
    payment_summary[payment_summary["payment_type"].isin(selected_payments)]
    if selected_payments else pd.DataFrame()
)

# 4. RFM Segment Filter
st.sidebar.markdown("#### 👥 Segmen Pelanggan (RFM)")
rfm_segment_options = ["Semua Segmen"] + list(rfm_summary["segment"].unique())
selected_rfm_segment = st.sidebar.selectbox(
    "Pilih Fokus Segmen RFM",
    options=rfm_segment_options,
    index=0,
    help="Menyaring tampilan profil dan tabel actionable playbook pada Seksi 6."
)

st.sidebar.markdown("---")
st.sidebar.caption("👨‍💼 **Portfolio:** Data Analyst & Commercial Intelligence  \n🎓 **Analyst:** Ilfa Antaries Yusuf Wijaya  \n📊 **Data:** Brazilian Olist Marketplace")

# ----------------------------------------------------------
# EXECUTIVE OVERVIEW RIBBON (4 KPI METRIC CARDS)
# ----------------------------------------------------------
st.markdown("### 📊 Ringkasan Kinerja Utama (Executive Overview)")

# Compute KPI metrics safely
calc_revenue = filtered_sales["total_revenue"].sum() if not filtered_sales.empty else sales_by_category["total_revenue"].sum()
calc_orders = filtered_monthly["total_orders"].sum() if not filtered_monthly.empty else monthly_sales["total_orders"].sum()
calc_avg_review = review_summary["avg_review_score"].mean() if not review_summary.empty else 0.0

if not filtered_sales.empty:
    top_cat_row = filtered_sales.nlargest(1, "total_revenue").iloc[0]
    top_cat_name = str(top_cat_row["product_category_name_english"]).replace("_", " ").title()
    top_cat_val = fmt_id(top_cat_row["total_revenue"], is_currency=True)
else:
    top_cat_name = "-"
    top_cat_val = "-"

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.metric(
        label="💰 Total Net Revenue",
        value=fmt_id(calc_revenue, is_currency=True),
        delta=f"{len(selected_categories)} Kategori Terpilih" if selected_categories else "Semua Kategori",
        help="Total omset pendapatan kotor terealisasi (mencakup harga produk dan ongkos kirim) pada pesanan delivered."
    )

with kpi_col2:
    st.metric(
        label="📦 Total Delivered Orders",
        value=fmt_id(calc_orders),
        delta=f"{len(filtered_monthly)} Bulan Transaksi",
        help="Total volume transaksi unik yang berhasil dikirim ke pelanggan."
    )

with kpi_col3:
    st.metric(
        label="⭐ Average Review Score",
        value=f"{calc_avg_review:.2f} / 5.0",
        delta="Benchmark Kepuasan: 4.0+",
        help="Rata-rata penilaian kepuasan ulasan pelanggan (skala 1 hingga 5 bintang)."
    )

with kpi_col4:
    st.metric(
        label="🏆 Kategori Terlaris",
        value=top_cat_name,
        delta=f"Omset: {top_cat_val}",
        help="Kategori produk dengan perolehan omset tertinggi pada filter aktif."
    )

# Secondary Metadata Ribbon
st.markdown(f"""
<div class="meta-ribbon">
    <span>👥 <b>Basis Pelanggan Unik:</b> 93.358 ID (97,0% Pembelian Tunggal, 3,0% Repeat)</span>
    <span>🎯 <b>Konsentrasi Revenue:</b> 57,6% Dikuasai <i>Potential Loyalists</i> & <i>At Risk</i></span>
    <span>💳 <b>Metode Dominan:</b> Kartu Kredit (78,1% Total Nilai)</span>
    <span>🛍️ <b>Rata-rata Nilai Belanja (AOV):</b> R$ 166 per Pelanggan</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ----------------------------------------------------------
# SECTION 1 — PENJUALAN PER KATEGORI PRODUK
# ----------------------------------------------------------
with st.expander("📦 Seksi 1: Penjualan per Kategori Produk", expanded=True):
    if filtered_sales.empty:
        st.info("ℹ️ Tidak ada data kategori yang dipilih. Silakan pilih minimal 1 kategori pada filter sidebar.")
    else:
        tab_cat_vis, tab_cat_table = st.tabs(["📊 Visualisasi Top Kategori", "📋 Rincian & Analisis AOV Kategori"])

        total_avail_cats = len(filtered_sales)
        if total_avail_cats <= 5:
            cat_slider = total_avail_cats
        else:
            cat_slider = st.slider(
                "Tampilkan Top-N Kategori Teratas",
                min_value=5,
                max_value=min(25, total_avail_cats),
                value=min(10, total_avail_cats),
                key="sec1_cat_slider"
            )

        top_rev = filtered_sales.nlargest(cat_slider, "total_revenue").sort_values(by="total_revenue", ascending=True)
        top_trans = filtered_sales.nlargest(cat_slider, "total_transactions").sort_values(by="total_transactions", ascending=True)

        with tab_cat_vis:
            col_s1_left, col_s1_right = st.columns(2)

            with col_s1_left:
                fig_rev = px.bar(
                    top_rev,
                    x="total_revenue",
                    y="product_category_name_english",
                    orientation="h",
                    text="total_revenue",
                    color="total_revenue",
                    color_continuous_scale="Blues",
                    labels={"total_revenue": "Total Revenue (BRL)", "product_category_name_english": "Kategori"}
                )
                fig_rev.update_traces(
                    texttemplate="R$ %{text:,.0f}",
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>Revenue: R$ %{x:,.2f}<extra></extra>"
                )
                fig_rev.update_coloraxes(showscale=False)
                apply_plot_theme(fig_rev, title=f"Top {cat_slider} Kategori Berdasarkan Revenue", x_title="Revenue (BRL)")
                st.plotly_chart(fig_rev, use_container_width=True)

            with col_s1_right:
                fig_trans = px.bar(
                    top_trans,
                    x="total_transactions",
                    y="product_category_name_english",
                    orientation="h",
                    text="total_transactions",
                    color="total_transactions",
                    color_continuous_scale="Greens",
                    labels={"total_transactions": "Total Transaksi", "product_category_name_english": "Kategori"}
                )
                fig_trans.update_traces(
                    texttemplate="%{text:,.0f}",
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>Transaksi: %{x:,.0f}<extra></extra>"
                )
                fig_trans.update_coloraxes(showscale=False)
                apply_plot_theme(fig_trans, title=f"Top {cat_slider} Kategori Berdasarkan Transaksi", x_title="Jumlah Transaksi")
                st.plotly_chart(fig_trans, use_container_width=True)

        with tab_cat_table:
            st.markdown("##### 📋 Tabel Portofolio Kategori Lengkap & Nilai Pesanan Rata-rata (AOV)")
            cat_display = filtered_sales.sort_values(by="total_revenue", ascending=False).copy()
            cat_display["revenue_fmt"] = cat_display["total_revenue"].apply(lambda x: fmt_id(x, is_currency=True))
            cat_display["trans_fmt"] = cat_display["total_transactions"].apply(fmt_id)
            cat_display["aov_fmt"] = cat_display["aov"].apply(lambda x: fmt_id(x, is_currency=True, decimals=2))
            
            show_cat_cols = {
                "product_category_name_english": "Nama Kategori Produk",
                "revenue_fmt": "Total Revenue",
                "trans_fmt": "Total Transaksi",
                "aov_fmt": "Average Order Value (AOV)"
            }
            st.dataframe(
                cat_display[list(show_cat_cols.keys())].rename(columns=show_cat_cols),
                use_container_width=True,
                hide_index=True
            )
            
            # Download category report
            csv_cat = cat_display[["product_category_name_english", "total_revenue", "total_transactions", "aov"]].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Unduh Ringkasan Kategori (CSV)",
                data=csv_cat,
                file_name="category_sales_summary.csv",
                mime="text/csv",
                key="dl_cat_summary"
            )

        highest_cat = top_rev.iloc[-1]["product_category_name_english"].replace("_", " ").title()
        highest_rev_val = fmt_id(top_rev.iloc[-1]["total_revenue"], is_currency=True)
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-card-title">💡 Insight Kunci Penjualan Kategori</div>
            <div class="insight-card-body">
                Kategori penyumbang omset tertinggi saat ini adalah <b>{highest_cat}</b> ({highest_rev_val}).
                Kategori bernilai tinggi umumnya terkonsentrasi pada segmen <i>health & beauty</i>, <i>watches & gifts</i>, serta <i>bed bath table</i>, yang menunjukkan pola belanja barang kebutuhan rumah tangga dan gaya hidup.
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ----------------------------------------------------------
# SECTION 2 — KINERJA PENJUAL (SELLER ECONOMICS)
# ----------------------------------------------------------
with st.expander("👨‍💼 Seksi 2: Analisis Kinerja Penjual (Seller Economics)", expanded=False):
    if seller_summary.empty:
        st.info("ℹ️ Data kinerja penjual tidak tersedia.")
    else:
        tab_sell_vis, tab_sell_pareto = st.tabs(["👨‍💼 Top Penjual & Korelasi Kepuasan", "📈 Analisis Skala & Konsentrasi Penjual"])

        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("💰 Avg Revenue per Penjual", fmt_id(seller_summary["total_revenue"].mean(), is_currency=True))
        sc2.metric("📦 Total Pesanan Terkelola", fmt_id(seller_summary["total_orders"].sum()))
        sc3.metric("⭐ Avg Skor Penjual", f"{seller_summary['avg_review_score'].mean():.2f} / 5.0")

        with tab_sell_vis:
            top_s_n = st.slider("Pilih Jumlah Top Penjual", 5, 20, 10, key="sec2_seller_slider")

            # Top Sellers by Revenue and Orders
            top_sellers_rev = seller_summary.nlargest(top_s_n, "total_revenue").copy()
            top_sellers_rev["short_seller_id"] = top_sellers_rev["seller_id"].apply(lambda x: str(x)[:8] + "...")
            top_sellers_rev = top_sellers_rev.sort_values(by="total_revenue", ascending=True)

            top_sellers_ord = seller_summary.nlargest(top_s_n, "total_orders").copy()
            top_sellers_ord["short_seller_id"] = top_sellers_ord["seller_id"].apply(lambda x: str(x)[:8] + "...")
            top_sellers_ord = top_sellers_ord.sort_values(by="total_orders", ascending=True)

            col_sell_1, col_sell_2 = st.columns(2)

            with col_sell_1:
                fig_sell_rev = px.bar(
                    top_sellers_rev,
                    x="total_revenue",
                    y="short_seller_id",
                    orientation="h",
                    color="total_revenue",
                    color_continuous_scale="Blues",
                    hover_data={"seller_id": True, "total_revenue": ":,.2f", "total_orders": ":,.0f", "avg_review_score": ":.2f"}
                )
                fig_sell_rev.update_traces(
                    hovertemplate="<b>Seller ID:</b> %{customdata[0]}<br><b>Revenue:</b> R$ %{x:,.2f}<br><b>Orders:</b> %{customdata[1]:,.0f}<br><b>Rating:</b> %{customdata[2]:.2f} ⭐<extra></extra>"
                )
                fig_sell_rev.update_coloraxes(showscale=False)
                apply_plot_theme(fig_sell_rev, title=f"Top {top_s_n} Penjual Berdasarkan Revenue", x_title="Revenue (BRL)")
                st.plotly_chart(fig_sell_rev, use_container_width=True)

            with col_sell_2:
                fig_sell_ord = px.bar(
                    top_sellers_ord,
                    x="total_orders",
                    y="short_seller_id",
                    orientation="h",
                    color="total_orders",
                    color_continuous_scale="Teal",
                    hover_data={"seller_id": True, "total_orders": ":,.0f", "total_revenue": ":,.2f", "avg_review_score": ":.2f"}
                )
                fig_sell_ord.update_traces(
                    hovertemplate="<b>Seller ID:</b> %{customdata[0]}<br><b>Orders:</b> %{x:,.0f}<br><b>Revenue:</b> R$ %{customdata[1]:,.2f}<br><b>Rating:</b> %{customdata[2]:.2f} ⭐<extra></extra>"
                )
                fig_sell_ord.update_coloraxes(showscale=False)
                apply_plot_theme(fig_sell_ord, title=f"Top {top_s_n} Penjual Berdasarkan Volume Order", x_title="Jumlah Order")
                st.plotly_chart(fig_sell_ord, use_container_width=True)

            # Correlation Analysis: Orders vs Review Score
            clean_seller_corr = seller_summary.dropna(subset=["total_orders", "avg_review_score"])
            spearman_rho, spearman_p = stats.spearmanr(clean_seller_corr["total_orders"], clean_seller_corr["avg_review_score"])

            fig_scatter = px.scatter(
                seller_summary,
                x="total_orders",
                y="avg_review_score",
                color="avg_review_score",
                color_continuous_scale="Viridis",
                trendline="ols",
                trendline_color_override="#F59E0B",
                hover_data={"seller_id": True, "total_revenue": ":,.2f"},
                labels={"total_orders": "Volume Pesanan (Orders)", "avg_review_score": "Rata-rata Skor Review (1-5)"}
            )
            fig_scatter.update_traces(
                marker=dict(size=6, opacity=0.7),
                hovertemplate="<b>Seller:</b> %{customdata[0]}<br><b>Orders:</b> %{x}<br><b>Review Score:</b> %{y:.2f}<br><b>Revenue:</b> R$ %{customdata[1]:,.2f}<extra></extra>"
            )
            fig_scatter.update_coloraxes(showscale=False)
            apply_plot_theme(
                fig_scatter,
                title=f"Korelasi Volume Pesanan vs Skor Kepuasan Ulasan (Spearman ρ = {spearman_rho:.3f}, p = {spearman_p:.4f})",
                x_title="Volume Pesanan Penjual (Orders)",
                y_title="Rata-rata Skor Review"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        with tab_sell_pareto:
            st.markdown("##### 📈 Konsentrasi Omset Penjual (Merchant Concentration)")
            seller_sorted = seller_summary.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)
            seller_sorted["cum_revenue"] = seller_sorted["total_revenue"].cumsum()
            total_sell_rev = seller_sorted["total_revenue"].sum()
            seller_sorted["cum_pct"] = (seller_sorted["cum_revenue"] / total_sell_rev) * 100
            
            top_10_share = seller_sorted.iloc[:10]["total_revenue"].sum() / total_sell_rev * 100
            top_50_share = seller_sorted.iloc[:50]["total_revenue"].sum() / total_sell_rev * 100
            
            pcol1, pcol2 = st.columns(2)
            pcol1.metric("🏆 Kontribusi Top 10 Penjual", f"{top_10_share:.1f}% Total Omset")
            pcol2.metric("🏢 Kontribusi Top 50 Penjual", f"{top_50_share:.1f}% Total Omset")
            
            fig_pareto_sell = go.Figure()
            fig_pareto_sell.add_trace(
                go.Scatter(
                    x=list(range(1, len(seller_sorted) + 1)),
                    y=seller_sorted["cum_pct"],
                    mode="lines",
                    line=dict(color="#3B82F6", width=2.5),
                    name="Kumulatif Omset (%)",
                    hovertemplate="Top %{x} Penjual: %{y:.2f}% Revenue<extra></extra>"
                )
            )
            fig_pareto_sell.add_hline(y=80, line_dash="dash", line_color="#F43F5E", annotation_text="Garis Ambang 80% Omset")
            apply_plot_theme(fig_pareto_sell, title="Kurva Konsentrasi Kumulatif Pendapatan Penjual", x_title="Peringkat Penjual (Rank)", y_title="% Kumulatif Omset")
            st.plotly_chart(fig_pareto_sell, use_container_width=True)

        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-card-title">🔍 Evaluasi Kinerja & Stabilitas Layanan Penjual</div>
            <div class="insight-card-body">
                Korelasi peringkat Spearman tercatat sebesar <b>ρ = {spearman_rho:.3f}</b> (mendekati 0).
                Hal ini mengindikasikan bahwa <b>penjual dengan volume pesanan besar tetap mampu menjaga konsistensi kepuasan pelanggan</b> tanpa mengalami penurunan mutu layanan logistik secara signifikan.
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ----------------------------------------------------------
# SECTION 3 — METODE PEMBAYARAN & CICILAN
# ----------------------------------------------------------
with st.expander("💳 Seksi 3: Analisis Metode Pembayaran & Cicilan", expanded=False):
    if filtered_payment.empty:
        st.info("ℹ️ Tidak ada data metode pembayaran yang dipilih.")
    else:
        tab_pay_share, tab_pay_aov = st.tabs(["💳 Pangsa Transaksi & Distribusi Cicilan", "🏷️ Analisis Nilai Belanja (AOV) per Frekuensi Cicilan"])

        col_pay_1, col_pay_2 = st.columns(2)
        dominant_pay = filtered_payment.loc[filtered_payment["total_payment_value"].idxmax()]
        
        with col_pay_1:
            st.metric(
                label="💰 Total Nilai Transaksi Pembayaran",
                value=fmt_id(filtered_payment["total_payment_value"].sum(), is_currency=True),
                delta=f"Instrumen Dominan: {dominant_pay['payment_type'].title()}"
            )
        with col_pay_2:
            st.metric(
                label="💳 Dominansi Kartu Kredit",
                value=f"{(dominant_pay['total_payment_value'] / filtered_payment['total_payment_value'].sum() * 100):.1f}%",
                delta="Preferensi Utama Konsumen"
            )

        with tab_pay_share:
            col_ps1, col_ps2 = st.columns(2)

            with col_ps1:
                fig_donut = px.pie(
                    filtered_payment,
                    values="total_payment_value",
                    names="payment_type",
                    hole=0.55,
                    color="payment_type",
                    color_discrete_map={
                        "credit_card": "#3B82F6",
                        "boleto": "#10B981",
                        "voucher": "#F59E0B",
                        "debit_card": "#8B5CF6"
                    }
                )
                fig_donut.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                    hovertemplate="<b>%{label}</b><br>Nilai: R$ %{value:,.2f}<br>Proporsi: %{percent}<extra></extra>"
                )
                apply_plot_theme(fig_donut, title="Pangsa Nilai Transaksi per Metode Pembayaran")
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_ps2:
                inst_top10 = installment_summary.sort_values(by="total_orders", ascending=False).head(10).copy()
                inst_top10["installments_label"] = inst_top10["payment_installments"].apply(lambda x: f"{x}x Cicilan" if x > 1 else "1x (Lunas)")

                fig_inst = px.bar(
                    inst_top10,
                    x="total_orders",
                    y="installments_label",
                    orientation="h",
                    color="total_orders",
                    color_continuous_scale="Purples",
                    labels={"total_orders": "Jumlah Order", "installments_label": "Pilihan Cicilan"}
                )
                fig_inst.update_traces(
                    texttemplate="%{x:,.0f}",
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>Jumlah Pesanan: %{x:,.0f}<br>Nilai Total: R$ %{customdata:,.2f}<extra></extra>",
                    customdata=inst_top10["total_payment_value"]
                )
                fig_inst.update_coloraxes(showscale=False)
                apply_plot_theme(fig_inst, title="Distribusi Jumlah Order Berdasarkan Frekuensi Cicilan", x_title="Jumlah Order")
                st.plotly_chart(fig_inst, use_container_width=True)

        with tab_pay_aov:
            st.markdown("##### 🛍️ Dampak Fasilitas Cicilan terhadap Ukuran Keranjang Belanja (Basket Size)")
            inst_aov_df = installment_summary[installment_summary["payment_installments"] <= 12].sort_values(by="payment_installments").copy()
            inst_aov_df["label"] = inst_aov_df["payment_installments"].apply(lambda x: f"{x}x")

            fig_inst_aov = px.bar(
                inst_aov_df,
                x="label",
                y="aov",
                text="aov",
                color="aov",
                color_continuous_scale="Blues",
                labels={"label": "Frekuensi Cicilan", "aov": "AOV (BRL)"}
            )
            fig_inst_aov.update_traces(
                texttemplate="R$ %{text:,.0f}",
                textposition="outside",
                hovertemplate="<b>Cicilan %{x}</b><br>Rata-rata Belanja: R$ %{y:,.2f}<br>Total Pesanan: %{customdata:,.0f}<extra></extra>",
                customdata=inst_aov_df["total_orders"]
            )
            fig_inst_aov.update_coloraxes(showscale=False)
            apply_plot_theme(fig_inst_aov, title="Rata-rata Nilai Belanja (AOV) berdasarkan Jumlah Cicilan", x_title="Termin Cicilan", y_title="AOV (BRL)")
            st.plotly_chart(fig_inst_aov, use_container_width=True)

            aov_1x = inst_aov_df[inst_aov_df["payment_installments"] == 1]["aov"].iloc[0]
            aov_10x = inst_aov_df[inst_aov_df["payment_installments"] == 10]["aov"].iloc[0]
            multiplier = aov_10x / aov_1x

            st.markdown(f"""
            <div style="background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3B82F6; padding: 0.8rem 1rem; border-radius: 6px; font-size: 0.9rem; color: #DBEAFE;">
                💡 <b>Financing Leverage Insight:</b> Pelanggan dengan opsi <b>10x cicilan</b> memiliki rata-rata keranjang belanja <b>{multiplier:.1f}x lipat lebih tinggi</b> (R$ {aov_10x:.0f} vs R$ {aov_1x:.0f}) dibanding pembeli bayar lunas (1x). Program cicilan tanpa bunga merupakan instrumen pendorong omset produk bernilai tinggi yang vital.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class="insight-card">
            <div class="insight-card-title">💡 Karakteristik Pembiayaan Transaksi Konsumen</div>
            <div class="insight-card-body">
                <b>Kartu kredit mendominasi lebih dari 78% total omset transaksi</b>. Konsumen Brasil sangat mengandalkan fasilitas cicilan (hingga 10x s.d. 12x) untuk pembelian produk bernilai tinggi. Kemitraan perbankan untuk program <i>0% installment</i> merupakan faktor pendorong konversi yang krusial.
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ----------------------------------------------------------
# SECTION 4 — KEPUASAN PELANGGAN PER KATEGORI
# ----------------------------------------------------------
with st.expander("⭐ Seksi 4: Kepuasan Pelanggan per Kategori Produk", expanded=False):
    if review_summary.empty:
        st.info("ℹ️ Data ulasan pelanggan tidak tersedia.")
    else:
        tab_rev_topbot, tab_rev_resp = st.tabs(["⭐ Kategori Rating Tertinggi & Terendah", "💬 Analisis Waktu Tanggap Ulasan"])

        col_rev_1, col_rev_2 = st.columns(2)
        with col_rev_1:
            st.metric("⭐ Rata-rata Kepuasan Keseluruhan", f"{review_summary['avg_review_score'].mean():.2f} / 5.0")
        with col_rev_2:
            st.metric("💬 Total Ulasan Terekam", fmt_id(review_summary["total_reviews"].sum()))

        rev_n = st.slider("Jumlah Kategori untuk Perbandingan Rating", 5, 15, 8, key="sec4_review_slider")

        top_rated = review_summary.nlargest(rev_n, "avg_review_score").sort_values(by="avg_review_score", ascending=True)
        bot_rated = review_summary.nsmallest(rev_n, "avg_review_score").sort_values(by="avg_review_score", ascending=True)

        with tab_rev_topbot:
            col_c_top, col_c_bot = st.columns(2)

            with col_c_top:
                fig_top_rev = px.bar(
                    top_rated,
                    x="avg_review_score",
                    y="product_category_name_english",
                    orientation="h",
                    color="avg_review_score",
                    color_continuous_scale="Blues",
                    range_x=[3.5, 5.0]
                )
                fig_top_rev.update_traces(
                    texttemplate="%{x:.2f} ⭐",
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>Rating: %{x:.2f} ⭐<br>Total Reviews: %{customdata:,.0f}<extra></extra>",
                    customdata=top_rated["total_reviews"]
                )
                fig_top_rev.update_coloraxes(showscale=False)
                apply_plot_theme(fig_top_rev, title=f"Top {rev_n} Kategori dengan Rating Tertinggi", x_title="Skor Ulasan")
                st.plotly_chart(fig_top_rev, use_container_width=True)

            with col_c_bot:
                fig_bot_rev = px.bar(
                    bot_rated,
                    x="avg_review_score",
                    y="product_category_name_english",
                    orientation="h",
                    color="avg_review_score",
                    color_continuous_scale="Reds",
                    range_x=[3.0, 4.5]
                )
                fig_bot_rev.update_traces(
                    texttemplate="%{x:.2f} ⭐",
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>Rating: %{x:.2f} ⭐<br>Total Reviews: %{customdata:,.0f}<extra></extra>",
                    customdata=bot_rated["total_reviews"]
                )
                fig_bot_rev.update_coloraxes(showscale=False)
                apply_plot_theme(fig_bot_rev, title=f"Top {rev_n} Kategori dengan Rating Terendah", x_title="Skor Ulasan")
                st.plotly_chart(fig_bot_rev, use_container_width=True)

        with tab_rev_resp:
            st.markdown("##### ⏱️ Waktu Respons Ulasan Pelanggan (Survey Response Latency)")
            resp_df = review_summary.dropna(subset=["avg_response_time_hours"]).nlargest(10, "total_reviews").sort_values(by="avg_response_time_hours", ascending=True)
            
            fig_resp = px.bar(
                resp_df,
                x="avg_response_time_hours",
                y="product_category_name_english",
                orientation="h",
                color="avg_response_time_hours",
                color_continuous_scale="Viridis",
                labels={"avg_response_time_hours": "Waktu Tanggap (Jam)", "product_category_name_english": "Kategori"}
            )
            fig_resp.update_traces(
                texttemplate="%{x:.1f} Jam",
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Waktu Respons: %{x:.1f} Jam (~%{customdata:.1f} Hari)<extra></extra>",
                customdata=resp_df["avg_response_time_hours"] / 24
            )
            fig_resp.update_coloraxes(showscale=False)
            apply_plot_theme(fig_resp, title="Rata-rata Waktu Respons Ulasan pada Kategori Bervolume Tinggi", x_title="Waktu Respons (Jam)")
            st.plotly_chart(fig_resp, use_container_width=True)

        st.markdown("""
        <div class="insight-card">
            <div class="insight-card-title">💡 Evaluasi Kualitas Produk & Ekspektasi Konsumen</div>
            <div class="insight-card-body">
                Kategori seperti <i>books_imported</i>, <i>books_general_interest</i>, dan <i>cds_dvds</i> konsisten meraih rating tertinggi (>4.4 ⭐) karena ekspektasi produk yang jelas dan risiko kerusakan fisik rendah saat pengiriman.
                Sebaliknya, kategori dengan rating terendah umumnya merupakan produk berdimensi besar yang rawan keterlambatan logistik.
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ----------------------------------------------------------
# SECTION 5 — TREN PENJUALAN BULANAN (18 BULAN)
# ----------------------------------------------------------
with st.expander("📈 Seksi 5: Tren Penjualan Bulanan & Musiman", expanded=False):
    if filtered_monthly.empty:
        st.info("ℹ️ Tidak ada data penjualan untuk rentang waktu yang dipilih.")
    else:
        tab_trend_dual, tab_trend_mom = st.tabs(["📈 Tren Omset & Pesanan Bulanan", "📊 Laju Pertumbuhan MoM & Stabilitas AOV"])

        total_avail_months = len(filtered_monthly)
        if total_avail_months <= 6:
            trend_months = total_avail_months
        else:
            trend_months = st.slider("Tampilkan N Bulan Terakhir", 6, total_avail_months, min(12, total_avail_months), key="sec5_trend_slider")

        df_trend = filtered_monthly.tail(trend_months).copy()
        df_trend["month_label"] = df_trend["order_month"].dt.strftime("%b %Y")

        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.metric("💰 Total Revenue (Periode Terpilih)", fmt_id(df_trend["total_revenue"].sum(), is_currency=True))
        col_t2.metric("📦 Total Orders (Periode Terpilih)", fmt_id(df_trend["total_orders"].sum()))
        col_t3.metric("🏷️ Rata-rata AOV Bulanan", fmt_id(df_trend["aov"].mean(), is_currency=True, decimals=2))

        with tab_trend_dual:
            # Dual-Axis Plotly Subplot
            fig_trend = make_subplots(specs=[[{"secondary_y": True}]])

            # Revenue trace (left axis)
            fig_trend.add_trace(
                go.Scatter(
                    x=df_trend["month_label"],
                    y=df_trend["total_revenue"],
                    name="Net Revenue (BRL)",
                    mode="lines+markers",
                    line=dict(color="#3B82F6", width=3),
                    marker=dict(size=8, color="#3B82F6"),
                    hovertemplate="<b>%{x}</b><br>Revenue: R$ %{y:,.2f}<extra></extra>"
                ),
                secondary_y=False
            )

            # Orders trace (right axis)
            fig_trend.add_trace(
                go.Scatter(
                    x=df_trend["month_label"],
                    y=df_trend["total_orders"],
                    name="Delivered Orders",
                    mode="lines+markers",
                    line=dict(color="#10B981", width=2.5, dash="dot"),
                    marker=dict(size=7, color="#10B981"),
                    hovertemplate="<b>%{x}</b><br>Orders: %{y:,.0f}<extra></extra>"
                ),
                secondary_y=True
            )

            # Highlight Black Friday if present
            if "Nov 2017" in df_trend["month_label"].values:
                nov_row = df_trend[df_trend["month_label"] == "Nov 2017"].iloc[0]
                fig_trend.add_annotation(
                    x="Nov 2017",
                    y=nov_row["total_revenue"],
                    text="🔥 Black Friday 2017 Peak",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="#F59E0B",
                    font=dict(color="#F8FAFC", size=11),
                    bgcolor="rgba(30, 41, 59, 0.9)",
                    bordercolor="#F59E0B",
                    borderwidth=1,
                    ay=-45
                )

            apply_plot_theme(fig_trend, title="Tren Penjualan Bulanan: Net Revenue vs Volume Orders")
            fig_trend.update_yaxes(title_text="Total Net Revenue (BRL)", secondary_y=False, showgrid=True, gridcolor="rgba(148, 163, 184, 0.12)")
            fig_trend.update_yaxes(title_text="Volume Orders", secondary_y=True, showgrid=False)
            fig_trend.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_trend, use_container_width=True)

        with tab_trend_mom:
            # MoM Growth Rate Bar Chart
            clean_mom = df_trend.dropna(subset=["mom_growth"]).copy()
            clean_mom["color"] = clean_mom["mom_growth"].apply(lambda x: "#10B981" if x >= 0 else "#F43F5E")

            fig_mom = go.Figure()
            fig_mom.add_trace(
                go.Bar(
                    x=clean_mom["month_label"],
                    y=clean_mom["mom_growth"],
                    marker_color=clean_mom["color"],
                    text=clean_mom["mom_growth"].apply(lambda x: f"{x:+.1f}%"),
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>Pertumbuhan MoM: %{y:+.2f}%<extra></extra>"
                )
            )
            apply_plot_theme(fig_mom, title="Laju Pertumbuhan Pendapatan Bulanan (Month-over-Month Growth %)", x_title="Bulan", y_title="Pertumbuhan (%)")
            st.plotly_chart(fig_mom, use_container_width=True)

        st.markdown("""
        <div class="insight-card">
            <div class="insight-card-title">📈 Pola Musiman & Pertumbuhan Marketplace</div>
            <div class="insight-card-body">
                Lonjakan pendapatan tertinggi tercatat pada <b>November 2017 (Black Friday)</b>, mencapai omset >R$ 1,1 juta dalam satu bulan (+53,5% MoM).
                Setelah kuartal 4 2017, volume pesanan bulanan stabil di kisaran 6.500 s.d. 7.500 pesanan per bulan, menandai maturitas operasional marketplace.
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ----------------------------------------------------------
# SECTION 6 — SEGMENTASI PELANGGAN (ANALISIS RFM)
# ----------------------------------------------------------
with st.expander("👥 Seksi 6: Segmentasi Pelanggan (Analisis RFM) — Strategic Centerpiece", expanded=True):
    if rfm_summary.empty:
        st.info("ℹ️ Data ringkasan segmentasi RFM tidak tersedia.")
    else:
        # Metrik Global RFM
        total_rfm_cust = int(rfm_summary["customer_count"].sum())
        total_rfm_rev = float(rfm_summary["total_monetary"].sum())
        avg_r_all = (rfm_summary["avg_recency"] * rfm_summary["customer_count"]).sum() / total_rfm_cust
        avg_f_all = (rfm_summary["avg_frequency"] * rfm_summary["customer_count"]).sum() / total_rfm_cust
        avg_m_all = total_rfm_rev / total_rfm_cust

        rfm_k1, rfm_k2, rfm_k3, rfm_k4 = st.columns(4)
        rfm_k1.metric("👥 Total Pelanggan Unik", fmt_id(total_rfm_cust), delta="93.358 Unique IDs")
        rfm_k2.metric("🗓️ Rata-rata Recency", f"{avg_r_all:.0f} Hari", delta="Waktu sejak order terakhir")
        rfm_k3.metric("🔁 Rata-rata Frekuensi", f"{avg_f_all:.2f} Order", delta="97% Pembeli Tunggal")
        rfm_k4.metric("💰 Rata-rata Monetary", fmt_id(avg_m_all, is_currency=True), delta="Nilai Belanja/Pelanggan")

        st.caption("Analisis RFM mengelompokkan 93.358 pelanggan unik ke dalam 7 kelompok perilaku belanja berdasarkan kebaruan (Recency), frekuensi (Frequency), dan total transaksi (Monetary).")

        # Color mapping for RFM segments
        segment_palette = {
            "Champions": "#10B981",          # Emerald
            "Loyal Customers": "#06B6D4",    # Cyan
            "Potential Loyalists": "#3B82F6",# Blue
            "New Customers": "#6366F1",      # Indigo
            "Need Attention": "#F59E0B",     # Amber
            "At Risk": "#F43F5E",            # Rose / Alert
            "Hibernating": "#64748B"         # Slate / Inactive
        }

        # 4 Enhanced Tabs
        tab_rfm_macro, tab_rfm_profile, tab_rfm_playbook, tab_rfm_lookup = st.tabs([
            "👥 Distribusi Segmen & Kontribusi Omset",
            "🔍 Profil Karakteristik 3D RFM",
            "🎯 Strategic Playbook & Action Plan",
            "🔎 Eksplorasi Pelanggan Granular & Ekspor CRM"
        ])

        with tab_rfm_macro:
            rfm_col_l, rfm_col_r = st.columns(2)

            with rfm_col_l:
                sorted_by_cust = rfm_summary.sort_values(by="customer_count", ascending=True)
                fig_rfm_cust = px.bar(
                    sorted_by_cust,
                    x="customer_count",
                    y="segment",
                    orientation="h",
                    color="segment",
                    color_discrete_map=segment_palette,
                    text="customer_pct",
                    labels={"customer_count": "Jumlah Pelanggan", "segment": "Segmen"}
                )
                fig_rfm_cust.update_traces(
                    texttemplate="%{text:.1f}%",
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>Pelanggan: %{x:,.0f} (%{text:.2f}%)<extra></extra>"
                )
                fig_rfm_cust.update_layout(showlegend=False)
                apply_plot_theme(fig_rfm_cust, title="Distribusi Jumlah Pelanggan per Segmen", x_title="Jumlah Pelanggan Unik")
                st.plotly_chart(fig_rfm_cust, use_container_width=True)

            with rfm_col_r:
                sorted_by_mon = rfm_summary.sort_values(by="total_monetary", ascending=True)
                fig_rfm_mon = px.bar(
                    sorted_by_mon,
                    x="total_monetary",
                    y="segment",
                    orientation="h",
                    color="segment",
                    color_discrete_map=segment_palette,
                    text="monetary_pct",
                    labels={"total_monetary": "Total Pendapatan (BRL)", "segment": "Segmen"}
                )
                fig_rfm_mon.update_traces(
                    texttemplate="%{text:.1f}%",
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>Revenue: R$ %{x:,.2f} (%{text:.2f}%)<extra></extra>"
                )
                fig_rfm_mon.update_layout(showlegend=False)
                apply_plot_theme(fig_rfm_mon, title="Kontribusi Total Pendapatan per Segmen (BRL)", x_title="Total Pendapatan (BRL)")
                st.plotly_chart(fig_rfm_mon, use_container_width=True)

        with tab_rfm_profile:
            st.markdown("##### 🔍 Profil Metrik Rata-rata (Recency, Frequency, Monetary) Antar Segmen")
            p_c1, p_c2, p_c3 = st.columns(3)

            with p_c1:
                fig_r = px.bar(
                    rfm_summary,
                    x="segment",
                    y="avg_recency",
                    color="segment",
                    color_discrete_map=segment_palette,
                    labels={"avg_recency": "Recency (Hari)", "segment": ""}
                )
                fig_r.update_traces(
                    texttemplate="%{y:.0f}h",
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>Avg Recency: %{y:.0f} hari<extra></extra>"
                )
                fig_r.update_layout(showlegend=False)
                apply_plot_theme(fig_r, title="Rata-rata Recency (Hari)", y_title="Hari")
                fig_r.update_xaxes(tickangle=45)
                st.plotly_chart(fig_r, use_container_width=True)

            with p_c2:
                fig_f = px.bar(
                    rfm_summary,
                    x="segment",
                    y="avg_frequency",
                    color="segment",
                    color_discrete_map=segment_palette,
                    labels={"avg_frequency": "Frekuensi (Order)", "segment": ""}
                )
                fig_f.update_traces(
                    texttemplate="%{y:.2f}",
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>Avg Frequency: %{y:.2f} orders<extra></extra>"
                )
                fig_f.update_layout(showlegend=False)
                apply_plot_theme(fig_f, title="Rata-rata Frekuensi (Pesanan)", y_title="Pesanan Unik")
                fig_f.update_xaxes(tickangle=45)
                st.plotly_chart(fig_f, use_container_width=True)

            with p_c3:
                fig_m = px.bar(
                    rfm_summary,
                    x="segment",
                    y="avg_monetary",
                    color="segment",
                    color_discrete_map=segment_palette,
                    labels={"avg_monetary": "Monetary (BRL)", "segment": ""}
                )
                fig_m.update_traces(
                    texttemplate="R$ %{y:.0f}",
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>Avg Monetary: R$ %{y:,.2f}<extra></extra>"
                )
                fig_m.update_layout(showlegend=False)
                apply_plot_theme(fig_m, title="Rata-rata Nilai Belanja (BRL)", y_title="R$ (BRL)")
                fig_m.update_xaxes(tickangle=45)
                st.plotly_chart(fig_m, use_container_width=True)

        with tab_rfm_playbook:
            st.markdown("##### 📋 Matriks Rincian Segmen & Strategic Playbook Eksekutif")

            if selected_rfm_segment != "Semua Segmen":
                display_summary = rfm_summary[rfm_summary["segment"] == selected_rfm_segment].copy()
                st.info(f"🎯 Menampilkan fokus analisis untuk segmen terpilih: **{selected_rfm_segment}**")
            else:
                display_summary = rfm_summary.copy()

            formatted_summary = display_summary.copy()
            formatted_summary["customer_count_fmt"] = formatted_summary["customer_count"].apply(fmt_id)
            formatted_summary["customer_pct_fmt"] = formatted_summary["customer_pct"].apply(lambda x: f"{x:.2f}%")
            formatted_summary["avg_recency_fmt"] = formatted_summary["avg_recency"].apply(lambda x: f"{x:.0f} hari")
            formatted_summary["avg_frequency_fmt"] = formatted_summary["avg_frequency"].apply(lambda x: f"{x:.2f}")
            formatted_summary["avg_monetary_fmt"] = formatted_summary["avg_monetary"].apply(lambda x: fmt_id(x, is_currency=True))
            formatted_summary["total_monetary_fmt"] = formatted_summary["total_monetary"].apply(lambda x: fmt_id(x, is_currency=True))

            display_cols = {
                "segment": "Segmen Perilaku",
                "customer_count_fmt": "Total Pelanggan",
                "customer_pct_fmt": "% Basis Pelanggan",
                "avg_recency_fmt": "Rata-rata Recency",
                "avg_frequency_fmt": "Rata-rata Frekuensi",
                "avg_monetary_fmt": "Rata-rata Belanja",
                "total_monetary_fmt": "Total Kontribusi Omset",
                "action_plan": "Strategic Action Playbook"
            }

            st.dataframe(
                formatted_summary[list(display_cols.keys())].rename(columns=display_cols),
                use_container_width=True,
                hide_index=True
            )

            # 4 Strategic Playbook Cards
            st.markdown("""
            <div class="playbook-grid">
                <div class="playbook-card potential">
                    <div class="playbook-header">
                        <span class="playbook-title">🚀 Potential Loyalists</span>
                        <span class="playbook-share">28,3% Omset</span>
                    </div>
                    <div class="playbook-desc">
                        14.454 pembeli baru (R≥4) dengan keranjang belanja bernilai tinggi (M≥4). Memiliki potensi terbesar untuk dikonversi menjadi pelanggan berulang.
                    </div>
                    <div class="playbook-action">
                        <b>Aksi Taktis:</b> Kirim voucher diskon pesanan kedua dalam 30 hari + rekomendasi produk komplementer.
                    </div>
                </div>
                <div class="playbook-card atrisk">
                    <div class="playbook-header">
                        <span class="playbook-title">⚠️ At Risk Customers</span>
                        <span class="playbook-share">29,3% Omset</span>
                    </div>
                    <div class="playbook-desc">
                        14.723 pembeli bernilai tinggi di masa lalu yang sudah tidak aktif (>1 tahun). Kehilangan segmen ini mengancam sepertiga omset historis.
                    </div>
                    <div class="playbook-action">
                        <b>Aksi Taktis:</b> Luncurkan kampanye win-back bernilai tinggi, survei kendala layanan, dan gratis ongkir khusus.
                    </div>
                </div>
                <div class="playbook-card champions">
                    <div class="playbook-header">
                        <span class="playbook-title">🏆 Champions & Loyal</span>
                        <span class="playbook-share">3,7% Omset</span>
                    </div>
                    <div class="playbook-desc">
                        1.813 pelanggan loyal yang bertransaksi berulang (F≥2) dan konsisten aktif. Merupakan advokat merek terbaik di platform.
                    </div>
                    <div class="playbook-action">
                        <b>Aksi Taktis:</b> Berikan program referral berhadiah, layanan VIP prioritas, dan early access produk eksklusif.
                    </div>
                </div>
                <div class="playbook-card attention">
                    <div class="playbook-header">
                        <span class="playbook-title">🔔 Need Attention & Hibernating</span>
                        <span class="playbook-share">28,4% Omset</span>
                    </div>
                    <div class="playbook-desc">
                        40.598 pembeli yang mulai menjauh atau dorman dengan keranjang belanja standar. Perlu pendekatan berbiaya rendah.
                    </div>
                    <div class="playbook-action">
                        <b>Aksi Taktis:</b> Gunakan automated email newsletters berkala bertarget kategori minat awal; hindari retargeting iklan mahal.
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with tab_rfm_lookup:
            st.markdown("##### 🔍 Eksplorasi Pelanggan Granular & Ekspor CRM (93.358 Pelanggan Unik)")
            rfm_granular = load_rfm_granular()
            
            if not rfm_granular.empty:
                col_srch1, col_srch2 = st.columns([2, 1])
                with col_srch1:
                    search_id = st.text_input("Ketik Customer Unique ID (atau sebagian ID):", placeholder="Contoh: 0000366f3b9a7992bf8c76cfdf3221e2")
                with col_srch2:
                    filter_sample_seg = st.selectbox(
                        "Filter Sampel Segmen:",
                        options=["Semua"] + list(rfm_summary["segment"].unique()),
                        index=0,
                        key="drilldown_seg_select"
                    )

                filtered_drilldown = rfm_granular
                if search_id.strip():
                    filtered_drilldown = filtered_drilldown[filtered_drilldown["customer_unique_id"].str.contains(search_id.strip(), case=False, na=False)]
                elif filter_sample_seg != "Semua":
                    filtered_drilldown = filtered_drilldown[filtered_drilldown["segment"] == filter_sample_seg]

                st.write(f"Menampilkan **{min(15, len(filtered_drilldown))}** sampel dari **{len(filtered_drilldown):,}** pelanggan terfilter:")
                
                show_df = filtered_drilldown.head(15).copy()
                show_df["monetary_fmt"] = show_df["monetary"].apply(lambda x: fmt_id(x, is_currency=True))
                show_df["recency_fmt"] = show_df["recency"].apply(lambda x: f"{x} hari")
                
                rename_dict = {
                    "customer_unique_id": "Customer Unique ID",
                    "recency_fmt": "Recency",
                    "frequency": "Frequency",
                    "monetary_fmt": "Total Belanja",
                    "r_score": "R Score (1-5)",
                    "f_score": "F Score (1-5)",
                    "m_score": "M Score (1-5)",
                    "rfm_score": "RFM Code",
                    "segment": "Segmen"
                }
                st.dataframe(show_df[list(rename_dict.keys())].rename(columns=rename_dict), use_container_width=True, hide_index=True)

                # Download CRM segment target list
                download_sample = filtered_drilldown.head(5000).to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Unduh Daftar Target CRM ({min(5000, len(filtered_drilldown)):,} Baris CSV)",
                    data=download_sample,
                    file_name=f"crm_segment_target_{filter_sample_seg.lower().replace(' ', '_')}.csv",
                    mime="text/csv",
                    key="dl_crm_csv"
                )
            else:
                st.info("ℹ️ File granular `rfm_data.csv` tidak ditemukan di direktori dashboard.")

        st.markdown("""
        <div class="insight-card">
            <div class="insight-card-title">💡 Strategic North Star: Konsentrasi Omset 57,6%</div>
            <div class="insight-card-body">
                Dua segmen terpenting yang mengendalikan lebih dari <b>57,6% total omset marketplace</b> adalah:
                <ul>
                    <li><span class="badge badge-potential">Potential Loyalists (28,3%)</span>: 14.454 pembeli baru dengan keranjang belanja besar. Prioritas aksi: Kirimkan <i>voucher diskon pembelian kedua</i> yang berlaku 30 hari untuk memicu repeat purchase sebelum mereka masuk fase dorman.</li>
                    <li><span class="badge badge-atrisk">At Risk (29,3%)</span>: 14.723 pembeli belanja besar di masa lalu yang sudah tidak aktif (>1 tahun). Prioritas aksi: Luncurkan kampanye <i>win-back</i> agresif berinsentif tinggi demi melindungi sepertiga basis pendapatan historis.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ----------------------------------------------------------
# FOOTER & CREDITS
# ----------------------------------------------------------
st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.85rem; padding: 1rem 0;">
    <b>E-Commerce Customer Segmentation & RFM Analytics Dashboard</b> • Olist Public Marketplace Analysis<br/>
    Developed with Clean Architecture & Spec-Driven Development by <b>Ilfa Antaries Yusuf Wijaya</b> | 
    <a href="mailto:contact.areswijaya@gmail.com" style="color: #3B82F6; text-decoration: none;">contact.areswijaya@gmail.com</a>
</div>
""", unsafe_allow_html=True)
