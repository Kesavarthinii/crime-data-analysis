import streamlit as st



# --- Page Config ---
st.set_page_config(
    page_title="Crime Data Search",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS Styling ---
st.markdown("""
    <style>

    html, body, .stApp {
        background: linear-gradient(135deg, #ffffff 0%, #f2f2f2 100%) !important;
        font-family: "Segoe UI", sans-serif;
        color: #111;
    }

    .landing-title {
        font-size: 3rem;
        font-weight: 900;
        color: black;
        text-align: center;
        margin-bottom: 35px;
    }

    div[data-baseweb="select"] > div {
        min-width: 450px !important;
        height: 55px !important;
        background: #fafafa !important;
        border-radius: 12px !important;
        border: 1px solid #d0d0d0 !important;
        padding: 4px 10px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin: 0 auto !important;
    }

    div[data-baseweb="select"] input {
        color: #111 !important;
    }

    /* Search button */
    button[aria-label="🔍 Search"] {
        background: linear-gradient(90deg, #ffc800, #ffe066);
        color: #000;
        font-weight: 800;
        padding: 0.9rem 3rem;
        border-radius: 50px;
        border: none;
        margin-top: 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.15);
    }
    button[aria-label="🔍 Search"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.22);
    }

    /* Centered section title */
    .section-title {
        font-size: 2rem;
        font-weight: 800;
        text-align: center;
        margin-top: 65px;
        margin-bottom: 25px;
        color: black;
    }

    /* Red View Prediction button */
    button[aria-label="View Prediction"] {
        background: linear-gradient(90deg, #ff3b3b, #ff0000);
        color: white;
        padding: 1rem 3rem;
        font-size: 1.2rem;
        font-weight: 800;
        border-radius: 50px;
        border: none;
        box-shadow: 0 8px 25px rgba(255,0,0,0.35);
    }
    button[aria-label="View Prediction"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 14px 40px rgba(255,0,0,0.55);
    }

    </style>
""", unsafe_allow_html=True)

# --- PAGE TITLE ---
st.markdown('<h1 class="landing-title">Crime Data Search</h1>', unsafe_allow_html=True)


# --- PAGE LOGIC ---
crime_pages = {
    "Burglary": "burglars.py",
    "Child Labor": "child_labor.py",
    "Drug offences - Cocaine": "cocaine.py",
    "Cruelty by Husband/Relatives": "cruelty_family.py",
    "Human Trafficking": "human_trafficking.py",
    "Kidnapping and Abduction": "kidnapping_abduction.py",
    "Missing Person": "missing_persons.py",
    "Murder": "murder.py",
    "Rape": "rape.py",
    "Rash Driving": "rash_driving.py",
    "Road Accidents": "road_accidents.py",
    "Sexual Harassment": "sexual_harassment.py",
    "Theft": "theft.py"
}


# --- DROPDOWN ---
selected_crime = st.selectbox("", sorted(crime_pages.keys()))


# --- SEARCH BUTTON ---
if st.button("🔍 Search"):
    page_file = crime_pages.get(selected_crime)
    if page_file:
        st.switch_page(f"pages/{page_file}")



# ----------------------------------------------------------
#      CENTERED PREDICTION SECTION + CENTERED BUTTON
# ----------------------------------------------------------

# Center heading
st.markdown('<h2 class="section-title">Crime Prediction & Hotspot Analysis</h2>',
            unsafe_allow_html=True)

# Center the button using columns
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if st.button("View Prediction"):
        st.switch_page("pages/prediction.py")
