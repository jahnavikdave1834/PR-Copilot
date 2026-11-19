"""View 1: Home Dashboard"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List
from ..api_client import BackendClient


def render_home(client: BackendClient) -> None:
    # Check backend health
    is_healthy = False
    try:
        health = client.check_health()
        is_healthy = health.get("status") == "ok"
    except Exception:
        is_healthy = False

    # Hero Banner
    status_indicator = '<span class="indicator-dot indicator-online"></span> Online' if is_healthy else '<span class="indicator-dot indicator-offline"></span> Offline'
    st.markdown(
        f"""
        <div class="hero-banner">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div class="hero-title">PR Understanding Copilot</div>
                    <div class="hero-subtitle">
                        Automated AI-driven technical interrogation and mentor evaluation platform for engineering interns.
                    </div>
                </div>
                <div class="hero-pill">
                    Backend: {status_indicator}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not is_healthy:
        st.error(
            "Cannot connect to the FastAPI backend at `http://127.0.0.1:8000`. "
            "Please ensure the backend server is running (`uvicorn backend.main:app --reload`)."
        )

    # Fetch assessment history for KPIs
    assessments: List[Dict[str, Any]] = []
    try:
        assessments = client.list_assessments()
    except Exception:
        pass

    total_count = len(assessments)
    completed_count = sum(1 for a in assessments if a.get("is_completed"))
    unique_interns = len({a.get("intern_id") for a in assessments if a.get("intern_id")})
    scored = [a.get("score_percentage") for a in assessments if a.get("score_percentage") is not None]
    avg_score = round(sum(scored) / len(scored), 1) if scored else 0.0

    # Top KPI Metrics Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value">{total_count}</div>
                <div class="metric-label">Total Assessments</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value">{completed_count}</div>
                <div class="metric-label">Completed Sessions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value">{unique_interns}</div>
                <div class="metric-label">Active Interns</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        score_display = f"{avg_score}%" if scored else "N/A"
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value" style="color: #1B365D;">{score_display}</div>
                <div class="metric-label">Avg Intern Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    st.write("")

    # Quick Action Cards
    st.subheader("Quick Workflows")
    qcol1, qcol2, qcol3 = st.columns(3)

    with qcol1:
        st.markdown(
            """
            <div class="saas-card" style="min-height: 180px;">
                <h4 style="margin: 0 0 8px 0; color: #0B192C;">New PR Assessment</h4>
                <p style="color: #3B4D66; font-size: 14px; margin-bottom: 16px;">
                    Fetch a GitHub pull request, parse diffs with Python AST, and generate targeted technical questions.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Start New Assessment →", key="btn_quick_new", use_container_width=True):
            st.session_state["nav_page"] = "New PR Assessment"
            st.rerun()

    with qcol2:
        st.markdown(
            """
            <div class="saas-card" style="min-height: 180px;">
                <h4 style="margin: 0 0 8px 0; color: #0B192C;">Mentor Dashboard</h4>
                <p style="color: #3B4D66; font-size: 14px; margin-bottom: 16px;">
                    Review cohort analytics, common misconceptions, knowledge gaps, and recommendation reports.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Mentor View →", key="btn_quick_mentor", use_container_width=True):
            st.session_state["nav_page"] = "Mentor Dashboard"
            st.rerun()

    with qcol3:
        st.markdown(
            """
            <div class="saas-card" style="min-height: 180px;">
                <h4 style="margin: 0 0 8px 0; color: #0B192C;">Assessment History</h4>
                <p style="color: #3B4D66; font-size: 14px; margin-bottom: 16px;">
                    Browse historical assessment runs, inspect answers, and review AI scoring evaluations.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Browse History →", key="btn_quick_history", use_container_width=True):
            st.session_state["nav_page"] = "Assessment History"
            st.rerun()

    st.write("")
    st.subheader("Recent Activity")

    if not assessments:
        st.info("No assessments found in the database. Click **Start New Assessment** to create one.")
    else:
        for item in assessments[:5]:
            aid = item.get("id")
            intern = item.get("intern_id", "Unknown")
            repo = item.get("repo_url", "").replace("https://github.com/", "")
            pr = item.get("pr_number", "")
            status = "Completed" if item.get("is_completed") else "In Progress"
            status_class = "status-completed" if item.get("is_completed") else "status-in-progress"
            score = f"{item.get('score_percentage')}%" if item.get("score_percentage") is not None else "Pending"

            with st.container():
                rcol1, rcol2, rcol3, rcol4, rcol5 = st.columns([1, 3, 2, 2, 2])
                with rcol1:
                    st.write(f"**#{aid}**")
                with rcol2:
                    st.write(f"Intern: `{intern}`")
                    st.caption(f"{repo} #{pr}")
                with rcol3:
                    st.markdown(f'<span class="status-pill {status_class}">{status}</span>', unsafe_allow_html=True)
                with rcol4:
                    st.write(f"Score: **{score}**")
                with rcol5:
                    if st.button("Inspect →", key=f"view_recent_{aid}", use_container_width=True):
                        st.session_state["current_assessment_id"] = aid
                        if item.get("is_completed"):
                            st.session_state["nav_page"] = "Assessment Results"
                        else:
                            st.session_state["nav_page"] = "Intern Q&A Interface"
                        st.rerun()
                st.divider()
