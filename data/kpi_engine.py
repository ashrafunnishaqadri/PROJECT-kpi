from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np

def calculate_current_metrics(df):
    """Calculates top-level KPI metrics from raw data."""
    if df.empty:
        return {
            "total_revenue": 0,
            "total_users": 0,
            "total_transactions": 0,
            "conversion_rate": 0,
            "avg_order_value": 0
        }
    
    total_revenue = df['revenue'].sum()
    total_users = df['users'].sum()
    total_transactions = df['transactions'].sum()
    conversion_rate = (total_transactions / total_users) * 100 if total_users > 0 else 0
    avg_order_value = total_revenue / total_transactions if total_transactions > 0 else 0
    
    return {
        "total_revenue": total_revenue,
        "total_users": total_users,
        "total_transactions": total_transactions,
        "conversion_rate": conversion_rate,
        "avg_order_value": avg_order_value
    }

def calculate_growth_metrics(current_df, previous_df):
    """Calculates growth percentage between two periods."""
    if current_df.empty or previous_df.empty:
        return {"revenue_growth": 0, "user_growth": 0}
        
    curr_rev = current_df['revenue'].sum()
    prev_rev = previous_df['revenue'].sum()
    rev_growth = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
    
    curr_users = current_df['users'].sum()
    prev_users = previous_df['users'].sum()
    user_growth = ((curr_users - prev_users) / prev_users * 100) if prev_users > 0 else 0
    
    return {
        "revenue_growth": rev_growth,
        "user_growth": user_growth
    }

class MLAnomalyDetector:
    """Uses Isolation Forest to detect multivariate anomalies."""
    def __init__(self, contamination=0.05):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_fitted = False
        
    def fit(self, df):
        # Features for anomaly detection: users, revenue, transactions
        features = df[['users', 'revenue', 'transactions']].fillna(0)
        self.model.fit(features)
        self.is_fitted = True
        
    def predict_anomaly(self, data_point):
        """Returns True if the data point is an anomaly."""
        if not self.is_fitted:
            return False
            
        # Reshape data point for prediction
        features = np.array([[data_point['users'], data_point['revenue'], data_point['transactions']]])
        # Prediction: -1 for outlier, 1 for inlier
        prediction = self.model.predict(features)
        return prediction[0] == -1

def detect_basic_anomaly(current_val, historical_mean, historical_std, threshold=2.0):
    """Detects if current value is an anomaly based on Z-score."""
    if historical_std == 0:
        return False
    z_score = abs(current_val - historical_mean) / historical_std
    return z_score > threshold

def check_threshold_breach(current_val, baseline_val, limit_pct=0.2, direction="down"):
    """Checks if current value has breached a threshold percentage."""
    if baseline_val == 0:
        return False
        
    if direction == "down":
        change_pct = (baseline_val - current_val) / baseline_val
    else:
        change_pct = (current_val - baseline_val) / baseline_val
        
    return change_pct > limit_pct
