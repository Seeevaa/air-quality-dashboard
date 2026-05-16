import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# ── PAGE CONFIG ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Beijing Air Quality Dashboard",
    page_icon="🌍",
    layout="wide"
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        .section-title {
            font-size: 18px;
            font-weight: 700;
            color: #1a1a2e;
            border-left: 4px solid #2196F3;
            padding-left: 10px;
            margin-bottom: 4px;
        }
        .section-desc {
            font-size: 13px;
            color: #555;
            margin-bottom: 16px;
            padding-left: 14px;
        }
        .insight-box {
            background-color: #f0f7ff;
            border-left: 4px solid #2196F3;
            padding: 12px 16px;
            border-radius: 4px;
            font-size: 13px;
            color: #1a1a2e;
            margin-top: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# ── COLOR PALETTE ─────────────────────────────────────────────────────────
PRIMARY   = "#2196F3"
HIGHLIGHT = "#D32F2F"
GOOD      = "#4CAF50"
CATEGORY_COLORS = {
    'Good':          '#4CAF50',
    'Moderate':      '#FFC107',
    'Unhealthy':     '#FF9800',
    'Very Unhealthy':'#F44336',
    'Hazardous':     '#9C27B0'
}
CATEGORY_FOLIUM = {
    'Good': 'green', 'Moderate': 'blue',
    'Unhealthy': 'orange', 'Very Unhealthy': 'red', 'Hazardous': 'darkred'
}
CATEGORY_ORDER = ['Good', 'Moderate', 'Unhealthy', 'Very Unhealthy', 'Hazardous']

STATION_COORDS = {
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

MONTH_NAMES = {
    1:'January', 2:'February', 3:'March', 4:'April',
    5:'May', 6:'June', 7:'July', 8:'August',
    9:'September', 10:'October', 11:'November', 12:'December'
}

# ── HELPERS ───────────────────────────────────────────────────────────────
def categorize_pm25(v):
    if v <= 35:   return 'Good'
    elif v <= 75: return 'Moderate'
    elif v <= 115:return 'Unhealthy'
    elif v <= 150:return 'Very Unhealthy'
    else:         return 'Hazardous'

# Radius dampak berdasarkan kategori (meter)
RADIUS_MAP = {
    'Good': 3000, 'Moderate': 5000,
    'Unhealthy': 8000, 'Very Unhealthy': 12000, 'Hazardous': 16000
}
RADIUS_OPACITY = {
    'Good': 0.08, 'Moderate': 0.10,
    'Unhealthy': 0.13, 'Very Unhealthy': 0.16, 'Hazardous': 0.20
}

# ── LOAD DATA ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    url = "https://drive.google.com/uc?id=1W5iLYgGPHQ-bwDp2gyc2TnFoaB-eAFa1"
    df = pd.read_csv(url)
    df['datetime'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
    df['pm25_category'] = df['PM2.5'].apply(categorize_pm25)
    return df

main_df = load_data()

# ── SIDEBAR ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Beijing Air Quality")
    st.caption("PRSA Dataset — 2013 to 2017")
    st.markdown("---")

    st.markdown("**Date Range**")
    min_date = main_df['datetime'].min().date()
    max_date = main_df['datetime'].max().date()
    start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
    end_date   = st.date_input("End Date",   value=max_date, min_value=min_date, max_value=max_date)

    if start_date > end_date:
        st.warning("Start date cannot be later than end date.")
        st.stop()

    st.markdown("**Station**")
    locations = ['All Stations'] + sorted(main_df['location'].unique().tolist())
    selected_location = st.selectbox("Select Station", locations, label_visibility='collapsed')

    st.markdown("**Pollutant**")
    pollutant = st.radio("Select Pollutant", ['PM2.5','PM10','SO2','NO2','CO','O3'],
                         index=0, label_visibility='collapsed')

    st.markdown("---")
    st.caption("Built with Streamlit · PRSA Beijing")

# ── FILTER ────────────────────────────────────────────────────────────────
try:
    filtered_df = main_df[
        (main_df['datetime'].dt.date >= start_date) &
        (main_df['datetime'].dt.date <= end_date)
    ].copy()
    if selected_location != 'All Stations':
        filtered_df = filtered_df[filtered_df['location'] == selected_location]
    if filtered_df.empty:
        st.warning("No data available for the selected filters. Please adjust the date range.")
        st.stop()
except Exception as e:
    st.error(f"Filter error: {e}")
    st.stop()

# ── HEADER ────────────────────────────────────────────────────────────────
st.title("Beijing Air Quality Analysis")
st.markdown(
    f"Analyzing **{pollutant}** concentration across 12 monitoring stations in Beijing "
    f"from **{start_date.strftime('%d %b %Y')}** to **{end_date.strftime('%d %b %Y')}**."
)
st.markdown("---")

# ── METRICS ───────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Average " + pollutant,  f"{filtered_df[pollutant].mean():.1f} µg/m³")
c2.metric("Peak " + pollutant,     f"{filtered_df[pollutant].max():.1f} µg/m³")
c3.metric("Minimum " + pollutant,  f"{filtered_df[pollutant].min():.1f} µg/m³")
c4.metric("Data Points",           f"{len(filtered_df):,}")
st.markdown("---")

# ── SECTION 1: SEASONAL TREND ─────────────────────────────────────────────
st.markdown('<div class="section-title">Seasonal Trend Analysis</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">Monthly average concentration to identify recurring seasonal patterns across years.</div>',
    unsafe_allow_html=True
)

tab1, tab2 = st.tabs(["Year-over-Year", "Monthly Average"])

with tab1:
    yearly_data = []
    for year in sorted(filtered_df['year'].unique()):
        df_y = filtered_df[filtered_df['year'] == year].groupby('month')[pollutant].mean().reset_index()
        df_y['Year'] = str(year)
        yearly_data.append(df_y)
    if yearly_data:
        df_plot = pd.concat(yearly_data)
        fig = px.line(df_plot, x='month', y=pollutant, color='Year', markers=True,
                      labels={'month':'Month', pollutant:f'{pollutant} (µg/m³)'})
        fig.update_layout(
            xaxis=dict(tickmode='array', tickvals=list(range(1,13)),
                       ticktext=list(MONTH_NAMES.values())),
            yaxis=dict(rangemode='tozero'),
            hovermode='x unified', height=400
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    seasonal = filtered_df.groupby('month')[pollutant].mean().reset_index()
    max_m = seasonal.loc[seasonal[pollutant].idxmax(), 'month']
    min_m = seasonal.loc[seasonal[pollutant].idxmin(), 'month']
    colors = [HIGHLIGHT if m == max_m else (GOOD if m == min_m else PRIMARY) for m in seasonal['month']]

    fig = go.Figure(go.Bar(
        x=seasonal['month'], y=seasonal[pollutant],
        marker_color=colors,
        text=seasonal[pollutant].round(1), textposition='outside'
    ))
    fig.update_layout(
        xaxis=dict(tickmode='array', tickvals=list(range(1,13)),
                   ticktext=list(MONTH_NAMES.values()), title='Month'),
        yaxis=dict(rangemode='tozero', title=f'{pollutant} (µg/m³)'),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        f'<div class="insight-box">Peak concentration occurs in <b>{MONTH_NAMES[max_m]}</b> '
        f'({seasonal.loc[seasonal["month"]==max_m, pollutant].values[0]:.1f} µg/m³), '
        f'while the lowest is in <b>{MONTH_NAMES[min_m]}</b> '
        f'({seasonal.loc[seasonal["month"]==min_m, pollutant].values[0]:.1f} µg/m³). '
        f'This consistent pattern suggests a strong seasonal influence driven by winter heating and atmospheric stability.</div>',
        unsafe_allow_html=True
    )

st.markdown("---")

# ── SECTION 2: STATION COMPARISON ────────────────────────────────────────
st.markdown('<div class="section-title">Station-level Concentration Comparison</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">Average pollutant concentration per monitoring station to identify high-risk areas.</div>',
    unsafe_allow_html=True
)

loc_df = filtered_df.groupby('location')[pollutant].mean().sort_values(ascending=True).reset_index()
n = len(loc_df)
colors = [HIGHLIGHT if i == n-1 else (GOOD if i == 0 else PRIMARY) for i in range(n)]

fig = go.Figure(go.Bar(
    x=loc_df[pollutant], y=loc_df['location'],
    orientation='h', marker_color=colors,
    text=loc_df[pollutant].round(1), textposition='outside'
))
fig.update_layout(
    xaxis=dict(rangemode='tozero', title=f'{pollutant} (µg/m³)'),
    yaxis=dict(title=None), height=420
)
st.plotly_chart(fig, use_container_width=True)

worst = loc_df.iloc[-1]
best  = loc_df.iloc[0]
st.markdown(
    f'<div class="insight-box">'
    f'<b>{worst["location"]}</b> records the highest average {pollutant} at <b>{worst[pollutant]:.1f} µg/m³</b>, '
    f'while <b>{best["location"]}</b> records the lowest at <b>{best[pollutant]:.1f} µg/m³</b> '
    f'— a difference of <b>{worst[pollutant]-best[pollutant]:.1f} µg/m³</b>. '
    f'Urban-center stations consistently show higher pollution levels than suburban stations.</div>',
    unsafe_allow_html=True
)

with st.expander("View detailed station statistics"):
    tbl = filtered_df.groupby('location')[pollutant].agg(['mean','max','min','std']).round(2)
    tbl.columns = ['Mean','Max','Min','Std Dev']
    tbl = tbl.sort_values('Mean', ascending=False)
    st.dataframe(tbl, use_container_width=True)

st.markdown("---")

# ── SECTION 3: DIURNAL PATTERN ────────────────────────────────────────────
st.markdown('<div class="section-title">Diurnal Pollution Pattern</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">Hourly average concentration throughout the day to identify peak pollution hours.</div>',
    unsafe_allow_html=True
)

hourly = filtered_df.groupby('hour')[pollutant].mean().reset_index()
hourly.columns = ['hour', 'value']
peak_h = hourly.loc[hourly['value'].idxmax(), 'hour']
low_h  = hourly.loc[hourly['value'].idxmin(), 'hour']
colors = [HIGHLIGHT if h == peak_h else (GOOD if h == low_h else PRIMARY) for h in hourly['hour']]

fig = go.Figure(go.Bar(
    x=hourly['hour'], y=hourly['value'],
    marker_color=colors,
    text=hourly['value'].round(1), textposition='outside'
))
fig.update_layout(
    xaxis=dict(tickmode='linear', title='Hour of Day (0–23)'),
    yaxis=dict(rangemode='tozero', title=f'{pollutant} (µg/m³)'),
    height=400
)
st.plotly_chart(fig, use_container_width=True)
st.markdown(
    f'<div class="insight-box">'
    f'Concentration peaks at <b>{peak_h:02d}:00</b> ({hourly.loc[hourly["hour"]==peak_h,"value"].values[0]:.1f} µg/m³) '
    f'and reaches its lowest at <b>{low_h:02d}:00</b> ({hourly.loc[hourly["hour"]==low_h,"value"].values[0]:.1f} µg/m³). '
    f'Elevated nighttime levels are attributed to reduced atmospheric mixing and increased heavy vehicle activity during off-peak traffic hours.</div>',
    unsafe_allow_html=True
)

st.markdown("---")

# ── SECTION 4: WEATHER CORRELATION ───────────────────────────────────────
st.markdown('<div class="section-title">Weather-Pollution Correlation</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">Correlation matrix and PM2.5-specific coefficients to quantify the influence of meteorological factors.</div>',
    unsafe_allow_html=True
)

corr_cols = ['PM2.5','TEMP','PRES','DEWP','RAIN','WSPM']
corr_matrix = filtered_df[corr_cols].corr().round(2)

col_l, col_r = st.columns(2)
with col_l:
    fig = px.imshow(corr_matrix, text_auto=True, color_continuous_scale='RdBu_r',
                    zmin=-1, zmax=1, title='Correlation Matrix')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    pm25_corr = corr_matrix['PM2.5'].drop('PM2.5').sort_values()
    colors = [GOOD if v < 0 else HIGHLIGHT for v in pm25_corr]
    fig = go.Figure(go.Bar(
        x=pm25_corr.values, y=pm25_corr.index,
        orientation='h', marker_color=colors,
        text=pm25_corr.round(3), textposition='outside'
    ))
    fig.update_layout(
        title='Correlation with PM2.5',
        xaxis=dict(title='Correlation Coefficient', zeroline=True, zerolinecolor='black'),
        yaxis=dict(title=None), height=400
    )
    st.plotly_chart(fig, use_container_width=True)

strongest = pm25_corr.abs().idxmax()
st.markdown(
    f'<div class="insight-box">'
    f'<b>{strongest}</b> shows the strongest correlation with PM2.5 '
    f'(r = {pm25_corr[strongest]:.3f}). '
    f'Wind speed (WSPM) has a negative correlation, meaning higher wind speed effectively disperses pollutants. '
    f'Dew point (DEWP) shows a positive correlation, indicating humid conditions tend to trap pollutants near the surface.</div>',
    unsafe_allow_html=True
)

st.markdown("---")

# ── SECTION 5: AQI CLUSTERING ─────────────────────────────────────────────
st.markdown('<div class="section-title">Air Quality Index Clustering</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">'
    'Manual grouping of PM2.5 readings into AQI categories based on China National Ambient Air Quality Standards (GB 3095-2012). '
    'This segmentation helps quantify the proportion of time each station operates under hazardous conditions.'
    '</div>',
    unsafe_allow_html=True
)

col5a, col5b = st.columns(2)
cat_counts = filtered_df['pm25_category'].value_counts().reindex(CATEGORY_ORDER).fillna(0).reset_index()
cat_counts.columns = ['Category', 'Count']

with col5a:
    fig = px.bar(cat_counts, x='Category', y='Count',
                 color='Category', color_discrete_map=CATEGORY_COLORS,
                 text='Count', category_orders={'Category': CATEGORY_ORDER},
                 title='Distribution of AQI Categories')
    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig.update_layout(showlegend=False, yaxis=dict(rangemode='tozero'), height=380)
    st.plotly_chart(fig, use_container_width=True)

with col5b:
    fig = px.pie(cat_counts, values='Count', names='Category',
                 color='Category', color_discrete_map=CATEGORY_COLORS,
                 category_orders={'Category': CATEGORY_ORDER},
                 title='AQI Category Proportion')
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

unhealthy_pct = cat_counts[cat_counts['Category'].isin(['Unhealthy','Very Unhealthy','Hazardous'])]['Count'].sum()
total = cat_counts['Count'].sum()
st.markdown(
    f'<div class="insight-box">'
    f'<b>{unhealthy_pct/total*100:.1f}%</b> of all hourly readings fall under Unhealthy or worse categories. '
    f'Only <b>{cat_counts.loc[cat_counts["Category"]=="Good","Count"].values[0]/total*100:.1f}%</b> '
    f'of readings meet the Good air quality threshold (PM2.5 ≤ 35 µg/m³).</div>',
    unsafe_allow_html=True
)

with st.expander("View category breakdown by station"):
    cat_st = filtered_df.groupby(['location','pm25_category']).size().unstack(fill_value=0)
    cat_st = cat_st.reindex(columns=CATEGORY_ORDER, fill_value=0)
    st.dataframe(cat_st, use_container_width=True)

st.markdown("---")

# ── SECTION 6: GEOSPATIAL ─────────────────────────────────────────────────
st.markdown('<div class="section-title">Geospatial Pollution Impact Radius</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">'
    'Each station is visualized with an impact radius proportional to its pollution severity, '
    'based on estimated atmospheric dispersion under typical Beijing wind conditions. '
    'Larger and darker circles indicate a wider area potentially affected by poor air quality. '
    'This analysis helps identify geographic zones requiring priority intervention.'
    '</div>',
    unsafe_allow_html=True
)

station_df = filtered_df.groupby('location')['PM2.5'].mean().reset_index()
station_df.columns = ['location', 'PM2.5_mean']
station_df['lat']           = station_df['location'].map(lambda x: STATION_COORDS.get(x,(0,0))[0])
station_df['lon']           = station_df['location'].map(lambda x: STATION_COORDS.get(x,(0,0))[1])
station_df['pm25_category'] = station_df['PM2.5_mean'].apply(categorize_pm25)
station_df['radius']        = station_df['pm25_category'].map(RADIUS_MAP)
station_df['opacity']       = station_df['pm25_category'].map(RADIUS_OPACITY)
station_df = station_df.round(2)

m = folium.Map(location=[39.95, 116.38], zoom_start=10, tiles='CartoDB positron')

for _, row in station_df.iterrows():
    color = CATEGORY_FOLIUM[row['pm25_category']]

    # Impact radius circle
    folium.Circle(
        location=[row['lat'], row['lon']],
        radius=row['radius'],
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=row['opacity'],
        weight=1
    ).add_to(m)

    # Station marker
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=8,
        color='white',
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        weight=2,
        popup=folium.Popup(
            f"<b>{row['location']}</b><br>"
            f"PM2.5: {row['PM2.5_mean']} µg/m³<br>"
            f"Category: {row['pm25_category']}<br>"
            f"Est. Impact Radius: {row['radius']//1000} km",
            max_width=220
        ),
        tooltip=f"{row['location']} — {row['pm25_category']} ({row['PM2.5_mean']} µg/m³)"
    ).add_to(m)

# Legend
legend_html = """
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
     background: white; padding: 12px 16px; border-radius: 8px;
     box-shadow: 0 2px 8px rgba(0,0,0,0.2); font-size: 13px;">
  <b>AQI Category</b><br>
  <span style="color:green">●</span> Good (≤35 µg/m³)<br>
  <span style="color:blue">●</span> Moderate (36–75 µg/m³)<br>
  <span style="color:orange">●</span> Unhealthy (76–115 µg/m³)<br>
  <span style="color:red">●</span> Very Unhealthy (116–150 µg/m³)<br>
  <span style="color:darkred">●</span> Hazardous (>150 µg/m³)
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=1200, height=520)

# Impact radius table
with st.expander("View station impact radius details"):
    tbl = station_df[['location','PM2.5_mean','pm25_category','radius']].copy()
    tbl['radius'] = tbl['radius'].apply(lambda x: f"{x//1000} km")
    tbl.columns = ['Station','Avg PM2.5 (µg/m³)','AQI Category','Est. Impact Radius']
    tbl = tbl.sort_values('Avg PM2.5 (µg/m³)', ascending=False)
    st.dataframe(tbl, use_container_width=True)

st.markdown("---")
st.caption("Beijing Air Quality Dashboard · Data source: PRSA Dataset (2013–2017) · Built with Streamlit")