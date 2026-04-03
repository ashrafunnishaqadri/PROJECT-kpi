import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

from services.alert_service import AlertService
from services.gemini_service import GeminiService

# --- STABLE STYLING (Fixed Heights) ---
# Moved to show_dashboard function to prevent import-time side-effects

def get_filtered_data(selected_region, selected_category):
    if 'stream_data' not in st.session_state:
        return pd.DataFrame()
    df = pd.DataFrame(st.session_state.stream_data)
    if not df.empty:
        if selected_region != "All":
            df = df[df['region'] == selected_region]
        if selected_category != "All":
            df = df[df['category'] == selected_category]
    return df

@st.fragment() # 100% Static Snapshot Fragment
def render_dashboard_snapshot(stream_gen, selected_region, selected_category):
    """
    Renders a rock-solid, static snapshot of the dashboard.
    Only updates when the fragment itself is re-triggered (e.g. by filters or manual buttons).
    """
    df_filtered = get_filtered_data(selected_region, selected_category)
    if df_filtered.empty:
        st.info("📊 No snapshot data available. Please click 'Sync' to load data.")
        return

    # 1. Metrics Header
    col1, col2, col3, col4 = st.columns(4)
    latest_rev = df_filtered['revenue'].sum()
    latest_users = df_filtered['users'].sum()
    latest_conv = (df_filtered['transactions'].sum() / latest_users * 100) if latest_users > 0 else 0
    
    with col1: st.metric("Overall Revenue", f"₹{latest_rev:,.0f}")
    with col2: st.metric("Engagement", f"{latest_users:,}")
    with col3: st.metric("Efficiency", f"{latest_conv:.1f}%")
    with col4: 
        anomalies = df_filtered['is_anomaly'].sum()
        st.metric("System Health", "STABLE" if anomalies == 0 else f"ISSUES ({anomalies})", 
                  delta_color="normal" if anomalies == 0 else "inverse")

    st.markdown("---")

    # 2. Charts Row
    c1, c2 = st.columns(2)
    
    with c1:
        with st.container(border=True):
            fig_rev = px.area(df_filtered.tail(60), x='timestamp', y='revenue', 
                             title="Revenue Analytic Snapshot", 
                             template="plotly_dark", color_discrete_sequence=["#00D1FF"])
            fig_rev.update_layout(height=380, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig_rev, use_container_width=True, config={'displayModeBar': False})
        
    with c2:
        with st.container(border=True):
            df_cat = df_filtered.groupby('category')['revenue'].sum().reset_index()
            fig_cat = px.bar(df_cat, x='category', y='revenue', color='category', 
                            title="Categorical Contribution", 
                            template="plotly_dark", 
                            color_discrete_sequence=["#00FF7F", "#FF2D55", "#FFCC00", "#AF52DE"])
            fig_cat.update_layout(height=380, margin=dict(l=10, r=10, t=50, b=10), showlegend=False)
            st.plotly_chart(fig_cat, use_container_width=True, config={'displayModeBar': False})

    # 3. Allocation (Donut)
    with st.container(border=True):
        df_reg = df_filtered.groupby('region')['revenue'].sum().reset_index()
        fig_reg = px.pie(df_reg, values='revenue', names='region', 
                        title="Regional Market Share Distribution", 
                        hole=0.6, template="plotly_dark")
        fig_reg.update_layout(height=450, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_reg, use_container_width=True, config={'displayModeBar': False})

def show_dashboard(stream_gen):
    """Renders the stable base of the Dashboard."""
    
    st.markdown("""
    <style>
        .metric-card { background: #1E252E; padding: 15px; border-radius: 10px; border-left: 5px solid #58A6FF; }
        .chart-box { min-height: 400px; padding: 10px; background: #161B22; border-radius: 12px; border: 1px solid #30363D; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown(f"""
        <div style="background: #161B22; padding: 20px; border-radius: 12px; margin-bottom: 25px; border-left: 6px solid #58A6FF;">
            <h2 style="margin: 0; color: white;">🛡️ Still Analytic Console</h2>
            <p style="margin: 5px 0 0 0; color: #8B949E; font-size: 1em;">Manual Sync Mode Active: Data is static until intentionally updated.</p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar
    st.sidebar.markdown("### ⚙️ Command Hub")
    
    # THE ONLY WAY DATA CHANGES: Manual Button
    if st.sidebar.button("🔄 Sync Fresh Analytics", type="primary", use_container_width=True):
        with st.sidebar.status("Fetching latest telemetry..."):
            # Fetch 5 new data points for a meaningful update
            for _ in range(5):
                data_point = next(stream_gen)
                st.session_state.stream_data.append(data_point)
                if len(st.session_state.stream_data) > 100:
                    st.session_state.stream_data.pop(0)
            time.sleep(0.5)
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Filters")
    hist_df = pd.DataFrame(st.session_state.stream_data)
    regions = ["All"] + sorted(list(hist_df['region'].unique()))
    categories = ["All"] + sorted(list(hist_df['category'].unique()))
    
    selected_region = st.sidebar.selectbox("Region Filter", regions)
    selected_category = st.sidebar.selectbox("Product Filter", categories)

    st.sidebar.markdown("---")
    AlertService.show_pulse_feed()

    # Data Rendering (No 'run_every', no blinking)
    render_dashboard_snapshot(stream_gen, selected_region, selected_category)
