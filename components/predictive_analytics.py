import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from models.churn_predictor import ChurnPredictor
from models.forecaster import SalesForecaster
from services.gemini_service import GeminiService
from data.kpi_engine import MLAnomalyDetector

def show_predictive_analytics(df_historical):
    """Renders the Predictive Analytics and ML module."""
    st.subheader("🔮 ML Insights & Forecasting")
    
    # --- 1. Customer Churn Prediction ---
    with st.expander("🚨 Churn Risk Analysis", expanded=True):
        cp = ChurnPredictor()
        cp.train()
        
        # Simulate a batch of customers
        mock_customers = pd.DataFrame({
            "tenure": [300, 10, 50, 150, 40],
            "frequency": [2, 1, 15, 8, 2],
            "total_spend": [1500, 50, 1000, 800, 200],
            "support_calls": [0, 5, 1, 2, 4]
        })
        
        mock_customers['churn_prob'] = cp.predict_churn(mock_customers)
        
        col1, col2 = st.columns([1, 1], gap="large")
        col1.markdown("**Top At-Risk Segment**")
        col1.dataframe(mock_customers.style.background_gradient(subset=['churn_prob'], cmap='RdYlGn_r'), use_container_width=True)
        
        high_risk = mock_customers[mock_customers['churn_prob'] > 0.5].copy()
        
        if not high_risk.empty:
            col2.warning(f"**{len(high_risk)} users flagged as high-risk.**")
            selected_idx = col2.selectbox("Deep-Dive AI Analysis for:", high_risk.index)
            user_data = high_risk.loc[selected_idx]
            
            if col2.button("Generate Prevention Strategy", type="primary"):
                gemini = GeminiService()
                with col2.spinner("Analyzing behavioral patterns..."):
                    prompt = (f"Customer Profile: Tenure={user_data['tenure']}d, "
                             f"Frequency={user_data['frequency']} orders/mo, Calls={user_data['support_calls']}. "
                             f"Churn Risk {user_data['churn_prob']:.0%}. Provide a retention plan.")
                    strategy = gemini.answer_query(prompt, df_historical)
                    st.info(strategy)
        else:
            col2.success("✅ Retention levels are healthy.")

    st.markdown("---")
    
    # --- 2. Advanced Multi-Metric Forecasting & What-If Scenarios ---
    st.write("### 📅 Strategic 'What-If' Scenario Forecasting")
    
    with st.container(border=True):
        c_a, c_b, c_c = st.columns(3)
        rev_multiplier = c_a.slider("💰 Revenue Impact (e.g. Price Change)", 0.5, 2.0, 1.0, 0.05)
        user_multiplier = c_b.slider("👥 Traffic Impact (e.g. Marketing)", 0.5, 2.0, 1.0, 0.05)
        st.caption("Adjust sliders to simulate shifts in business drivers and see the projected impact on the next 24 hours.")

    forecaster = SalesForecaster()
    
    # Forecast Revenue (Baseline vs Scenario)
    df_rev = df_historical.groupby('timestamp')['revenue'].sum().reset_index()
    rev_forecast_base = forecaster.forecast(df_rev, target_col='revenue', steps=24)
    rev_forecast_scen = forecaster.forecast(df_rev, target_col='revenue', steps=24, scenario_multiplier=rev_multiplier)
    rev_summary = forecaster.get_forecast_summary(rev_forecast_scen)
    
    # Forecast User Growth (Baseline vs Scenario)
    df_users = df_historical.groupby('timestamp')['users'].sum().reset_index()
    user_forecast_base = forecaster.forecast(df_users, target_col='users', steps=24)
    user_forecast_scen = forecaster.forecast(df_users, target_col='users', steps=24, scenario_multiplier=user_multiplier)
    user_summary = forecaster.get_forecast_summary(user_forecast_scen)
    
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"#### Sales Trend: {rev_summary}")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_rev['timestamp'].tail(50), y=df_rev['revenue'].tail(50), name="Actual Revenue", line=dict(color="#4682B4")))
        future_rev_time = pd.date_range(start=df_rev['timestamp'].iloc[-1], periods=len(rev_forecast_base)+1, freq='H')[1:]
        
        fig1.add_trace(go.Scatter(x=future_rev_time, y=rev_forecast_base, name="Baseline", line=dict(dash='dot', color='#888888')))
        fig1.add_trace(go.Scatter(x=future_rev_time, y=rev_forecast_scen, name="Scenario", line=dict(dash='dash', color='orange', width=3)))
        
        fig1.update_layout(title="Revenue Forecast (24h)", template="plotly_dark", height=320, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.write(f"#### User Traffic: {user_summary}")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df_users['timestamp'].tail(50), y=df_users['users'].tail(50), name="Actual Users", line=dict(color="#20B2AA")))
        future_user_time = pd.date_range(start=df_users['timestamp'].iloc[-1], periods=len(user_forecast_base)+1, freq='H')[1:]
        
        fig2.add_trace(go.Scatter(x=future_user_time, y=user_forecast_base, name="Baseline", line=dict(dash='dot', color='#888888')))
        fig2.add_trace(go.Scatter(x=future_user_time, y=user_forecast_scen, name="Scenario", line=dict(dash='dash', color='#4CAF50', width=3)))
        
        fig2.update_layout(title="User Traffic Forecast (24h)", template="plotly_dark", height=320, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig2, use_container_width=True)

    # --- 3. Multivariate Anomaly Detection (Isolation Forest) ---
    st.markdown("---")
    st.write("### 🔬 Advanced Anomaly Detection (Isolation Forest)")
    detector = MLAnomalyDetector(contamination=0.03)
    detector.fit(df_historical)
    
    df_anomaly = df_historical.tail(100).copy()
    # Check if a data point is an anomaly
    df_anomaly['ml_anomaly'] = df_anomaly.apply(lambda row: detector.predict_anomaly(row), axis=1)
    
    # Visualize anomaly distribution
    fig_anom = px.scatter(df_anomaly, x="revenue", y="users", color="ml_anomaly", 
                         symbol="ml_anomaly", title="Revenue vs Users: Isolation Forest Outliers",
                         color_discrete_map={True: "red", False: "#4CAF50"},
                         template="plotly_dark")
    st.plotly_chart(fig_anom, use_container_width=True)
    st.caption("Red points indicate multi-variate anomalies detected by the Isolation Forest engine.")
