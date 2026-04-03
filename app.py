import streamlit as st

# --- 1. CRITICAL: Page Configuration MUST BE FIRST ---
st.set_page_config(
    page_title="KPI Pulse Pro | Enterprise BI Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
from datetime import datetime
from data.simulator import seed_database_if_empty, stream_real_time_data, generate_historical_sales
from components.dashboard import show_dashboard
from components.predictive_analytics import show_predictive_analytics
from components.ai_chat import show_ai_chat, show_top_insights
from components.reports import show_reports
import os

# --- 2. GLOBAL STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    div[data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    div[data-testid="stMetricValue"] { font-weight: 800; color: #58A6FF; }
    div[data-testid="stMetricDelta"] > div { font-weight: 600; }
    .stPlotlyChart { border-radius: 12px; overflow: hidden; border: 1px solid #30363D; }
</style>
""", unsafe_allow_html=True)

# --- 3. CACHED INITIALIZATION (Maximum Stability) ---
@st.cache_resource(show_spinner=False)
def get_stream_generator():
    return stream_real_time_data(persist=True)

@st.cache_data(show_spinner=False)
def load_historical_data():
    return seed_database_if_empty()

# Initialize Persistent Session State
if 'df_historical' not in st.session_state:
    st.session_state.df_historical = load_historical_data()
if 'stream_gen' not in st.session_state:
    st.session_state.stream_gen = get_stream_generator()
if 'stream_data' not in st.session_state:
    st.session_state.stream_data = st.session_state.df_historical.tail(20).to_dict('records')
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None

def login():
    st.markdown("""
        <div style="text-align: center; margin-top: 50px;">
            <h1 style="font-size: 3em;">📡 KPI <span style="color: #4CAF50;">Pulse Pro</span></h1>
            <p style="color: #8B949E; font-style: italic;">Analytical Intelligence & Still Monitoring Console</p>
        </div>
    """, unsafe_allow_html=True)
    
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        with st.container(border=True):
            st.subheader("Secure Access")
            user = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password")
            if st.button("Access Hub", type="primary", use_container_width=True):
                if user == "admin" and password == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.user_role = "admin"
                    st.rerun()
                elif user == "manager" and password == "manager123":
                    st.session_state.authenticated = True
                    st.session_state.user_role = "manager"
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            st.caption("admin/admin123")

def logout():
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.rerun()

# --- 4. NAVIGATION & ROUTING ---
if not st.session_state.authenticated:
    login()
else:
    # Sidebar
    st.sidebar.markdown(f"### 👋 Welcome, **{st.session_state.user_role.capitalize()}**")
    nav_options = ["Dashboard", "AI Chat", "Reports"]
    if st.session_state.user_role == "admin": nav_options.insert(1, "Analytics")
    
    page = st.sidebar.radio("Navigation", nav_options)
    
    # Admin Data Management Console
    if st.session_state.user_role == "admin":
        with st.sidebar.expander("🛠️ Data Management"):
            # 1. Custom Upload
            st.markdown("**Upload Real Corporate Data**")
            st.caption("Auto-clears simulation and loads your CSV pipeline.")
            uploaded_file = st.file_uploader("Must include: timestamp, users, revenue, transactions", type=['csv'])
            if uploaded_file is not None:
                if st.button("Process & Override Core", type="primary", use_container_width=True):
                    try:
                        df_up = pd.read_csv(uploaded_file)
                        
                        # 1. Normalize headers (lowercase, strip whitespace)
                        df_up.columns = df_up.columns.str.lower().str.strip()
                        
                        # 2. Map common real-world CSV aliases to our internal schema
                        alias_map = {
                            'date': 'timestamp', 'datetime': 'timestamp', 'time': 'timestamp',
                            'visitors': 'users', 'customers': 'users', 'traffic': 'users',
                            'sales': 'revenue', 'amount': 'revenue', 'total': 'revenue',
                            'orders': 'transactions', 'purchases': 'transactions', 'qty': 'transactions'
                        }
                        df_up.rename(columns=alias_map, inplace=True)

                        # Ensure string timestamps parse gracefully (handling international day-first formats)
                        try:
                            df_up['timestamp'] = pd.to_datetime(df_up['timestamp'], format='mixed', dayfirst=True)
                        except TypeError:
                            # Fallback for older pandas versions
                            df_up['timestamp'] = pd.to_datetime(df_up['timestamp'], dayfirst=True, errors='coerce')
                        
                        req_cols = ['timestamp', 'users', 'revenue', 'transactions']
                        missing = [col for col in req_cols if col not in df_up.columns]
                        if missing:
                            st.error(f"Missing essential columns: {', '.join(missing)}")
                        else:
                            # Impute secondary dimensions if missing
                            if 'region' not in df_up.columns: df_up['region'] = 'Global'
                            if 'category' not in df_up.columns: df_up['category'] = 'General'
                            if 'weather' not in df_up.columns: df_up['weather'] = 'Stable'
                            if 'market_trend' not in df_up.columns: df_up['market_trend'] = 'Stable'
                            if 'is_anomaly' not in df_up.columns: df_up['is_anomaly'] = False
                            if 'anomaly_type' not in df_up.columns: df_up['anomaly_type'] = None
                            
                            with st.spinner("Purging old data & migrating core..."):
                                from data.database_manager import DatabaseManager
                                db = DatabaseManager()
                                db.truncate_kpi_data() # WIPE CLEAN first to avoid sim overlap
                                db.save_kpi_data(df_up)
                                
                                st.cache_data.clear()
                                st.cache_resource.clear()
                                st.session_state.df_historical = db.get_historical_data(1000)
                                st.session_state.stream_data = st.session_state.df_historical.tail(100).to_dict('records')
                            st.rerun()
                    except Exception as e:
                        st.error(f"Parse error: {e}")
            
            st.markdown("---")
            # 2. Reset back to Dev Sandbox
            if st.button("Revert to Test Sandbox", use_container_width=True):
                 from data.database_manager import DatabaseManager
                 db = DatabaseManager()
                 db.truncate_kpi_data() # Wipe real data
                 
                 st.cache_data.clear()
                 st.cache_resource.clear()
                 st.session_state.df_historical = seed_database_if_empty() # Reseed strictly
                 st.session_state.stream_data = st.session_state.df_historical.tail(20).to_dict('records')
                 st.rerun()

    if st.sidebar.button("Logout", type="secondary", use_container_width=True):
        logout()

    # Page Routing
    if page == "Dashboard":
        st.title("🛡️ Analytical Console")
        # Ensure insights only render if data exists
        if st.session_state.stream_data:
            show_top_insights(pd.DataFrame(st.session_state.stream_data))
        show_dashboard(st.session_state.stream_gen)
    
    elif page == "Analytics":
        st.title("🔮 Predictive Insights")
        show_predictive_analytics(st.session_state.df_historical)

    elif page == "AI Chat":
        st.title("🤖 Data Query Core")
        show_ai_chat(st.session_state.df_historical)

    elif page == "Reports":
        st.title("📊 Enterprise Reports")
        show_reports(st.session_state.df_historical)
