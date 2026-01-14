import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Page Config ---
st.set_page_config(page_title="Crime Data Analysis", layout="wide")

# --- Custom Styling ---
st.markdown("""
    <style>
    .title-text {
        text-align: center;
        font-size: 40px;
        font-weight: bold;
        color: #FF4B4B;
    }
    .tagline {
        text-align: center;
        font-size: 18px;
        color: #555;
        margin-bottom: 20px;
    }
    .dropdown {
        text-align: right;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title & Tagline ---
st.markdown("<div class='title-text'>🔍 Crime Data Analysis in Indian Cities</div>", unsafe_allow_html=True)
st.markdown("<div class='tagline'>Explore crime trends, visualize data, and gain insights by state and year</div>", unsafe_allow_html=True)

# --- Load CSV ---
df = pd.read_csv("data\states_crime_data.csv")

# --- Convert Wide to Long Format ---
df_long = df.melt(id_vars=["State"], var_name="Year", value_name="Total Crimes")

# --- Dropdown Search ---
st.markdown("<div class='dropdown'>", unsafe_allow_html=True)
state_list = df_long['State'].unique()
selected_state = st.selectbox("🔎 Select State", state_list)
st.markdown("</div>", unsafe_allow_html=True)

# --- Filter Data ---
state_data = df_long[df_long['State'] == selected_state]

# --- Show Year-wise Crimes ---
st.subheader(f"📈 Year-wise Crimes in {selected_state}")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(state_data['Year'], state_data['Total Crimes'], marker='o', color='red')
ax.set_xlabel("Year")
ax.set_ylabel("Total Crimes")
ax.set_title(f"Crime Trend in {selected_state}")
st.pyplot(fig)

# --- Preview Table ---
st.subheader("📊 Filtered Data")
st.dataframe(state_data)
