import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import json

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Human Trafficking Analysis", layout="wide")

st.markdown(
    """
    <style>
        .stApp { background-color: #0b0b0b; color: white; }
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        h1, h2, h3, h4 { color: #FFFFFF !important; }
        label { color: #FFD700 !important; font-weight:600; }
        .dataframe thead th { color: #FFD700; background-color: #111; }
        .css-ffhzg2 { color: #FFFFFF; } /* fallback */
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='text-align: center; font-size: 2.8rem; margin-bottom: 8px;'>HUMAN TRAFFICKING CASES (2020 - 2022)</h1>",
    unsafe_allow_html=True
)

# ---------------- SIDEBAR: Uploads & Settings ----------------
st.sidebar.markdown("<h3 style='color:#FFD700;'>Data & GeoJSON (optional)</h3>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Upload Human Trafficking Excel (.xlsx)", type=["xlsx"])
uploaded_geo = st.sidebar.file_uploader("Upload India GeoJSON (.json/.geojson)", type=["json", "geojson"])

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data(path=None):
    if path is not None:
        df = pd.read_excel(path)
    else:
        df = pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Human Trafficking.xlsx")
    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]
    # Ensure required year columns
    for y in ['2020', '2021', '2022']:
        if y not in df.columns:
            df[y] = 0
    # Ensure state column named 'state'
    if 'state' not in [c.lower() for c in df.columns]:
        # try to rename common variations
        for c in df.columns:
            if c.lower() in ['state', 'state/ut', 'state_name', 'st_nm']:
                df = df.rename(columns={c: 'state'})
                break
        else:
            df = df.rename(columns={df.columns[0]: 'state'})
    df = df.rename(columns={c: c if c.lower() != 'state' else 'state' for c in df.columns})
    df['state'] = df['state'].astype(str).str.strip()
    # Coerce numeric
    for y in ['2020', '2021', '2022']:
        df[y] = pd.to_numeric(df[y], errors='coerce').fillna(0).astype(int)
    return df

df = load_data(uploaded_file)

# ---------------- LOAD GEOJSON ----------------
@st.cache_data
def load_geojson(path=None):
    if path is not None:
        try:
            # uploaded file-like object
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

# ---------------- UI: Year & Visualization Selection ----------------
st.markdown("<h4 style='margin-top:10px; color:white;'>Select Year & Visualization</h4>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])
with col1:
    selected_year = st.selectbox("Choose Year", [2020, 2021, 2022])
with col2:
    viz_options = [
        "Choropleth Map ",
        "Top 10 States (Table)",
        "Least 5 States (Table)",
        "Horizontal Bar Chart (Selected Year)",
        "Grouped Bar Chart (2020–2022)",
        "Year-wise Slope per State"
    ]
    selected_viz = st.selectbox("Choose Visualization", viz_options)

st.markdown(f"<h2 style='text-align:center; color:white; margin-top:12px;'>🔎 {selected_viz} — {selected_year}</h2>", unsafe_allow_html=True)

# Prepare year_data
year_col = str(selected_year)
if year_col not in df.columns:
    st.error(f"Year {year_col} not found in the data.")
    st.stop()
year_data = df[['state', year_col]].copy().rename(columns={year_col: 'Count'})
year_data['state_norm'] = year_data['state'].astype(str).str.strip().str.lower()

# ---------------- Helper: Apply intensity ranges to geojson ----------------
def apply_intensity(geojson, data_df):
    """
    Intensity ranges:
        < 50
        50 - 100
        100 - 500
        > 500
    Colors: light peach -> yellow -> orange -> deep red
    """
    for feature in geojson.get('features', []):
        props = feature.get('properties', {})
        st_nm = str(props.get('st_nm') or props.get('STATE') or '').strip().lower()
        match = data_df.loc[data_df['state_norm'] == st_nm, 'Count']
        val = int(match.values[0]) if not match.empty else 0
        feature['properties']['Count'] = val
        feature['properties']['hover_text'] = f"{(props.get('st_nm') or st_nm).title()}: {val:,}"

        if val > 500:
            feature['properties']['color'] = "#8B0000"   # very high - deep red
        elif 100 < val <= 500:
            feature['properties']['color'] = "#FF4500"   # high - orange-red
        elif 50 < val <= 100:
            feature['properties']['color'] = "#FFD700"   # moderate - gold
        else:
            feature['properties']['color'] = "#FFEFD5"   # low - light peach

# ---------------- Visualizations ----------------

# 1) CHOROPLETH MAP (Large, Dark)
if selected_viz == "Choropleth Map (Large, Dark)":
    apply_intensity(india_geo, year_data)

    # extract polygon coords, colors, hover texts
    lons, lats, colors, hovers = [], [], [], []
    for feature in india_geo.get('features', []):
        geom = feature.get('geometry', {})
        props = feature.get('properties', {})
        color = props.get('color', "#111111")
        hover = props.get('hover_text', '')
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
        title=dict(text=f"🗺 Human Trafficking Cases Across India — {selected_year}", x=0.5, font=dict(color='white', size=20))
    )

    col_map, col_legend = st.columns([4, 1])
    with col_map:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col_legend:
        st.markdown("### 🎨 Intensity Scale", unsafe_allow_html=True)
        st.markdown("""
            <div style="background:#FFEFD5; padding:6px; margin:6px; border-radius:6px;">⬜ &lt; 50</div>
            <div style="background:#FFD700; padding:6px; margin:6px; border-radius:6px;">⬜ 50 – 100</div>
            <div style="background:#FF4500; padding:6px; margin:6px; border-radius:6px; color:white;">⬜ 100 – 500</div>
            <div style="background:#8B0000; padding:6px; margin:6px; border-radius:6px; color:white;">⬜ &gt; 500</div>
        """, unsafe_allow_html=True)

# 2) TOP 10 STATES (Table + Horizontal Bar)
elif selected_viz == "Top 10 States (Table + Bar)":
    df['Total'] = df[['2020', '2021', '2022']].sum(axis=1)
    top10 = df.sort_values('Total', ascending=False).head(10).reset_index(drop=True)
    st.markdown("### 🔝 Top 10 States by Total Cases (2020–2022)", unsafe_allow_html=True)
    st.dataframe(top10.style.format({'Total':"{:,}", '2020':"{:,}", '2021':"{:,}", '2022':"{:,}"}).set_properties(**{'background-color':'#0f0f0f','color':'white'}))
    # bar for top10
    fig = px.bar(top10.sort_values('Total'), x='Total', y='state', orientation='h', text='Total', color='Total', color_continuous_scale='Reds')
    fig.update_layout(paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=620)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# 3) LEAST 5 STATES (Table)
elif selected_viz == "Least 5 States (Table)":
    df['Total'] = df[['2020', '2021', '2022']].sum(axis=1)
    least5 = df.sort_values('Total', ascending=True).head(5).reset_index(drop=True)
    st.markdown("### 🔻 Least 5 States by Total Cases (2020–2022)", unsafe_allow_html=True)
    st.dataframe(least5.style.format({'Total':"{:,}"}).set_properties(**{'background-color':'#0f0f0f','color':'white'}))

# 4) HORIZONTAL BAR CHART (Selected Year)
elif selected_viz == "Horizontal Bar Chart (Selected Year)":
    sorted_df = year_data.sort_values('Count')
    fig = px.bar(sorted_df, x='Count', y='state', orientation='h', color='Count', text='Count', color_continuous_scale='OrRd')
    fig.update_layout(paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=780)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# 5) GROUPED BAR CHART (2020–2022)
elif selected_viz == "Grouped Bar Chart (2020–2022)":
    df_melt = df.melt(id_vars='state', value_vars=['2020','2021','2022'], var_name='Year', value_name='Count')
    top10 = df.sort_values('Total', ascending=False).head(10)
    df_melt_top10 = top10.melt(id_vars='state', value_vars=['2020','2021','2022'], var_name='Year', value_name='Count')
    fig = px.bar(df_melt_top10, x='state', y='Count', color='Year', barmode='group', color_discrete_sequence=['#FFCC80','#FFD700','#FF7F0E'])
    fig.update_layout(paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=850,
                      xaxis=dict(tickangle=-45, tickfont=dict(color='white')), legend=dict(font=dict(color='white')))
    # small annotation with year labels in top-right
    fig.add_annotation(
        x=1, y=1.02, xref="paper", yref="paper",
        text="<b style='color:white;'>2019 &nbsp;&nbsp; 2020 &nbsp;&nbsp; 2021</b>",
        showarrow=False, align="right", font=dict(color="white", size=12)
    )
    st.plotly_chart(fig, use_container_width=True)

# 6) YEAR-WISE SLOPE PER STATE
elif selected_viz == "Year-wise Slope per State":
    if "state_index" not in st.session_state:
        st.session_state.state_index = 0

    states = df['state'].tolist()
    col_prev, col_center, col_next = st.columns([1, 6, 1])
    with col_prev:
        if st.button("⬅️ Previous"):
            st.session_state.state_index = (st.session_state.state_index - 1) % len(states)
    with col_next:
        if st.button("Next ➡️"):
            st.session_state.state_index = (st.session_state.state_index + 1) % len(states)

    selected_state = states[st.session_state.state_index]
    state_data = df[df['state'] == selected_state][['2020','2021','2022']].melt(var_name='Year', value_name='Count')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=state_data['Year'], y=state_data['Count'],
        mode='lines+markers+text',
        line=dict(color='#FFD700', width=3),
        marker=dict(color='white', size=10),
        text=state_data['Count'],
        textposition='top center'
    ))
    fig.update_layout(title=f"📈 Year-wise Trend — {selected_state}", paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=600)
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"Showing {selected_state} ({st.session_state.state_index+1}/{len(states)})", icon="ℹ️")

# ---------------- INSIGHTS ----------------
with st.expander("📌 Key Insights (2020 - 2022)"):
    total_cases = int(df[['2020','2021','2022']].sum().sum())
    year_sums = df[['2020','2021','2022']].sum()
    max_year = year_sums.idxmax()
    min_year = year_sums.idxmin()
    max_state = df.set_index('state')[['2020','2021','2022']].sum(axis=1).idxmax()
    min_state = df.set_index('state')[['2020','2021','2022']].sum(axis=1).idxmin()
    increase_2022 = int(df['2022'].sum() - df['2020'].sum())
    trend_icon = "📈 Increase" if increase_2022 > 0 else "📉 Decrease"
    st.markdown(f"""
        <div style="background:#1e1e1e;padding:16px;border-radius:8px;color:#FFD700;">
            <p><b>Total cases (2020–2022):</b> {total_cases:,}</p>
            <p><b>Year with max cases:</b> {max_year}</p>
            <p><b>Year with min cases:</b> {min_year}</p>
            <p><b>State with most cases:</b> {max_state}</p>
            <p><b>State with least cases:</b> {min_state}</p>
            <p><b>Trend (2020 → 2022):</b> {trend_icon} </p>
        </div>
    """, unsafe_allow_html=True)
