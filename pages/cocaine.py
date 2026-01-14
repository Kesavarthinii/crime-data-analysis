import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import json

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Cocaine Consumption Analysis", layout="wide")
st.markdown(
    """
    <style>
        .stApp { background-color: #0b0b0b; color: white; }
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        h1, h2, h3, h4 { color: #FFFFFF !important; }
        label { color: #FFD700 !important; font-weight:600; }
        .dataframe thead th { color: #FFD700; background-color: #111; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='text-align: center; font-size: 2.8rem; margin-bottom: 16px;'>DRUG OFFENCES — CONSUMPTION OF COCAINE (2019–2021)</h1>",
    unsafe_allow_html=True
)

# ---------------- SIDEBAR (optional uploads) ----------------
st.sidebar.markdown("<h3 style='color:#FFD700;'>Data / GeoJSON (optional)</h3>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Upload cocaine Excel (.xlsx)", type=["xlsx"])
uploaded_geo = st.sidebar.file_uploader("Upload India geojson (.json/.geojson)", type=["json","geojson"])

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data(path=None):
    if path is not None:
        df = pd.read_excel(path)
    else:
        df = pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\cocaine.xlsx")
    # Normalize columns
    df.columns = [str(c).strip() for c in df.columns]
    # Ensure expected year cols exist
    for y in ['2019','2020','2021']:
        if y not in df.columns:
            df[y] = 0
    # Ensure State/UT column
    if 'State/UT' not in df.columns:
        # try common alternatives
        for c in df.columns:
            if c.lower() in ['state','state_ut','state/ut','state_ut_name']:
                df = df.rename(columns={c: 'State/UT'})
                break
        else:
            df = df.rename(columns={df.columns[0]: 'State/UT'})
    df['State/UT'] = df['State/UT'].astype(str).str.strip()
    # coerce numeric years
    for y in ['2019','2020','2021']:
        df[y] = pd.to_numeric(df[y], errors='coerce').fillna(0).astype(int)
    return df

df = load_data(uploaded_file)

# ---------------- LOAD GEOJSON ----------------
@st.cache_data
def load_geojson(path=None):
    if path is not None:
        # uploaded file-like object
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

india_geo = load_geojson(uploaded_geo)

# ---------------- UI: Standard 6 Visualizations ----------------
st.markdown("<h3 style='margin-top:10px; color:white;'>Select Year & Visualization</h3>", unsafe_allow_html=True)
col_y, col_v = st.columns([1, 2])
with col_y:
    selected_year = st.selectbox("Choose Year", [2019, 2020, 2021])
with col_v:
    viz_options = [
        "Choropleth Map ",
        "Top 10 States (Table)",
        "Least 5 States (Table)",
        "Horizontal Bar Chart (Selected Year)",
        "Grouped Bar Chart (2019–2021)",
        "Year-wise Slope per State"
    ]
    selected_viz = st.selectbox("Choose Visualization", viz_options)

st.markdown(f"<h2 style='text-align:center; color:white; margin-top:14px;'>🔎 {selected_viz} — {selected_year}</h2>", unsafe_allow_html=True)

# Prepare year_data
year_col = str(selected_year)
if year_col not in df.columns:
    st.error(f"No '{year_col}' column found in dataframe.")
    st.stop()

year_data = df[['State/UT', year_col]].copy().rename(columns={year_col: 'Consumption'})
year_data['state_norm'] = year_data['State/UT'].astype(str).str.strip().str.lower()

# ---------------- Helper: apply color scale to geojson ----------------
def apply_cocaine_scale(geojson, data_df):
    """
    Interprets ranges:
    - < 1000
    - 1000 - 5000
    - 5000 - 10000
    - 10 - 30  -> 10,000 - 30,000
    - 30 - 50  -> 30,000 - 50,000
    - 50 - 70  -> 50,000 - 70,000
    - > 70     -> > 70,000
    Colors: light -> dark red
    """
    for feature in geojson.get('features', []):
        props = feature.get('properties', {})
        st_nm = str(props.get('st_nm') or props.get('STATE') or '').strip().lower()
        match = data_df.loc[data_df['state_norm'] == st_nm, 'Consumption']
        val = int(match.values[0]) if not match.empty else 0
        feature['properties']['Consumption'] = val
        feature['properties']['hover_text'] = f"{(props.get('st_nm') or st_nm).title()}: {val:,}"

        # Apply thresholds (interpreting small shorthand as thousands)
        if val > 70000:
            feature['properties']['color'] = "#8B0000"   # deepest red
        elif 50000 < val <= 70000:
            feature['properties']['color'] = "#B22222"
        elif 30000 < val <= 50000:
            feature['properties']['color'] = "#FF4500"
        elif 10000 < val <= 30000:
            feature['properties']['color'] = "#FF8C00"
        elif 5000 < val <= 10000:
            feature['properties']['color'] = "#FFD700"
        elif 1000 < val <= 5000:
            feature['properties']['color'] = "#FFE680"
        else:
            feature['properties']['color'] = "#FFF8DC"

# ---------------- 1) Choropleth Map (Large, Dark) ----------------
if selected_viz == "Choropleth Map (Dark, Large)":
    apply_cocaine_scale(india_geo, year_data)

    lons, lats, colors, hovers = [], [], [], []
    for f in india_geo.get('features', []):
        geom = f.get('geometry', {})
        props = f.get('properties', {})
        color = props.get('color', "#111111")
        hover = props.get('hover_text', '')
        # handle polygon and multipolygon (take first polygon ring)
        if geom.get('type') == 'Polygon':
            coords = geom.get('coordinates')[0]
        elif geom.get('type') == 'MultiPolygon':
            coords = geom.get('coordinates')[0][0]
        else:
            coords = []
        if coords:
            lons.append([c[0] for c in coords])
            lats.append([c[1] for c in coords])
            colors.append(color)
            hovers.append(hover)

    fig = go.Figure()
    for lon, lat, color, hover in zip(lons, lats, colors, hovers):
        fig.add_trace(go.Scattergeo(
            lon=lon, lat=lat,
            mode='lines', fill='toself',
            fillcolor=color, line=dict(width=0.5, color='white'),
            hoverinfo='text', text=hover, showlegend=False
        ))

    fig.update_layout(
        geo=dict(showland=True, landcolor="#0b0b0b", showcountries=True, countrycolor="white",
                 projection_type='mercator', fitbounds="locations"),
        paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b",
        font_color="white", height=820,
        margin=dict(t=40, b=10, l=10, r=10),
        title=dict(text=f"🗺 Cocaine Consumption Across India — {selected_year}", x=0.5, font=dict(color='white', size=20))
    )

    col_map, col_legend = st.columns([4, 1])
    with col_map:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col_legend:
        st.markdown("### 🎨 Intensity Scale", unsafe_allow_html=True)
        st.markdown("""
            <div style="background:#FFF8DC; padding:6px; margin:6px; border-radius:6px;">⬜ &lt; 1,000</div>
            <div style="background:#FFE680; padding:6px; margin:6px; border-radius:6px;">⬜ 1,000 – 5,000</div>
            <div style="background:#FFD700; padding:6px; margin:6px; border-radius:6px;">⬜ 5,000 – 10,000</div>
            <div style="background:#FF8C00; padding:6px; margin:6px; border-radius:6px; color:white;">⬜ 10,000 – 30,000</div>
            <div style="background:#FF4500; padding:6px; margin:6px; border-radius:6px; color:white;">⬜ 30,000 – 50,000</div>
            <div style="background:#B22222; padding:6px; margin:6px; border-radius:6px; color:white;">⬜ 50,000 – 70,000</div>
            <div style="background:#8B0000; padding:6px; margin:6px; border-radius:6px; color:white;">⬜ &gt; 70,000</div>
        """, unsafe_allow_html=True)

# ---------------- 2) Top 10 States (Table + bar) ----------------
elif selected_viz == "Top 10 States (Table)":
    df['Total'] = df[['2019','2020','2021']].sum(axis=1)
    top10 = df.sort_values('Total', ascending=False).head(10).reset_index(drop=True)
    st.markdown("### 🔝 Top 10 States by Total Consumption (2019–2021)", unsafe_allow_html=True)
    st.dataframe(top10.style.format({'Total':"{:,}", '2019':"{:,}", '2020':"{:,}", '2021':"{:,}"}).set_properties(**{'background-color':'#0f0f0f','color':'white'}))
    # horizontal bar for top10
    fig = px.bar(top10.sort_values('Total'), x='Total', y='State/UT', orientation='h', text='Total', color='Total', color_continuous_scale='Reds')
    fig.update_layout(paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=600)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# ---------------- 3) Least 5 States (Table) ----------------
elif selected_viz == "Least 5 States (Table)":
    df['Total'] = df[['2019','2020','2021']].sum(axis=1)
    least5 = df.sort_values('Total', ascending=True).head(5).reset_index(drop=True)
    st.markdown("### 🔻 Least 5 States by Total Consumption (2019–2021)", unsafe_allow_html=True)
    st.dataframe(least5.style.format({'Total':"{:,}"}).set_properties(**{'background-color':'#0f0f0f','color':'white'}))

# ---------------- 4) Horizontal Bar Chart (Selected Year) ----------------
elif selected_viz == "Horizontal Bar Chart (Selected Year)":
    sorted_df = year_data.sort_values('Consumption')
    fig = px.bar(sorted_df, x='Consumption', y='State/UT', orientation='h', color='Consumption', text='Consumption', color_continuous_scale='Reds')
    fig.update_layout(paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=800)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# ---------------- 5) Grouped Bar Chart (2019–2021) ----------------
elif selected_viz == "Grouped Bar Chart (2019–2021)":
    df_melt = df.melt(id_vars='State/UT', value_vars=['2019','2020','2021'], var_name='Year', value_name='Consumption')
    fig = px.bar(df_melt, x='State/UT', y='Consumption', color='Year', barmode='group',
                 color_discrete_sequence=['#FFCC80','#FFD700','#FF7F0E'])
    fig.update_layout(paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=850,
                      xaxis=dict(tickangle=-45, tickfont=dict(color='white')), legend=dict(font=dict(color='white')))
    # place year labels (legend already white); also annotate years in top-right
    fig.add_annotation(
        x=1, y=1.02, xref="paper", yref="paper",
        text="<b style='color:white;'>2019 &nbsp;&nbsp; 2020 &nbsp;&nbsp; 2021</b>",
        showarrow=False, align="right", font=dict(color="white", size=12)
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------- 6) Year-wise Slope per State ----------------
elif selected_viz == "Year-wise Slope per State":
    if "state_index" not in st.session_state:
        st.session_state.state_index = 0
    states = df['State/UT'].tolist()
    col_prev, col_mid, col_next = st.columns([1, 6, 1])
    with col_prev:
        if st.button("⬅️ Previous"):
            st.session_state.state_index = (st.session_state.state_index - 1) % len(states)
    with col_next:
        if st.button("Next ➡️"):
            st.session_state.state_index = (st.session_state.state_index + 1) % len(states)
    selected_state = states[st.session_state.state_index]
    state_data = df[df['State/UT'] == selected_state][['2019','2020','2021']].melt(var_name='Year', value_name='Consumption')
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=state_data['Year'], y=state_data['Consumption'],
        mode='lines+markers+text',
        line=dict(color='#FFD700', width=4),
        marker=dict(size=12, color='white'),
        text=state_data['Consumption'],
        textposition='top center'
    ))
    fig.update_layout(title=f"📈 Year-wise Trend — {selected_state}", paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=600)
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"Showing {selected_state} ({st.session_state.state_index + 1}/{len(states)})")

# ---------------- INSIGHTS ----------------
with st.expander("📌 Key Insights (2019–2021)"):
    total = df[['2019','2020','2021']].sum().sum()
    year_sums = df[['2019','2020','2021']].sum()
    max_year = year_sums.idxmax()
    min_year = year_sums.idxmin()
    top_state = df.set_index('State/UT')[['2019','2020','2021']].sum(axis=1).idxmax()
    st.markdown(f"""
        <div style="background:#1e1e1e;padding:16px;border-radius:8px;color:#FFD700;">
            <p><b>Total consumption (2019–2021):</b> {total:,} grams</p>
            <p><b>Year with max consumption:</b> {max_year}</p>
            <p><b>Year with min consumption:</b> {min_year}</p>
            <p><b>Top consuming State/UT:</b> {top_state}</p>
        </div>
    """, unsafe_allow_html=True)
