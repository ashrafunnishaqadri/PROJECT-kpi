import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

from services.alert_service import AlertService
from services.gemini_service import GeminiService

def show_dashboard(df_historical, stream_gen):
    """Renders the Real-Time KPI Dashboard."""
    
    st.markdown("""
        <div style="background-color: #1E1E1E; padding: 10px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #4CAF50;">
            <h4 style="margin: 0; color: white;">🛰️ Live Intelligence Stream</h4>
            <p style="margin: 0; color: #AAAAAA; font-size: 0.9em;">Monitoring global sales, user traffic, and environmental factors.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 1. AI Service Instance
    gemini = GeminiService()
    
    # Placeholder for real-time content
    metrics_placeholder = st.empty()
    charts_placeholder = st.empty()
    
    # Track streaming data in session state
    if 'stream_data' not in st.session_state:
        st.session_state.stream_data = df_historical.tail(30).to_dict('records')
    
    # Sidebar Filters (Drill-down)
    st.sidebar.markdown("### 🔍 Drill-Down Filters")
    regions = ["All"] + sorted(list(df_historical['region'].unique()))
    selected_region = st.sidebar.selectbox("Filter by Region", regions)
    
    categories = ["All"] + sorted(list(df_historical['category'].unique()))
    selected_category = st.sidebar.selectbox("Filter by Category", categories)

    # Display the live pulse feed in the sidebar
    AlertService.show_pulse_feed()

    # Main LOOP for real-time updates
    for data_point in stream_gen:
        # Append to session state
        st.session_state.stream_data.append(data_point)
        if len(st.session_state.stream_data) > 100:
            st.session_state.stream_data.pop(0)
            
        # Convert to DataFrame for visualization
        df_stream = pd.DataFrame(st.session_state.stream_data)
        
        # Apply filters
        df_filtered = df_stream.copy()
        if selected_region != "All":
            df_filtered = df_filtered[df_filtered['region'] == selected_region]
        if selected_category != "All":
            df_filtered = df_filtered[df_filtered['category'] == selected_category]
            
        # 1. Top Section: Metrics & External Factors
        with metrics_placeholder.container():
            # External Factors Row
            e1, e2, e3 = st.columns([1, 1, 2])
            with e1:
                st.markdown(f"**Weather:** {data_point.get('weather', 'N/A')}")
            with e2:
                st.markdown(f"**Market:** {data_point.get('market_trend', 'N/A')}")
            with e3:
                # Progress bar for "System Load" (randomly simulated)
                st.progress(0.4 + (0.1 * (time.time() % 5)) / 5, text="System Stability Score")

            # Main KPI Cards
            col1, col2, col3, col4 = st.columns(4)
            latest_rev = df_filtered['revenue'].sum()
            latest_users = df_filtered['users'].sum()
            latest_conv = (df_filtered['transactions'].sum() / latest_users * 100) if latest_users > 0 else 0
            
            # Simulated delta logic
            col1.metric("Total Revenue", f"${latest_rev:,.2f}", delta="+5.2%")
            col2.metric("Active Users", f"{latest_users:,}", delta="-1.5%")
            col3.metric("Conversion", f"{latest_conv:.2f}%", delta="+0.4%")
            
            anomalies = df_filtered['is_anomaly'].sum()
            col4.metric("Anomalies", f"{anomalies}", delta="CRITICAL" if data_point['is_anomaly'] else "Normal", delta_color="inverse")

        # 2. Logic: Handle Real-Time Alerts
        if data_point['is_anomaly']:
            severity = 'critical' if data_point.get('anomaly_type') == 'Critical Sales Drop' else 'warning'
            category = data_point.get('anomaly_type', 'Unusual Pattern')
            msg = f"{category} detected in {data_point['region']}!"
            
            ai_exp = ""
            # Automatically generate explanation for CRITICAL alerts
            if severity == 'critical' and gemini.has_key:
                ai_exp = gemini.generate_alert_explanation(msg, df_filtered)
            
            # Log to persistent service
            AlertService.log_alert(msg, level=severity, category=category, ai_explanation=ai_exp)
            
            # Show on-page warning
            with st.container(border=True):
                st.error(f"🔥 **{severity.upper()} ANOMALY:** {msg}")
                if ai_exp:
                    st.info(f"🤖 **Automated AI Analysis:** {ai_exp}")
                elif st.checkbox("Generate AI Explanation", key=f"ai_explain_{time.time()}"):
                    with st.spinner("AI analyzing roots..."):
                        manual_exp = gemini.generate_alert_explanation(msg, df_filtered)
                        st.info(f"🤖 **AI INSIGHT:** {manual_exp}")

        # 3. Middle Section: Charts
        with charts_placeholder.container():
            c1, c2 = st.columns(2)
            
            # Revenue Trend
            fig_rev = px.area(df_filtered, x='timestamp', y='revenue', 
                             title="Interactive Revenue Stream", 
                             template="plotly_dark",
                             color_discrete_sequence=['#4CAF50'])
            fig_rev.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
            c1.plotly_chart(fig_rev, use_container_width=True)
            
            # Category Breakdown
            df_cat = df_filtered.groupby('category')['revenue'].sum().reset_index()
            fig_cat = px.bar(df_cat, x='category', y='revenue', color='category', 
                            title="Sales by Category", template="plotly_dark")
            fig_cat.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
            c2.plotly_chart(fig_cat, use_container_width=True)
            
            # Regional Heatmap / Pie
            st.markdown("---")
            df_reg = df_filtered.groupby('region')['revenue'].sum().reset_index()
            fig_reg = px.pie(df_reg, values='revenue', names='region', 
                            title="Regional Revenue Allocation", hole=0.5, template="plotly_dark")
            st.plotly_chart(fig_reg, use_container_width=True)
            
        time.sleep(2) # Sync with simulator
