import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime, timedelta
import sys
import plotly.express as px

# Constants
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Decision Wave | Unified Data Manager", layout="wide")

st.title("⚖️ Unified Data Manager")
st.markdown("### Tiered Architecture: Buffer -> Warehouse -> Archive")

# Data loading helpers
@st.cache_data(ttl=1) # Fast refresh
def get_entity_list():
    try:
        res = requests.get(f"{API_URL}/entities", timeout=5)
        if res.status_code == 200:
            entities = res.json()
            return {f"{e['name']} (ID: {e['id']})": e['id'] for e in entities}
        else:
            return {f"API Error ({res.status_code})": 0}
    except requests.exceptions.Timeout:
        return {"Connection Timeout (API Busy)": 0}
    except Exception as e:
        return {f"Connection Error: {e}": 0}

entity_map = get_entity_list()

# Sidebar - Selection
with st.sidebar:
    st.header("🔍 Search & Select")
    search_label = st.selectbox("Select Entity", options=list(entity_map.keys()), index=0)
    entity_id = entity_map[search_label]
    
    st.divider()
    st.header("📈 Visualization")
    
    # Query metrics from API
    try:
        res = requests.get(f"{API_URL}/market/metrics/{entity_id}")
        if res.status_code == 200:
            available_metrics = res.json()
        else:
            available_metrics = []
    except:
        available_metrics = []
        
    if not available_metrics:
        available_metrics = ["price", "value", "volume"]
    
    selected_metrics = st.multiselect("Metrics to Overlay", options=available_metrics, default=[available_metrics[0]] if available_metrics else [])
    limit = st.slider("Lookback Points", 10, 5000, 500)

# Fetch layered data for multiple metrics via API
def fetch_multi_metric_data(e_id, metrics, lim):
    dfs = []
    try:
        for m in metrics:
            params = {"entity_id": e_id, "metric_name": m, "limit": lim}
            res = requests.get(f"{API_URL}/market/series", params=params)
            if res.status_code == 200:
                data = res.json()
                if data:
                    df = pd.DataFrame(data)
                    df['metric'] = m
                    df['type'] = 'observation'
                    dfs.append(df)
            
            # Fetch predictions if available
            p_res = requests.get(f"{API_URL}/market/predictions/{e_id}")
            if p_res.status_code == 200:
                p_data = p_res.json()
                if p_data:
                    pdf = pd.DataFrame(p_data)
                    pdf['metric'] = f"{m} (Pred)"
                    pdf['type'] = 'prediction'
                    dfs.append(pdf)

    except Exception as e:
        st.error(f"API Access Error: {e}")
    return pd.concat(dfs) if dfs else pd.DataFrame()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 Dashboard", "📂 Explorer", "🛠️ Overrides", "⚖️ Alignment", "🥇 Prioritization"])

with tab1:
    st.header(f"Live Overlay: {search_label}")
    if entity_id >= 0: # Support Entity 0
        data_df = fetch_multi_metric_data(entity_id, selected_metrics, limit)
        
        if not data_df.empty:
            fig = px.line(data_df, x='timestamp', y='value', color='metric', 
                          line_dash='type',
                          template="plotly_dark", title=f"Multi-Metric Layered View: {search_label}")
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Data Grid Editor")
            st.info("💡 You can edit cells directly. Click 'Apply Sync' to save changes to the API.")
            
            # Pivot table for the editor (only observations)
            obs_only = data_df[data_df['type'] == 'observation']
            if not obs_only.empty:
                pivot_df = obs_only.pivot(index='timestamp', columns='metric', values='value').reset_index()
                edited_df = st.data_editor(pivot_df, use_container_width=True, key="data_editor", num_rows="dynamic")
                
                if st.button("💾 Apply Sync (Save Changes)"):
                    success_count = 0
                    for index, row in edited_df.iterrows():
                        ts = row['timestamp']
                        for col in edited_df.columns:
                            if col == 'timestamp': continue
                            val = row[col]
                            if pd.isna(val) or val is None: continue
                            
                            payload = {
                                "entity_id": int(entity_id),
                                "metric_name": col,
                                "value": float(val),
                                "event_type": "override",
                                "timestamp": str(ts)
                            }
                            requests.post(f"{API_URL}/market/observations", json=payload)
                            success_count += 1
                    st.success(f"Synced {success_count} data points.")
                    st.rerun()
            else:
                st.info("No observations found for current view.")
        else:
            st.info("No data found for the selected metrics.")
    else:
        st.warning("Please select a valid entity.")

with tab2:
    st.header("📂 Entity Explorer")
    try:
        res = requests.get(f"{API_URL}/entities")
        if res.status_code == 200:
            entities = res.json()
            table_data = [{"ID": e['id'], "Name": e['name'], "Type": e['entity_type']} for e in entities]
            st.dataframe(table_data, use_container_width=True)
            st.caption("💡 Entity ID 0 ('SYSTEM-ALIGNMENT') tracks internal agent behavior meta-metrics.")
        else:
            st.warning("Could not reach API for entities.")
    except Exception as e:
        st.error(f"Explorer Error: {e}")

with tab3:
    st.header("🛠️ Manual Overrides & Predictions")
    with st.form("manual_entry"):
        st.subheader("Add Data Point")
        c1, c2, c3 = st.columns(3)
        m_name = c1.selectbox("Metric", options=available_metrics)
        o_val = c2.number_input("Value", step=0.01)
        o_ts = c3.text_input("Timestamp (ISO)", value=datetime.utcnow().isoformat())
        if st.form_submit_button("Submit Observation"):
            payload = {"entity_id": entity_id, "metric_name": m_name, "value": o_val, "event_type": "override", "timestamp": o_ts}
            requests.post(f"{API_URL}/market/observations", json=payload)
            st.success("Accepted")
            st.rerun()

    st.divider()
    if st.button("🔄 Reset to Warehouse (Delete All Overrides)"):
        requests.delete(f"{API_URL}/market/overrides/{entity_id}")
        st.rerun()

with tab4:
    st.header("⚖️ Quantum-Statistical Alignment")
    # Feedback sidebar
    with st.sidebar:
        st.divider()
        st.header("🗳️ Alignment Feedback")
        with st.form("alignment_feedback"):
            st.info("💡 **Scoring Guidance**: \n- **Satisfaction**: How well I followed your intent/aesthetics.\n- **Performance**: Did the code/system actually work?")
            u_score = st.slider("User Satisfaction (Intent)", 0.0, 1.0, 0.8)
            a_score = st.slider("Agent Performance (Execution)", 0.0, 1.0, 0.85)
            f_notes = st.text_area("Notes")
            if st.form_submit_button("Submit Alignment Event"):
                f_params = {"user_score": u_score, "agent_score": a_score, "notes": f_notes}
                requests.post(f"{API_URL}/alignment/feedback", params=f_params)
                st.success("Synchronized!")
                st.rerun()

    try:
        res = requests.get(f"{API_URL}/alignment/stats")
        if res.status_code == 200:
            stats = res.json()
            obj = stats.get('objective', 0.5)
            weights = stats.get('weights', {})
            history = stats.get('history', [])
            phase = stats.get('phase', 'N/A')

            c1, c2 = st.columns([1, 3])
            with c1:
                st.metric("Alignment Objective", f"{obj:.2f}", delta=f"{(obj-0.5):.2f}")
                st.subheader("Engine Status")
                st.markdown(f"**Phase**: `{phase}`")
                
                st.subheader("Entropy Weights")
                st.info("**Metric Guide**:\n- **Pearson R**: Correlation accuracy\n- **Knowledge Gain**: Delta vs baseline\n- **Stability Score**: Noise resilience")
                for m, w in weights.items():
                    st.write(f"**{m}**: {w:.2%}")
                    st.progress(w)
            
            with c2:
                if history:
                    df_h = pd.DataFrame(history)
                    df_h['timestamp'] = pd.to_datetime(df_h['timestamp'])
                    
                    # Alignment Objective Trend with Confidence Aura
                    fig_obj = px.line(df_h, x='timestamp', y='alignment_objective', title="Alignment Objective Trend", template="plotly_dark")
                    if 'aleatoric_uncertainty' in df_h.columns:
                        fig_obj.add_scatter(x=df_h['timestamp'], y=df_h['alignment_objective'] + df_h['aleatoric_uncertainty'], fill=None, mode='lines', line_color='rgba(255,255,255,0)', showlegend=False)
                        fig_obj.add_scatter(x=df_h['timestamp'], y=df_h['alignment_objective'] - df_h['aleatoric_uncertainty'], fill='tonexty', mode='lines', line_color='rgba(255,255,255,0)', fillcolor='rgba(0,176,246,0.2)', name='Confidence Aura')
                    st.plotly_chart(fig_obj, use_container_width=True)

                    # Variance Chart
                    if 'aleatoric_uncertainty' in df_h.columns:
                        st.subheader("📉 Variance & Noise Reduction")
                        df_h['variance'] = df_h['aleatoric_uncertainty'] ** 2
                        fig_var = px.area(df_h, x='timestamp', y='variance', title="System Variance (Entropy²)", template="plotly_dark", color_discrete_sequence=['#ef553b'])
                        st.plotly_chart(fig_var, use_container_width=True)
                else:
                    st.info("No alignment history yet.")

            # Raw Ledger Table (Restored)
            if history:
                with st.expander("📜 View Raw Alignment Ledger"):
                    st.dataframe(pd.DataFrame(history).sort_values('timestamp', ascending=False), use_container_width=True)

            # Technical Debt Section
            try:
                res_debt = requests.get(f"{API_URL}/alignment/debt")
                if res_debt.status_code == 200:
                    debt_data = res_debt.json()
                    st.subheader(f"🛠️ Technical Debt Entropy: {debt_data.get('debt_score', 0)}")
                    if debt_data.get('violations'):
                        with st.expander("🔍 View Architectural Violations"):
                            for v in debt_data['violations']:
                                st.error(f"**{v['type']}**: {v['detail']}")
                                st.caption(f"File: `{v['file']}`")
            except: pass
        else: st.warning("Alignment API Unreachable")
    except Exception as e: st.error(f"UI Stats Error: {e}")

with tab5:
    st.header("🥇 Urgency Prioritization Leaderboard")
    try:
        res_p = requests.get(f"{API_URL}/status/priorities")
        if res_p.status_code == 200:
            priorities = res_p.json()
            if priorities:
                df_p = pd.DataFrame(priorities)
                fig_p = px.bar(df_p, x='urgency_score', y='name', orientation='h', color='urgency_score', color_continuous_scale='Reds', template="plotly_dark", title="Self-Correction Priority Heatmap")
                st.plotly_chart(fig_p, use_container_width=True)
                st.table(df_p[['name', 'urgency_score', 'uncertainty', 'weight']])
            else: st.info("No entities tracked for prioritization.")
    except: st.warning("Prioritization offline.")

# Footer
st.divider()
try:
    res = requests.get(f"{API_URL}/summary")
    if res.status_code == 200:
        s = res.json()
        c1, c2, c3 = st.columns(3)
        c1.metric("Entities", s['entities'])
        c2.metric("Observations", s['observations'])
        c3.metric("Predictions", s['predictions'])
except: pass
