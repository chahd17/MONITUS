#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MONITUS Dashboard - First visual prototype using Streamlit
Uses existing detection/verification engines.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from ai_service.anomaly_detector import AnomalyDetector
from ai_service.regional_detector import RegionalDetector
from ai_service.alert_verifier import AlertVerifier


# Color scheme: deep turquoise, navy and white
COLORS = {
    "navy": "#102A43",
    "dark_navy": "#102A43",
    "deep_turquoise": "#00BFC1",
    "turquoise": "#00BFC1",
    "white": "#FFFFFF",
    "light_gray": "#F4F7F9",
    "card_gray": "#F4F7F9",
    "body_text": "#243B53",
    "red": "#DC143C",
    "orange": "#FF8C00"
}


def load_and_process(scenario_file: str):
    """Load and process data using existing engines."""
    data_dir = project_root / "data" / "synthetic"
    csv_path = data_dir / scenario_file
    
    detector = AnomalyDetector(window_size=21, threshold=3.5)
    regional_detector = RegionalDetector(min_supporting_hospitals=2)
    verifier = AlertVerifier(persistence_days=2, persistence_window=3)
    
    # Get individual results
    individual_results = detector.analyze_file(csv_path)
    
    # Get regional results
    regional_reports = regional_detector.corroborate(individual_results)
    
    # Get verification
    assessments = verifier.verify(regional_reports, individual_results)
    
    return individual_results, regional_reports, assessments, csv_path


def main():
    st.set_page_config(
        page_title="MONITUS Dashboard",
        page_icon="🏥",
        layout="wide"
    )
    
    # Set light theme and fix contrast via CSS
    st.markdown(f"""
    <style>
    .stApp {{
        background-color: {COLORS['white']} !important;
    }}
    .main {{
        background-color: {COLORS['white']} !important;
    }}
    [data-testid="stHeader"] {{
        background-color: {COLORS['white']} !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: {COLORS['light_gray']} !important;
    }}
    h1 {{
        color: {COLORS['navy']} !important;
        border-bottom: 3px solid {COLORS['deep_turquoise']} !important;
        padding-bottom: 10px;
    }}
    h2 {{
        color: {COLORS['navy']} !important;
    }}
    h3 {{
        color: {COLORS['navy']} !important;
    }}
    p, span, label, div {{
        color: {COLORS['body_text']} !important;
    }}
    .stSelectbox label, .stSelectbox div, .stMarkdown {{
        color: {COLORS['navy']} !important;
    }}
    .metric-card {{
        background-color: {COLORS['card_gray']} !important;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid {COLORS['deep_turquoise']} !important;
        color: {COLORS['navy']} !important;
    }}
    .metric-card h3, .metric-card p {{
        color: {COLORS['navy']} !important;
    }}
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
        color: {COLORS['navy']} !important;
    }}
    .stDataFrame {{
        background-color: {COLORS['white']} !important;
    }}
    table {{
        color: {COLORS['body_text']} !important;
    }}
    .stAlert {{
        background-color: {COLORS['light_gray']} !important;
        color: {COLORS['body_text']} !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Title
    st.markdown(f"<h1>MONITUS - AI-Powered Disease Outbreak Detection & Decentralized Emergency Response</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: {COLORS['navy']} !important; font-weight: bold;'>⚠️ ALL HOSPITAL DATA IS SYNTHETIC - NO REAL PATIENT DATA</p>", unsafe_allow_html=True)
    
    # Scenario selector
    st.markdown("### Scenario Selection")
    scenario = st.selectbox(
        "Select scenario:",
        ["normal", "regional_outbreak", "reporting_error"],
        format_func=lambda x: {
            "normal": "Normal - Stable Baseline",
            "regional_outbreak": "Regional Outbreak - Multi-site Increase",
            "reporting_error": "Reporting Error - Isolated Spike"
        }[x]
    )
    
    scenario_file = f"{scenario}.csv"
    
    try:
        individual_results, regional_reports, assessments, csv_path = load_and_process(scenario_file)
        
        # Hospital mapping
        hospital_info = {
            "HOSP_TUN": {"name": "Tunis", "city": "Tunis"},
            "HOSP_SOU": {"name": "Sousse", "city": "Sousse"},
            "HOSP_SFX": {"name": "Sfax", "city": "Sfax"}
        }
        
        # Hospital cards
        st.markdown("### Hospital Overview (SYNTHETIC DATA)")
        cols = st.columns(3)
        for idx, (hid, info) in enumerate(hospital_info.items()):
            with cols[idx]:
                results = individual_results.get(hid, [])
                anomaly_count = sum(1 for r in results if r.get('anomaly_flag', False))
                st.markdown(f"""
                <div class='metric-card'>
                    <h3 style='margin:0; color: {COLORS['navy']} !important;'>{info['name']}</h3>
                    <p style='margin:5px 0; color: {COLORS['navy']} !important;'>Hospital ID: {hid}</p>
                    <p style='margin:5px 0; color: {COLORS['navy']} !important;'><strong>Anomalous Days: {anomaly_count}</strong></p>
                    <p style='margin:5px 0; font-size:12px; color: {COLORS['deep_turquoise']} !important;'>SYNTHETIC</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Time series charts
        st.markdown("### Time Series - Daily Respiratory Cases")
        for hid, info in hospital_info.items():
            results = individual_results.get(hid, [])
            if not results:
                continue
            
            df = pd.DataFrame(results)
            df['date'] = pd.to_datetime(df['date'])
            
            fig = go.Figure()
            
            # Line chart for cases
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['observed_cases'],
                mode='lines+markers',
                name='Cases',
                line=dict(color=COLORS['navy'], width=2),
                marker=dict(size=6)
            ))
            
            # Highlight anomalies
            anomalies = df[df['anomaly_flag'] == True]
            if not anomalies.empty:
                fig.add_trace(go.Scatter(
                    x=anomalies['date'],
                    y=anomalies['observed_cases'],
                    mode='markers',
                    name='Anomaly Detected',
                    marker=dict(
                        color=COLORS['red'],
                        size=12,
                        symbol='x',
                        line=dict(width=2, color=COLORS['red'])
                    )
                ))
            
            fig.update_layout(
                title=f"{info['name']} ({hid}) - SYNTHETIC",
                xaxis_title="Date",
                yaxis_title="Respiratory Cases",
                height=400,
                plot_bgcolor=COLORS['white'],
                paper_bgcolor=COLORS['white'],
                font=dict(color=COLORS['navy']),
                legend=dict(font=dict(color=COLORS['navy']))
            )
            fig.update_xaxes(title_font=dict(color=COLORS['navy']), tickfont=dict(color=COLORS['navy']))
            fig.update_yaxes(title_font=dict(color=COLORS['navy']), tickfont=dict(color=COLORS['navy']))
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Regional signals and verification
        st.markdown("### Regional Corroboration & Alert Verification")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Regional Signal Summary")
            regional_signals = [r for r in regional_reports if r['regional_signal']]
            st.metric("Regional Signal Days (≥2 hospitals)", len(regional_signals))
            if regional_signals:
                for rs in regional_signals:
                    st.markdown(f"<p style='color:{COLORS['body_text']} !important;'><strong>{rs['date']}</strong>: {', '.join(rs['supporting_hospitals'])} (scores: {rs['individual_anomaly_scores']})</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='color:{COLORS['body_text']} !important;'>No regional signals detected</p>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### Alert Verification Status")
            if assessments:
                for a in assessments:
                    status_color = COLORS['red'] if a['status'] in ['REGIONAL_SIGNAL_REQUIRES_REVIEW'] else COLORS['orange'] if a['status'] == 'REGIONAL_SIGNAL_UNCONFIRMED' else COLORS['deep_turquoise'] if a['status'] == 'ISOLATED_ANOMALY' else COLORS['navy']
                    st.markdown(f"<p style='color:{COLORS['body_text']} !important;'><strong>{a['date']}</strong>: <span style='color:{status_color} !important; font-weight:bold;'>{a['status']}</span></p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:{COLORS['body_text']} !important;'>Sites: {a['num_supporting_sites']} - {a['supporting_hospitals']}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='color:{COLORS['body_text']} !important;'>No alerts to verify</p>", unsafe_allow_html=True)
        
        # Flagged table
        st.markdown("### Flagged Dates - Detailed View")
        flagged_data = []
        for a in assessments:
            if a['status'] != 'NORMAL':
                flagged_data.append({
                    'Date': a['date'],
                    'Hospitals': ', '.join(a['supporting_hospitals']),
                    'Supporting Sites': a['num_supporting_sites'],
                    'Verification Status': a['status'],
                    'Explanation': a['explanation'][:100] + '...' if len(a['explanation']) > 100 else a['explanation']
                })
        
        if flagged_data:
            df_flagged = pd.DataFrame(flagged_data)
            st.dataframe(df_flagged, use_container_width=True)
        else:
            st.markdown(f"<p style='color:{COLORS['body_text']} !important;'>No flagged dates in this scenario</p>", unsafe_allow_html=True)
        
        # Data quality warnings
        all_warnings = []
        for a in assessments:
            for w in a.get('data_quality_warnings', []):
                all_warnings.append(f"{a['date']}: {w}")
        if all_warnings:
            st.markdown("### Data Quality Warnings")
            for w in all_warnings:
                st.markdown(f"<p style='color:{COLORS['body_text']} !important;'>⚠️ {w}</p>", unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure the data has been generated and all modules are available.")


if __name__ == "__main__":
    main()
