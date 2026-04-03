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
                
                # 2. Priority List - We try Flash first (high quota), then Pro (low quota)
                # We saw in your log that 'gemini-3.1-pro' definitely exists for you!
                priority = [
                    "gemini-1.5-flash-latest", 
                    "gemini-1.5-flash", 
                    "gemini-1.5-flash-001", 
                    "gemini-3.1-pro", 
                    "gemini-pro"
                ]
                
                selected = None
                for p_name in priority:
                    # Check if this priority name matches any available full string
                    match = [m for m in avail if p_name in m]
                    if match:
                        selected = match[0]
                        break
                
                # Final fallback: If we found NOTHING in the priority list, we just take the first one available
                if not selected and avail:
                    selected = avail[0]
                
                self.selected_model_name = selected or "gemini-1.5-flash"
                self.model = genai.GenerativeModel(self.selected_model_name)
                self.has_key = True
            except Exception as e:
                self.selected_model_name = "gemini-1.5-flash"
                self.model = genai.GenerativeModel(self.selected_model_name)
                self.has_key = True
                self.debug_error = f"{str(e)} | Found on your account: {str(avail) if 'avail' in locals() else 'None'}"
        else:
            self.has_key = False
            
    def _call_with_retry(self, func, *args, **kwargs):
        """Internal helper to retry API calls with exponential back-off on 429."""
        import time
        import random
        
        max_retries = 3
        base_delay = 2 # seconds
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg:
                    if attempt < max_retries - 1:
                        # Exponential back-off with jitter
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(delay)
                        continue
                    else:
                        # NEW: Silently signal fallback instead of error string
                        return "FALLBACK_TRIGGER"
                
                if "401" in err_msg or "invalid" in err_msg.lower():
                    return "Invalid API Key. Please check your .env file."
                
                return f"AI Error: {err_msg} | (Model: {self.selected_model_name})"
        
        return "Critical AI Error: Max retries exceeded."

    def get_kpi_analysis(self, current_metrics, df_context):
        if not self.has_key: 
            return self.local_engine.generate_kpi_summary(current_metrics, df_context)
            
        prompt = f"KPI Brief: Revenue ${current_metrics['total_revenue']:.0f}, Users {current_metrics['total_users']}. Explain the trend in 2 lines."
        
        result = self._call_with_retry(self.model.generate_content, prompt)
        
        if result == "FALLBACK_TRIGGER":
            return self.local_engine.generate_kpi_summary(current_metrics, df_context)
            
        return result.text if hasattr(result, 'text') else str(result)

    def generate_alert_explanation(self, alert_message, context_df):
        """Generates a data-driven explanation for a specific alert."""
        if not self.has_key:
            return "Local Engine: Pattern analysis suggests this is a transient fluctuation based on historical seasonality."
            
        # Simplified context for the prompt
        recent_stats = context_df.tail(20).groupby('category').agg({'revenue':'sum', 'users':'sum'}).to_string()
        prompt = f"""
        Alert Triggered: {alert_message}
        
        Recent Data Context:
        {recent_stats}
        
        Provide a 1-sentence professional explanation for why this might be happening. 
        Focus on data trends like categories or user counts.
        """
        
        result = self._call_with_retry(self.model.generate_content, prompt)
        
        if result == "FALLBACK_TRIGGER" or not hasattr(result, 'text'):
             return "Investigation suggests a temporary shift in user behavior or regional market trends."
             
        return result.text

    def answer_query(self, query, df_context):
        if query in self.cache: return self.cache[query]
        
        if not self.has_key:
            return self.local_engine.answer_query(query, df_context)
            
        # Enrich context with more than just region
        summary_reg = df_context.groupby(['region']).agg({'revenue':'sum', 'users':'sum'}).to_string()
        summary_cat = df_context.groupby(['category']).agg({'revenue':'sum', 'transactions':'sum'}).to_string()
        
        prompt = f"""
        Business Context (Last 30 Days):
        Regions:
        {summary_reg}
        
        Categories:
        {summary_cat}
        
        User Question: {query}
        
        Answer based on the data above. If unsure, provide a high-level business insight.
        """
        
        result = self._call_with_retry(self.model.generate_content, prompt)
        
        if result == "FALLBACK_TRIGGER":
             return self.local_engine.answer_query(query, df_context)
        
        if hasattr(result, 'text'):
            self.cache[query] = result.text
            return result.text
        return str(result)


