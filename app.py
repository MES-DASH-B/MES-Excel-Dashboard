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
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if st.session_state.section == "section_2":
    local_css("section2_style.css")
else:
    local_css("style.css")

# Helper functions
@st.cache_data
def load_data():
    data = pd.read_csv("youtube_channel_data.csv")
    data['DATE'] = pd.to_datetime(data['DATE'])
    data['NET_SUBSCRIBERS'] = data['SUBSCRIBERS_GAINED'] - data['SUBSCRIBERS_LOST']
    return data

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
    elif freq == 'M':
        next_month = date.replace(day=28) + timedelta(days=4)
        return next_month.replace(day=1) <= today
    elif freq == 'Q':
        # Calculate current quarter start date
        current_month = (today.month - 1) // 3 * 3 + 1
        current_quarter_start = datetime(today.year, current_month, 1)
        return date < current_quarter_start
    return True

def create_metric_chart(df, column, chart_type, time_frame='Daily', height=150):
    # Prepare dataframe with DATE as index and resample
    df = df.set_index("DATE")
    if time_frame == 'Quarterly':
        df_resampled = df.resample('Q').sum()
    elif time_frame == 'Monthly':
        df_resampled = df.resample('M').sum()
    elif time_frame == 'Weekly':
        df_resampled = df.resample('W').sum()
    else:
        df_resampled = df.resample('D').sum()

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
        with st.container():
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
            freq_map = {'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M', 'Quarterly': 'Q'}
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

    elif st.session_state.page == "metric":
        if st.session_state.section == "section_1":
            if st.button("← Back to Section 1"):
                st.session_state.page = "section_1"
                st.session_state.metric_page = None
                st.rerun()
        elif st.session_state.section == "section_2":
            if st.button("← Back to Section 2"):
                st.session_state.page = "section_2"
                st.session_state.metric_page = None
                st.rerun()

    # Common filters for main pages and metrics
    if st.session_state.page in ["section_1", "section_2", "metric"]:
        st.header("⚙️ Settings")
        max_date = df['DATE'].max().date()
        default_start_date = max_date - timedelta(days=365)
        default_end_date = max_date

        start_date = st.date_input("Start date", default_start_date,
                                   min_value=df['DATE'].min().date(),
                                   max_value=max_date,
                                   key="start_date")
        end_date = st.date_input("End date", default_end_date,
                                 min_value=df['DATE'].min().date(),
                                 max_value=max_date,
                                 key="end_date")
        time_frame = st.selectbox("Select time frame", ("Daily", "Weekly", "Monthly", "Quarterly"), key="time_frame")
        chart_type = st.selectbox("Chart Type", ["Bar", "Area"], key="chart_type")

# Define your metrics
metrics = [
    ("Total Subscribers", "NET_SUBSCRIBERS", '#29b80a'),
    ("Total Views", "VIEWS", '#FF9F36'),
    ("Total Watch Hours", "WATCH_HOURS", '#D45B90'),
    ("Total Likes", "LIKES", '#7D44CF'),
    ("Total Shares", "SHARES", '#3AAFA9'),
    ("Total Comments", "COMMENTS", '#2B7A78'),
    ("Subscribers Gained", "SUBSCRIBERS_GAINED", '#17252A'),
    ("Subscribers Lost", "SUBSCRIBERS_LOST", '#FF6F59'),
]

# Main page logic
if st.session_state.page == "welcome":
    st.title("Welcome to the YouTube Channel Dashboard!")
    st.write("Use the sidebar to navigate to different sections.")

elif st.session_state.page == "section_1":
    st.header("Section 1: All-Time Statistics")
    cols = st.columns(4)
    for i, (title, column, color) in enumerate(metrics):
        total_value = df[column].sum()
        display_metric_with_button(cols[i % 4], title, total_value, df, column, color, key_suffix="section1", section="section_1")

elif st.session_state.page == "section_2":
    st.header("Section 2: Advanced Analytics")
    cols = st.columns(4)
    for i, (title, column, color) in enumerate(metrics):
        total_value = df[column].sum()
        display_metric_with_button(cols[i % 4], title, total_value, df, column, color, key_suffix="section2", section="section_2")

elif st.session_state.page == "metric":
    metric_title = st.session_state.metric_page.replace("_", " ").title()
    st.title(f"{metric_title} Chart")
    column_map = {m[0]: m[1] for m in metrics}
    metric_column = column_map.get(metric_title, None)

    if metric_column:
        create_metric_chart(df, metric_column, st.session_state.chart_type, time_frame=st.session_state.time_frame)
    else:
        st.error("Metric column not found.")

