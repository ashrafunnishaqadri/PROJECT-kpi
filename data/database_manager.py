import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

class DatabaseManager:
    """Manages SQLite operations for the KPI Pulse Pro system."""
    
    DB_PATH = "data/kpi_pulse.db"
    
    def __init__(self):
        self._ensure_dir()
        self.setup_db()
        
    def _ensure_dir(self):
        if not os.path.exists("data"):
            os.makedirs("data")
            
    def get_connection(self):
        return sqlite3.connect(self.DB_PATH)

    def setup_db(self):
        """Initializes the required database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # KPI Data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kpi_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    users INTEGER,
                    revenue REAL,
                    transactions INTEGER,
                    region TEXT,
                    category TEXT,
                    weather TEXT,
                    market_trend TEXT,
                    is_anomaly BOOLEAN,
                    anomaly_type TEXT
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    message TEXT,
                    level TEXT,
                    category TEXT,
                    ai_explanation TEXT
                )
            ''')
            conn.commit()

    def save_kpi_data(self, df):
        """Saves a pandas DataFrame to the kpi_data table."""
        if df.empty:
            return
            
        with self.get_connection() as conn:
            # Ensure timestamp is string for SQLite
            df_to_save = df.copy()
            # Ensure columns match the schema table (filter out unexpected ones)
            schema_cols = ['timestamp', 'users', 'revenue', 'transactions', 'region', 'category', 'weather', 'market_trend', 'is_anomaly', 'anomaly_type']
            for col in schema_cols:
                if col not in df_to_save.columns:
                    df_to_save[col] = None
            
            df_to_save = df_to_save[schema_cols]
            df_to_save.to_sql('kpi_data', conn, if_exists='append', index=False)

    def get_historical_data(self, limit=1000):
        """Retrieves history from the database as a DataFrame."""
        query = f"SELECT * FROM kpi_data ORDER BY timestamp DESC LIMIT {limit}"
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # Order chronologically for charts
                df = df.sort_values('timestamp')
            return df

    def save_alert(self, alert_data):
        """Saves a specific alert dictionary to the history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts_history (timestamp, message, level, category, ai_explanation)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                alert_data.get('time', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                alert_data.get('message'),
                alert_data.get('level', 'warning'),
                alert_data.get('category', 'General'),
                alert_data.get('ai_explanation', '')
            ))
            conn.commit()

    def get_recent_alerts(self, days=7):
        """Retrieves alerts from the last N days."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        query = "SELECT * FROM alerts_history WHERE timestamp >= ? ORDER BY timestamp DESC"
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=(cutoff,))
            return df.to_dict('records')
            
    def clear_old_data(self, days_to_keep=30):
        """Optionally clear indices older than N days."""
        cutoff = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM kpi_data WHERE timestamp < ?", (cutoff,))
            conn.commit()
