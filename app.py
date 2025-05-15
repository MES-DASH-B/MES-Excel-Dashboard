import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta, datetime

# Set page config
st.set_page_config(page_title="YouTube Channel Dashboard", layout="wide")

# Initialize session state for page navigation and settings
if "page" not in st.session_state:
    st.session_state.page = "welcome"
if "metric_page" not in st.session_state:
    st.session_state.metric_page = None
if "section" not in st.session_state:
    st.session_state.section = None
if "time_frame" not in st.session_state:
    st.session_state.time_frame = "Daily"
if "chart_type" not in st.session_state:
    st.session_state.chart_type = "Bar"

# Load CSS styles
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file '{file_name}' not found. Please ensure it is in the app directory.")

if st.session_state.section == "section_2":
    local_css("section2_style.css")
else:
    local_css("style.css")

# Helper functions
@st.cache_data
def load_data():
    try:
        data = pd.read_csv("youtube_channel_data.csv")
        data['DATE'] = pd.to_datetime(data['DATE'])
        data['NET_SUBSCRIBERS'] = data['SUBSCRIBERS_GAINED'] - data['SUBSCRIBERS_LOST']
        return data
    except FileNotFoundError:
        st.error("Data file 'youtube_channel_data.csv' not found. Please upload it to the app directory.")
        st.stop()

def calculate_delta(df, column):
    if len(df) < 2:
        return 0, 0
    current_value = df[column].iloc[-1]
    previous_value = df[column].iloc[-2]
    delta = current_value - previous_value
    delta_percent = (delta / previous_value) * 100 if previous_value != 0 else 0
    return delta, delta_percent

def is_period_complete(date, freq):
    today = datetime.now()
    if freq == 'D':
        return date.date() < today.date()
    elif freq == 'W':
        return date + timedelta(days=6) < today
    elif freq == 'ME':
        next_month = date.replace(day=28) + timedelta(days=4)
        return next_month.replace(day=1) <= today
    elif freq == 'QE':
        # Calculate current quarter start date
        current_month = (today.month - 1) // 3 * 3 + 1
        current_quarter_start = datetime(today.year, current_month, 1)
        return date < current_quarter_start
    return True

def create_metric_chart(df, column, chart_type, time_frame='Daily', height=150):
    df = df.set_index("DATE")
    freq_map = {'Daily': 'D', 'Weekly': 'W', 'Monthly': 'ME', 'Quarterly': 'QE'}
    freq = freq_map.get(time_frame, 'D')
    
    try:
        df_resampled = df.resample(freq).sum()
    except ValueError as e:
        st.error(f"Error in resampling: {e}")
        return
    
    if column not in df_resampled.columns:
        st.warning(f"Column '{column}' not found for chart.")
        return

    chart_data = df_resampled[[column]]
    
    if chart_type == 'Bar':
        st.bar_chart(chart_data, height=height)
    elif chart_type == 'Area':
        st.area_chart(chart_data, height=height)

def display_metric_with_button(col, title, value, df, column, color, key_suffix="", section=""):
    with col:
        delta, delta_percent = calculate_delta(df, column)
        delta_str = f"{delta:+,.0f} ({delta_percent:+.2f}%)"
        
        col.markdown(f"""
            <div class="stContainer {section}">
                <div class="metric-title" style="color:{color}; font-weight:bold;">{title}</div>
                <div class="metric-value" style="font-size:24px;">{value:,}</div>
                <p style="font-size:0.9rem; color:grey;">Change: {delta_str}</p>
            </div>
        """, unsafe_allow_html=True)

        # Small chart below metric
        create_metric_chart(
            df,
            column,
            chart_type=st.session_state.chart_type,
            time_frame=st.session_state.time_frame,
            height=150
        )

        # Check if last period incomplete
        last_period = df.set_index("DATE").index[-1]
        freq_map = {'Daily': 'D', 'Weekly': 'W', 'Monthly': 'ME', 'Quarterly': 'QE'}
        freq = freq_map.get(st.session_state.time_frame, 'D')
        if not is_period_complete(last_period, freq):
            st.caption(f"Note: The last {st.session_state.time_frame.lower()[:-2] if st.session_state.time_frame != 'Daily' else 'day'} is incomplete.")

        if col.button(f"Open {title}", key=f"btn_{title.replace(' ', '_').lower()}_{key_suffix}"):
            st.session_state.metric_page = title.replace(" ", "_").lower()
            st.session_state.page = "metric"
            st.session_state.section = section
            st.rerun()

# Load data
df = load_data()

# Sidebar navigation and settings
with st.sidebar:
    st.title("YouTube Channel Dashboard")

    if st.session_state.page == "welcome":
        if st.button("Section 1"):
            st.session_state.page = "section_1"
            st.session_state.section = "section_1"
            st.rerun()

        if st.button("Section 2"):
            st.session_state.page = "section_2"
            st.session_state.section = "section_2"
            st.rerun()

    elif st.session_state.page in ["section_1", "section_2"]:
        if st.button("← Back to Welcome"):
            st.session_state.page = "welcome"
            st.session_state.section = None
            st.rerun()

    # Common filters for main pages and metrics
    if st.session_state.page in ["section_1", "section_2", "metric"]:
        st.header("⚙️ Settings")
        max_date = df['DATE'].max().date()
        min_date = df['DATE'].min().date()

        start_date = st.date_input("Start date", min_date, min_value=min_date, max_value=max_date, key="start_date")
        end_date = st.date_input("End date", max_date, min_value=min_date, max_value=max_date, key="end_date")
        st.session_state.time_frame = st.selectbox("Select time frame", ["Daily", "Weekly", "Monthly", "Quarterly"])
        st.session_state.chart_type = st.selectbox("Chart Type", ["Bar", "Area"])

# Define metrics
metrics = [
    ("Total Subscribers", "NET_SUBSCRIBERS", '#29b80a'),
    ("Total Views", "VIEWS", '#FF9F36'),
    ("Total Watch Hours", "WATCH_HOURS", '#D45B90'),
]

# Main page logic
if st.session_state.page == "section_1":
    st.header("Section 1: All-Time Statistics")
    for title, column, color in metrics:
        total_value = df[column].sum()
        display_metric_with_button(st, title, total_value, df, column, color)

elif st.session_state.page == "metric":
    st.title(st.session_state.metric_page.replace("_", " ").title() + " Chart")
