import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
import warnings

warnings.filterwarnings("ignore")

class SalesForecaster:
    """Class to perform time-series forecasting using ARIMA."""
    
    def __init__(self, data=None):
        self.data = data
        
    def forecast(self, historical_df, target_col='revenue', steps=7, scenario_multiplier=1.0):
        """Forecasts next `steps` intervals with an optional scenario multiplier."""
        if historical_df.empty:
            return pd.Series([0] * steps)
            
        df = historical_df.copy()
        if 'timestamp' in df.columns:
            df = df.set_index('timestamp')
        
        try:
            series = df[target_col].astype(float)
            model = ARIMA(series, order=(5, 1, 0))
            model_fit = model.fit()
            forecast_result = model_fit.forecast(steps=steps)
            # Apply scenario impact
            return forecast_result * scenario_multiplier
        except Exception as e:
            # Fallback to moving average + noise if ARIMA fails
            mean_val = df[target_col].mean()
            return pd.Series([mean_val * (1 + np.random.normal(0, 0.05)) for _ in range(steps)])

    def get_forecast_summary(self, forecast_series):
        """Returns a string description of the forecasted trend."""
        if len(forecast_series) < 2:
            return "Stable"
            
        start_val = forecast_series.iloc[0]
        end_val = forecast_series.iloc[-1]
        
        if start_val == 0: return "Growth Potential"
        
        change_pct = (end_val - start_val) / start_val
        
        if change_pct > 0.05:
            return f"📈 Growth Trend (+{change_pct:.1%})"
        elif change_pct < -0.05:
            return f"📉 Declining Trend ({change_pct:.1%})"
        else:
            return "➡️ Stable Trend"
