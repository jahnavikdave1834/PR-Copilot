"""View 7: Assessment History"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List
from ..api_client import BackendClient


def render_history(client: BackendClient) -> None:
    st.title("Assessment History & Archives")
    st.markdown("Search, inspect, and resume historical assessment sessions.")

    with st.spinner("Loading history logs..."):
        try:
            assessments = client.list_assessments()
        except Exception as exc:
            st.error(f"Failed to fetch assessment history: {exc}")
            return

    if not assessments:
        st.info("No past assessments found. Create your first assessment from the **New PR Assessment** tab.")
        return

    # Search & Filter Bar
    scol1, scol2 = st.columns([3, 1])
    with scol1:
        query = st.text_input("Search by Intern ID or Repository URL...", placeholder="e.g. intern_alex or fastapi")
    with scol2:
        sort_order = st.selectbox("Sort Order:", ["Newest First", "Oldest First", "Highest Score"])

    filtered = assessments
    if query:
        q_lower = query.lower()
        filtered = [
            a for a in filtered
            if q_lower in str(a.get("intern_id", "")).lower() or q_lower in str(a.get("repo_url", "")).lower()
        ]

    # Sorting
    if sort_order == "Newest First":
        filtered = sorted(filtered, key=lambda x: str(x.get("created_at")), reverse=True)
    elif sort_order == "Oldest First":
        filtered = sorted(filtered, key=lambda x: str(x.get("created_at")))
    elif sort_order == "Highest Score":
        filtered = sorted(filtered, key=lambda x: (x.get("score_percentage") or 0.0), reverse=True)

    st.write(f"Showing **{len(filtered)}** of **{len(assessments)}** assessments")

    if not filtered:
        st.warning(f"No assessments match search '{query}'.")
        return

    for item in filtered:
        aid = item.get("id")
        intern = item.get("intern_id", "Unknown")
        repo = item.get("repo_url", "").replace("https://github.com/", "")
        pr = item.get("pr_number", "")
        created = item.get("created_at", "")[:19].replace("T", " ")
        q_count = item.get("question_count", 0)
        sub_count = item.get("submitted_count", 0)
        is_comp = item.get("is_completed")

        status_text = "Completed" if is_comp else f"In Progress ({sub_count}/{q_count})"
        status_class = "status-completed" if is_comp else "status-in-progress"
        score_display = f"{item.get('score_percentage')}%" if item.get("score_percentage") is not None else "-"

        with st.container():
            c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
            with c1:
                st.write(f"**#{aid}**")
            with c2:
                st.write(f"Intern: `{intern}`")
                st.caption(f"{repo} #{pr}")
            with c3:
                st.markdown(f'<span class="status-pill {status_class}">{status_text}</span>', unsafe_allow_html=True)
                st.caption(created)
            with c4:
                st.write(f"Score: **{score_display}**")
            with c5:
                if is_comp:
                    if st.button("View Report", key=f"hist_rep_{aid}", use_container_width=True):
                        st.session_state["current_assessment_id"] = aid
                        st.session_state["nav_page"] = "Assessment Results"
                        st.rerun()
                else:
                    if st.button("Resume Assessment", key=f"hist_resume_{aid}", use_container_width=True):
                        st.session_state["current_assessment_id"] = aid
                        st.session_state["nav_page"] = "Intern Q&A Interface"
                        st.rerun()
            st.divider()
