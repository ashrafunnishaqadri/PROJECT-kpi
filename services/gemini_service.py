import os
import google.generativeai as genai
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

from services.insights_engine import LocalInsightsEngine

class GeminiService:
    """Service to handle interactions with the Gemini API for KPI insights."""
    
    def __init__(self, api_key=None):
        load_dotenv()
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.debug_error = ""
        self.selected_model_name = "None"
        self.cache = {}
        self.local_engine = LocalInsightsEngine()

        
        if api_key:
            genai.configure(api_key=api_key)
            try:
                # 1. Get ALL models available to this key
                avail = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # 2. Priority List - Using 'latest' aliases is more robust
                priority = [
                    "gemini-1.5-flash-latest", 
                    "gemini-1.5-pro-latest",
                    "gemini-1.5-flash", 
                    "gemini-pro"
                ]
                
                selected = None
                for p_name in priority:
                    # Check if this priority name matches any available full string
                    match = [m for m in avail if p_name in m]
                    if match:
                        selected = match[0]
                        break
                
                # Final fallback: If nothing found, try standard gemini-pro
                self.selected_model_name = selected or "gemini-1.5-flash-latest"
                self.model = genai.GenerativeModel(self.selected_model_name)
                self.has_key = True
            except Exception as e:
                # Silently catch list_models failure and try default
                self.selected_model_name = "gemini-1.5-flash-latest"
                self.model = genai.GenerativeModel(self.selected_model_name)
                self.has_key = True
                self.debug_error = str(e)
        else:
            self.has_key = False
            
    def _call_with_retry(self, func, *args, **kwargs):
        """Internal helper to retry API calls with exponential back-off on 429."""
        import time
        import random
        
        max_retries = 2
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err_msg = str(e)
                # If it's a quote/rate limit or a 404 model error, trigger fallback
                if "429" in err_msg or "404" in err_msg or "not found" in err_msg.lower():
                    return "FALLBACK_TRIGGER"
                
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (attempt + 1))
                    continue
                
                return "FALLBACK_TRIGGER"
        
        return "FALLBACK_TRIGGER"

    def get_kpi_analysis(self, current_metrics, df_context):
        if not self.has_key: 
            return self.local_engine.generate_kpi_summary(current_metrics, df_context)
            
        prompt = f"KPI Brief: Revenue ₹{current_metrics['total_revenue']:.0f}, Users {current_metrics['total_users']}. Explain the trend in 2 lines."
        
        result = self._call_with_retry(self.model.generate_content, prompt)
        
        if result == "FALLBACK_TRIGGER" or not hasattr(result, 'text'):
            return self.local_engine.generate_kpi_summary(current_metrics, df_context)
            
        return result.text

    def generate_alert_explanation(self, alert_message, context_df):
        """Generates a data-driven explanation for a specific alert."""
        if not self.has_key:
            return self.local_engine.generate_kpi_summary({'revenue': 0, 'users': 0}, context_df) # Placeholder
            
        recent_stats = context_df.tail(20).groupby('category').agg({'revenue':'sum', 'users':'sum'}).to_string()
        prompt = f"Alert: {alert_message}. Context: {recent_stats}. 1-sentence explanation."
        
        result = self._call_with_retry(self.model.generate_content, prompt)
        
        if result == "FALLBACK_TRIGGER" or not hasattr(result, 'text'):
             return "Pattern analysis suggests a temporary shift in user behavior or regional market trends."
             
        return result.text

    def answer_query(self, query, df_context):
        if query in self.cache: return self.cache[query]
        
        if not self.has_key:
            return self.local_engine.answer_query(query, df_context)
            
        summary_reg = df_context.groupby(['region']).agg({'revenue':'sum', 'users':'sum'}).to_string()
        summary_cat = df_context.groupby(['category']).agg({'revenue':'sum', 'transactions':'sum'}).to_string()
        
        prompt = f"Data: {summary_reg}\n{summary_cat}\nQuestion: {query}. Short answer."
        
        result = self._call_with_retry(self.model.generate_content, prompt)
        
        if result == "FALLBACK_TRIGGER" or not hasattr(result, 'text'):
             return self.local_engine.answer_query(query, df_context)
        
        self.cache[query] = result.text
        return result.text


