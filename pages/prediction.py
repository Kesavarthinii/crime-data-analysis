import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

# Page Config
st.set_page_config(page_title="Crime Prediction", layout="wide")

st.markdown("""
<style>

/* ======== LIGHT THEME BACKGROUND ======== */
.stApp {
    background-color: #ffffff !important;
    color: black !important;
}

/* ======== PAGE HEADERS ======== */
h1, h2, h3, h4, p, label {
    color: black !important;
}

/* ======== SEARCH-PAGE STYLE WHITE DROPDOWN ======== */
div[data-baseweb="select"] > div {
    background-color: #f5f5f5 !important;
    border-radius: 10px !important;
    border: 1px solid #ddd !important;
    min-width: 380px !important;
    height: 55px !important;
}

div[data-baseweb="select"] input {
    height: 100% !important;
    padding-left: 12px !important;
    font-size: 1rem !important;
    color: #222222 !important;
}

div[data-baseweb="select"] span {
    color: #222222 !important;
    white-space: normal !important;
}

/* Dropdown label text */
.stSelectbox label {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: black !important;
}

/* Fix unwanted dark background overlay */
.css-1n76uvr.e1fqkh3o4 {
    background-color: transparent !important;
}

/* Button Style */
.stButton>button {
    padding: 0.9rem 2.4rem !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    border-radius: 50px !important;
    border: none !important;
    cursor: pointer !important;
    background-color: #ffd700 !important;
    color: #000 !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.2) !important;
    transition: all 0.3s ease !important;
}

.stButton>button:hover {
    transform: translateY(-3px) !important;
    background-color: #ffea6b !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.25) !important;
}

/* Center Everything */
.main .block-container {
    display: flex;
    flex-direction: column;
    align-items: center;
}

</style>
""", unsafe_allow_html=True)


# Load all crime datasets
@st.cache_data
def load_crime_data():
    datasets = {
        'Burglars' : pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Burglars.xlsx"),
        'Child Labour' : pd.read_excel(r"C:\\Users\\kesav\\OneDrive\\DWM\\crime-data-mining\\data\\Child Labour.xlsx"),
        'Cruelty cases' : pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Cruelty by Husband or his Relatives.xlsx"),
        'Drug Consumption' : pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\cocaine.xlsx"),
        'Human Trafficking' : pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Human Trafficking.xlsx"),
        'Kidnapping and Abduction' : pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Kidnapping and Abduction.xlsx"),
        'Murder': pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Murder.xlsx"),
        'Theft': pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Theft.xlsx"),
        'Rash Driving': pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Rash Driving.xlsx"),
        'Rape' : pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\rape.xlsx"),
        'Road Accidents': pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Road Accidents.xlsx"),
        'Sexual Harassment': pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Sexual Harassment.xlsx"),
        'Missing Persons': pd.read_excel(r"C:\Users\kesav\OneDrive\DWM\crime-data-mining\data\Missing Persons.xlsx")
    }

    for crime_type, df in datasets.items():
        df.columns = ['State/UT', '2020', '2021', '2022']
    return datasets

datasets = load_crime_data()

crime_type = st.selectbox("Select Crime Type for Prediction:", list(datasets.keys()))
df = datasets[crime_type]

# -----------------------------
# Prediction Functions (Recursive Polynomial degree=2)
# -----------------------------
def predict_future_trends(state_name):
    """
    Recursive forecasting as requested:
    - Predict 2023 using actual [2020,2021,2022]
    - Predict 2024 using [2020,2021,2022, pred_2023]
    - Predict 2025 using [2020,2021,2022, pred_2023, pred_2024]
    Uses polynomial regression (degree=2) at each step so the curve can bend.
    """
    # Extract actuals
    row = df[df['State/UT'] == state_name][['2020','2021','2022']].values.flatten().astype(float)
    years = [2020, 2021, 2022]
    values = list(row.tolist())

    # helper to fit poly and predict single year
    def fit_poly_and_predict(years_list, values_list, year_to_pred, degree=2):
        X = np.array(years_list).reshape(-1, 1)
        poly = PolynomialFeatures(degree=degree, include_bias=False)
        X_poly = poly.fit_transform(X)
        lr = LinearRegression()
        lr.fit(X_poly, np.array(values_list))
        X_pred = poly.transform(np.array([[year_to_pred]]))
        y_pred = lr.predict(X_pred)[0]
        return y_pred

    # Predict 2023
    pred_2023 = fit_poly_and_predict(years, values, 2023, degree=2)
    values.append(pred_2023)
    years.append(2023)

    # Predict 2024 (use 2020,2021,2022,pred_2023)
    pred_2024 = fit_poly_and_predict(years, values, 2024, degree=2)
    values.append(pred_2024)
    years.append(2024)

    # Predict 2025 (use 2020,2021,2022,pred_2023,pred_2024)
    pred_2025 = fit_poly_and_predict(years, values, 2025, degree=2)

    # Round and ensure non-negative ints
    return {
        '2023': max(0, int(round(pred_2023))),
        '2024': max(0, int(round(pred_2024))),
        '2025': max(0, int(round(pred_2025)))
    }

def crime_hotspot_analysis():
    df_analysis = df.copy()
    df_analysis['Total_Cases'] = df_analysis[['2020', '2021', '2022']].sum(axis=1)
    df_analysis['Growth_Rate'] = df_analysis.apply(
        lambda row: (row['2022'] - row['2020']) / row['2020'] if row['2020'] > 0 else 0,
        axis=1
    )

    from sklearn.preprocessing import StandardScaler
    X = df_analysis[['Total_Cases', 'Growth_Rate']].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=3, random_state=42)
    df_analysis['Cluster'] = kmeans.fit_predict(X_scaled)

    centroids = df_analysis.groupby('Cluster')[['Total_Cases', 'Growth_Rate']].mean()
    critical = centroids['Total_Cases'].idxmax()
    safe = centroids['Total_Cases'].idxmin()
    watch = list({0,1,2} - {critical, safe})[0]

    label_map = {critical: 'Critical Hotspot', watch: 'Watch Zone', safe: 'Safe Zone'}
    color_map = {'Critical Hotspot': 'red', 'Watch Zone': 'yellow', 'Safe Zone': 'green'}
    df_analysis['Cluster_Label'] = df_analysis['Cluster'].map(label_map)
    df_analysis['Cluster_Color'] = df_analysis['Cluster_Label'].map(color_map)

    return df_analysis


# Tabs
tab1, tab2, tab3 = st.tabs(["📈 State-wise Prediction", "🔥 Hotspot Clustering", "📊 Risk Analysis"])

# ================= TAB 1 ==================
with tab1:
    st.subheader("State-wise Crime Forecast")
    
    selected_state = st.selectbox("Select State:", df['State/UT'].unique())
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("")
        if st.button("🔮 Predict Future Trends"):
            predictions = predict_future_trends(selected_state)

            state_data = df[df['State/UT'] == selected_state]
            years_hist = [2020, 2021, 2022]
            cases_hist = state_data[['2020', '2021', '2022']].values.flatten()
            future_years = [2023, 2024, 2025]
            future_cases = [predictions['2023'], predictions['2024'], predictions['2025']]

            # ===================== New Graph =====================
            fig = go.Figure()

            # Historical cases as bars
            fig.add_trace(go.Bar(
                x=years_hist,
                y=cases_hist,
                name='Historical Cases',
                marker_color='#FFD700',
                text=[f'{c:,}' for c in cases_hist],
                textposition='auto'
            ))

            # Future predictions as a dashed line
            fig.add_trace(go.Scatter(
                x=future_years,
                y=future_cases,
                mode='lines+markers+text',
                name='Predicted Cases',
                line=dict(color='#FF2400', width=3, dash='dash'),
                marker=dict(size=10, color='#FF2400', symbol='star'),
                text=[f'{c:,}' for c in future_cases],
                textposition='top center'
            ))

            fig.update_layout(
                title=f"Crime Trend for {selected_state}",
                xaxis_title="Year",
                yaxis_title="Number of Cases",
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                font=dict(color="black"),
                height=600,
                width=900,
                legend=dict(x=0.02, y=0.98)
            )

            st.write("<div style='text-align:center'>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=False)
            st.write("</div>", unsafe_allow_html=True)

            current_cases = cases_hist[2]

            st.success(f"""
            **Prediction Results for {selected_state}:**
            - **2022 Actual Cases:** {current_cases:,}
            - **2023 Predicted Cases:** {predictions['2023']:,}
            - **2024 Predicted Cases:** {predictions['2024']:,}
            - **2025 Predicted Cases:** {predictions['2025']:,}
            """)

# ================= TAB 2 ==================
with tab2:
    st.subheader("Crime Hotspot Clustering")
    if st.button("Run Hotspot Analysis"):
        clustered_df = crime_hotspot_analysis()
        clustered_df = clustered_df.sort_values("Total_Cases", ascending=False)

        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            fig = px.bar(
                clustered_df,
                x="Total_Cases",
                y="State/UT",
                orientation="h",
                color="Cluster_Label",
                color_discrete_map={
                    "Critical Hotspot": "red",
                    "Watch Zone": "yellow",
                    "Safe Zone": "green"
                },
                title="Crime Hotspot Clustering Analysis"
                # Removed: text="Growth_Rate"
            )
            # Removed: fig.update_traces(texttemplate='%{text:.2f}', textposition='outside', marker=dict(line=dict(color='black', width=1)))
            fig.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", font=dict(color="black"), height=700, width=900)
            st.plotly_chart(fig, use_container_width=False)

        st.subheader("📋 Cluster Interpretation")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div style="background:#ffffff; border:2px solid #FF2400; padding:15px; border-radius:10px; text-align:center;">
                <h3 style="color:#FF2400;">🔴 CRITICAL HOTSPOT</h3>
                <p style='color:black;'>High crime + Rapid growth</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="background:#ffffff; border:2px solid #FFD700; padding:15px; border-radius:10px; text-align:center;">
                <h3 style="color:#FFD700;">🟡 WATCH ZONES</h3>
                <p style='color:black;'>Moderate crime + Stable growth</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div style="background:#ffffff; border:2px solid #00FF00; padding:15px; border-radius:10px; text-align:center;">
                <h3 style="color:#00FF00;">🟢 SAFE ZONE</h3>
                <p style='color:black;'>Low crime + Decreasing trend</p>
            </div>
            """, unsafe_allow_html=True)

# ================= TAB 3 ==================
with tab3:
    st.subheader("📊 State Risk Scoring & Ranking")
    df_risk = df.copy()
    df_risk['Avg_Cases'] = df_risk[['2020', '2021', '2022']].mean(axis=1)
    
    # Growth_Factor as a Multiplier (End/Start) - Fix for Growth Rate display confusion
    df_risk['Growth_Factor'] = df_risk.apply(lambda row: row['2022'] / row['2020'] if row['2020'] > 0 else 1.0, axis=1)
    
    df_risk['Stability_Score'] = df_risk[['2020','2021','2022']].std(axis=1) / (df_risk['Avg_Cases'] + 1)
    
    df_risk['Risk_Score'] = df_risk['Avg_Cases'] * (1 + abs(df_risk['Growth_Factor'])) * (1 + df_risk['Stability_Score'])
    df_risk['Risk_Score_Normalized'] = (df_risk['Risk_Score'] - df_risk['Risk_Score'].min()) / (df_risk['Risk_Score'].max() - df_risk['Risk_Score'].min()) * 100

    top_risky = df_risk.nlargest(10, 'Risk_Score_Normalized')[['State/UT', 'Risk_Score_Normalized', 'Avg_Cases', 'Growth_Factor']]
    
    # Corrected formatting to display factor '{:.2f}' and fixed set_properties call
    styled = (
        top_risky.style
        .format({'Risk_Score_Normalized': '{:.1f}','Avg_Cases': '{:,.0f}','Growth_Factor': '{:.2f}'})
        .set_properties(
            subset=None, 
            **{'background-color': '#ffffff', 'color': 'black'}
        )
    )
    
    st.dataframe(styled, use_container_width=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        fig = px.bar(
            top_risky.sort_values('Risk_Score_Normalized'),
            x='Risk_Score_Normalized',
            y='State/UT',
            orientation='h',
            title='Top 10 High-Risk States',
            color='Risk_Score_Normalized',
            color_continuous_scale='reds',
            text='Risk_Score_Normalized'
        )
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", font=dict(color="black"), height=500, width=800)
        st.plotly_chart(fig, use_container_width=False)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; padding: 20px; background-color: #ffffff; border-radius: 10px;'>"
    "<h3 style='color:black;'>Crime Prediction Dashboard</h3>",
    
    unsafe_allow_html=True
)