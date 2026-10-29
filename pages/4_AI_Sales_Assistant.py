"""
Page 4: AI Sales Assistant.
Interactive natural language business intelligence assistant with optional local Ollama LLM and deterministic fallback.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.ai_assistant import ask_sales_assistant, build_analytical_context
from src.local_llm import check_ollama_status


st.set_page_config(page_title="AI Sales Assistant | AI E-Commerce", page_icon="🤖", layout="wide")

st.title("🤖 Local AI Commercial Sales Assistant")
st.caption("Ask natural-language questions about commercial revenue, top products, international markets, and customer behavior.")

if "cleaned_df" not in st.session_state or st.session_state.cleaned_df is None or st.session_state.cleaned_df.empty:
    st.warning("⚠️ No active dataset available. Please load data from the homepage.")
    st.stop()

df = st.session_state.cleaned_df

# Check Ollama Status
ollama_info = check_ollama_status()

# Assistant Configuration Sidebar / Expander
with st.expander("⚙️ Assistant Engine Settings & Hardware Status", expanded=not ollama_info["available"]):
    col_cfg1, col_cfg2 = st.columns([1, 1])

    with col_cfg1:
        st.markdown("#### Engine Selection")
        use_llm = st.toggle(
            "Enable Local Generative LLM (Ollama)",
            value=ollama_info["available"],
            disabled=not ollama_info["available"],
            help="Requires Ollama running locally. When disabled, the deterministic rule-based assistant runs instead.",
        )

        if ollama_info["available"]:
            model_options = ollama_info["models"] if ollama_info["models"] else ["llama3.2:1b", "qwen2.5:1.5b"]
            selected_model = st.selectbox("Select Local Model:", model_options)
        else:
            selected_model = "None (Ollama Offline)"
            st.warning("⚠️ Local Ollama daemon was not detected on `http://127.0.0.1:11434`. The deterministic fallback assistant is active.")

    with col_cfg2:
        st.markdown("#### Privacy & Architecture Principles")
        st.markdown(
            """
            - **100% Local & Free:** Never sends data to external cloud APIs or paid services.
            - **PII Guarded:** Only high-level mathematical aggregations are passed to the model.
            - **No Hallucinations:** Numbers are strictly verified against dataset calculations.
            """
        )

# Analytical Context Builder
rfm_df = st.session_state.get("rfm_labeled_df", None)
context = build_analytical_context(df, rfm_labeled_df=rfm_df)

# Quick Prompts
st.markdown("##### 💡 Suggested Questions")
prompt_cols = st.columns(4)
sample_queries = [
    "What is the total revenue and AOV?",
    "Which products generated the most sales?",
    "Which countries are the largest markets?",
    "How have sales changed over the period?",
]

selected_prompt = None
for idx, q_text in enumerate(sample_queries):
    with prompt_cols[idx]:
        if st.button(q_text, key=f"quick_prompt_{idx}", use_container_width=True):
            selected_prompt = q_text

# Chat Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": "Hello! I am your AI Sales Assistant. You can ask me any question regarding your e-commerce revenue, best-selling SKUs, international markets, or customer segments.",
            "mode": "System",
            "evidence": None,
        }
    ]

# Reset Chat
col_chat_title, col_reset = st.columns([4, 1])
with col_reset:
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# Display Chat History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("mode") and message["role"] == "assistant":
            badge_type = "badge-success" if "LLM" in message["mode"] else "badge-info"
            st.markdown(
                f'<span class="badge-pill {badge_type}">Engine: {message["mode"]}</span>',
                unsafe_allow_html=True,
            )

# Input handling
user_input = st.chat_input("Ask a question about the active dataset...")
active_query = user_input or selected_prompt

if active_query:
    # Append user question
    st.session_state.chat_history.append({"role": "user", "content": active_query})
    with st.chat_message("user"):
        st.markdown(active_query)

    # Process answer
    with st.chat_message("assistant"):
        with st.spinner("Analyzing dataset metrics..."):
            ans_payload = ask_sales_assistant(
                query=active_query,
                context=context,
                use_local_llm=use_llm and ollama_info["available"],
                selected_model=selected_model if ollama_info["available"] else "llama3.2:1b",
            )
            st.markdown(ans_payload["answer"])

            engine_mode = ans_payload.get("mode", "deterministic")
            badge_class = "badge-success" if "LLM" in engine_mode else "badge-info"
            st.markdown(
                f'<span class="badge-pill {badge_class}">Engine: {engine_mode}</span>',
                unsafe_allow_html=True,
            )

            if ans_payload.get("evidence"):
                with st.expander("🔍 Verified Analytical Evidence"):
                    st.json(ans_payload["evidence"])

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": ans_payload["answer"],
        "mode": engine_mode,
        "evidence": ans_payload.get("evidence"),
    })
