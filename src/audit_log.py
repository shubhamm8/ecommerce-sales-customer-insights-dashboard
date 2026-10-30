"""
Audit Log Module.

Tracks user actions within the Streamlit session for the Admin Panel.
All events are stored in st.session_state.audit_log as a list of dicts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st


def initialize_audit_log() -> None:
    """Ensure the audit_log list exists in session state."""
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []


def log_event(event_type: str, detail: str, severity: str = "INFO") -> None:
    """
    Append a timestamped event to the session audit log.

    Args:
        event_type: Category label (e.g. 'DATA_LOAD', 'SETTINGS_CHANGE').
        detail: Human-readable description of the event.
        severity: One of 'INFO', 'WARNING', 'ERROR'.
    """
    initialize_audit_log()
    st.session_state.audit_log.append(
        {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Severity": severity,
            "Event Type": event_type,
            "Detail": detail,
        }
    )


def get_audit_log() -> pd.DataFrame:
    """Return the current audit log as a DataFrame."""
    initialize_audit_log()
    if not st.session_state.audit_log:
        return pd.DataFrame(columns=["Timestamp", "Severity", "Event Type", "Detail"])
    return pd.DataFrame(st.session_state.audit_log)


def clear_audit_log() -> None:
    """Wipe the audit log for this session."""
    st.session_state.audit_log = []
