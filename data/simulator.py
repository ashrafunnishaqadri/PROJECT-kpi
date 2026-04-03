import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
from data.database_manager import DatabaseManager

def generate_historical_sales(days=30):
    """Generates historical sales, users, and external factor data."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='H')
    
    data = []
    weather_options = ["Sunny", "Cloudy", "Rainy", "Stormy"]
    market_options = ["Bullish", "Stable", "Bearish"]
    
    for dt in date_range:
        # Base daily seasonality
        hour_factor = np.sin((dt.hour / 24) * 2 * np.pi) + 1.2
        day_factor = 1.3 if dt.weekday() >= 5 else 1.0 # Weekend boost
        
        # External Factors
        weather = random.choice(weather_options)
        market = random.choice(market_options)
        
        # Weather impact: Stormy/Rainy reduces traffic
        weather_impact = 0.7 if weather in ["Stormy", "Rainy"] else 1.0
        # Market impact: Bearish reduces revenue per transaction
        market_impact = 0.8 if market == "Bearish" else 1.2 if market == "Bullish" else 1.0
        
        # Random noise
        noise = np.random.normal(0, 0.1)
        
        # Calculate values
        base_users = 120
        users = int(base_users * hour_factor * day_factor * weather_impact * (1 + noise))
        
        base_revenue = 600
        revenue = base_revenue * hour_factor * day_factor * market_impact * (1 + noise)
        
        # Base conversion rate ~15%
        conv_rate = 0.15 * market_impact * (0.9 if weather == "Stormy" else 1.0)
        transactions = int(users * conv_rate * (1 + noise)) 
        
        region = random.choice(["North", "South", "East", "West"])
        product_category = random.choice(["Electronics", "Fashion", "Home", "Beauty"])

        data.append({
            "timestamp": dt,
            "users": max(5, users),
            "revenue": max(0, revenue),
            "transactions": max(0, transactions),
            "region": region,
            "category": product_category,
            "weather": weather,
            "market_trend": market,
            "is_anomaly": False
        })
        
    return pd.DataFrame(data)

def seed_database_if_empty():
    """Initializes the database with historical data if no records exist."""
    db = DatabaseManager()
    existing_data = db.get_historical_data(limit=1)
    
    if existing_data.empty:
        print("🗄️ Database empty. Seeding 30 days of historical KPI data...")
        df_history = generate_historical_sales(days=30)
        db.save_kpi_data(df_history)
        return df_history
    else:
        print("🗄️ Database records found. Loading existing history.")
        return db.get_historical_data(limit=1000)

def stream_real_time_data(persist=False):
    """Generator function simulating live data stream with external factors."""
    weather_options = ["Sunny", "Cloudy", "Rainy", "Stormy"]
    market_options = ["Bullish", "Stable", "Bearish"]
    
    while True:
        dt = datetime.now()
        
        # Seasonality & Factors
        hour_factor = np.sin((dt.hour / 24) * 2 * np.pi) + 1.2
        day_factor = 1.3 if dt.weekday() >= 5 else 1.0
        
        weather = random.choice(weather_options)
        market = random.choice(market_options)
        
        weather_impact = 0.7 if weather in ["Stormy", "Rainy"] else 1.0
        market_impact = 0.8 if market == "Bearish" else 1.2 if market == "Bullish" else 1.0
        
        noise = np.random.normal(0, 0.05)
        
        users = int(120 * hour_factor * day_factor * weather_impact * (1 + noise))
        revenue = 600 * hour_factor * day_factor * market_impact * (1 + noise)
        conv_rate = 0.15 * market_impact * (0.9 if weather == "Stormy" else 1.0)
        transactions = int(users * conv_rate * (1 + noise))
        
        # Simulate a sudden anomaly (5% chance)
        is_anomaly = random.random() < 0.05
        anomaly_type = None
        if is_anomaly:
            scenario = random.choice(["DIP", "SPIKE"])
            if scenario == "DIP":
                revenue *= 0.3 # 70% drop
                transactions = int(transactions * 0.2)
                anomaly_type = "Critical Sales Drop"
            else:
                users *= 3 # Sudden traffic spike
                anomaly_type = "Traffic Surge"
            
        data_point = {
            "timestamp": dt,
            "users": max(1, users),
            "revenue": max(0, revenue),
            "transactions": max(0, transactions),
            "region": random.choice(["North", "South", "East", "West"]),
            "category": random.choice(["Electronics", "Fashion", "Home", "Beauty"]),
            "weather": weather,
            "market_trend": market,
            "is_anomaly": is_anomaly,
            "anomaly_type": anomaly_type
        }
        
        
        if persist:
            db = DatabaseManager()
            db.save_kpi_data(pd.DataFrame([data_point]))
            
        yield data_point
