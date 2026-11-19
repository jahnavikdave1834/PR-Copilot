"""PR Understanding Copilot - Streamlit Frontend Application.
Main entry point coordinating navigation, session state, and view rendering.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure kg_demo directory is on sys.path
root_dir = Path(__file__).parent.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st

from frontend.api_client import BackendClient
from frontend.styles import CSS_THEME
from frontend.views.home import render_home
from frontend.views.new_assessment import render_new_assessment
from frontend.views.pr_details import render_pr_details
from frontend.views.intern_qa import render_intern_qa
from frontend.views.results import render_results
from frontend.views.mentor_dashboard import render_mentor_dashboard
from frontend.views.history import render_history

# 1. Page Configuration (Strictly no emojis)
st.set_page_config(
    page_title="PR Understanding Copilot",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Inject SaaS CSS Theme (Beige, Orange, Navy Blue)
st.markdown(CSS_THEME, unsafe_allow_html=True)

# 3. Session State Initialization
if "api_base_url" not in st.session_state:
    st.session_state["api_base_url"] = "http://127.0.0.1:8000/api"

if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "Home Dashboard"

if "current_pr" not in st.session_state:
    st.session_state["current_pr"] = None

if "current_assessment_id" not in st.session_state:
    st.session_state["current_assessment_id"] = None

if "assessment_data" not in st.session_state:
    st.session_state["assessment_data"] = None

if "answers_draft" not in st.session_state:
    st.session_state["answers_draft"] = {}

if "report_data" not in st.session_state:
    st.session_state["report_data"] = None

# Initialize Backend Client
client = BackendClient(base_url=st.session_state["api_base_url"])

# 4. Sidebar Navigation & Controls
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 10px 0 20px 0; border-bottom: 1px solid #D8CEBD; margin-bottom: 20px;">
            <div style="font-size: 20px; font-weight: 800; color: #0F1E36; display: flex; align-items: center; gap: 10px; letter-spacing: -0.02em;">
                <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #1B365D;"></span>
                PR Copilot
            </div>
            <div style="font-size: 12px; color: #4A5E78; margin-top: 5px; font-weight: 600;">
                Intern Assessment & Mentorship Engine
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation Menu
    pages = [
        "Home Dashboard",
        "New PR Assessment",
        "PR Details & Changes",
        "Intern Q&A Interface",
        "Assessment Results",
        "Mentor Dashboard",
        "Assessment History",
    ]

    selected_page = st.radio(
        "Navigation",
        options=pages,
        index=pages.index(st.session_state["nav_page"]) if st.session_state["nav_page"] in pages else 0,
        label_visibility="collapsed",
    )
    if selected_page != st.session_state["nav_page"]:
        st.session_state["nav_page"] = selected_page
        st.rerun()

    st.write("")
    st.divider()

    # Active Session Context Indicator
    curr_id = st.session_state.get("current_assessment_id")
    if curr_id:
        st.markdown(
            f"""
            <div style="background: #F2EEE7; border: 1px solid #DDD6C8; border-left: 4px solid #EA580C; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
                <div style="font-size: 11px; font-weight: 700; color: #3B4D66; text-transform: uppercase; letter-spacing: 0.05em;">Active Session</div>
                <div style="font-size: 15px; font-weight: 800; color: #0B192C; margin-top: 2px;">Assessment #{curr_id}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Backend Connection Settings Expander
    with st.expander("Server Configuration"):
        new_url = st.text_input("FastAPI Base URL", value=st.session_state["api_base_url"])
        if new_url != st.session_state["api_base_url"]:
            st.session_state["api_base_url"] = new_url
            st.rerun()

        # Ping health
        try:
            health_res = client.check_health()
            st.success(f"Connected: {health_res.get('status')}")
        except Exception:
            st.error("Backend unreachable")

    st.caption("PR Understanding Copilot v1.0.0")

# 5. Route to Selected Page
current_view = st.session_state["nav_page"]

if current_view == "Home Dashboard":
    render_home(client)
elif current_view == "New PR Assessment":
    render_new_assessment(client)
elif current_view == "PR Details & Changes":
    render_pr_details(client)
elif current_view == "Intern Q&A Interface":
    render_intern_qa(client)
elif current_view == "Assessment Results":
    render_results(client)
elif current_view == "Mentor Dashboard":
    render_mentor_dashboard(client)
elif current_view == "Assessment History":
    render_history(client)
