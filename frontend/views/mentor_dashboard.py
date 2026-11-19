"""View 6: Mentor Dashboard"""

from __future__ import annotations

import json
import streamlit as st
import pandas as pd
import altair as alt
from typing import Any, Dict, List
from ..api_client import BackendClient


def render_mentor_dashboard(client: BackendClient) -> None:
    st.title("Mentor Oversight Dashboard")
    st.markdown("Cohort-level performance insights, common misconceptions, and intern assessment tracking.")

    # Load all assessments
    with st.spinner("Aggregating cohort performance data..."):
        try:
            assessments = client.list_assessments()
        except Exception as exc:
            st.error(f"Failed to load assessments: {exc}")
            return

    if not assessments:
        st.info("No assessments found in the database. When interns complete assessments, their results will appear here.")
        return

    # Top Metrics
    total = len(assessments)
    completed = [a for a in assessments if a.get("is_completed")]
    completed_count = len(completed)
    scores = [a.get("score_percentage") for a in completed if a.get("score_percentage") is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    pass_count = sum(1 for s in scores if s >= 70.0)
    pass_rate = round((pass_count / len(scores)) * 100, 1) if scores else 0.0

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value">{total}</div>
                <div class="metric-label">Total Assigned</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with mcol2:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value">{completed_count}</div>
                <div class="metric-label">Completed Assessments</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with mcol3:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value" style="color: #EA580C;">{avg_score}%</div>
                <div class="metric-label">Cohort Avg Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with mcol4:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value" style="color: #0B192C;">{pass_rate}%</div>
                <div class="metric-label">Pass Rate (>=70%)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    st.write("")

    # Filters
    st.subheader("Filter & Inspect Assessments")
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        intern_filter = st.selectbox(
            "Filter by Intern:",
            options=["All Interns"] + sorted(list({a.get("intern_id") for a in assessments if a.get("intern_id")})),
        )
    with fcol2:
        status_filter = st.selectbox(
            "Filter by Status:",
            options=["All Statuses", "Completed", "In Progress"],
        )

    filtered = assessments
    if intern_filter != "All Interns":
        filtered = [a for a in filtered if a.get("intern_id") == intern_filter]
    if status_filter == "Completed":
        filtered = [a for a in filtered if a.get("is_completed")]
    elif status_filter == "In Progress":
        filtered = [a for a in filtered if not a.get("is_completed")]

    # Table of assessments
    st.write("")
    for item in filtered:
        aid = item.get("id")
        intern = item.get("intern_id", "Unknown")
        repo = item.get("repo_url", "").replace("https://github.com/", "")
        pr = item.get("pr_number", "")
        is_comp = item.get("is_completed")
        status_label = "Completed" if is_comp else "In Progress"
        status_class = "status-completed" if is_comp else "status-in-progress"
        score_val = f"{item.get('score_percentage')}%" if item.get("score_percentage") is not None else "Pending"

        with st.container():
            c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
            with c1:
                st.write(f"**#{aid}**")
            with c2:
                st.write(f"**{intern}**")
                st.caption(f"`{repo} #{pr}` • {item.get('created_at', '')[:10]}")
            with c3:
                st.markdown(f'<span class="status-pill {status_class}">{status_label}</span>', unsafe_allow_html=True)
            with c4:
                st.write(f"Score: **{score_val}**")
            with c5:
                if st.button("Review Report →", key=f"btn_mentor_review_{aid}", use_container_width=True):
                    st.session_state["current_assessment_id"] = aid
                    st.session_state["nav_page"] = "Assessment Results"
                    st.rerun()
            st.divider()

    # Cohort Export
    st.write("")
    st.download_button(
        label="Export Cohort Assessments (JSON)",
        data=json.dumps(assessments, indent=2),
        file_name="cohort_assessments.json",
        mime="application/json",
    )
