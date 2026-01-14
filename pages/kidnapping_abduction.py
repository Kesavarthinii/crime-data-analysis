# kidnapping_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# ---------------- PAGE CONFIG & THEME ----------------
st.set_page_config(page_title="Kidnapping & Abduction Analysis", layout="wide")

# Global CSS for dark theme + gold headings
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

st.markdown("<h1 style='text-align:center; font-size:2.6rem; margin-bottom:8px; color:white;'>KIDNAPPING & ABDUCTION (2020 - 2022)</h1>", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("<h3 style='color:#FFD700;'>Data & GeoJSON (optional)</h3>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Upload Kidnapping Excel (.xlsx)", type=["xlsx"])
uploaded_geo = st.sidebar.file_uploader("Upload India GeoJSON (.json/.geojson)", type=["json", "geojson"])

# ---------------- DATA LOADING UTILITIES ----------------
@st.cache_data
def load_excel(path=None):
    if path is not None:
        df = pd.read_excel(path)
    else:
        df = pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Kidnapping and Abduction.xlsx")
    # Normalize & ensure columns
    df.columns = [str(c).strip() for c in df.columns]
    # Try to find state column and rename to 'state'
    state_col = None
    for c in df.columns:
        if c.lower() in ['state', 'state/ut', 'state_ut', 'state name', 'st_nm', 'state name/ut']:
            state_col = c
            break
    if state_col is None:
        state_col = df.columns[0]
    df = df.rename(columns={state_col: 'state'})
    # Ensure year columns exist
    for y in ['2020', '2021', '2022']:
        if y not in df.columns:
            df[y] = 0
    # Clean state names and numeric coercion
    df['state'] = df['state'].astype(str).str.strip()
    for y in ['2020', '2021', '2022']:
        df[y] = pd.to_numeric(df[y], errors='coerce').fillna(0).astype(int)
    return df

@st.cache_data
def load_geo(path=None):
    if path is not None:
        try:
            obj = path.read()
            if isinstance(obj, (bytes, bytearray)):
                obj = obj.decode('utf-8')
            return json.loads(obj)
        except Exception:
            path.seek(0)
            return json.load(path)
    else:
        with open(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\india.geojson", "r", encoding="utf-8") as f:
            return json.load(f)

# Load data
df = load_excel(uploaded_file)
india_geo = load_geo(uploaded_geo)

# ---------------- UI: Year & Visualization Dropdown (fixed order) ----------------
col_y, col_v = st.columns([1, 2])
with col_y:
    selected_year = st.selectbox("Select Year", [2020, 2021, 2022])
with col_v:
    viz_options = [
        "Choropleth Map",
        "Top 10 States Table",
        "Least 5 States Table",
        "Horizontal Bar Chart",
        "Grouped Bar Chart (2020-2022)",
        "Year-wise Slope per State"
    ]
    selected_viz = st.selectbox("Select Visualization", viz_options)

st.markdown(f"<h3 style='text-align:center; color:white;'>🔎 {selected_viz} — {selected_year}</h3>", unsafe_allow_html=True)

# Prepare year_data
year_col = str(selected_year)
if year_col not in df.columns:
    st.error(f"Selected year {year_col} not found in dataset.")
    st.stop()
year_data = df[['state', year_col]].copy().rename(columns={year_col: 'Count'})
year_data['state_norm'] = year_data['state'].str.strip().str.lower()

# ---------------- Intensity Scale & Color Map (confirmed) ----------------
# Ranges:
# <1000, 1000–5000, 5000–10000, 10000–15000, 15000–20000, >20000
def kidnap_color(val):
    if val > 20000:
        return "#FF2400"
    elif 15000 < val <= 20000:
        return "#FF7F0E"
    elif 10000 < val <= 15000:
        return "#FFAA00"
    elif 5000 < val <= 10000:
        return "#FFD700"
    elif 1000 < val <= 5000:
        return "#FFCC80"
    else:
        return "#FFEFD5"

# ---------------- Helper to add counts to geojson ----------------
def attach_counts_to_geo(geojson, data_df):
    for feat in geojson.get('features', []):
        props = feat.get('properties', {})
        # try possible property names for state
        st_name = ""
        for key in ['st_nm', 'ST_NM', 'STATE', 'state', 'NAME']:
            if key in props:
                st_name = str(props[key]).strip()
                break
        st_norm = st_name.strip().lower()
        match = data_df.loc[data_df['state_norm'] == st_norm, 'Count']
        val = int(match.values[0]) if not match.empty else 0
        props['Count'] = val
        props['hover_text'] = f"{st_name.title()}: {val:,} cases"
        props['color'] = kidnap_color(val)
    return geojson

# ---------------- VISUALIZATIONS ----------------

# 1) Choropleth Map
if selected_viz == "Choropleth Map":
    # attach counts/colors
    geo_with_counts = attach_counts_to_geo(india_geo, year_data)

    # build polygon lists
    lons, lats, colors, hovers = [], [], [], []
    for feat in geo_with_counts.get('features', []):
        geom = feat.get('geometry', {})
        props = feat.get('properties', {})
        coords = []
        if geom.get('type') == 'Polygon':
            coords = geom.get('coordinates')[0]
        elif geom.get('type') == 'MultiPolygon':
            # take first polygon for centroid/shape display
            coords = geom.get('coordinates')[0][0]
        if coords:
            lons.append([c[0] for c in coords])
            lats.append([c[1] for c in coords])
            colors.append(props.get('color', '#FFEFD5'))
            hovers.append(props.get('hover_text', ''))

    fig = go.Figure()
    for lon, lat, color, hover in zip(lons, lats, colors, hovers):
        fig.add_trace(go.Scattergeo(
            lon=lon, lat=lat,
            mode='lines', fill='toself',
            fillcolor=color, line=dict(width=0.5, color='white'),
            hoverinfo='text', text=hover, showlegend=False
        ))

    fig.update_layout(
        geo=dict(
            showland=True,
            landcolor="#1e1e1e",
            showcountries=True,
            countrycolor="white",
            showocean=True,
            oceancolor="#121212",
            projection_type="mercator",
            fitbounds="locations"
        ),
        paper_bgcolor="#121212",
        plot_bgcolor="#121212",
        font_color="white",
        height=820,
        margin=dict(l=10, r=10, t=60, b=10),
        title=dict(text=f"🗺 Kidnapping & Abduction Across India — {selected_year}", x=0.5, font=dict(size=18, color='white'))
    )

    col_map, col_legend = st.columns([3, 1])
    with col_map:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col_legend:
        st.markdown("### 🎨 Intensity Scale", unsafe_allow_html=True)
        st.markdown("""
            <div style="background:#FFEFD5; padding:6px; margin:6px; border-radius:6px;">⬜ &lt; 1,000</div>
            <div style="background:#FFCC80; padding:6px; margin:6px; border-radius:6px;">⬜ 1,000 – 5,000</div>
            <div style="background:#FFD700; padding:6px; margin:6px; border-radius:6px;">⬜ 5,000 – 10,000</div>
            <div style="background:#FFAA00; padding:6px; margin:6px; border-radius:6px; color:black;">⬜ 10,000 – 15,000</div>
            <div style="background:#FF7F0E; padding:6px; margin:6px; border-radius:6px; color:black;">⬜ 15,000 – 20,000</div>
            <div style="background:#FF2400; padding:6px; margin:6px; border-radius:6px; color:white;">⬜ &gt; 20,000</div>
        """, unsafe_allow_html=True)

# 2) Top 10 States Table + Bar
elif selected_viz == "Top 10 States Table":
    df['Total'] = df[['2020', '2021', '2022']].sum(axis=1)
    top10 = df.sort_values('Total', ascending=False).head(10).reset_index(drop=True)
    st.markdown("### 🔝 Top 10 States by Total Cases (2020–2022)", unsafe_allow_html=True)
    # dark styled dataframe via st.dataframe (pandas style visual only shows in some UIs)
    st.dataframe(top10[['state', '2020', '2021', '2022', 'Total']].rename(columns={'state': 'State/UT'}), height=300)
    # Large horizontal bar chart
    fig = px.bar(top10.sort_values('Total'), x='Total', y='state', orientation='h', text='Total', color='Total', color_continuous_scale=['#FFEFD5','#FFCC80','#FFD700','#FFAA00','#FF7F0E','#FF2400'])
    fig.update_traces(textposition='outside')
    fig.update_layout(paper_bgcolor="#121212", plot_bgcolor="#121212", font_color='white', height=700, margin=dict(l=50, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

# 3) Least 5 States Table
elif selected_viz == "Least 5 States Table":
    df['Total'] = df[['2020', '2021', '2022']].sum(axis=1)
    least5 = df.sort_values('Total', ascending=True).head(5).reset_index(drop=True)
    st.markdown("### 🔻 Least 5 States by Total Cases (2020–2022)", unsafe_allow_html=True)
    st.dataframe(least5[['state', '2020', '2021', '2022']].rename(columns={'state': 'State/UT'}), height=260)

# 4) Horizontal Bar Chart (Selected Year)
elif selected_viz == "Horizontal Bar Chart":
    sorted_df = year_data.sort_values('Count', ascending=True)
    fig = px.bar(sorted_df, x='Count', y='state', orientation='h', color='Count', text='Count', color_continuous_scale=['#FFEFD5','#FFCC80','#FFD700','#FFAA00','#FF7F0E','#FF2400'])
    fig.update_layout(paper_bgcolor="#121212", plot_bgcolor="#121212", font_color='white', height=820, margin=dict(l=50,r=20,t=40,b=20))
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# 5) Grouped Bar Chart (2020-2022) for Top 10 states
elif selected_viz == "Grouped Bar Chart (2020-2022)":
    df['Total'] = df[['2020', '2021', '2022']].sum(axis=1)
    top10 = df.sort_values('Total', ascending=False).head(10)
    df_melt = top10.melt(id_vars='state', value_vars=['2020','2021','2022'], var_name='Year', value_name='Count')
    fig = px.bar(df_melt, x='state', y='Count', color='Year', barmode='group', color_discrete_sequence=['#FFCC80', '#FFD700', '#FF7F0E'])
    fig.update_layout(paper_bgcolor="#121212", plot_bgcolor="#121212", font_color='white', height=880, margin=dict(l=50,r=20,t=50,b=80))
    # Put year labels in top-right (small white annotation)
    fig.add_annotation(x=1, y=1.02, xref='paper', yref='paper', text="<b style='color:white;'>2020 &nbsp;&nbsp; 2021 &nbsp;&nbsp; 2022</b>", showarrow=False, align='right', font=dict(color='white'))
    st.plotly_chart(fig, use_container_width=True)

# 6) Year-wise Slope per State (Next / Previous)
elif selected_viz == "Year-wise Slope per State":
    if "state_idx" not in st.session_state:
        st.session_state.state_idx = 0
    states = df['state'].tolist()
    col_prev, col_center, col_next = st.columns([1, 6, 1])
    with col_prev:
        if st.button("⬅️ Previous"):
            st.session_state.state_idx = (st.session_state.state_idx - 1) % len(states)
    with col_next:
        if st.button("Next ➡️"):
            st.session_state.state_idx = (st.session_state.state_idx + 1) % len(states)

    sel_state = states[st.session_state.state_idx]
    st.markdown(f"### 📈 Year-wise Trend for **{sel_state}**", unsafe_allow_html=True)
    state_row = df[df['state'] == sel_state][['2020','2021','2022']].T.reset_index()
    state_row.columns = ['Year', 'Count']

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=state_row['Year'], y=state_row['Count'], mode='lines+markers+text',
                             line=dict(color='#FFD700', width=3),
                             marker=dict(color='white', size=10),
                             text=state_row['Count'], textposition='top center'))
    fig.update_layout(paper_bgcolor="#121212", plot_bgcolor="#121212", font_color='white', height=580, margin=dict(t=40,b=20))
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"Showing {sel_state} ({st.session_state.state_idx + 1}/{len(states)})", icon="ℹ️")

# ---------------- INSIGHTS EXPANDER ----------------
with st.expander("📌 Key Insights (2020 - 2022)"):
    total = int(df[['2020','2021','2022']].sum().sum())
    year_sums = df[['2020','2021','2022']].sum()
    max_year = year_sums.idxmax()
    min_year = year_sums.idxmin()
    max_state = df.set_index('state')[['2020','2021','2022']].sum(axis=1).idxmax()
    min_state = df.set_index('state')[['2020','2021','2022']].sum(axis=1).idxmin()
    inc_2022 = int(df['2022'].sum() - df['2020'].sum())
    trend = "📈 Increase" if inc_2022 > 0 else "📉 Decrease"

    st.markdown(f"""
    <div style="background:#1e1e1e;padding:16px;border-radius:8px;color:#FFD700;">
        <p><b>Total cases (2020–2022):</b> {total:,}</p>
        <p><b>Year with max cases:</b> {max_year}</p>
        <p><b>Year with min cases:</b> {min_year}</p>
        <p><b>State with most cases (total):</b> {max_state}</p>
        <p><b>State with least cases (total):</b> {min_state}</p>
        <p><b>Trend (2020 → 2022):</b> {trend} </p>
    </div>
    """, unsafe_allow_html=True)
