import streamlit as st
import json
import os
from datetime import datetime

from data.database_manager import DatabaseManager

class AlertService:
    """Service to handle modular system-wide alerts, history, and notifications."""
    
    @staticmethod
    def log_alert(message, level='warning', category="General", ai_explanation=""):
        """Logs an alert to session state and SQLite database."""
        db = DatabaseManager()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert = {
            "time": timestamp,
            "message": message,
            "level": level,
            "category": category,
            "ai_explanation": ai_explanation
        }
        
        # 1. Update Session State (for real-time UI immediate reactive update)
        if 'system_pulse' not in st.session_state:
            st.session_state.system_pulse = []
        st.session_state.system_pulse.insert(0, alert)
        
        # 2. Update Database (Permanent Audit Log)
        try:
            db.save_alert(alert)
        except Exception as e:
            print(f"Failed to log alert to database: {e}")

        # 3. Trigger Real-Time Notification (Streamlit Toast)
        # Note: st.toast only works during script execution in a browser-bound thread
        try:
            if level == 'critical':
                st.toast(f"🚨 CRITICAL: {message}", icon="🔥")
            elif level == 'warning':
                st.toast(f"⚠️ WARNING: {message}", icon="❗")
        except:
             pass # st.toast might fail in some background contexts

        # 4. Mock SMTP / External Notification
        AlertService._send_mock_email(alert)

    @staticmethod
    def _send_mock_email(alert):
        """Simulates semi-structured SMTP email sending."""
        if alert['level'] == 'critical':
            print(f"\n--- MOCK SMTP NOTIFICATION ---")
            print(f"Subject: [KPI ALERT] {alert['level'].upper()} - {alert['category']}")
            print(f"Body: At {alert['time']}, the system detected: {alert['message']}.")
            print(f"--- END OF EMAIL ---\n")

    @staticmethod
    def get_latest_alerts(limit=50):
        """Retrieve recent alerts from the database (7-day window)."""
        db = DatabaseManager()
        # The database manager already handles the 7-day filter logic
        return db.get_recent_alerts(days=7)

    @staticmethod
    def show_pulse_feed():
        """UI Component to display the 'Live Pulse' alert feed."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📟 System Pulse (Live Alerts)")
        
        alerts = AlertService.get_latest_alerts()
        if not alerts:
            st.sidebar.info("System is healthy. No active alerts.")
        else:
            for alert in alerts:
                emoji = "ℹ️"
                if alert['level'] == 'warning': emoji = "⚠️"
                elif alert['level'] == 'critical': emoji = "🚨"
                
                with st.sidebar.expander(f"{emoji} {alert['timestamp'][-8:]}"):
                    st.write(f"**{alert['level'].upper()}:** {alert['message']}")
                    st.caption(f"Category: {alert['category']}")
                    if alert.get('ai_explanation'):
                        st.info(f"🤖 **AI:** {alert['ai_explanation']}")

        if st.sidebar.button("Clear Visual Logs"):
            st.session_state.system_pulse = []
            st.rerun()
