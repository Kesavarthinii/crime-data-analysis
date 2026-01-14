import streamlit as st
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# ---------------- PAGE CONFIG & THEME ----------------
st.set_page_config(page_title="Theft Analysis", layout="wide")

st.markdown(
    """
    <style>
        .stApp { background-color: #121212; color: white; }
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        h1, h2, h3, h4 { color: #FFFFFF !important; }
        label, .css-1b7m0tm { color: #FFD700 !important; font-weight:600; }
        .dataframe thead th { color: #FFD700 !important; background-color: #111 !important; }
        .stSelectbox > div { color: #FFD700 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='text-align:center; font-size:2.6rem; margin-bottom:8px; color:white;'>THEFT CASES (2020 - 2022)</h1>",
    unsafe_allow_html=True
)

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("<h3 style='color:#FFD700;'>Data & GeoJSON (optional)</h3>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Upload Theft Excel (.xlsx)", type=["xlsx"])
uploaded_geo = st.sidebar.file_uploader("Upload India GeoJSON (.json/.geojson)", type=["json", "geojson"])

# ---------------- DATA LOADERS ----------------
@st.cache_data
def load_excel(path=None):
    if path is not None:
        df = pd.read_excel(path)
    else:
        df = pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Theft.xlsx")
    # Normalize & ensure columns
    df.columns = [str(c).strip() for c in df.columns]
    # Rename first likely column to 'State/UT' if needed
    state_col = None
    for c in df.columns:
        if c.lower() in ['state', 'state/ut', 'state_ut', 'st_nm', 'state name', 'state/ut name']:
            state_col = c
            break
    if state_col is None:
        state_col = df.columns[0]
    df = df.rename(columns={state_col: 'State/UT'})
    # Ensure year columns exist
    for y in ['2020', '2021', '2022']:
        if y not in df.columns:
            df[y] = 0
    # Clean and coerce
    df['State/UT'] = df['State/UT'].astype(str).str.strip()
    for y in ['2020','2021','2022']:
        df[y] = pd.to_numeric(df[y], errors='coerce').fillna(0).astype(int)
    return df

@st.cache_data
def load_geo(path=None):
    if path is not None:
        try:
            content = path.read()
            if isinstance(content, (bytes, bytearray)):
                content = content.decode('utf-8')
            return json.loads(content)
        except Exception:
            path.seek(0)
            return json.load(path)
    else:
        with open(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\india.geojson", "r", encoding="utf-8") as f:
            return json.load(f)

# Load data and geojson
df = load_excel(uploaded_file)
india_geo = load_geo(uploaded_geo)

# ---------------- UI: Year & Visual Selection (Fixed Order) ----------------
col1, col2 = st.columns([1, 2])
with col1:
    selected_year = st.selectbox("Select Year", [2020, 2021, 2022])
with col2:
    viz_options = [
        "Choropleth Map",
        "Top 10 States — Table",
        "Bottom 5 States — Table",
        "Horizontal Bar Chart (Selected Year)",
        "Grouped Bar Chart (2020–2022)",
        "Slope Graph — State-wise Trend"
    ]
    selected_viz = st.selectbox("Select Visualization ", viz_options)

st.markdown(f"<h3 style='text-align:center; color:white;'>🔎 {selected_viz} — {selected_year}</h3>", unsafe_allow_html=True)

# ---------------- PREPARE YEAR DATA ----------------
year_col = str(selected_year)
if year_col not in df.columns:
    st.error(f"Year {year_col} not present in dataset.")
    st.stop()

year_data = df[['State/UT', year_col]].copy().rename(columns={year_col: 'Count'})
year_data['state_norm'] = year_data['State/UT'].str.strip().str.lower()

# ---------------- INTENSITY SCALE & COLORS ----------------
# KEEPING THE EXACT SAME RANGES FROM ORIGINAL THEFT CODE
def intensity_color(v):
    if v > 60000:
        return "#8B0000"  # Deep Red
    elif 50000 < v <= 60000:
        return "#B22222"  # Firebrick
    elif 30000 < v <= 50000:
        return "#FF4500"  # Orange Red
    elif 20000 < v <= 30000:
        return "#FF8C00"  # Dark Orange
    elif 10000 < v <= 20000:
        return "#FFD700"  # Gold
    else:
        return "#FFF5E6"  # Light (<1000)

# Helper to attach counts/colors to geojson
def attach_counts(geojson, data_df):
    for feat in geojson.get('features', []):
        props = feat.get('properties', {})
        # try keys for state name
        st_nm = ""
        for k in ['st_nm','ST_NM','STATE','state','NAME','district']:
            if k in props and props[k]:
                st_nm = str(props[k]).strip()
                break
        st_norm = st_nm.lower().strip()
        match = data_df.loc[data_df['state_norm'] == st_norm, 'Count']
        val = int(match.values[0]) if not match.empty else 0
        props['Count'] = val
        props['hover'] = f"{st_nm.title() if st_nm else 'Unknown'}: {val:,} cases"
        props['color'] = intensity_color(val)
    return geojson

# ---------------- 1) CHOROPLETH MAP ----------------
if selected_viz == "Choropleth Map":
    geo = attach_counts(india_geo, year_data)

    lons, lats, colors, hovers = [], [], [], []
    for feat in geo.get('features', []):
        geom = feat.get('geometry', {})
        props = feat.get('properties', {})
        coords = []
        if geom.get('type') == 'Polygon':
            coords = geom.get('coordinates')[0]
        elif geom.get('type') == 'MultiPolygon':
            coords = geom.get('coordinates')[0][0]
        if coords:
            lons.append([c[0] for c in coords])
            lats.append([c[1] for c in coords])
            colors.append(props.get('color', '#FFF5E6'))
            hovers.append(props.get('hover', ''))

    fig = go.Figure()
    for lon, lat, color, hover in zip(lons, lats, colors, hovers):
        fig.add_trace(go.Scattergeo(
            lon=lon, lat=lat,
            mode='lines', fill='toself',
            fillcolor=color, line=dict(width=0.5, color='white'),
            hoverinfo='text', text=hover, showlegend=False
        ))

    fig.update_layout(
        geo=dict(showland=True, landcolor="#1e1e1e", showcountries=True, countrycolor="white",
                 showocean=True, oceancolor="#121212", projection_type='mercator', fitbounds="locations"),
        paper_bgcolor="#121212", plot_bgcolor="#121212", font_color="white",
        height=680, margin=dict(t=40, b=10, l=10, r=10),
        title=dict(text=f"🗺 Theft Cases Across India — {selected_year}", x=0.5, font=dict(size=18, color='white'))
    )

    col_map, col_leg = st.columns([3,1])
    with col_map:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col_leg:
        st.markdown("### ⚠️ Intensity Scale", unsafe_allow_html=True)
        st.markdown("""
            <div style="background-color:#FFF5E6; padding:6px; margin:5px; border-radius:6px; color:black;">⬜ Below 10000</div>
            <div style="background-color:#FFD700; padding:6px; margin:5px; border-radius:6px; color:black;">⬜ 10000 – 20000</div>
            <div style="background-color:#FF8C00; padding:6px; margin:5px; border-radius:6px; color:black;">⬜ 20000 – 30000</div>
            <div style="background-color:#FF4500; padding:6px; margin:5px; border-radius:6px; color:black;">⬜ 30000 – 50000</div>
            <div style="background-color:#B22222; padding:6px; margin:5px; border-radius:6px; color:white;">⬜ 50000 – 60000</div>
            <div style="background-color:#8B0000; padding:6px; margin:5px; border-radius:6px; color:white;">⬜ Above 60000</div>
        """, unsafe_allow_html=True)

# ---------------- 2) TOP 10 STATES — TABLE ----------------
elif selected_viz == "Top 10 States — Table":
    df['Total'] = df[['2020','2021','2022']].sum(axis=1)
    top10 = df.sort_values('Total', ascending=False).head(10).reset_index(drop=True)
    st.markdown("### 🔝 Top 10 States by Total Theft Cases (2020–2022)", unsafe_allow_html=True)
    st.dataframe(top10[['State/UT','2020','2021','2022','Total']].rename(columns={'State/UT':'State/UT'}), height=360)
    
    # horizontal bar for top10
    fig = px.bar(top10.sort_values('Total'), x='Total', y='State/UT', orientation='h', text='Total',
                 color='Total', color_continuous_scale=['#FFF5E6','#FFD700','#FF8C00','#FF4500','#B22222','#8B0000'])
    fig.update_traces(textposition='outside')
    fig.update_layout(
        paper_bgcolor="#121212", 
        plot_bgcolor="#121212", 
        font_color='white', 
        height=500, 
        margin=dict(l=50,r=20,t=30,b=20),
        xaxis_title="Total Theft Cases (2020-2022)",
        yaxis_title="State/UT"
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------- 3) BOTTOM 5 STATES — TABLE ----------------
elif selected_viz == "Bottom 5 States — Table":
    df['Total'] = df[['2020','2021','2022']].sum(axis=1)
    bottom5 = df.sort_values('Total', ascending=True).head(5).reset_index(drop=True)
    st.markdown("### 🔻 Bottom 5 States by Total Theft Cases (2020–2022)", unsafe_allow_html=True)
    st.dataframe(bottom5[['State/UT','2020','2021','2022','Total']].rename(columns={'State/UT':'State/UT'}), height=300)

# ---------------- 4) HORIZONTAL BAR CHART (SELECTED YEAR) ----------------
elif selected_viz == "Horizontal Bar Chart (Selected Year)":
    sorted_df = year_data.sort_values('Count')
    fig = px.bar(sorted_df, x='Count', y='State/UT', orientation='h', text='Count',
                 color='Count', color_continuous_scale=['#FFF5E6','#FFD700','#FF8C00','#FF4500','#B22222','#8B0000'])
    fig.update_traces(textposition='outside')
    fig.update_layout(
        paper_bgcolor="#121212", 
        plot_bgcolor="#121212", 
        font_color='white', 
        height=800, 
        margin=dict(l=50,r=20,t=30,b=20),
        xaxis_title=f"Number of Theft Cases ({selected_year})",
        yaxis_title="State/UT"
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------- 5) GROUPED BAR CHART (2020–2022) ----------------
elif selected_viz == "Grouped Bar Chart (2020–2022)":
    df['Total'] = df[['2020','2021','2022']].sum(axis=1)
    top10 = df.sort_values('Total', ascending=False).head(10)
    df_melt = top10.melt(id_vars='State/UT', value_vars=['2020','2021','2022'], var_name='Year', value_name='Count')
    fig = px.bar(df_melt, x='State/UT', y='Count', color='Year', barmode='group',
                 color_discrete_sequence=['#FF8C00', '#FFD700', '#FF4500'])
    fig.update_layout(
        paper_bgcolor="#121212", 
        plot_bgcolor="#121212", 
        font_color='white', 
        height=600, 
        margin=dict(l=60,r=20,t=50,b=90),
        xaxis_title="State/UT",
        yaxis_title="Number of Theft Cases"
    )
    # Add small white year labels at top-right
    fig.add_annotation(x=1, y=1.02, xref='paper', yref='paper', 
                      text="<b style='color:white;'>2020 &nbsp;&nbsp; 2021 &nbsp;&nbsp; 2022</b>", 
                      showarrow=False, align='right', font=dict(color='white'))
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# ---------------- 6) SLOPE GRAPH — STATE-WISE TREND ----------------
elif selected_viz == "Slope Graph — State-wise Trend":
    if "state_idx" not in st.session_state:
        st.session_state.state_idx = 0
    states = df['State/UT'].tolist()
    col_prev, col_ctl, col_next = st.columns([1,6,1])
    with col_prev:
        if st.button("⬅️ Previous"):
            st.session_state.state_idx = (st.session_state.state_idx - 1) % len(states)
    with col_next:
        if st.button("Next ➡️"):
            st.session_state.state_idx = (st.session_state.state_idx + 1) % len(states)

    sel_state = states[st.session_state.state_idx]
    st.markdown(f"### 📈 Year-wise Trend for **{sel_state}**", unsafe_allow_html=True)
    row = df[df['State/UT'] == sel_state][['2020','2021','2022']].T.reset_index()
    row.columns = ['Year','Count']

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=row['Year'], y=row['Count'],
        mode='lines+markers+text',
        line=dict(color='#FFD700', width=3),
        marker=dict(color='white', size=10),
        text=row['Count'],
        textposition='top center'
    ))
    fig.update_layout(
        paper_bgcolor="#121212", 
        plot_bgcolor="#121212", 
        font_color='white', 
        height=500, 
        margin=dict(t=40,b=20),
        xaxis_title="Year",
        yaxis_title="Number of Theft Cases"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"Showing {sel_state} ({st.session_state.state_idx + 1}/{len(states)})", icon="ℹ️")

# ---------------- INSIGHTS ----------------
with st.expander("📌 Key Insights (2020 - 2022)"):
    total = int(df[['2020','2021','2022']].sum().sum())
    year_sums = df[['2020','2021','2022']].sum()
    max_year = year_sums.idxmax()
    min_year = year_sums.idxmin()
    max_state = df.set_index('State/UT')[['2020','2021','2022']].sum(axis=1).idxmax()
    min_state = df.set_index('State/UT')[['2020','2021','2022']].sum(axis=1).idxmin()
    inc_2022 = int(df['2022'].sum() - df['2020'].sum())
    trend = "📈 Increase" if inc_2022 > 0 else "📉 Decrease"

    st.markdown(f"""
    <div style="background:#1e1e1e;padding:16px;border-radius:8px;color:#FFD700;">
        <p><b>Total theft cases (2020–2022):</b> {total:,}</p>
        <p><b>Year with max cases:</b> {max_year}</p>
        <p><b>Year with min cases:</b> {min_year}</p>
        <p><b>State with most cases (total):</b> {max_state}</p>
        <p><b>State with least cases (total):</b> {min_state}</p>
        <p><b>Trend (2020 → 2022):</b> {trend} </p>
    </div>
    """, unsafe_allow_html=True)