import streamlit as st
import pandas as pd
from datetime import datetime
from data.simulator import seed_database_if_empty, stream_real_time_data
from components.dashboard import show_dashboard
from components.predictive_analytics import show_predictive_analytics
from components.ai_chat import show_ai_chat, show_top_insights
from components.reports import show_reports
import os

# --- Page configuration ---
st.set_page_config(
    page_title="KPI Pulse Pro | Enterprise BI Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Historical Data (Baseline from SQLite)
if 'df_historical' not in st.session_state:
    with st.spinner("🚀 Connecting to Enterprise KPI Database..."):
        st.session_state.df_historical = seed_database_if_empty()
if 'stream_gen' not in st.session_state:
    st.session_state.stream_gen = stream_real_time_data(persist=True)

# Initialize Real-Time Data Buffer
if 'stream_data' not in st.session_state:
    st.session_state.stream_data = st.session_state.df_historical.tail(20).to_dict('records')

# --- Authentication Logic (RBAC) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None

def login():
    # Centered login box
    st.markdown("""
        <div style="text-align: center; margin-top: 50px;">
            <h1 style="font-size: 3em;">📡 KPI <span style="color: #4CAF50;">Pulse Pro</span></h1>
            <p style="color: #888; font-style: italic;">Advanced Real-Time Monitoring & AI-Driven Predictive Analytics</p>
        </div>
    """, unsafe_allow_html=True)
    
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        with st.container(border=True):
            st.subheader("User Login")
            user = st.text_input("Username", placeholder="admin / manager")
            password = st.text_input("Password", type="password")
            if st.button("Access Dashboard", type="primary", use_container_width=True):
                # Mock authentication
                if user == "admin" and password == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.user_role = "admin"
                    st.rerun()
                elif user == "manager" and password == "manager123":
                    st.session_state.authenticated = True
                    st.session_state.user_role = "manager"
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please attempt again.")
            
            st.caption("Default: admin/admin123 or manager/manager123")

def logout():
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.rerun()

# --- Main App Logic ---
if not st.session_state.authenticated:
    login()
else:
    # Sidebar navigation
    st.sidebar.markdown(f"### 👋 Welcome, **{st.session_state.user_role.capitalize()}**")
    st.sidebar.info(f"Role: {st.session_state.user_role.upper()} Access")
    
    # Define navigation based on RBAC
    nav_options = ["Dashboard", "AI Chat (Ask Data)", "Reports"]
    if st.session_state.user_role == "admin":
        nav_options.insert(1, "Predictive Analytics")
    
    page = st.sidebar.radio("Navigation", nav_options)
    st.sidebar.markdown("---")
    
    # --- Maintenance Section (Admin Only) ---
    if st.session_state.user_role == "admin":
        with st.sidebar.expander("🛠️ System Maintenance"):
            if st.button("Reset Simulation", use_container_width=True):
                 st.session_state.df_historical = generate_historical_sales(days=30)
                 st.rerun()
            if st.button("Check Connectivity", use_container_width=True):
                st.toast("Checking Gemini API Connectivity...", icon="🌐")
                # Add check logic here if needed

    if st.sidebar.button("Logout", type="secondary", use_container_width=True):
        logout()

    # Routing
    if page == "Dashboard":
        st.title("🚀 Real-Time KPI Dashboard")
        
        # Quick AI summary at the top (using the existing buffer)
        show_top_insights(pd.DataFrame(st.session_state.stream_data))
        
        # Render Dashboard with internal Fragment-based refresh
        show_dashboard(st.session_state.stream_gen)
    
    elif page == "Predictive Analytics":
        st.title("🔮 Predictive Insights")
        show_predictive_analytics(st.session_state.df_historical)

    elif page == "AI Chat (Ask Data)":
        st.title("🤖 AI Insights Chat")
        show_ai_chat(st.session_state.df_historical)

    elif page == "Reports":
        st.title("📊 Performance Reports")
        show_reports(st.session_state.df_historical)
