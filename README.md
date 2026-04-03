# 📊 KPI Pulse Pro: Advanced Real-Time BI System

Advanced Real-Time Monitoring, Predictive Analytics, and AI-Driven Insights in a unified platform. Fully upgraded with multivariate anomaly detection, dual-metric forecasting, hybrid AI implementation, and comprehensive reporting.

---

## 🚀 Features & Capabilities

### 1. Real-Time Monitoring & Adaptive Alerting
- **Enriched Simulation**: Uses a robust generator-based simulator that injects realistic variance using hourly seasonality, day-of-week boosts, **Weather Conditions** (Sunny, Stormy, etc.), and **Market Trends** (Bullish, Bearish).
- **Multivariate Anomaly Detection**: Integrated **Isolation Forest** (from `scikit-learn`) to detect complex outliers across revenue, users, and transactions. Random anomaly simulation mimics real-world traffic surges and sales dips.
- **Categorized Sidebar Alerts**: Real-time "System Pulse" feed with visual severity levels (`INFO`, `WARNING`, `CRITICAL`).
- **AI Alert Explainer**: Automatically generates natural language explanations for anomalies using the Google Gemini API, bringing human-readable context to sudden spikes or dips.

### 2. Hybrid Intelligence Core (Dual AI Engine)
- **Primary AI (Google Gemini)**: Deep integration with **Google Gemini 1.5 Flash / 3.1 Pro** for advanced natural language querying, instant executive summaries, and intelligent alert explanations.
- **Resilient Fallback (Local Engine)**: An automated, robust **Local Intelligence Core** that takes over if API quotas are reached, network fails, or keys invalidate—ensuring 100% uptime for analytics.
- **Context-Aware Chat ("Ask Data")**: Users can query the current data state (e.g., "Why did sales drop yesterday?", "Summarize regional performance") and receive highly tailored generative insights.
- **Intelligent API Retry**: Built-in exponential back-off logic gracefully handles API `HTTP 429` rate-limit errors before failing over.

### 3. Predictive Analytics (Machine Learning)
- **Time-Series Forecasting**: **ARIMA (AutoRegressive Integrated Moving Average)** based forecasting for projecting future **Sales Revenue** and **Customer Growth** trends.
- **Interactive "What-If" Scenarios**: Forecast models come with scenario multipliers, allowing business users to simulate growth multipliers and assess impact instantly.
- **Churn Prediction**: Supervised **Random Forest** implementation scoring customer retention risk based on simulated tenure and support behavior.
- **Prescriptive Mitigation**: AI-generated 3-step retention plans mapping out direct actions for high-risk customer segments.

### 4. Enterprise Reporting & Persistence
- **Persistent Local Database**: Uses standardized **SQLite** (`database_manager.py`) to auto-seed 30 days of historical data and continuously append real-time streaming records.
- **Executive PDF Reporting**: Generate and download professional PDF summaries featuring AI-penned insights, actionable recommendations, and historical highlights powered by `FPDF2`.
- **Data Export capabilities**: Clean CSV headers and standard date formatting for external tool integration.

### 5. Role-Based Access Control (RBAC)
- **Admin**: Full access to all components, maintenance tools (like database resets), predictive models, AI chat, and reports.
- **Manager**: Securely restricted access—can only view the real-time monitoring dashboard, chat with the AI, and export reports.

---

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```cmd
   git clone <repository-url>
   cd PROJECT-KPI
   ```

2. **Install Dependencies**:
   Ensure you have Python installed, then install required libraries:
   ```cmd
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Create a `.env` file in the root directory and add your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
   *(Note: The system will operate using the local fallback engine if no key is provided.)*

4. **Run the Application**:
   ```cmd
   streamlit run app.py
   ```

---

## 🔐 Credentials (Demo Mode)
- **Admin**: `admin / admin123`
- **Manager**: `manager / manager123`

---

## 🏗️ Technical Architecture
- **Front-end**: Streamlit (Python-based Web Framework for intuitive UI components)
- **Data Persistence**: SQLite Database via standard `sqlite3` driver
- **Data Science / ML**: Pandas, NumPy, Scikit-Learn (`IsolationForest`, `RandomForestClassifier`), Statsmodels (`ARIMA`)
- **Visuals**: Plotly Express, Plotly Graph Objects (for responsive charts)
- **AI Core**: Google Generative AI SDK, Custom Local Rule-based KPI Engine
- **Reporting**: FPDF2 engine for report generation
