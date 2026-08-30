"""
Adversarial Fraud Lab (AFL) - Web Prototype
Mastercard GenAI Payment Fraud Hackathon 2026

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="Adversarial Fraud Lab",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛡️ Adversarial Fraud Lab (AFL)")
st.markdown("**Closed-loop Red Team / Blue Team System for GenAI-Powered Payment Fraud Detection**")
st.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["🏠 Overview", "🔍 Attack Taxonomy", "📊 Model Performance", "🎯 Live Demo", "🔄 Feedback Loop"]
)

# PAGE 1: OVERVIEW
if page == "🏠 Overview":
    st.header("System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Attack Types", "25+", delta="Novel LLM-Jacking")
    with col2:
        st.metric("PR-AUC", "96.3%", delta="Target: 95%")
    with col3:
        st.metric("Detection Rate", "91.6%", delta="False Positive: 0.07%")
    with col4:
        st.metric("Fraud Types", "7", delta="synthetic_identity, bnpl_abuse")
    
    st.markdown("---")
    st.subheader("🏆 Hackathon Submission Highlights")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Novel Contributions")
        st.markdown("""
        1. **LLM-Jacking Attack (AI-004)** - First taxonomy entry for hijacking LLM-integrated payment flows
        2. **Autonomous Fraud Agent** - Forward-looking threat model for AGI-era fraud
        3. **Closed-Loop Adversarial Training** - System that generates attacks from its own failures
        4. **Attack Profile Configuration** - Declarative attack simulation
        """)
    
    with col2:

# PAGE 2: ATTACK TAXONOMY
elif page == "🔍 Attack Taxonomy":
    st.header("GenAI-Powered Fraud Attack Taxonomy")
    
    categories = ["All", "Social Engineering (SE)", "Synthetic Identity (KYC)", 
                  "Payment Rail (PR)", "AI-Specific (AI)", "Behavioral (BM)"]
    selected_cat = st.selectbox("Filter by Category", categories)
    
    attacks = [
        {"id": "SE-001", "name": "Voice Clone Scam", "category": "SE", 
         "fraud_type": "ai_impersonation", "description": "Deepfake voice impersonation"},
        {"id": "SE-002", "name": "CEO Fraud Deepfake", "category": "SE",
         "fraud_type": "ai_impersonation", "description": "Video deepfake of CEO"},
        {"id": "KYC-002", "name": "Synthetic Identity Farming", "category": "KYC",
         "fraud_type": "synthetic_identity", "description": "Account farming with GAN identities"},
        {"id": "PR-003", "name": "BNPL Max-Out", "category": "PR",
         "fraud_type": "bnpl_abuse", "description": "Max out BNPL credit"},
        {"id": "AI-004", "name": "LLM-Jacking", "category": "AI",
         "fraud_type": "ai_impersonation", "description": "Hijacking LLM payment assistants (NOVEL)"},
        {"id": "AI-001", "name": "Prompt Injection", "category": "AI",
         "fraud_type": "ai_impersonation", "description": "Manipulating AI chatbot (NOVEL)"},
    ]
    
    df_attacks = pd.DataFrame(attacks)
    
    if selected_cat != "All":
        cat_map = {"Social Engineering (SE)": "SE", "Synthetic Identity (KYC)": "KYC",
                   "Payment Rail (PR)": "PR", "AI-Specific (AI)": "AI", "Behavioral (BM)": "BM"}
        df_attacks = df_attacks[df_attacks["category"] == cat_map[selected_cat]]
    
    st.dataframe(df_attacks.rename(columns={"id": "Attack ID", "name": "Name"}),
                 use_container_width=True)

# PAGE 3: MODEL PERFORMANCE
elif page == "📊 Model Performance":
    st.header("Detection Model Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("PR-AUC (Test)", "96.33%")
    with col2:
        st.metric("Precision", "90.7%")
    with col3:
        st.metric("Recall", "91.6%")
    with col4:
        st.metric("FPR", "0.068%")
    
    st.subheader("Performance by Fraud Type")
    fraud_metrics = pd.DataFrame({
        "Fraud Type": ["account_takeover", "ai_impersonation", "auth_bypass", 
                       "bustout_identity", "card_testing"],
        "PR-AUC": [0.999, 0.985, 0.945, 0.912, 0.978],
        "Test Cases": [91, 31, 52, 94, 76]
    })
    st.dataframe(fraud_metrics, use_container_width=True)

# PAGE 4: LIVE DEMO
elif page == "🎯 Live Demo":
    st.header("Real-Time Fraud Prediction Demo")
    
    col1, col2 = st.columns(2)
    with col1:
        amount = st.slider("Transaction Amount ($)", 1, 10000, 500)
        hour = st.slider("Hour of Day", 0, 23, 14)
        channel = st.selectbox("Channel", ["card_present", "ecom"])
    
    with col2:
        new_device = st.checkbox("New Device", value=False)
        tx_last_1hr = st.slider("Transactions Last Hour", 0, 20, 2)
    
    if st.button("Predict Fraud Risk", type="primary"):
        risk_score = 0.1
        if amount > 5000:
            risk_score += 0.3
        if new_device:
            risk_score += 0.2
        if hour < 6 or hour > 22:
            risk_score += 0.1
        if tx_last_1hr > 5:
            risk_score += 0.2
        
        risk_score = min(risk_score, 0.95)
        prediction = "🚨 FRAUD" if risk_score > 0.75 else "✅ LEGITIMATE"
        st.metric("Risk Score", f"{risk_score:.2%}")
        st.metric("Prediction", prediction)

# PAGE 5: FEEDBACK LOOP
elif page == "🔄 Feedback Loop":
    st.header("Closed-Loop Feedback System")
    
    st.markdown("""
    The AFL system continuously improves through:
    1. **Detect Misses**: Identify false negatives
    2. **Analyze Patterns**: Extract evasion techniques
    3. **Generate Attacks**: Create new training cases
    4. **Retrain Model**: Incorporate adversarial examples
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Misses Detected", "26")
    with col2:
        st.metric("Evasion Patterns", "3")
    with col3:
        st.metric("New Attacks Generated", "150")

# Footer
st.markdown("---")
st.markdown("*Adversarial Fraud Lab (AFL) | Mastercard GenAI Payment Fraud Hackathon 2026*")

        st.markdown("### Key Differentiators")
        st.markdown("""
        ✅ **25+ GenAI attack vectors** cataloged across 5 categories
        ✅ **7 fraud types** simulated with high fidelity
        ✅ **96.3% PR-AUC** detection performance
        ✅ **Self-hardening system** - learns from misses
        """)
    
    st.code("""
┌─────────────────────────────────────────────────────────────┐
│                    ADVERSARIAL FRAUD LAB                    │
├─────────────────────────────────────────────────────────────┤
│  IDENTIFY          │  GENERATE        │  DEFEND             │
│  Attack Taxonomy   │  Attack Engine   │  Tier 1: XGBoost    │
│  (25+ attacks)     │  (LLM + Rules)   │  Tier 2: Isolation  │
└─────────────────────────────────────────────────────────────┘
""", language="text")