import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import json

# ---------------- Page Config ----------------
st.set_page_config(page_title="Burglary Crime Analysis", layout="wide")
st.markdown(
    """
    <style>
        /* overall dark background */
        .stApp { background-color: #0f0f0f; color: white; }
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }

        /* headings */
        h1 { color: #FFFFFF !important; text-align: center; }
        h2, h3, h4, h5 { color: #FFFFFF !important; }

        /* sidebar title */
        .stSidebar .css-1d391kg { color: #FFD700 !important; }

        /* ensure selectbox labels readable */
        label { color: #FFFFFF !important; }

        /* tables */
        .dataframe thead th { color: #FFD700; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='font-size: 3rem; margin-bottom: 20px;'>📂 BURGLARY CASES (2020 - 2022)</h1>",
    unsafe_allow_html=True
)

# ---------------- Sidebar ----------------
st.sidebar.markdown("<h2 style='color:#FFD700; text-align:center;'>⚙️ Settings</h2>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("📑 Upload Crime Data (Excel)", type=["xlsx"])
uploaded_geo = st.sidebar.file_uploader("🗺 Upload India GeoJSON", type=["json", "geojson"])

# ---------------- Load Data ----------------
@st.cache_data
def load_data(file_path=None):
    if file_path is not None:
        df = pd.read_excel(file_path)
    else:
        df = pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Burglars.xlsx")
    # normalize column names if needed
    df.columns = [str(c).strip() for c in df.columns]
    # expect first column to be state name, last three columns years (2020,2021,2022)
    # Try to coerce to required format
    # If header names are already 'state','2020','2021','2022' this will still work
    cols_lower = [c.lower() for c in df.columns]
    # find year columns
    # If exact names present, rename them as standard
    rename_map = {}
    for y in ['2020','2021','2022']:
        for c in df.columns:
            if str(c).strip() == y:
                rename_map[c] = y
    if rename_map:
        df = df.rename(columns=rename_map)
    # Ensure first column is state
    if 'state' not in [c.lower() for c in df.columns]:
        # assume first column is state
        cols = list(df.columns)
        df = df.rename(columns={cols[0]: 'state'})
    # final rename to standard
    standard_cols = ['state', '2020', '2021', '2022']
    # If some year columns missing, keep what exists
    existing = [c for c in standard_cols if c in df.columns]
    df = df[[col for col in df.columns if col in existing or col == 'state'] + [c for c in df.columns if c not in existing and c != 'state']]
    # Strip state names
    df['state'] = df['state'].astype(str).str.strip()
    # Ensure numeric columns are numeric
    for y in ['2020','2021','2022']:
        if y in df.columns:
            df[y] = pd.to_numeric(df[y], errors='coerce').fillna(0).astype(int)
    return df

df = load_data(uploaded_file)

# ---------------- Load GeoJSON ----------------
@st.cache_data
def load_geojson(file_path=None):
    if file_path is not None:
        # uploaded_geo is an UploadedFile object from Streamlit; read bytes then json.loads
        try:
            content = file_path.read()
            return json.loads(content)
        except Exception:
            file_path.seek(0)
            return json.load(file_path)
    else:
        with open(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\india.geojson", "r", encoding="utf-8") as f:
            return json.load(f)

india_geo = load_geojson(uploaded_geo)

# ---------------- UI: Year & Visualization Selection ----------------
st.markdown("<h3 style='margin-top:10px;'>📅 Select Year & Visualization</h3>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])
with col1:
    selected_year = st.selectbox("Choose Year", [2020, 2021, 2022])
with col2:
    viz_options = [
        "Choropleth Map (Big View)",
        "Top 10 States (Table)",
        "Least 5 States (Table)",
        "Horizontal Bar Chart (Selected Year)",
        "Grouped Bar Chart (2020–2022)",
        "Yearwise Slope per State"
    ]
    selected_viz = st.selectbox("Choose Visualization", viz_options)

# Prepare year_data
year_data = df[['state', str(selected_year)]].copy()
year_data.rename(columns={str(selected_year): 'Count'}, inplace=True)

# Big visualization title (white text)
st.markdown(f"<h2 style='margin:20px 0; text-align:center; color: #FFFFFF;'>🔎 {selected_viz} - {selected_year}</h2>", unsafe_allow_html=True)

# ---------------- Helper: prepare geoplot properties ----------------
def prepare_geojson_values(data_df, geojson, value_col='Count'):
    """Populate geojson features with Count and color according to Option A scale."""
    # Normalize state names in data
    data_df['state_norm'] = data_df['state'].astype(str).str.strip().str.lower()

    for feature in geojson.get('features', []):
        st_nm = feature['properties'].get('st_nm', feature['properties'].get('STATE', '')).strip().lower()
        match = data_df.loc[data_df['state_norm'] == st_nm, value_col]
        val = int(match.values[0]) if not match.empty else 0
        feature['properties']['Count'] = int(val)
        feature['properties']['hover_text'] = f"{feature['properties'].get('st_nm', st_nm).title()}: {val:,}"

        # Option A thresholds (interpreted as thousands)
        # <1000, 10k-20k, 20k-30k, 30k-50k, 50k-60k, >60k
        if val > 30000:
            feature['properties']['color'] = "#8B0000"  # deep red
        elif 15000 < val <= 30000:
            feature['properties']['color'] = "#B22222"
        elif 5000 < val <= 15000:
            feature['properties']['color'] = "#FF4500"
        elif 2000 < val <= 5000:
            feature['properties']['color'] = "#FF8C00"
        elif 1000 < val <= 2000:
            feature['properties']['color'] = "#FFDAB9"
        else:
            feature['properties']['color'] = "#2E2E2E" if val >= 1000 else "#1E1E1E"  # darker greys for low/very low

# ---------------- Visualizations ----------------

# 1) Choropleth Map (Big View)
if selected_viz == "Choropleth Map (Big View)":
    prepare_geojson_values(year_data, india_geo, value_col='Count')

    # Extract polygon coordinates
    lons, lats, colors, hovers = [], [], [], []
    for feature in india_geo['features']:
        geom = feature['geometry']
        colors.append(feature['properties'].get('color', '#1e1e1e'))
        hovers.append(feature['properties'].get('hover_text', ''))

        if geom['type'] == 'Polygon':
            coords = geom['coordinates'][0]
            lons.append([c[0] for c in coords])
            lats.append([c[1] for c in coords])
        elif geom['type'] == 'MultiPolygon':
            coords = geom['coordinates'][0][0]
            lons.append([c[0] for c in coords])
            lats.append([c[1] for c in coords])

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
            showland=True, landcolor="#0b0b0b",
            showcountries=True, countrycolor="white",
            showocean=False,
            projection_type='mercator',
            fitbounds="locations"
        ),
        margin=dict(t=40, b=10, l=10, r=10),
        paper_bgcolor="#0b0b0b",
        plot_bgcolor="#0b0b0b",
        font=dict(color='white', family="Arial"),
        height=900,
        title=dict(text=f"🗺 Burglary Cases Across India — {selected_year}", x=0.5, font=dict(size=20, color='white'))
    )

    # show map large + legend on side
    col_map, col_legend = st.columns([4, 1])
    with col_map:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_legend:
        st.markdown("### 🔸 Intensity Scale", unsafe_allow_html=True)
        st.markdown("""
        <div style="background-color:#1e1e1e; padding:8px; border-radius:6px;">
        <div style="background-color:#1E1E1E; padding:6px; margin:6px; color:white;">⬜ Below 1,000</div>
        <div style="background-color:#FFD700; padding:6px; margin:6px; color:black;">⬜ 1000 – 2000</div>
        <div style="background-color:#FF8C00; padding:6px; margin:6px; color:black;">⬜ 2000 – 5000</div>
        <div style="background-color:#FF4500; padding:6px; margin:6px; color:white;">⬜ 5000 – 15000</div>
        <div style="background-color:#B22222; padding:6px; margin:6px; color:white;">⬜ 15000 – 30000</div>
        <div style="background-color:#8B0000; padding:6px; margin:6px; color:white;">⬜ Above 30000</div>
        </div>
        """, unsafe_allow_html=True)

# 2) Top 10 States (Table)
elif selected_viz == "Top 10 States (Table)":
    df['total'] = df[['2020','2021','2022']].sum(axis=1)
    top10 = df.sort_values('total', ascending=False).head(10).reset_index(drop=True)
    # style dataframe for better visibility
    st.markdown("### 🔝 Top 10 States by Total Burglary (2020–2022)", unsafe_allow_html=True)
    st.dataframe(top10.style.format({ 'total': "{:,}" , '2020':"{:,}", '2021':"{:,}", '2022':"{:,}" }).set_properties(**{'color': 'white', 'background-color': '#1e1e1e'}))

# 3) Least 5 States (Table)
elif selected_viz == "Least 5 States (Table)":
    df['total'] = df[['2020','2021','2022']].sum(axis=1)
    least5 = df.sort_values('total', ascending=True).head(5).reset_index(drop=True)
    st.markdown("### 🔻 Least 5 States by Total Burglary (2020–2022)", unsafe_allow_html=True)
    st.dataframe(least5.style.format({ 'total': "{:,}" , '2020':"{:,}", '2021':"{:,}", '2022':"{:,}" }).set_properties(**{'color': 'white', 'background-color': '#1e1e1e'}))

# 4) Horizontal Bar Chart (Selected Year)
elif selected_viz == "Horizontal Bar Chart (Selected Year)":
    # big figure
    sorted_states = year_data.sort_values('Count', ascending=True)
    fig = go.Figure(go.Bar(
        x=sorted_states['Count'],
        y=sorted_states['state'],
        orientation='h',
        marker=dict(color=sorted_states['Count'], colorscale='Inferno', showscale=True),
        text=sorted_states['Count'],
        textposition='outside'
    ))
    fig.update_layout(
        title=f"Burglary Cases by State — {selected_year}",
        paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=800,
        xaxis=dict(tickfont=dict(color='white')), yaxis=dict(tickfont=dict(color='white'))
    )
    st.plotly_chart(fig, use_container_width=True)

elif selected_viz == "Grouped Bar Chart (2020–2022)":
    df_melt = df.melt(id_vars='state', value_vars=['2020','2021','2022'],
                      var_name='Year', value_name='Count')

    fig = px.bar(
        df_melt,
        x='state',
        y='Count',
        color='Year',
        barmode='group',
        color_discrete_sequence=px.colors.sequential.Plasma
    )

    fig.update_layout(
        title="Burglary Cases Across States (2020–2022)",
        paper_bgcolor="#0b0b0b",
        plot_bgcolor="#0b0b0b",
        font_color='white',
        height=800,

        # axis labels white
        xaxis=dict(tickangle=-45, tickfont=dict(color='white')),
        yaxis=dict(tickfont=dict(color='white')),

        # ⭐ legend text (year numbers) made white ⭐
        legend=dict(
            font=dict(color='white', size=14),
            bgcolor="rgba(0,0,0,0)"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

# 6) Yearwise Slope per State
elif selected_viz == "Yearwise Slope per State":
    if "state_index" not in st.session_state:
        st.session_state.state_index = 0

    states = df['state'].tolist()
    col_prev, col_info, col_next = st.columns([1, 6, 1])
    with col_prev:
        if st.button("⬅️ Previous"):
            st.session_state.state_index = (st.session_state.state_index - 1) % len(states)
    with col_next:
        if st.button("Next ➡️"):
            st.session_state.state_index = (st.session_state.state_index + 1) % len(states)

    selected_state = states[st.session_state.state_index]
    state_data = df[df['state'] == selected_state].melt(id_vars='state', value_vars=['2020','2021','2022'],
                                                       var_name='Year', value_name='Count')
    # build slope chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=state_data['Year'], y=state_data['Count'],
        mode='lines+markers+text',
        text=state_data['Count'],
        textposition='top center',
        line=dict(color='#FFD700', width=4),
        marker=dict(size=12, color='#FFD700')
    ))
    fig.update_layout(
        title=f"📈 Year-wise Burglary Trend — {selected_state}",
        paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=600,
        xaxis=dict(tickfont=dict(color='white')), yaxis=dict(tickfont=dict(color='white'))
    )
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"Showing {selected_state} ({st.session_state.state_index+1}/{len(states)})", icon="ℹ️")

# ---------------- Insights ----------------
with st.expander("📊 Key Insights (2020 - 2022)"):
    total_crimes = int(df[['2020','2021','2022']].sum().sum())
    # sum by year
    sum_by_year = df[['2020','2021','2022']].sum()
    max_year = sum_by_year.idxmax()
    min_year = sum_by_year.idxmin()
    max_state = df.set_index('state')[['2020','2021','2022']].sum(axis=1).idxmax()
    min_state = df.set_index('state')[['2020','2021','2022']].sum(axis=1).idxmin()
    increase_2022 = int(df['2022'].sum() - df['2020'].sum())
    avg_crimes = float(df[['2020','2021','2022']].mean().mean())

    st.markdown(f"""
    <div style="font-size:16px; line-height:1.8; color:#FFFFFF; background-color:#0b0b0b; padding:18px; border-radius:10px;">
        <p>📌 <b>Total burglaries (2020–2022):</b> {total_crimes:,}</p>
        <p>📌 <b>Year with max crimes:</b> {max_year}</p>
        <p>📌 <b>Year with min crimes:</b> {min_year}</p>
        <p>📌 <b>Most affected state:</b> {max_state}</p>
        <p>📌 <b>Least affected state:</b> {min_state}</p>
        <p>📌 <b>Trend (2020 → 2022):</b> {"📈 Increase" if increase_2022 > 0 else "📉 Decrease"}</p>
        <p>📌 <b>Average crimes per year:</b> {avg_crimes:.2f}</p>
    </div>
    """, unsafe_allow_html=True)
