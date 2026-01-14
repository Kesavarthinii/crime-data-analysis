import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Cruelty by Husband/Relatives Analysis", layout="wide")
st.markdown(
    """
    <style>
        /* dark app background */
        .stApp { background-color: #0b0b0b; color: white; }
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        h1, h2, h3, h4 { color: #FFFFFF !important; }
        .stSidebar .css-1d391kg { color: #FFD700 !important; }
        label { color: #FFFFFF !important; }
        .dataframe thead th { color: #FFD700; background-color: #111; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='font-size: 2.6rem; text-align:center; margin-bottom:18px;'>CASES BASED ON CRUELTY BY HUSBAND OR HIS RELATIVES (2020–2022)</h1>",
    unsafe_allow_html=True
)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data(path=None):
    if path is not None:
        df = pd.read_excel(path)
    else:
        df = pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Cruelty by Husband or his Relatives.xlsx")
    # normalize
    df.columns = [str(c).strip() for c in df.columns]
    # Ensure columns: state, 2020, 2021, 2022
    if 'state' not in [c.lower() for c in df.columns]:
        df = df.rename(columns={df.columns[0]: 'state'})
    rename_map = {}
    for y in ['2020','2021','2022']:
        for c in df.columns:
            if str(c).strip() == y:
                rename_map[c] = y
    if rename_map:
        df = df.rename(columns=rename_map)
    # Ensure years exist
    for y in ['2020','2021','2022']:
        if y not in df.columns:
            df[y] = 0
    df = df[['state','2020','2021','2022']]
    df['state'] = df['state'].astype(str).str.strip()
    # coerce numeric
    for y in ['2020','2021','2022']:
        df[y] = pd.to_numeric(df[y], errors='coerce').fillna(0).astype(int)
    return df

df = load_data(None)

# ---------------- LOAD GEOJSON ----------------
@st.cache_data
def load_geojson(path=None):
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

india_geo = load_geojson(None)

# ---------------- UI: Year & Visualization Selection ----------------
st.markdown("<h3 style='margin-top:8px; color:white;'>📅 Select Year & Visualization</h3>", unsafe_allow_html=True)
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
        "Yearwise Slope per State"
    ]
    selected_viz = st.selectbox("Choose Visualization", viz_options)

# prepare year_data
year_data = df[['state', str(selected_year)]].copy().rename(columns={str(selected_year): 'Count'})
year_data['state_norm'] = year_data['state'].str.strip().str.lower()

# big title
st.markdown(f"<h2 style='text-align:center; color:white; margin:16px 0;'>🔎 {selected_viz} — {selected_year}</h2>", unsafe_allow_html=True)

# ---------------- helper: populate geojson using user's final scale ----------------
def apply_cruelty_scale(geojson, data_df):
    """
    Intensity ranges (as provided):
    - < 500 -> 0 - 500
    - 1000 - 3000 -> 1000 - 3000
    - 3000 - 7000 -> 3000 - 7000
    - 7000 - 10000 -> 7000 - 10000
    - 10000 - 15000 -> 10000 - 15000
    - > 15000
    Colors assigned accordingly.
    """
    # normalize data names
    data_df['state_norm'] = data_df['state'].astype(str).str.strip().str.lower()
    for feature in geojson.get('features', []):
        props = feature.get('properties', {})
        st_nm = str(props.get('st_nm') or props.get('STATE') or '').strip().lower()
        match = data_df.loc[data_df['state_norm'] == st_nm, 'Count']
        val = int(match.values[0]) if not match.empty else 0
        feature['properties']['Count'] = val
        feature['properties']['hover_text'] = f"{(props.get('st_nm') or st_nm).title()}: {val:,}"

        # apply ranges (interpreting '15' as 15,000)
        if val > 15000:
            feature['properties']['color'] = "#FF2400"   # deep red
        elif 10000 < val <= 15000:
            feature['properties']['color'] = "#FF4500"   # orange-red
        elif 7000 < val <= 10000:
            feature['properties']['color'] = "#FF8C00"   # orange
        elif 3000 < val <= 7000:
            feature['properties']['color'] = "#FFD700"   # gold
        elif 1000 < val <= 3000:
            feature['properties']['color'] = "#FFCC80"   # light orange
        elif val <= 500:
            feature['properties']['color'] = "#FFEFD5"   # peach (very low)
        else:
            # for 501 - 1000 and  301-500 ranges fallback to light peach
            feature['properties']['color'] = "#FFF2E0"

# ---------------- VISUALIZATIONS ----------------

# 1) Choropleth Map (Big View)
if selected_viz == "Choropleth Map (Big View)":
    apply_cruelty_scale(india_geo, year_data)

    # extract polygons
    lons, lats, colors, hovers = [], [], [], []
    for feature in india_geo.get('features', []):
        geom = feature.get('geometry', {})
        props = feature.get('properties', {})
        color = props.get('color', "#1E1E1E")
        hover = props.get('hover_text', '')
        if geom.get('type') == 'Polygon':
            coords = geom.get('coordinates')[0]
            lons.append([c[0] for c in coords])
            lats.append([c[1] for c in coords])
            colors.append(color)
            hovers.append(hover)
        elif geom.get('type') == 'MultiPolygon':
            # take first polygon part
            coords = geom.get('coordinates')[0][0]
            lons.append([c[0] for c in coords])
            lats.append([c[1] for c in coords])
            colors.append(color)
            hovers.append(hover)

    fig = go.Figure()
    for lon, lat, color, hover in zip(lons, lats, colors, hovers):
        fig.add_trace(go.Scattergeo(
            lon=lon, lat=lat,
            mode='lines', fill='toself',
            fillcolor=color,
            line=dict(width=0.5, color='white'),
            hoverinfo='text', text=hover,
            showlegend=False
        ))

    fig.update_layout(
        geo=dict(
            showland=True, landcolor="#0b0b0b",
            showcountries=True, countrycolor="white",
            projection_type='mercator',
            fitbounds="locations"
        ),
        paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b",
        font_color="white",
        height=900,
        margin=dict(t=40, b=10, l=10, r=10),
        title=dict(text=f"🗺 Cruelty by Husband/Relatives — {selected_year}", x=0.5, font=dict(color='white', size=20))
    )

    col_map, col_legend = st.columns([4, 1])
    with col_map:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col_legend:
        st.markdown("### 🎨 Intensity Scale", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#FFEFD5; padding:6px; margin:6px; border-radius:6px;">⬜ 0 – 500</div>
        <div style="background:#FFCC80; padding:6px; margin:6px; border-radius:6px;">⬜ 1,000 – 3,000</div>
        <div style="background:#FFD700; padding:6px; margin:6px; border-radius:6px;">⬜ 3,000 – 7,000</div>
        <div style="background:#FF8C00; padding:6px; margin:6px; border-radius:6px; color:white;">⬜ 7,000 – 10,000</div>
        <div style="background:#FF4500; padding:6px; margin:6px; border-radius:6px; color:white;">⬜ 10,000 – 15,000</div>
        <div style="background:#FF2400; padding:6px; margin:6px; border-radius:6px; color:white;">⬜ Above 15,000</div>
        """, unsafe_allow_html=True)

# 2) Top 10 States (Table)
elif selected_viz == "Top 10 States (Table)":
    df['Total'] = df[['2020','2021','2022']].sum(axis=1)
    top10 = df.sort_values('Total', ascending=False).head(10).reset_index(drop=True)
    st.markdown("### 🔝 Top 10 States by Total Cases (2020–2022)", unsafe_allow_html=True)
    st.dataframe(top10.style.format({'Total':"{:,}", '2020':"{:,}", '2021':"{:,}", '2022':"{:,}"}).set_properties(**{'background-color':'#0f0f0f','color':'white'}))

# 3) Least 5 States (Table)
elif selected_viz == "Least 5 States (Table)":
    df['Total'] = df[['2020','2021','2022']].sum(axis=1)
    least5 = df.sort_values('Total', ascending=True).head(5).reset_index(drop=True)
    st.markdown("### 🔻 Least 5 States by Total Cases (2020–2022)", unsafe_allow_html=True)
    st.dataframe(least5.style.format({'Total':"{:,}", '2020':"{:,}", '2021':"{:,}", '2022':"{:,}"}).set_properties(**{'background-color':'#0f0f0f','color':'white'}))

# 4) Horizontal Bar Chart (Selected Year)
elif selected_viz == "Horizontal Bar Chart (Selected Year)":
    sorted_states = year_data.sort_values('Count', ascending=True)
    fig = go.Figure(go.Bar(
        x=sorted_states['Count'],
        y=sorted_states['state'],
        orientation='h',
        marker=dict(color=sorted_states['Count'], colorscale='YlOrRd', showscale=True),
        text=sorted_states['Count'],
        textposition='outside'
    ))
    fig.update_layout(
        title=f"Cases by State — {selected_year}",
        paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b",
        font_color='white', height=800,
        xaxis=dict(tickfont=dict(color='white')), yaxis=dict(tickfont=dict(color='white'))
    )
    st.plotly_chart(fig, use_container_width=True)

# 5) Grouped Bar Chart (2020–2022) with white legend text
elif selected_viz == "Grouped Bar Chart (2020–2022)":
    df_melt = df.melt(id_vars='state', value_vars=['2020','2021','2022'], var_name='Year', value_name='Count')
    fig = px.bar(df_melt, x='state', y='Count', color='Year', barmode='group',
                 color_discrete_sequence=['#FFCC80','#FFD700','#FF7F0E'])
    fig.update_layout(
        title="Comparison (2020–2022)",
        paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=850,
        xaxis=dict(tickangle=-45, tickfont=dict(color='white')),
        yaxis=dict(tickfont=dict(color='white')),
        legend=dict(font=dict(color='white', size=14), bgcolor='rgba(0,0,0,0)')
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
    state_data = df[df['state'] == selected_state].melt(id_vars='state', value_vars=['2020','2021','2022'], var_name='Year', value_name='Count')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=state_data['Year'], y=state_data['Count'],
        mode='lines+markers+text',
        text=state_data['Count'],
        textposition='top center',
        line=dict(color='#FFD700', width=4),
        marker=dict(size=12, color='white')
    ))
    fig.update_layout(
        title=f"📈 Year-wise Trend — {selected_state}",
        paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b", font_color='white', height=600,
        xaxis=dict(tickfont=dict(color='white')), yaxis=dict(tickfont=dict(color='white'))
    )
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"Showing {selected_state} ({st.session_state.state_index + 1}/{len(states)})", icon="ℹ️")

# ---------------- INSIGHTS ----------------
with st.expander("📊 Key Insights (2020 - 2022)"):
    total_cases = int(df[['2020','2021','2022']].sum().sum())
    sum_by_year = df[['2020','2021','2022']].sum()
    max_year = sum_by_year.idxmax()
    min_year = sum_by_year.idxmin()
    max_state = df.set_index('state')[['2020','2021','2022']].sum(axis=1).idxmax()
    min_state = df.set_index('state')[['2020','2021','2022']].sum(axis=1).idxmin()
    increase_2022 = int(df['2022'].sum() - df['2020'].sum())
    trend_icon = "📈 Increase" if increase_2022 > 0 else "📉 Decrease"

    st.markdown(f"""
    <div style="font-size:17px; line-height:1.8; background-color:#1e1e1e; padding:16px; border-radius:10px; color:#FFD700;">
        <p>💔 <b>Total reported cases (2020–2022):</b> {total_cases:,}</p>
        <p>📅 <b>Year with maximum cases:</b> {max_year}</p>
        <p>📌 <b>State with most cases overall:</b> {max_state}</p>
        <p>⚖️ <b>State with least cases:</b> {min_state}</p>
        <p>📈 <b>Overall trend (2020 → 2022):</b> {trend_icon} </p>
    </div>
    """, unsafe_allow_html=True)
