"""
Admin Panel — Platform Control Center.

Provides system monitoring, data management, app settings,
audit logging, and dataset health checks for administrators.
"""

from __future__ import annotations

import io
import platform
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.audit_log import clear_audit_log, get_audit_log, initialize_audit_log, log_event
from src.data_cleaning import clean_ecommerce_data
from src.data_loader import generate_synthetic_ecommerce_data, load_dataset_from_source
from src.metrics import compute_executive_kpis

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Admin Panel | AI E-Commerce",
    page_icon="🔧",
    layout="wide",
)

initialize_audit_log()

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .admin-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        border-radius: 14px;
        padding: 28px 32px;
        margin-bottom: 24px;
        border: 1px solid #334155;
    }
    .admin-header h1 { color: #f1f5f9; margin: 0; font-size: 1.8rem; font-weight: 700; }
    .admin-header p  { color: #94a3b8; margin: 6px 0 0; font-size: 0.9rem; }

    .stat-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-bottom: 12px;
    }
    .stat-card .label { color: #94a3b8; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }
    .stat-card .value { color: #f1f5f9; font-size: 1.5rem; font-weight: 700; margin-top: 6px; }
    .stat-card .sub   { color: #64748b; font-size: 0.75rem; margin-top: 4px; }

    .status-ok      { color: #22c55e; font-weight: 700; }
    .status-warn    { color: #f59e0b; font-weight: 700; }
    .status-error   { color: #ef4444; font-weight: 700; }

    .badge { display: inline-block; padding: 2px 10px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700; }
    .badge-ok      { background: #dcfce7; color: #15803d; }
    .badge-warn    { background: #fef3c7; color: #b45309; }
    .badge-error   { background: #fee2e2; color: #b91c1c; }
    .badge-info    { background: #e0f2fe; color: #0369a1; }

    .log-row-INFO    { border-left: 3px solid #3b82f6; padding-left: 8px; margin-bottom: 4px; }
    .log-row-WARNING { border-left: 3px solid #f59e0b; padding-left: 8px; margin-bottom: 4px; }
    .log-row-ERROR   { border-left: 3px solid #ef4444; padding-left: 8px; margin-bottom: 4px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="admin-header">
        <h1>🔧 Admin Control Center</h1>
        <p>Platform administration, monitoring, data management & configuration &nbsp;|&nbsp;
        Session started at {st.session_state.get('session_start', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "session_start" not in st.session_state:
    st.session_state.session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🖥️ System Status", "📁 Data Management", "⚙️ App Settings", "📋 Audit Log", "📊 Platform Health"]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SYSTEM STATUS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("🖥️ System & Runtime Status")
    st.caption("Live environment diagnostics for the running Streamlit instance.")

    # ── Runtime info ──────────────────────────────────────────────────────────
    try:
        import psutil
        mem = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=0.5)
        disk = psutil.disk_usage("/")
        mem_used_gb = mem.used / (1024**3)
        mem_total_gb = mem.total / (1024**3)
        mem_pct = mem.percent
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        disk_pct = disk.percent
        psutil_ok = True
    except ImportError:
        psutil_ok = False
        cpu_pct = mem_pct = disk_pct = 0
        mem_used_gb = mem_total_gb = disk_used_gb = disk_total_gb = 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""<div class="stat-card">
            <div class="label">Python Version</div>
            <div class="value">{platform.python_version()}</div>
            <div class="sub">{platform.system()} {platform.machine()}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="stat-card">
            <div class="label">Streamlit Version</div>
            <div class="value">{st.__version__}</div>
            <div class="sub">Web framework</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c3:
        mem_val = f"{mem_used_gb:.1f} / {mem_total_gb:.1f} GB" if psutil_ok else "N/A"
        mem_sub = f"{mem_pct:.0f}% utilised" if psutil_ok else "Install psutil for live data"
        st.markdown(
            f"""<div class="stat-card">
            <div class="label">Memory Usage</div>
            <div class="value">{mem_val}</div>
            <div class="sub">{mem_sub}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c4:
        cpu_val = f"{cpu_pct:.0f}%" if psutil_ok else "N/A"
        st.markdown(
            f"""<div class="stat-card">
            <div class="label">CPU Load</div>
            <div class="value">{cpu_val}</div>
            <div class="sub">{'Live reading' if psutil_ok else 'Install psutil'}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Gauge charts ─────────────────────────────────────────────────────────
    if psutil_ok:
        gc1, gc2, gc3 = st.columns(3)
        for col, pct, label, color in [
            (gc1, cpu_pct,  "CPU %",    "#6366f1"),
            (gc2, mem_pct,  "Memory %", "#0ea5e9"),
            (gc3, disk_pct, "Disk %",   "#10b981"),
        ]:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pct,
                number={"suffix": "%", "font": {"size": 28, "color": "#f1f5f9"}},
                title={"text": label, "font": {"color": "#94a3b8", "size": 14}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#475569"},
                    "bar": {"color": color},
                    "bgcolor": "#1e293b",
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, 60],  "color": "#0f172a"},
                        {"range": [60, 80], "color": "#1e293b"},
                        {"range": [80, 100],"color": "#2d1515"},
                    ],
                    "threshold": {"line": {"color": "#ef4444", "width": 2}, "thickness": 0.75, "value": 90},
                },
            ))
            fig.update_layout(
                height=200,
                margin=dict(l=20, r=20, t=40, b=10),
                paper_bgcolor="#0f172a",
                font_color="#f1f5f9",
            )
            col.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 Install `psutil` for live CPU / Memory / Disk gauges: `pip install psutil`")

    st.markdown("---")

    # ── Environment table ─────────────────────────────────────────────────────
    st.subheader("🔬 Environment Details")
    env_data = [
        {"Property": "OS Platform",         "Value": platform.platform()},
        {"Property": "CPU Cores",            "Value": str(platform.processor() or "N/A")},
        {"Property": "Python Executable",   "Value": sys.executable},
        {"Property": "Working Directory",    "Value": str(PROJECT_ROOT)},
        {"Property": "Session Start",        "Value": st.session_state.get("session_start", "—")},
        {"Property": "Active Dataset",       "Value": st.session_state.get("dataset_name", "None")},
        {"Property": "Dataset Rows",         "Value": f"{len(st.session_state.cleaned_df):,}" if st.session_state.get("cleaned_df") is not None else "0"},
        {"Property": "Audit Events Logged",  "Value": str(len(st.session_state.get("audit_log", [])))},
    ]
    st.dataframe(pd.DataFrame(env_data), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DATA MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("📁 Data Management Console")
    st.caption("Inspect, refresh, export, or clear the active dataset.")

    df = st.session_state.get("cleaned_df")
    raw_df = st.session_state.get("raw_df")

    if df is not None and not df.empty:
        kpis = compute_executive_kpis(df)

        # Dataset stats
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Clean Rows",    f"{len(df):,}")
        m2.metric("Raw Rows",      f"{len(raw_df):,}" if raw_df is not None else "N/A")
        m3.metric("Columns",       f"{df.shape[1]}")
        m4.metric("Memory (MB)",   f"{df.memory_usage(deep=True).sum() / 1024**2:.2f}")
        m5.metric("Date Range",    f"{df['InvoiceDate'].dt.date.min() if 'InvoiceDate' in df.columns else '—'}")

        st.markdown("---")

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### 📤 Export Dataset")
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False)
            st.download_button(
                label="⬇️ Download Cleaned CSV",
                data=csv_buf.getvalue().encode("utf-8"),
                file_name=f"ecommerce_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            excel_buf = io.BytesIO()
            with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Clean Data")
                if raw_df is not None:
                    raw_df.head(5000).to_excel(writer, index=False, sheet_name="Raw Data (sample)")
            st.download_button(
                label="⬇️ Download Excel Workbook",
                data=excel_buf.getvalue(),
                file_name=f"ecommerce_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_right:
            st.markdown("#### 🔄 Data Controls")
            st.markdown("**Regenerate Synthetic Dataset**")
            n_records = st.number_input("Records to generate:", min_value=500, max_value=50000, value=2500, step=500)
            seed_val  = st.number_input("Random seed:",         min_value=0,   max_value=9999,  value=42,   step=1)
            if st.button("🔃 Regenerate Synthetic Data", use_container_width=True):
                with st.spinner("Generating..."):
                    raw_new = generate_synthetic_ecommerce_data(num_records=int(n_records), random_seed=int(seed_val))
                    clean_new, sum_new = clean_ecommerce_data(raw_new)
                    st.session_state.raw_df          = raw_new
                    st.session_state.cleaned_df      = clean_new
                    st.session_state.cleaning_summary = sum_new
                    st.session_state.dataset_name    = f"Synthetic ({n_records:,} records, seed={seed_val})"
                    st.session_state.is_sample       = True
                    log_event("DATA_REGEN", f"Synthetic data regenerated: {n_records} records, seed={seed_val}")
                st.success(f"✅ Generated {len(clean_new):,} clean records.")
                st.rerun()

            st.markdown("---")
            st.markdown("**⚠️ Clear Session Cache**")
            if st.button("🗑️ Clear All Session Data", use_container_width=True, type="secondary"):
                for key in ["raw_df", "cleaned_df", "cleaning_summary", "dataset_name"]:
                    st.session_state[key] = None
                st.session_state.is_sample = True
                log_event("CACHE_CLEAR", "Session data cleared by admin.", severity="WARNING")
                st.warning("Session cleared. Return to home to reload data.")
                st.rerun()

        st.markdown("---")
        st.subheader("🔍 Data Preview")
        preview_tab1, preview_tab2 = st.tabs(["Clean Data", "Raw Data"])
        with preview_tab1:
            st.dataframe(df.head(100), use_container_width=True)
        with preview_tab2:
            if raw_df is not None:
                st.dataframe(raw_df.head(100), use_container_width=True)
            else:
                st.info("Raw data not available.")
    else:
        st.warning("⚠️ No dataset loaded. Return to the home page and load data first.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — APP SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("⚙️ Application Settings")
    st.caption("Configure runtime behaviour for this Streamlit session.")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown("#### 🎨 Display Preferences")
        chart_theme = st.selectbox(
            "Plotly Chart Theme",
            ["plotly_dark", "plotly", "ggplot2", "seaborn", "simple_white"],
            index=0,
        )
        st.session_state["chart_theme"] = chart_theme

        top_n_products = st.slider("Default Top-N Products to Show", 5, 30, value=st.session_state.get("top_n_products", 10))
        st.session_state["top_n_products"] = top_n_products

        top_n_customers = st.slider("Default Top-N Customers to Show", 5, 50, value=st.session_state.get("top_n_customers", 20))
        st.session_state["top_n_customers"] = top_n_customers

        if st.button("💾 Save Display Settings", use_container_width=True):
            log_event("SETTINGS_CHANGE", f"Display: theme={chart_theme}, top_n_products={top_n_products}, top_n_customers={top_n_customers}")
            st.success("Display settings saved to session.")

    with col_s2:
        st.markdown("#### 🤖 ML Model Settings")
        kmeans_k = st.slider(
            "K-Means Cluster Count (Customer Segmentation)",
            min_value=2, max_value=10,
            value=st.session_state.get("kmeans_k", 4),
        )
        st.session_state["kmeans_k"] = kmeans_k

        forecast_horizon = st.slider(
            "Sales Forecast Horizon (days)",
            min_value=7, max_value=180,
            value=st.session_state.get("forecast_horizon", 30),
        )
        st.session_state["forecast_horizon"] = forecast_horizon

        ml_random_seed = st.number_input(
            "Global ML Random Seed",
            min_value=0, max_value=9999,
            value=st.session_state.get("ml_random_seed", 42),
        )
        st.session_state["ml_random_seed"] = ml_random_seed

        anomaly_contamination = st.slider(
            "Anomaly Detection Contamination Factor",
            min_value=0.01, max_value=0.20,
            value=st.session_state.get("anomaly_contamination", 0.05),
            step=0.01,
        )
        st.session_state["anomaly_contamination"] = anomaly_contamination

        if st.button("💾 Save ML Settings", use_container_width=True):
            log_event(
                "SETTINGS_CHANGE",
                f"ML: k={kmeans_k}, horizon={forecast_horizon}, seed={ml_random_seed}, contamination={anomaly_contamination}",
            )
            st.success("ML settings saved to session.")

    st.markdown("---")
    st.markdown("#### 🔗 External Integrations")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        ollama_host = st.text_input(
            "Ollama API Host",
            value=st.session_state.get("ollama_host", "http://localhost:11434"),
        )
        st.session_state["ollama_host"] = ollama_host
    with col_e2:
        ollama_model = st.text_input(
            "Preferred Ollama Model",
            value=st.session_state.get("ollama_model", "llama3"),
        )
        st.session_state["ollama_model"] = ollama_model

    if st.button("💾 Save Integration Settings", use_container_width=True):
        log_event("SETTINGS_CHANGE", f"Ollama host={ollama_host}, model={ollama_model}")
        st.success("Integration settings saved.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — AUDIT LOG
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("📋 Session Audit Log")
    st.caption("Chronological record of all platform events for this session.")

    log_df = get_audit_log()

    col_a1, col_a2, col_a3 = st.columns([1, 1, 2])
    with col_a1:
        st.metric("Total Events", len(log_df))
    with col_a2:
        if not log_df.empty and "Severity" in log_df.columns:
            warn_count = int((log_df["Severity"] == "WARNING").sum()) + int((log_df["Severity"] == "ERROR").sum())
            st.metric("Warnings / Errors", warn_count)
        else:
            st.metric("Warnings / Errors", 0)

    st.markdown("---")

    if not log_df.empty:
        # Filter by severity
        severities = ["ALL"] + sorted(log_df["Severity"].unique().tolist())
        filter_sev = st.selectbox("Filter by Severity:", severities)
        display_df = log_df if filter_sev == "ALL" else log_df[log_df["Severity"] == filter_sev]

        # Color-code severity
        def color_severity(val):
            colors = {"INFO": "color: #3b82f6", "WARNING": "color: #f59e0b", "ERROR": "color: #ef4444"}
            return colors.get(val, "")

        styled = display_df.style.applymap(color_severity, subset=["Severity"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # Export log
        log_csv = log_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Export Audit Log (CSV)",
            data=log_csv,
            file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

        if st.button("🗑️ Clear Audit Log", type="secondary"):
            clear_audit_log()
            st.success("Audit log cleared.")
            st.rerun()
    else:
        st.info("📭 No events logged yet in this session. Interact with the dashboard to generate events.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — PLATFORM HEALTH
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("📊 Dataset & Platform Health")
    st.caption("Completeness, schema validation, and data quality diagnostics.")

    df = st.session_state.get("cleaned_df")
    if df is None or df.empty:
        st.warning("⚠️ No dataset loaded.")
        st.stop()

    # ── Completeness overview ─────────────────────────────────────────────────
    st.markdown("#### ✅ Column Completeness")
    total_rows = len(df)
    completeness = []
    for col in df.columns:
        non_null = int(df[col].notna().sum())
        pct = non_null / total_rows * 100 if total_rows > 0 else 0
        status = "✅ OK" if pct >= 95 else ("⚠️ Partial" if pct >= 50 else "❌ Sparse")
        completeness.append({"Column": col, "Non-Null": non_null, "Missing": total_rows - non_null, "Completeness %": round(pct, 1), "Status": status})

    comp_df = pd.DataFrame(completeness)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    overall_completeness = comp_df["Completeness %"].mean()
    st.progress(int(overall_completeness), text=f"Overall Dataset Completeness: {overall_completeness:.1f}%")

    st.markdown("---")

    # ── Missing value heatmap ─────────────────────────────────────────────────
    st.markdown("#### 🗺️ Missing Value Heatmap (sample of 500 rows)")
    sample = df.sample(min(500, len(df)), random_state=42)
    missing_matrix = sample.isnull().astype(int)
    fig_heat = px.imshow(
        missing_matrix.T,
        color_continuous_scale=[[0, "#1e293b"], [1, "#ef4444"]],
        aspect="auto",
        title="Missing Values (red = missing)",
        labels=dict(color="Missing"),
    )
    fig_heat.update_layout(
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font_color="#f1f5f9",
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        coloraxis_showscale=False,
        xaxis=dict(showticklabels=False),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")

    # ── Schema validation ─────────────────────────────────────────────────────
    st.markdown("#### 🔍 Schema Validation")
    expected_cols = {
        "InvoiceNo":   "object",
        "StockCode":   "object",
        "Description": "object",
        "Quantity":    "int64",
        "InvoiceDate": "datetime64",
        "UnitPrice":   "float64",
        "CustomerID":  "object",
        "Country":     "object",
    }

    schema_rows = []
    for col, expected_dtype in expected_cols.items():
        present = col in df.columns
        actual = str(df[col].dtype) if present else "—"
        dtype_ok = expected_dtype.lower() in actual.lower() if present else False
        schema_rows.append({
            "Column":          col,
            "Expected Dtype":  expected_dtype,
            "Actual Dtype":    actual,
            "Present":         "✅" if present else "❌",
            "Dtype Match":     "✅" if dtype_ok else ("⚠️" if present else "❌"),
        })
    st.dataframe(pd.DataFrame(schema_rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Duplicate check ──────────────────────────────────────────────────────
    st.markdown("#### 🔄 Duplicate Records Check")
    dup_count = int(df.duplicated().sum())
    dup_pct   = dup_count / len(df) * 100 if len(df) > 0 else 0

    d1, d2, d3 = st.columns(3)
    d1.metric("Total Rows",       f"{len(df):,}")
    d2.metric("Duplicate Rows",   f"{dup_count:,}")
    d3.metric("Duplicate %",      f"{dup_pct:.2f}%")

    if dup_count == 0:
        st.success("✅ No duplicate rows detected.")
    elif dup_pct < 5:
        st.warning(f"⚠️ {dup_count:,} duplicate rows found ({dup_pct:.1f}%). Consider deduplication.")
    else:
        st.error(f"❌ High duplicate rate: {dup_count:,} rows ({dup_pct:.1f}%). Data quality may be compromised.")

    st.markdown("---")

    # ── Numerical distribution summary ────────────────────────────────────────
    st.markdown("#### 📐 Numerical Column Statistics")
    num_df = df.select_dtypes(include="number")
    if not num_df.empty:
        st.dataframe(num_df.describe().round(2).T.rename(columns={"50%": "median"}), use_container_width=True)
    else:
        st.info("No numerical columns found.")
