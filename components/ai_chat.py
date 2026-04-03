import streamlit as st
from services.gemini_service import GeminiService
import pandas as pd

def show_ai_chat(df_context):
    """Renders the AI Business Intelligence Chat component."""
    st.subheader("🤖 Ask Your Data Anything")
    st.write("Ask questions like 'Which region performed best?', 'Why did sales drop?', or 'What is our current conversion rate?'")
    
    gemini = GeminiService()
    
    if not gemini.has_key:
        st.warning("⚠️ Gemini API Key not found. Set the `GEMINI_API_KEY` to enable AI summaries.")
    
    # Simple Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    if prompt := st.chat_input("How can I help you today?"):
        # Add user message to UI
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Get AI response
        with st.chat_message("assistant"):
            if gemini.has_key:
                with st.spinner("Analyzing data..."):
                    response = gemini.answer_query(prompt, df_context)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                # Mock response if no API key
                mock_resp = "I'm sorry, I need a Gemini API key to analyze this data. Based on the snapshot, it looks like South region is leading in revenue."
                st.markdown(mock_resp)
                st.session_state.messages.append({"role": "assistant", "content": mock_resp})

def show_top_insights(df_context):
    """Display quick AI insights at the top of the dashboard with smart caching."""
    import time
    
    # Initialize cache in session state
    if 'ai_insight_cache' not in st.session_state:
        st.session_state.ai_insight_cache = None
        st.session_state.ai_insight_time = 0
    
    gemini = GeminiService()
    if gemini.has_key:
        with st.expander("✨ AI Automated Insight (Click to expand)"):
            current_time = time.time()
            cache_duration = 300 # 5 minutes
            
            # Use Cache logic
            is_expired = (current_time - st.session_state.ai_insight_time > cache_duration)
            refresh_clicked = st.button("🔄 Refresh AI Insight", key="refresh_ai")
            
            if not st.session_state.ai_insight_cache or is_expired or refresh_clicked:
                with st.spinner("Analyzing performance data..."):
                    metrics = {
                        'total_revenue': df_context['revenue'].sum(),
                        'conversion_rate': (df_context['transactions'].sum() / df_context['users'].sum() * 100) if df_context['users'].sum() > 0 else 0,
                        'total_users': df_context['users'].sum()
                    }
                    # GeminiService now automatically fails over to Local Core on 429
                    st.session_state.ai_insight_cache = gemini.get_kpi_analysis(metrics, df_context)
                    st.session_state.ai_insight_time = current_time
                if refresh_clicked:
                    st.rerun()
            
            st.write(st.session_state.ai_insight_cache)

            if st.session_state.ai_insight_time > 0:
                st.caption(f"🕒 Last updated: {time.strftime('%H:%M:%S', time.localtime(st.session_state.ai_insight_time))}")


