import pandas as pd
import numpy as np

class LocalInsightsEngine:
    """A rule-based analysis engine to generate KPI insights without AI API calls."""
    
    def generate_kpi_summary(self, metrics, df_context):
        """Generates a human-like summary of KPIs using rule-based calculations."""
        rev = metrics.get('total_revenue', 0)
        users = metrics.get('total_users', 0)
        conv = metrics.get('conversion_rate', 0)
        
        # Analyze trends from context
        df_context['timestamp'] = pd.to_datetime(df_context['timestamp']) 
        midpoint = len(df_context) // 2
        first_half = df_context.iloc[:midpoint]['revenue'].sum()
        second_half = df_context.iloc[midpoint:]['revenue'].sum()
        
        trend = "trending upwards" if second_half >= first_half else "showing a slight decline"
        growth = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        
        # Find top region
        top_region = df_context.groupby('region')['revenue'].sum().idxmax()
        
        # Build the natural language response
        summary = f"✨ [LOCAL CORE] Performance analysis: Total revenue is ₹{rev:,.0f} and is {trend} ({growth:+.1f}%). "
        summary += f"The {top_region} region is currently leading in sales. "
        summary += f"Conversion rate is steady at {conv:.1f}% of {users:,} active users. "
        
        if conv < 2.0:
            summary += "Recommendation: Focus on checkout optimization."
        elif growth > 10:
            summary += "Insight: Strong seasonal demand detected."
            
        return summary

    def answer_query(self, query, df_context):
        """Simple rule-based Q&A for common data queries."""
        query = query.lower()
        
        if "region" in query:
            reg_stats = df_context.groupby('region')['revenue'].sum().sort_values(ascending=False)
            top = reg_stats.index[0]
            bot = reg_stats.index[-1]
            return f"✨ [LOCAL CORE] {top} is your top performing region, while {bot} needs attention."
        
        if "revenue" in query or "sales" in query:
            total = df_context['revenue'].sum()
            return f"✨ [LOCAL CORE] Total revenue analyzed in this session is ₹{total:,.2f}."
            
        if "category" in query:
            top_cat = df_context.groupby('category')['revenue'].sum().idxmax()
            return f"✨ [LOCAL CORE] {top_cat} is currently the most profitable category."
            
        if "conversion" in query:
            total_users = df_context['users'].sum()
            total_transactions = df_context['transactions'].sum()
            conv = (total_transactions / total_users * 100) if total_users > 0 else 0
            return f"✨ [LOCAL CORE] Your current overall conversion rate is {conv:.2f}%."
            
        if "user" in query or "traffic" in query:
            total_users = df_context['users'].sum()
            return f"✨ [LOCAL CORE] We have tracked a total of {total_users:,} users in the selected period."
            
        return "✨ [LOCAL CORE] I analyzed the current data: trends are steady, but I need the Cloud AI for more abstract questions!"
