# CRIME DATA ANALYSIS & PREDICTION

Crime Data Analysis & Prediction is a Python + Streamlit based application that transforms raw crime statistics into meaningful insights and future forecasts.
It not only analyzes historical crime data but also predicts future crime trends, identifies hotspots, and performs risk scoring for better decision-making.

The system:

Reads structured crime datasets (CSV/Excel)

Cleans and processes data using Pandas

Visualizes insights through interactive dashboards

Uses predictive models to forecast crime patterns

Instead of working with static tables, this project gives a dynamic, visual, and predictive view of crime data.


## WHAT THIS PROJECT CAN DO
### Analysis

State-wise and year-wise crime trend analysis

Crime type comparison

Interactive filtering and dashboards

### Prediction

Forecast future crime cases

State-wise crime prediction

Trend-based growth and decline analysis

### Hotspot & Risk Intelligence

Crime hotspot clustering

Risk scoring and ranking of states

Identification of critical, watch, and safe zones

## Features 
### Crime Data Search
This feature allows users to search crime data by selecting specific crime types.
It makes exploring large datasets faster and more focused.
<img width="1545" height="853" alt="Screenshot 2026-01-14 103545" src="https://github.com/user-attachments/assets/0719d994-f742-4ac2-beb9-5842fc8015cf" />
<img width="1888" height="850" alt="Screenshot 2026-01-14 103615" src="https://github.com/user-attachments/assets/4ffda543-b89b-4cbd-843c-c0d897545b9e" />

### Choropleth Crime Map
This map visualizes crime intensity across Indian states using color scales.
It helps quickly identify regions with higher or lower crime concentration.
<img width="1892" height="815" alt="Screenshot 2026-01-14 103749" src="https://github.com/user-attachments/assets/fb950383-3bcc-40c6-a25c-6f8b39e1ded3" />

### Top States by Crime Cases
This view ranks states based on total reported cases over multiple years.
It highlights which regions require greater attention and policy focus.
<img width="1888" height="784" alt="Screenshot 2026-01-14 103833" src="https://github.com/user-attachments/assets/7d082add-6a68-40c8-ae0d-a5e1d8b0784d" />

### Grouped Bar Chart Analysis
This chart compares crime cases across years for multiple states side by side.
It makes year-wise growth and decline patterns easy to understand.
<img width="1871" height="806" alt="Screenshot 2026-01-14 103909" src="https://github.com/user-attachments/assets/72505ffb-591c-4d5c-9801-1b8415455ce6" />

### State-wise Trend (Slope Graph)
This visualization shows how crime trends change over time for a selected state.
It clearly presents whether crime is increasing, decreasing, or stabilizing.
<img width="1902" height="788" alt="Screenshot 2026-01-14 103935" src="https://github.com/user-attachments/assets/0c769e45-77c4-4ddf-93bb-c16a4c0aa5ef" />

### Key Insights Panel
This section summarizes important findings like highest crime year and top states.
It provides instant takeaways without needing deep data analysis.
<img width="1840" height="547" alt="Screenshot 2026-01-14 104008" src="https://github.com/user-attachments/assets/8647166d-d259-4bfd-9836-864a7882af31" />

### State-wise Crime Prediction
This dashboard forecasts future crime cases using historical data trends.
It helps understand how crime patterns may evolve in the coming years.
<img width="1852" height="794" alt="Screenshot 2026-01-14 104135" src="https://github.com/user-attachments/assets/3f8e4b68-32a5-4826-8c49-24d5999027f1" />
<img width="1741" height="790" alt="Screenshot 2026-01-14 104249" src="https://github.com/user-attachments/assets/d22caf8c-edd4-45d4-895d-3a651beb272b" />

### Hotspot Clustering Analysis
This feature groups states into critical, watch, and safe zones using clustering.
It supports better risk assessment and safety planning.
<img width="1786" height="836" alt="Screenshot 2026-01-14 104357" src="https://github.com/user-attachments/assets/f2f27f2d-fefc-4ff0-8a04-0d38ec1ab0f6" />

### Risk Scoring & Ranking
This dashboard ranks states based on normalized risk scores and growth factors.
It helps identify the most vulnerable regions at a glance.
<img width="1592" height="567" alt="Screenshot 2026-01-14 104452" src="https://github.com/user-attachments/assets/e3a18883-49a2-448a-b2f0-2cc4a5b23c6d" />


## HOW TO RUN THIS?
Clone the repository
git clone https://github.com/your-username/crime-data-analysis.git
cd crime-data-analysis

Set up your Python environment
python -m venv venv


Activate it:

Windows

venv\Scripts\activate


macOS / Linux

source venv/bin/activate

Install dependencies
pip install -r requirements.txt

Run the application
!streamlit run splash.py


The app will open at:
http://localhost:8501


## DATASET

This project uses publicly available crime datasets such as:

NCRB (National Crime Records Bureau)

data.gov.in


## WHAT THIS PROJECT SHOWS

Practical use of Python for data analysis

Real-world application of:

Data preprocessing

Visualization

Predictive modeling

Ability to build end-to-end analytical systems

Experience with Streamlit dashboards
