import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

from services.alert_service import AlertService
from services.gemini_service import GeminiService

def show_dashboard(stream_gen):
    """Renders the stable base of the Dashboard."""
    
    # 1. Base UI (Non-blinking)
    st.markdown("""
        <div style="background-color: #1E1E1E; padding: 10px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #4CAF50;">
            <h4 style="margin: 0; color: white;">🛰️ Live Intelligence Stream</h4>
            <p style="margin: 0; color: #AAAAAA; font-size: 0.9em;">Monitoring global sales, user traffic, and environmental factors.</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. Sidebar Filters (Static/Outside Fragment)
    st.sidebar.markdown("### 🔍 Drill-Down Filters")
    # Initialize values from history for selector ranges
    hist_df = pd.DataFrame(st.session_state.stream_data)
    regions = ["All"] + sorted(list(hist_df['region'].unique()))
    selected_region = st.sidebar.selectbox("Filter by Region", regions)
    
    categories = ["All"] + sorted(list(hist_df['category'].unique()))
    selected_category = st.sidebar.selectbox("Filter by Category", categories)

    st.sidebar.markdown("---")
    AlertService.show_pulse_feed()

    # 3. THE FRAGMENT: Only this part refreshes/blinks
    @st.fragment(run_every=2)
    def render_live_updates():
        # A. Fetch new data
        try:
            data_point = next(stream_gen)
            if 'stream_data' in st.session_state:
                st.session_state.stream_data.append(data_point)
                if len(st.session_state.stream_data) > 100:
                    st.session_state.stream_data.pop(0)
        except Exception:
            st.warning("⚠️ Waiting for sensor response...")
            return

        gemini = GeminiService()
        df_stream = pd.DataFrame(st.session_state.stream_data)

        # B. Apply Filters
        df_filtered = df_stream.copy()
        if selected_region != "All":
            df_filtered = df_filtered[df_filtered['region'] == selected_region]
        if selected_category != "All":
            df_filtered = df_filtered[df_filtered['category'] == selected_category]

        # C. Render Metrics Row
        e1, e2, e3 = st.columns([1, 1, 2])
        with e1: st.write(f"**Weather:** {data_point.get('weather', 'N/A')}")
        with e2: st.write(f"**Market:** {data_point.get('market_trend', 'N/A')}")
        with e3: st.progress(0.4 + (0.1 * (time.time() % 5)) / 5, "System Integrity")

        col1, col2, col3, col4 = st.columns(4)
        latest_rev = df_filtered['revenue'].sum()
        latest_users = df_filtered['users'].sum()
        latest_conv = (df_filtered['transactions'].sum() / latest_users * 100) if latest_users > 0 else 0
        
        col1.metric("Total Revenue", f"${latest_rev:,.2f}", "+3.2%")
        col2.metric("Active Users", f"{latest_users:,}", "-0.8%")
        col3.metric("Conversion", f"{latest_conv:.2f}%", "+0.1%")
        col4.metric("Anomalies", f"{df_filtered['is_anomaly'].sum()}", "CRITICAL" if data_point['is_anomaly'] else "Normal", delta_color="inverse")

        # D. Anomaly Alerts
        if data_point['is_anomaly']:
            severity = 'critical' if data_point.get('anomaly_type') == 'Critical Sales Drop' else 'warning'
            msg = f"{data_point.get('anomaly_type', 'Pattern Shift')} in {data_point['region']}!"
            
            ai_exp = ""
            if severity == 'critical' and gemini.has_key:
                ai_exp = gemini.generate_alert_explanation(msg, df_filtered)
            
            AlertService.log_alert(msg, level=severity, category=data_point.get('anomaly_type'), ai_explanation=ai_exp)
            
            st.error(f"🔥 **{severity.upper()} ANOMALY:** {msg}")
            if ai_exp: st.info(f"🤖 **AI Analysis:** {ai_exp}")

        # E. Charts
        c1, c2 = st.columns(2)
        fig_rev = px.area(df_filtered, x='timestamp', y='revenue', title="Interactive Revenue Stream", template="plotly_dark", color_discrete_sequence=['#4CAF50'])
        fig_rev.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
        c1.plotly_chart(fig_rev, use_container_width=True)
        
        df_cat = df_filtered.groupby('category')['revenue'].sum().reset_index()
        fig_cat = px.bar(df_cat, x='category', y='revenue', color='category', title="Sales by Category", template="plotly_dark")
        fig_cat.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
        c2.plotly_chart(fig_cat, use_container_width=True)
        
        st.markdown("---")
        df_reg = df_filtered.groupby('region')['revenue'].sum().reset_index()
        fig_reg = px.pie(df_reg, values='revenue', names='region', title="Regional Revenue Allocation", hole=0.5, template="plotly_dark")
        st.plotly_chart(fig_reg, use_container_width=True)

    # Trigger the live updates
    render_live_updates()
