import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

# ---------------- PAGE CONFIG & THEME ----------------
st.set_page_config(page_title="RAPE CASES", layout="wide")

st.markdown(
    """
    <style>
        /* page background and general text */
        .stApp { background-color: #0b0b0b; color: #FFFFFF; }
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        h1, h2, h3, h4, h5 { color: #FFFFFF !important; }
        /* sidebar labels */
        .stSidebar .stMarkdown, .stSidebar label { color: #FFD700 !important; font-weight:600; }
        /* selectbox label */
        .stSelectbox > label { color: #FFD700 !important; font-weight:600; }
        /* dataframe header */
        .dataframe thead th { color: #FFD700 !important; background-color: #111 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='text-align:center; font-size:2.6rem; margin-bottom:6px; color:white;'>RAPE CASES (2020 - 2022)</h1>",
    unsafe_allow_html=True
)

# ---------------- Sidebar ----------------
st.sidebar.markdown("<h3 style='color:#FFD700;'>Data & GeoJSON (optional)</h3>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Upload Rape Excel (.xlsx)", type=["xlsx"])
uploaded_geo = st.sidebar.file_uploader("Upload India GeoJSON (.json/.geojson)", type=["json", "geojson"])

# ---------------- Load Data Helpers ----------------
@st.cache_data
def load_excel(path=None):
    if path is not None:
        df = pd.read_excel(path)
    else:
        df = pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\rape.xlsx")
    # Normalize columns & ensure years present
    df.columns = [str(c).strip() for c in df.columns]
    # find state column
    state_col = None
    for c in df.columns:
        if c.lower() in ['state', 'state/ut', 'state/ut', 'state/ut name', 'st_nm', 'state name']:
            state_col = c
            break
    if state_col is None:
        state_col = df.columns[0]
    df = df.rename(columns={state_col: 'State/UT'})
    for y in ['2020', '2021', '2022']:
        if y not in df.columns:
            df[y] = 0
    df['State/UT'] = df['State/UT'].astype(str).str.strip()
    for y in ['2020', '2021', '2022']:
        df[y] = pd.to_numeric(df[y], errors='coerce').fillna(0).astype(int)
    return df

@st.cache_data
def load_geo(path=None):
    if path is not None:
        # uploaded file is an UploadedFile object
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

# load
df = load_excel(uploaded_file)
india_geo = load_geo(uploaded_geo)

# ---------------- UI: Year & Viz Dropdown (fixed 6 visuals) ----------------
col1, col2 = st.columns([1, 2])
with col1:
    selected_year = st.selectbox("Select Year", [2020, 2021, 2022])
with col2:
    viz_options = [
        "Choropleth Map ",
        "Top 10 States — Table",
        "Bottom 5 States — Table",
        "Horizontal Bar Chart (Selected Year)",
        "Grouped Bar Chart (2020–2022)",
        "Slope Graph — State-wise Trend "
    ]
    selected_viz = st.selectbox("Select Visualization", viz_options)

st.markdown(f"<h3 style='text-align:center; color:white;'>🔎 {selected_viz} — {selected_year}</h3>", unsafe_allow_html=True)

# Prepare year-specific dataframe
year_col = str(selected_year)
if year_col not in df.columns:
    st.error(f"Year {year_col} not found in dataset.")
    st.stop()
year_data = df[['State/UT', year_col]].copy().rename(columns={year_col: 'Cases'})
year_data['state_norm'] = year_data['State/UT'].str.strip().str.lower()

# ---------------- INTENSITY SCALE (exact provided) ----------------
def intensity_color(val):
    # Use exact scale user gave
    if val > 5000:
        return "#FF2400"  # Red
    elif 2500 < val <= 5000:
        return "#FF7F0E"  # Orange
    elif 1000 < val <= 2500:
        return "#FFD700"  # Yellow
    elif 500 < val <= 1000:
        return "#FFCC80"  # Light Orange
    else:
        return "#FFEFD5"  # Peach

def attach_counts_to_geo(geojson, data_df):
    # Attach Count, hover and color props to each feature
    for feat in geojson.get('features', []):
        props = feat.get('properties', {})
        # try common property keys for state name
        st_nm = ""
        for k in ['st_nm','ST_NM','STATE','state','NAME','DISTRICT','district']:
            if k in props and props[k]:
                st_nm = str(props[k])
                break
        st_norm = st_nm.strip().lower()
        match = data_df.loc[data_df['state_norm'] == st_norm, 'Cases']
        val = int(match.values[0]) if not match.empty else 0
        props['Cases'] = val
        props['hover_text'] = f"{st_nm.title() if st_nm else 'Unknown'}: {val} cases"
        props['color'] = intensity_color(val)
    return geojson

# ---------------- 1) CHOROPLETH MAP ----------------
if selected_viz == viz_options[0]:
    geo = attach_counts_to_geo(india_geo, year_data)

    lons, lats, colors, hovers = [], [], [], []
    for feat in geo.get('features', []):
        geom = feat.get('geometry', {})
        coords = []
        if geom.get('type') == 'Polygon':
            coords = geom.get('coordinates')[0]
        elif geom.get('type') == 'MultiPolygon':
            # pick first polygon of multipolygon
            coords = geom.get('coordinates')[0][0]
        if coords:
            lons.append([c[0] for c in coords])
            lats.append([c[1] for c in coords])
            colors.append(feat.get('properties', {}).get('color', '#FFEFD5'))
            hovers.append(feat.get('properties', {}).get('hover_text', ''))

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
        paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color="white",
        height=880, margin=dict(t=40, b=10, l=10, r=10),
        title=dict(text=f"🗺 Rape Cases Across India — {selected_year}", x=0.5, font=dict(size=18, color='white'))
    )

    col_map, col_leg = st.columns([3,1])
    with col_map:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col_leg:
        st.markdown("### ⚠️ Intensity Scale", unsafe_allow_html=True)
        st.markdown("""
            <div style="background:#FFEFD5; padding:6px; margin:6px; border-radius:6px;">⬜ Below 500</div>
            <div style="background:#FFCC80; padding:6px; margin:6px; border-radius:6px;">⬜ 500 – 1000</div>
            <div style="background:#FFD700; padding:6px; margin:6px; border-radius:6px;">⬜ 1000 – 2500</div>
            <div style="background:#FF7F0E; padding:6px; margin:6px; border-radius:6px;">⬜ 2500 – 5000</div>
            <div style="background:#FF2400; padding:6px; margin:6px; border-radius:6px;">⬜ &gt; 5000</div>
        """, unsafe_allow_html=True)

# ---------------- 2) TOP 10 STATES — TABLE ----------------
elif selected_viz == viz_options[1]:
    df['Total'] = df[['2020','2021','2022']].sum(axis=1)
    top10 = df.sort_values('Total', ascending=False).head(10).reset_index(drop=True)
    st.markdown("### 🔝 Top 10 States by Total Rape Cases (2020–2022)", unsafe_allow_html=True)
    st.dataframe(top10[['State/UT','2020','2021','2022','Total']].rename(columns={'State/UT':'State/UT'}), height=300)

    # Horizontal bar chart (large)
    fig = px.bar(top10.sort_values('Total'), x='Total', y='State/UT', orientation='h', text='Total',
                 color='Total', color_continuous_scale=['#FFEFD5','#FFCC80','#FFD700','#FF7F0E','#FF2400'])
    fig.update_traces(textposition='outside')
    fig.update_layout(paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=760, margin=dict(l=60,r=20,t=30,b=20))
    st.plotly_chart(fig, use_container_width=True)

# ---------------- 3) BOTTOM 5 STATES — TABLE ----------------
elif selected_viz == viz_options[2]:
    df['Total'] = df[['2020','2021','2022']].sum(axis=1)
    bottom5 = df.sort_values('Total', ascending=True).head(5).reset_index(drop=True)
    st.markdown("### 🔻 Bottom 5 States by Total Rape Cases (2020–2022)", unsafe_allow_html=True)
    st.dataframe(bottom5[['State/UT','2020','2021','2022']].rename(columns={'State/UT':'State/UT'}), height=360)

# ---------------- 4) HORIZONTAL BAR CHART (SELECTED YEAR) ----------------
elif selected_viz == viz_options[3]:
    sorted_df = year_data.sort_values('Cases')
    fig = px.bar(sorted_df, x='Cases', y='State/UT', orientation='h', text='Cases',
                 color='Cases', color_continuous_scale=['#FFEFD5','#FFCC80','#FFD700','#FF7F0E','#FF2400'])
    fig.update_traces(textposition='outside')
    fig.update_layout(paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=880, margin=dict(l=60,r=20,t=30,b=20))
    st.plotly_chart(fig, use_container_width=True)

# ---------------- 5) GROUPED BAR CHART (2020–2022) ----------------
elif selected_viz == viz_options[4]:
    df['Total'] = df[['2020','2021','2022']].sum(axis=1)
    top10 = df.sort_values('Total', ascending=False).head(10)
    df_melt = top10.melt(id_vars='State/UT', value_vars=['2020','2021','2022'], var_name='Year', value_name='Count')

    fig = px.bar(df_melt, x='State/UT', y='Count', color='Year', barmode='group',
                 color_discrete_sequence=['#FFCC80', '#FFD700', '#FF7F0E'])
    fig.update_layout(paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=920, margin=dict(l=80,r=30,t=80,b=140))
    fig.update_xaxes(tickangle=-45)

    # Add white year labels on top-right
    fig.add_annotation(x=1, y=1.075, xref='paper', yref='paper',
                       text="<b style='color:white;'>2020&nbsp;&nbsp;&nbsp;2021&nbsp;&nbsp;&nbsp;2022</b>",
                       showarrow=False, align='right')

    st.plotly_chart(fig, use_container_width=True)

# ---------------- 6) SLOPE GRAPH — STATE-WISE TREND (BLACK BG) ----------------
elif selected_viz == viz_options[5]:
    # Index for state navigation
    if "state_idx" not in st.session_state:
        st.session_state.state_idx = 0

    states = df['State/UT'].tolist()
    col_prev, col_center, col_next = st.columns([1,6,1])
    with col_prev:
        if st.button("⬅️ Previous"):
            st.session_state.state_idx = (st.session_state.state_idx - 1) % len(states)
    with col_next:
        if st.button("Next ➡️"):
            st.session_state.state_idx = (st.session_state.state_idx + 1) % len(states)

    sel_state = states[st.session_state.state_idx]
    st.markdown(f"### 📈 Year-wise Trend for **{sel_state}**", unsafe_allow_html=True)
    r = df[df['State/UT'] == sel_state][['2020','2021','2022']].T.reset_index()
    r.columns = ['Year','Count']

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=r['Year'], y=r['Count'],
        mode='lines+markers+text',
        line=dict(color='#FFD700', width=3),
        marker=dict(color='white', size=12),
        text=r['Count'],
        textposition='top center'
    ))
    fig.update_layout(paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=620, margin=dict(t=40,b=20))
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
    <div style="background:#111;padding:16px;border-radius:8px;color:#FFD700;">
        <p><b>Total reported cases (2020–2022):</b> {total:,}</p>
        <p><b>Year with max cases:</b> {max_year}</p>
        <p><b>Year with min cases:</b> {min_year}</p>
        <p><b>State with most cases (total):</b> {max_state}</p>
        <p><b>State with least cases (total):</b> {min_state}</p>
        <p><b>Trend (2020 → 2022):</b> {trend} </p>
    </div>
    """, unsafe_allow_html=True)
