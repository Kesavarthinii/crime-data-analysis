import streamlit as st

# Page Config
st.set_page_config(
    page_title="Crime Data Analysis",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS ---
st.markdown("""
    <style>
        /* Hide Streamlit UI elements */
        #MainMenu, footer, header {visibility: hidden !important;}
        .block-container {padding: 0 !important;}
        
        /* Full page background */
        .stApp {
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)),
                        url('https://images.unsplash.com/photo-1549488344-9359e1875154?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80');
            background-size: cover;
            background-position: center;
            min-height: 100vh;
            position: relative;
        }
        
        /* Splash container for title and subtitle */
        .splash-container {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            width: 90%;
            max-width: 900px;
            padding: 40px 20px;
            z-index: 15;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 20px;
            backdrop-filter: blur(5px);
        }
        
        /* Main title - make it VERY visible */
        .splash-container h1 {
            font-family: 'Bebas Neue', sans-serif !important;
            font-size: 8rem !important;
            margin: 0 0 2rem 0 !important;
            color: #ffffff !important;
            text-shadow: 
                0 0 10px rgba(255,255,255,0.8),
                5px 5px 0px rgba(0,0,0,1),
                10px 10px 20px rgba(0,0,0,1) !important;
            line-height: 0.9 !important;
            font-weight: 900 !important;
            letter-spacing: 4px !important;
            text-transform: uppercase !important;
        }
        
        /* Subtitle */
        .splash-container h2 {
            font-family: 'Montserrat', sans-serif !important;
            font-size: 2.4rem !important;
            font-weight: 600 !important;
            margin: 0 !important;
            color: #ffd700 !important;
            text-shadow: 
                0 0 5px rgba(255,215,0,0.8),
                3px 3px 0px rgba(0,0,0,1),
                6px 6px 15px rgba(0,0,0,1) !important;
        }
        
        /* Position button at bottom of screen */
        .bottom-button {
            position: fixed;
            bottom: 50px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 20;
        }
        
        /* Center the Streamlit button */
        .bottom-button div.stButton {
            display: flex;
            justify-content: center;
            margin: 0;
        }
        
        .bottom-button div.stButton > button {
            padding: 1.2rem 4rem !important;
            font-size: 1.3rem !important;
            font-weight: 700 !important;
            font-family: 'Montserrat', sans-serif !important;
            text-transform: uppercase !important;
            color: #000 !important;
            background-color: #ffd700 !important;
            border: none !important;
            border-radius: 50px !important;
            box-shadow: 0 8px 25px rgba(0,0,0,0.6) !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
        }
        
        .bottom-button div.stButton > button:hover {
            transform: translateY(-4px) !important;
            background-color: #ffed4e !important;
            box-shadow: 0 12px 30px rgba(0,0,0,0.7) !important;
            color: #000 !important;
        }
    </style>
    <!-- Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# --- Splash Content ---
st.markdown("""
    <div class="splash-container">
        <h1>Crime Data Analysis</h1>
        <h2>Predictive Crime Insights with Hotspot and Risk Analysis Intelligence.</h2>
    </div>
""", unsafe_allow_html=True)

# Create button at bottom of screen
st.markdown('<div class="bottom-button">', unsafe_allow_html=True)
if st.button("VIEW ANALYSIS", key="go_dashboard"):
    st.switch_page("pages/search.py")
st.markdown('</div>', unsafe_allow_html=True)
