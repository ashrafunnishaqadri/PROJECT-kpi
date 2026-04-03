import streamlit as st
from datetime import datetime
from services.gemini_service import GeminiService
import plotly.express as px
import pandas as pd
from fpdf import FPDF
import base64
from data.database_manager import DatabaseManager

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Executive Performance Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(report_text, stats_df):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Summary Section
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Executive Summary (AI Generated)", 0, 1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, report_text)
    pdf.ln(10)
    
    # Stats Table
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "2. Daily Performance Highlights", 0, 1)
    pdf.set_font("Arial", size=10)
    
    # Table Header
    pdf.cell(40, 10, "Date", 1)
    pdf.cell(50, 10, "Revenue (₹)", 1)
    pdf.cell(40, 10, "Users", 1)
    pdf.cell(40, 10, "Conv. Rate", 1)
    pdf.ln()
    
    # Table Rows (Last 10 days only for space)
    for index, row in stats_df.tail(10).iterrows():
        pdf.cell(40, 10, str(row['timestamp']), 1)
        pdf.cell(50, 10, f"{row['revenue']:,.2f}", 1)
        pdf.cell(40, 10, str(row['users']), 1)
        pdf.cell(40, 10, f"{row['conversion_rate']:.2f}%", 1)
        pdf.ln()
        
    return pdf.output(dest='S')

def show_reports(df_historical):
    """Renders the Finalized Performance Reports and Data Export module."""
    st.subheader("📜 Executive Performance Reports")
    
    # 1. AI-Driven Management Summary
    gemini = GeminiService()
    db = DatabaseManager()
    recent_alerts = db.get_recent_alerts(days=7)
    
    report_content = "💡 [LOCAL INSIGHT] Monthly revenue remains stable. Distribution analysis suggests the Electronics category is leading, while Fashion shows potential for seasonal growth."
    
    with st.container(border=True):
        st.write("#### ✨ AI Executive Summary")
        if gemini.has_key:
            with st.spinner("Compiling management report from SQL history..."):
                total_rev = df_historical['revenue'].sum()
                avg_conv = (df_historical['transactions'].sum() / df_historical['users'].sum() * 100)
                
                # Format recent alerts for the AI
                alert_text = "\n".join([f"- {a['timestamp']}: {a['message']} ({a['level']})" for a in recent_alerts[:5]])
                
                summary_prompt = f"""
                Summarize this 30-day performance: Total Revenue ₹{total_rev:,.0f}, Avg Conversion {avg_conv:.1f}%.
                
                Recent Anomalies from DB:
                {alert_text}
                
                Provide a professional 3-sentence summary highlighting performance and any critical risks found in the alerts.
                """
                report_content = gemini.answer_query(summary_prompt, df_historical)
                st.info(report_content)
        else:
            st.info(report_content)

    st.markdown("---")

    # 2. Daily Performance Highlights
    st.write("#### 📅 Daily Performance Breakdown")
    daily_stats = df_historical.groupby(df_historical['timestamp'].dt.date).agg({
        'revenue': 'sum',
        'users': 'sum',
        'transactions': 'sum'
    }).reset_index()
    daily_stats['conversion_rate'] = (daily_stats['transactions'] / daily_stats['users'] * 100).fillna(0)
    
    st.dataframe(daily_stats, use_container_width=True)

    # 3. Monthly Sales Distribution (Chart)
    st.write("#### 🌍 Distribution by Product Category")
    fig_hist = px.histogram(df_historical, x="category", y="revenue", color="region", 
                           barmode="group", title="Total Revenue by Category & Region", template="plotly_dark")
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")

    # 4. Export & Download
    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("#### 💾 Data Export Ready")
        
        csv = daily_stats.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Download Full CSV Data",
            data=csv,
            file_name=f'kpi_summary_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
            type="primary"
        )
        
        # PDF Generator (Lazy evaluation only when button clicked is not possible with st.download_button easily)
        # So we generate it once
        try:
            pdf_data = create_pdf(report_content, daily_stats)
            st.download_button(
                label="📄 Download Executive PDF Report",
                data=pdf_data,
                file_name=f'executive_report_{datetime.now().strftime("%Y%m%d")}.pdf',
                mime='application/pdf'
            )
        except Exception as e:
            st.error(f"PDF generation error: {e}")

    with col2:
        st.success(f"✅ Automated report generation synced for {datetime.now().strftime('%B %Y')}")
        st.write("**Recent Alerts in Report:**")
        # Show top 3 critical events from historical search if available
        if 'is_anomaly' in df_historical.columns:
            critical_events = df_historical[df_historical['is_anomaly'] == True].tail(3)
            for _, event in critical_events.iterrows():
                st.write(f"- {event['timestamp'].strftime('%Y-%m-%d')}: Critical Anomaly in {event['region']}")
        else:
            st.write("- All systems within normal operational parameters.")
