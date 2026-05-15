import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np

# ── PAGE CONFIG ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Air Quality Dashboard - Beijing",
    page_icon="🌫️",
    layout="wide"
)

# ── CUSTOM CSS ───────────────────────────────────────────────────────────
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            text-align: center;
        }
        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 4px;
        }
        .section-desc {
            font-size: 13px;
            color: #7f8c8d;
            margin-bottom: 16px;
        }
    </style>
""", unsafe_allow_html=True)

# ── LOAD DATA ────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    url = "https://drive.google.com/uc?id=1W5iLYgGPHQ-bwDp2gyc2TnFoaB-eAFa1"
    df = pd.read_csv(url)
    df['datetime'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
    return df

main_df = load_data()

# ── SIDEBAR ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌫️ Air Quality")
    st.markdown("**Dataset:** PRSA Beijing 2013–2017")
    st.markdown("---")

    st.markdown("### 🔍 Filter Data")

    # Filter Stasiun
    locations = ['Semua Stasiun'] + sorted(main_df['location'].unique().tolist())
    selected_location = st.selectbox("📍 Pilih Stasiun", locations)

    # Filter Tahun
    years = ['Semua Tahun'] + sorted(main_df['year'].unique().tolist())
    selected_year = st.selectbox("📅 Pilih Tahun", years)

    # Filter Bulan
    month_names = {
        1:'Januari', 2:'Februari', 3:'Maret', 4:'April',
        5:'Mei', 6:'Juni', 7:'Juli', 8:'Agustus',
        9:'September', 10:'Oktober', 11:'November', 12:'Desember'
    }
    months = ['Semua Bulan'] + [month_names[m] for m in range(1, 13)]
    selected_month = st.selectbox("🗓️ Pilih Bulan", months)

    st.markdown("---")

    # Filter Polutan
    st.markdown("### 🧪 Pilih Polutan")
    pollutant = st.radio(
        "Polutan yang ditampilkan:",
        ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3'],
        index=0
    )

    st.markdown("---")
    st.caption("Dashboard Analisis Kualitas Udara Beijing")

# ── APPLY FILTER ─────────────────────────────────────────────────────────
filtered_df = main_df.copy()
if selected_location != 'Semua Stasiun':
    filtered_df = filtered_df[filtered_df['location'] == selected_location]
if selected_year != 'Semua Tahun':
    filtered_df = filtered_df[filtered_df['year'] == int(selected_year)]
if selected_month != 'Semua Bulan':
    month_num = {v: k for k, v in month_names.items()}[selected_month]
    filtered_df = filtered_df[filtered_df['month'] == month_num]

# ── HEADER ───────────────────────────────────────────────────────────────
st.title("🌫️ Dashboard Kualitas Udara Beijing (2013–2017)")
st.markdown("Analisis interaktif konsentrasi polutan udara di 12 stasiun pemantauan Beijing.")
st.markdown("---")

# ── METRICS ──────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric(
    label=f"📊 Rata-rata {pollutant}",
    value=f"{filtered_df[pollutant].mean():.1f} µg/m³"
)
col2.metric(
    label=f"📈 {pollutant} Tertinggi",
    value=f"{filtered_df[pollutant].max():.1f} µg/m³"
)
col3.metric(
    label=f"📉 {pollutant} Terendah",
    value=f"{filtered_df[pollutant].min():.1f} µg/m³"
)
col4.metric(
    label="🗃️ Total Data",
    value=f"{len(filtered_df):,} baris"
)

st.markdown("---")

# ── VISUALISASI 1: TREN BULANAN ───────────────────────────────────────────
st.markdown(f'<div class="section-title">📈 Pertanyaan 1: Tren {pollutant} per Bulan</div>', unsafe_allow_html=True)
st.markdown('<div class="section-desc">Bagaimana tren rata-rata konsentrasi polutan secara bulanan dan apakah terdapat pola musiman?</div>', unsafe_allow_html=True)

tab1a, tab1b = st.tabs(["📊 Per Tahun", "📊 Agregat"])

with tab1a:
    fig1, ax1 = plt.subplots(figsize=(14, 5))
    colors_year = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    for i, year in enumerate(sorted(filtered_df['year'].unique())):
        df_year = filtered_df[filtered_df['year'] == year].groupby('month')[pollutant].mean()
        ax1.plot(df_year.index, df_year.values, marker='o', label=str(year),
                color=colors_year[i % len(colors_year)], linewidth=2)
    ax1.set_title(f'Tren Rata-rata {pollutant} per Bulan per Tahun', fontsize=15, pad=15)
    ax1.set_xlabel('Bulan', fontsize=12)
    ax1.set_ylabel(f'{pollutant} (µg/m³)', fontsize=12)
    ax1.set_xticks(range(1, 13))
    ax1.set_xticklabels(['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'])
    ax1.set_ylim(bottom=0)
    ax1.legend(title='Tahun', bbox_to_anchor=(1.01, 1), loc='upper left')
    ax1.grid(axis='y', alpha=0.3)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig1)

with tab1b:
    seasonal = filtered_df.groupby('month')[pollutant].mean().reset_index()
    fig1b, ax1b = plt.subplots(figsize=(14, 5))
    bar_colors = ['#2196F3' if v == seasonal[pollutant].max() else
                  ('#4CAF50' if v == seasonal[pollutant].min() else '#CFD8DC')
                  for v in seasonal[pollutant]]
    bars = ax1b.bar(seasonal['month'], seasonal[pollutant], color=bar_colors, width=0.6)
    for bar, val in zip(bars, seasonal[pollutant]):
        ax1b.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                 f'{val:.1f}', ha='center', va='bottom', fontsize=9)
    ax1b.set_title(f'Rata-rata {pollutant} per Bulan (Agregat)', fontsize=15, pad=15)
    ax1b.set_xlabel('Bulan', fontsize=12)
    ax1b.set_ylabel(f'{pollutant} (µg/m³)', fontsize=12)
    ax1b.set_xticks(range(1, 13))
    ax1b.set_xticklabels(['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'])
    ax1b.set_ylim(bottom=0)
    ax1b.grid(axis='y', alpha=0.3)
    ax1b.spines['top'].set_visible(False)
    ax1b.spines['right'].set_visible(False)
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='#2196F3', label='Tertinggi'),
                       Patch(facecolor='#4CAF50', label='Terendah'),
                       Patch(facecolor='#CFD8DC', label='Lainnya')]
    ax1b.legend(handles=legend_elements, loc='upper right')
    plt.tight_layout()
    st.pyplot(fig1b)

# Tabel ringkasan
with st.expander("📋 Lihat Tabel Ringkasan Bulanan"):
    summary1 = filtered_df.groupby('month')[pollutant].agg(['mean', 'max', 'min']).round(2)
    summary1.index = [month_names[m] for m in summary1.index]
    summary1.columns = ['Rata-rata', 'Tertinggi', 'Terendah']
    st.dataframe(summary1, use_container_width=True)

st.markdown("---")

# ── VISUALISASI 2: PERBANDINGAN STASIUN ──────────────────────────────────
st.markdown(f'<div class="section-title">📍 Pertanyaan 2: Perbandingan {pollutant} antar Stasiun</div>', unsafe_allow_html=True)
st.markdown('<div class="section-desc">Stasiun mana yang mencatat konsentrasi tertinggi dan terendah?</div>', unsafe_allow_html=True)

location_poll = filtered_df.groupby('location')[pollutant].mean().sort_values(ascending=False).reset_index()
n = len(location_poll)
colors_loc = ['#D32F2F' if i == 0 else ('#388E3C' if i == n-1 else '#90A4AE') for i in range(n)]

fig2, ax2 = plt.subplots(figsize=(12, 6))
bars2 = ax2.barh(location_poll['location'], location_poll[pollutant], color=colors_loc, height=0.6)
ax2.invert_yaxis()
ax2.set_title(f'Rata-rata Konsentrasi {pollutant} per Stasiun', fontsize=15, pad=15)
ax2.set_xlabel(f'{pollutant} (µg/m³)', fontsize=12)
ax2.set_xlim(left=0)
for bar, val in zip(bars2, location_poll[pollutant]):
    ax2.text(val + 0.3, bar.get_y() + bar.get_height()/2,
             f'{val:.1f}', va='center', fontsize=10)
ax2.grid(axis='x', alpha=0.3)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
from matplotlib.patches import Patch
legend2 = [Patch(facecolor='#D32F2F', label='Tertinggi'),
           Patch(facecolor='#388E3C', label='Terendah'),
           Patch(facecolor='#90A4AE', label='Lainnya')]
ax2.legend(handles=legend2, loc='lower right')
plt.tight_layout()
st.pyplot(fig2)

with st.expander("📋 Lihat Tabel Perbandingan Stasiun"):
    summary2 = filtered_df.groupby('location')[pollutant].agg(['mean', 'max', 'min']).round(2)
    summary2.columns = ['Rata-rata', 'Tertinggi', 'Terendah']
    summary2 = summary2.sort_values('Rata-rata', ascending=False)
    st.dataframe(summary2, use_container_width=True)

st.markdown("---")

# ── VISUALISASI 3: PM2.5 PER JAM ─────────────────────────────────────────
st.markdown(f'<div class="section-title">🕐 Pertanyaan 3: Pola {pollutant} per Jam dalam Sehari</div>', unsafe_allow_html=True)
st.markdown('<div class="section-desc">Pada jam berapa konsentrasi polutan mencapai puncaknya?</div>', unsafe_allow_html=True)

hourly = filtered_df.groupby('hour')[pollutant].mean().reset_index()
hourly.columns = ['hour', 'value']
max_val = hourly['value'].max()
min_val = hourly['value'].min()
colors_h = ['#D32F2F' if v == max_val else ('#388E3C' if v == min_val else '#90A4AE')
            for v in hourly['value']]

fig3, ax3 = plt.subplots(figsize=(14, 5))
bars3 = ax3.bar(hourly['hour'], hourly['value'], color=colors_h, width=0.7)
ax3.set_title(f'Rata-rata Konsentrasi {pollutant} per Jam', fontsize=15, pad=15)
ax3.set_xlabel('Jam (0–23)', fontsize=12)
ax3.set_ylabel(f'{pollutant} (µg/m³)', fontsize=12)
ax3.set_xticks(range(0, 24))
ax3.set_ylim(bottom=0)
ax3.grid(axis='y', alpha=0.3)
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)
legend3 = [Patch(facecolor='#D32F2F', label='Jam Puncak'),
           Patch(facecolor='#388E3C', label='Jam Terendah'),
           Patch(facecolor='#90A4AE', label='Lainnya')]
ax3.legend(handles=legend3)

# Annotate puncak
peak_hour = hourly.loc[hourly['value'].idxmax(), 'hour']
peak_val = hourly['value'].max()
ax3.annotate(f'Puncak: Jam {peak_hour}\n{peak_val:.1f} µg/m³',
             xy=(peak_hour, peak_val),
             xytext=(peak_hour + 1.5, peak_val + 2),
             arrowprops=dict(arrowstyle='->', color='#D32F2F'),
             fontsize=10, color='#D32F2F')

plt.tight_layout()
st.pyplot(fig3)

with st.expander("📋 Lihat Tabel per Jam"):
    st.dataframe(hourly.rename(columns={'hour': 'Jam', 'value': f'Rata-rata {pollutant}'}),
                use_container_width=True)

st.markdown("---")

# ── VISUALISASI 4: KORELASI CUACA ────────────────────────────────────────
st.markdown('<div class="section-title">🌤️ Pertanyaan 4: Korelasi Faktor Cuaca dengan PM2.5</div>', unsafe_allow_html=True)
st.markdown('<div class="section-desc">Seberapa kuat hubungan antara faktor cuaca dengan konsentrasi PM2.5?</div>', unsafe_allow_html=True)

corr_cols = ['PM2.5', 'TEMP', 'PRES', 'DEWP', 'RAIN', 'WSPM']
corr_matrix = filtered_df[corr_cols].corr()

col_left, col_right = st.columns(2)

with col_left:
    fig4a, ax4a = plt.subplots(figsize=(7, 6))
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                center=0, linewidths=0.5, ax=ax4a,
                annot_kws={'size': 10})
    ax4a.set_title('Matriks Korelasi Polutan & Cuaca', fontsize=13, pad=15)
    plt.tight_layout()
    st.pyplot(fig4a)

with col_right:
    pm25_corr = corr_matrix['PM2.5'].drop('PM2.5').sort_values()
    bar_colors_c = ['#388E3C' if v < 0 else '#D32F2F' for v in pm25_corr]
    fig4b, ax4b = plt.subplots(figsize=(7, 6))
    bars4 = ax4b.barh(pm25_corr.index, pm25_corr.values, color=bar_colors_c, height=0.5)
    for bar, val in zip(bars4, pm25_corr.values):
        ax4b.text(val + 0.005 if val >= 0 else val - 0.005,
                 bar.get_y() + bar.get_height()/2,
                 f'{val:.3f}', va='center',
                 ha='left' if val >= 0 else 'right', fontsize=10)
    ax4b.axvline(x=0, color='black', linewidth=0.8)
    ax4b.set_title('Korelasi Faktor Cuaca terhadap PM2.5', fontsize=13, pad=15)
    ax4b.set_xlabel('Koefisien Korelasi', fontsize=11)
    ax4b.grid(axis='x', alpha=0.3)
    ax4b.spines['top'].set_visible(False)
    ax4b.spines['right'].set_visible(False)
    legend4 = [Patch(facecolor='#388E3C', label='Korelasi Negatif (menurunkan PM2.5)'),
               Patch(facecolor='#D32F2F', label='Korelasi Positif (menaikkan PM2.5)')]
    ax4b.legend(handles=legend4, loc='lower right', fontsize=9)
    plt.tight_layout()
    st.pyplot(fig4b)

st.markdown("---")

# ── VISUALISASI 5: CLUSTERING ─────────────────────────────────────────────
st.markdown('<div class="section-title">🗂️ Analisis Lanjutan: Clustering Kategori Kualitas Udara</div>', unsafe_allow_html=True)
st.markdown('<div class="section-desc">Distribusi data berdasarkan kategori kualitas udara menggunakan standar AQI China.</div>', unsafe_allow_html=True)

category_order = ['Good', 'Moderate', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
category_colors = ['#4CAF50', '#FFC107', '#FF9800', '#F44336', '#9C27B0']

col5a, col5b = st.columns(2)

with col5a:
    category_counts = filtered_df['pm25_category'].value_counts()
    category_counts = category_counts.reindex(category_order).fillna(0).reset_index()
    category_counts.columns = ['category', 'count']

    fig5a, ax5a = plt.subplots(figsize=(8, 5))
    bars5 = ax5a.bar(category_counts['category'], category_counts['count'],
                    color=category_colors, width=0.6)
    for bar, val in zip(bars5, category_counts['count']):
        ax5a.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
                 f'{int(val):,}', ha='center', fontsize=10)
    ax5a.set_title('Distribusi Kategori Kualitas Udara', fontsize=13, pad=15)
    ax5a.set_xlabel('Kategori', fontsize=11)
    ax5a.set_ylabel('Jumlah Data', fontsize=11)
    ax5a.set_ylim(bottom=0)
    ax5a.grid(axis='y', alpha=0.3)
    ax5a.spines['top'].set_visible(False)
    ax5a.spines['right'].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig5a)

with col5b:
    fig5b, ax5b = plt.subplots(figsize=(7, 5))
    valid_counts = category_counts[category_counts['count'] > 0]
    valid_colors = [category_colors[i] for i, c in enumerate(category_counts['count']) if c > 0]
    wedges, texts, autotexts = ax5b.pie(
        valid_counts['count'],
        labels=valid_counts['category'],
        colors=valid_colors,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.85
    )
    for text in autotexts:
        text.set_fontsize(10)
    ax5b.set_title('Proporsi Kategori Kualitas Udara', fontsize=13, pad=15)
    plt.tight_layout()
    st.pyplot(fig5b)

# Distribusi per stasiun
with st.expander("📋 Lihat Distribusi Kategori per Stasiun"):
    cat_station = filtered_df.groupby(['location', 'pm25_category']).size().unstack(fill_value=0)
    cat_station = cat_station.reindex(columns=category_order, fill_value=0)
    st.dataframe(cat_station, use_container_width=True)

st.markdown("---")
st.caption("Dashboard Kualitas Udara Beijing 2013–2017 | Data: PRSA Dataset")

# ── VISUALISASI 6: GEOSPATIAL ─────────────────────────────────────────────
import folium
from streamlit_folium import st_folium

st.markdown('<div class="section-title">🗺️ Analisis Lanjutan: Geospatial Kualitas Udara per Stasiun</div>', unsafe_allow_html=True)
st.markdown('<div class="section-desc">Distribusi konsentrasi PM2.5 berdasarkan lokasi geografis 12 stasiun pemantauan Beijing.</div>', unsafe_allow_html=True)

station_coords = {
    'Aotizhongxin': (39.9829, 116.3970),
    'Changping':    (40.2149, 116.2310),
    'Dingling':     (40.2900, 116.2200),
    'Dongsi':       (39.9290, 116.4170),
    'Guanyuan':     (39.9290, 116.3390),
    'Gucheng':      (39.9140, 116.1840),
    'Huairou':      (40.3280, 116.6280),
    'Nongzhanguan': (39.9370, 116.4610),
    'Shunyi':       (40.1270, 116.6550),
    'Tiantan':      (39.8860, 116.4070),
    'Wanliu':       (39.9870, 116.2870),
    'Wanshouxigong':(39.8780, 116.3520),
}

def categorize_pm25(value):
    if value <= 35:
        return 'Good'
    elif value <= 75:
        return 'Moderate'
    elif value <= 115:
        return 'Unhealthy'
    elif value <= 150:
        return 'Very Unhealthy'
    else:
        return 'Hazardous'

category_color = {
    'Good': 'green',
    'Moderate': 'blue',
    'Unhealthy': 'orange',
    'Very Unhealthy': 'red',
    'Hazardous': 'darkred'
}

station_df = filtered_df.groupby('location')['PM2.5'].mean().reset_index()
station_df.columns = ['location', 'PM2.5_mean']
station_df['lat'] = station_df['location'].map(lambda x: station_coords.get(x, (0,0))[0])
station_df['lon'] = station_df['location'].map(lambda x: station_coords.get(x, (0,0))[1])
station_df['pm25_category'] = station_df['PM2.5_mean'].apply(categorize_pm25)
station_df = station_df.round(2)

m = folium.Map(location=[39.95, 116.38], zoom_start=11, tiles='CartoDB positron')

for _, row in station_df.iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=15,
        color=category_color[row['pm25_category']],
        fill=True,
        fill_color=category_color[row['pm25_category']],
        fill_opacity=0.7,
        popup=folium.Popup(
            f"""
            <b>{row['location']}</b><br>
            PM2.5: {row['PM2.5_mean']} µg/m³<br>
            Kategori: {row['pm25_category']}
            """,
            max_width=200
        ),
        tooltip=f"{row['location']} - {row['PM2.5_mean']} µg/m³"
    ).add_to(m)

st_folium(m, width=1200, height=500)