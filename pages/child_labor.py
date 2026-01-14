import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import json

# ---------------- Page Config ----------------
st.set_page_config(page_title="Child Labor Analysis", layout="wide")
st.markdown(
    """
    <style>
        body {background-color: #121212;}
        .block-container {padding-top: 1rem; padding-bottom: 1rem;}
        h1 {color: black !important; text-align: center;}
        h2, h3, h4, h5 {color: black !important;}
        .stSelectbox label, .stFileUploader label {color: #FFD700 !important; font-weight: 600;}
        .css-1d391kg, .css-1offfwp, .stMarkdown {color: #e0e0e0 !important;}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='font-size: 3rem; margin-bottom: 25px;'>🧒 CHILD LABOR CASES (2020 - 2022)</h1>",
    unsafe_allow_html=True
)

# ---------------- Sidebar ----------------
st.sidebar.markdown(
    "<h2 style='color:#FFD700; text-align:center;'>⚙️ Settings</h2>",
    unsafe_allow_html=True
)
uploaded_file = st.sidebar.file_uploader("📑 Upload Child Labor Data (Excel)", type=["xlsx"])
uploaded_geo = st.sidebar.file_uploader("🗺 Upload India GeoJSON", type=["json", "geojson"])

# ---------------- Load Data ----------------
@st.cache_data
def load_data(file_path=None):
    if file_path:
        df = pd.read_excel(file_path)
    else:
        df = pd.read_excel(r"C:\\Users\\kesav\\OneDrive\\DWM\\crime-data-mining\\data\\Child Labour.xlsx")
    df.columns = ['state', '2020', '2021', '2022']
    df['state'] = df['state'].str.strip()
    return df

df = load_data(uploaded_file)

# ---------------- Load GeoJSON ----------------
@st.cache_data
def load_geojson(file_path=None):
    if file_path:
        geo_data = json.load(file_path)
    else:
        with open(r"C:\\Users\\kesav\\OneDrive\\DWM\\crime-data-mining\\data\\india.geojson", "r", encoding="utf-8") as f:
            geo_data = json.load(f)
    return geo_data

india_geo = load_geojson(uploaded_geo)

# ---------------- Year Selection ----------------
st.markdown("<h3 style='margin-top:20px;'>📅 Select Year & Visualization</h3>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])
with col1:
    selected_year = st.selectbox("Choose Year", [2020, 2021, 2022])
with col2:
    viz_options = [
        "Choropleth Map of India",
        "Top 10 States Table",
        "Least 5 States Table",
        "Horizontal Bar Chart (Selected Year)",
        "Grouped Bar Chart (2020–2022)",
        "Yearwise Slope per State"
    ]
    selected_viz = st.selectbox("Choose Visualization", viz_options)

year_data = df[['state', str(selected_year)]].copy()
year_data.rename(columns={str(selected_year): 'Count'}, inplace=True)

# ---------------- Section Title ----------------
st.markdown(
    f"<h2 style='margin:20px 0; text-align:center;'>🔎 {selected_viz} — {selected_year}</h2>",
    unsafe_allow_html=True
)

# -------------------------------------------------------------------
# ---------------------- VISUALIZATION LOGIC ------------------------
# -------------------------------------------------------------------

# ---------------------- 1️⃣ CHOROPLETH MAP --------------------------
if selected_viz == "Choropleth Map of India":
    
    year_data['state'] = year_data['state'].str.strip().str.lower()

    # Apply intensity scale logic
    for f in india_geo['features']:
        state_name = f['properties']['st_nm'].strip().lower()
        match = year_data.loc[year_data['state'] == state_name, 'Count']
        count = int(match.values[0]) if not match.empty else 0
        
        f['properties']['Count'] = count
        f['properties']['hover_text'] = f"{f['properties']['st_nm'].title()}: {count}"

        # --------------- Intensity Scale (based on 100 values) ---------------
        if count > 50:
            f['properties']['color'] = "#B22222"  # deep red
        elif 40 < count <= 50:
            f['properties']['color'] = "#FF4500"  # orange red
        elif 30 < count <= 40:
            f['properties']['color'] = "#FF8C00"  # dark orange
        elif 20< count <= 30:
            f['properties']['color'] = "#FFD700"  # gold
        elif 1 < count <= 20:
            f['properties']['color'] = "#FFE680"  # light yellow
        else:
            f['properties']['color'] = "#2E2E2E"  # very dark grey

    lons, lats, colors, hover_texts = [], [], [], []
    for feature in india_geo['features']:
        polygon = feature['geometry']
        colors.append(feature['properties']['color'])
        hover_texts.append(feature['properties']['hover_text'])

        if polygon['type'] == 'Polygon':
            lons.append([c[0] for c in polygon['coordinates'][0]])
            lats.append([c[1] for c in polygon['coordinates'][0]])

        elif polygon['type'] == 'MultiPolygon':
            lons.append([c[0] for c in polygon['coordinates'][0][0]])
            lats.append([c[1] for c in polygon['coordinates'][0][0]])

    fig = go.Figure()

    for lon, lat, color, hover in zip(lons, lats, colors, hover_texts):
        fig.add_trace(go.Scattergeo(
            lon=lon, lat=lat,
            mode='lines',
            fill='toself',
            fillcolor=color,
            line=dict(width=0.5, color="white"),
            hoverinfo='text', text=hover
        ))

    fig.update_layout(
        geo=dict(
            showland=True, landcolor="#1E1E1E",
            showcountries=True, countrycolor="white",
            projection_type='mercator',
            fitbounds="locations",
        ),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font_color="white",
        height=750,
        title=f"🗺 Child Labor Cases — {selected_year}"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🔥 Intensity Scale")
        st.markdown("""
        <div style='background:#2E2E2E; padding:6px; margin:4px;'>⬛ Below 1</div>
        <div style='background:#FFE680; padding:6px; margin:4px;'>🟨 1 – 20</div>
        <div style='background:#FFD700; padding:6px; margin:4px;'>🟧 20 – 30</div>
        <div style='background:#FF8C00; padding:6px; margin:4px;'>🟧 30 – 40</div>
        <div style='background:#FF4500; padding:6px; margin:4px;'>🟥 40 - 50</div>
        <div style='background:#B22222; padding:6px; margin:4px; color:white;'>🟥 Above 50</div>
        """, unsafe_allow_html=True)

# ---------------------- 2️⃣ TOP 10 STATES TABLE --------------------------
elif selected_viz == "Top 10 States Table":
    top10 = year_data.sort_values("Count", ascending=False).head(10)
    st.dataframe(top10.style.set_properties(**{'background-color': '#1E1E1E', 'color': 'white'}))

# ---------------------- 3️⃣ LEAST 5 STATES TABLE --------------------------
elif selected_viz == "Least 5 States Table":
    least5 = year_data.sort_values("Count", ascending=True).head(5)
    st.dataframe(least5.style.set_properties(**{'background-color': '#1E1E1E', 'color': 'white'}))

# ---------------------- 4️⃣ HORIZONTAL BAR CHART --------------------------
elif selected_viz == "Horizontal Bar Chart (Selected Year)":
    fig = px.bar(
        year_data.sort_values('Count'),
        x='Count', y='state',
        orientation='h',
        text='Count',
        color='Count',
        color_continuous_scale='Agsunset'
    )
    fig.update_layout(
        height=700,
        paper_bgcolor="#121212",
        plot_bgcolor="#121212",
        font_color="white"
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------- 5️⃣ GROUPED BAR CHART --------------------------
elif selected_viz == "Grouped Bar Chart (2020–2022)":

    df_melt = df.melt(id_vars='state', value_vars=['2020','2021','2022'],
                      var_name='Year', value_name='Count')

    fig = px.bar(
        df_melt,
        x='state',
        y='Count',
        color='Year',
        barmode='group',
        color_discrete_sequence=px.colors.sequential.Redor
    )

    fig.update_layout(
        title="Child Labor Cases Across Years",
        paper_bgcolor="#0b0b0b",
        plot_bgcolor="#0b0b0b",
        font_color='white',
        height=850,
        xaxis=dict(tickangle=-45, tickfont=dict(color='white')),
        yaxis=dict(tickfont=dict(color='white')),
        legend=dict(font=dict(color='white', size=16))
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------------- 6️⃣ YEARWISE SLOPE PER STATE --------------------------
elif selected_viz == "Yearwise Slope per State":

    if "state_index" not in st.session_state:
        st.session_state.state_index = 0

    states = df['state'].tolist()

    colA, colB, colC = st.columns([1, 2, 1])
    with colA:
        if st.button("⬅️ Previous"):
            st.session_state.state_index = (st.session_state.state_index - 1) % len(states)

    with colC:
        if st.button("Next ➡️"):
            st.session_state.state_index = (st.session_state.state_index + 1) % len(states)

    state = states[st.session_state.state_index]
    data = df[df['state'] == state].melt(
        id_vars='state',
        value_vars=['2020','2021','2022'],
        var_name='Year', value_name='Count'
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['Year'], y=data['Count'],
        mode='lines+markers+text',
        line=dict(color="gold", width=4),
        marker=dict(size=14, color="white"),
        text=[f"{v}" for v in data['Count']],
        textposition="top center"
    ))

    fig.update_layout(
        height=600,
        title=f"📈 Child Labor Trend – {state}",
        paper_bgcolor="#121212",
        plot_bgcolor="#121212",
        font_color="white"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.info(f"Showing {state} ({st.session_state.state_index + 1}/{len(states)})")

# -------------------------------------------------------------------
# --------------------------- INSIGHTS -------------------------------
# -------------------------------------------------------------------
with st.expander("📊 Key Insights (2020–2022)"):

    total = df[['2020','2021','2022']].sum().sum()
    max_year = df[['2020','2021','2022']].sum().idxmax()
    min_year = df[['2020','2021','2022']].sum().idxmin()
    max_state = df.set_index('state').sum(axis=1).idxmax()
    min_state = df.set_index('state').sum(axis=1).idxmin()

    increase = df['2022'].sum() - df['2020'].sum()
    trend = "📈 Increase" if increase > 0 else "📉 Decrease"

    st.markdown(f"""
    <div style='font-size:18px; padding:20px; border-radius:12px; background:#1E1E1E; color:#FFD700;'>
        <p>👶 Total Child Labor Cases (2020–2022): <b>{total}</b></p>
        <p>📅 Year with Most Cases: <b>{max_year}</b></p>
        <p>📅 Year with Least Cases: <b>{min_year}</b></p>
        <p>📍 Highest State (Total): <b>{max_state}</b></p>
        <p>📍 Lowest State (Total): <b>{min_state}</b></p>
        <p>📊 Trend (2020 → 2022): <b>{trend}</b> 
    </div>
    """, unsafe_allow_html=True)
