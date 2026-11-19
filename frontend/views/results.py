"""View 5: Assessment Results and Mentor Report"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import altair as alt
from typing import Any, Dict, List
from ..api_client import BackendClient


def render_results(client: BackendClient) -> None:
    st.title("Assessment Results & Report")
    st.markdown("Detailed breakdown of intern performance, rubric scoring, concept mastery, and mentor recommendations.")

    assessment_id = st.session_state.get("current_assessment_id")
    if not assessment_id:
        st.info("No active assessment selected. Please select an assessment from the **History** page.")
        return

    # Fetch report and assessment
    with st.spinner("Fetching assessment report..."):
        try:
            report_resp = client.get_report(int(assessment_id))
            report_data = report_resp.get("report", {})
            assessment = client.get_assessment(int(assessment_id))
        except Exception as exc:
            st.error(f"Failed to load report for assessment #{assessment_id}: {exc}")
            return

    total_score = report_data.get("total_score", 0)
    max_score = report_data.get("max_score", 0)
    percentage = report_data.get("percentage", 0.0)

    # Status badge
    if percentage >= 75:
        verdict_badge = '<span class="badge badge-easy" style="font-size: 14px;">Proficient / Pass</span>'
        banner_border = "#1B365D"
    elif percentage >= 50:
        verdict_badge = '<span class="badge badge-medium" style="font-size: 14px;">Needs Targeted Guidance</span>'
        banner_border = "#2C4A70"
    else:
        verdict_badge = '<span class="badge badge-hard" style="font-size: 14px;">Significant Knowledge Gaps</span>'
        banner_border = "#8C2424"

    # Score Overview Hero
    st.markdown(
        f"""
        <div class="saas-card" style="border-left: 6px solid {banner_border};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0; color: #0F1E36;">Assessment #{assessment_id} Summary</h2>
                    <p style="margin: 4px 0 0 0; color: #4A5E78;">
                        Intern: <code>{assessment.get('intern_id')}</code> • Repo: {assessment.get('repo_url')} #{assessment.get('pr_number')}
                    </p>
                </div>
                <div style="text-align: right;">
                    {verdict_badge}
                    <div style="font-size: 32px; font-weight: 800; color: #0F1E36; margin-top: 4px;">
                        {total_score} <span style="font-size: 18px; color: #4A5E78; font-weight: 500;">/ {max_score} pts ({percentage}%)</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Category Breakdown & Visualisation
    questions = assessment.get("questions", [])
    cat_data = []
    for q in questions:
        cat = q.get("category", "other").replace("_", " ").capitalize()
        eval_info = q.get("evaluation") or {}
        cat_data.append({
            "Category": cat,
            "Score": eval_info.get("score", 0),
            "Max Score": eval_info.get("max_score", 10),
        })

    col_chart, col_summary = st.columns([1, 1])

    with col_chart:
        st.subheader("Category Score Breakdown")
        if cat_data:
            df = pd.DataFrame(cat_data).groupby("Category").sum().reset_index()
            df["Percentage"] = (df["Score"] / df["Max Score"] * 100).round(1)

            chart = (
                alt.Chart(df)
                .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color="#1B365D")
                .encode(
                    x=alt.X("Percentage:Q", scale=alt.Scale(domain=[0, 100]), title="Proficiency (%)"),
                    y=alt.Y("Category:N", sort="-x", title=""),
                    tooltip=["Category", "Score", "Max Score", "Percentage"],
                )
                .properties(height=260)
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No category data available.")

    with col_summary:
        st.subheader("Key Insights")
        strengths = report_data.get("strengths", [])
        gaps = report_data.get("knowledge_gaps", [])
        misconceptions = report_data.get("misconceptions", [])

        st.markdown("**Demonstrated Strengths:**")
        if strengths:
            pills = "".join(f'<span class="pill-concept pill-correct">[Strength] {s}</span>' for s in strengths)
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.caption("No specific strengths identified.")

        st.write("")
        st.markdown("**Identified Knowledge Gaps:**")
        if gaps:
            pills = "".join(f'<span class="pill-concept pill-missing">[Gap] {g}</span>' for g in gaps)
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.caption("No major knowledge gaps detected.")

        if misconceptions:
            st.write("")
            st.markdown("**Misconceptions Detected:**")
            pills = "".join(f'<span class="pill-concept pill-misconception">[Misconception] {m}</span>' for m in misconceptions)
            st.markdown(pills, unsafe_allow_html=True)

    st.write("")
    st.subheader("Detailed Question Feedback & Evidence")

    for idx, q in enumerate(questions):
        q_eval = q.get("evaluation") or {}
        q_ans = q.get("answer") or {}
        score = q_eval.get("score", 0)
        max_s = q_eval.get("max_score", 10)
        feedback = q_eval.get("feedback", "No feedback recorded.")
        follow_up = q_eval.get("follow_up_question")
        ev_list = q.get("evidence", [])

        with st.expander(f"**Q{idx+1}: {q.get('text')}** - `{score}/{max_s} pts`", expanded=(idx == 0)):
            st.markdown(f"**Category:** `{q.get('category')}` | **Difficulty:** `{q.get('difficulty')}`")

            # Intern Answer
            st.markdown("**Intern's Answer:**")
            ans_text = q_ans.get("answer_text") or "_No answer submitted._"
            st.info(ans_text)

            # Evaluation & Rubric Feedback
            st.markdown("**Rubric Feedback:**")
            st.write(feedback)

            if follow_up:
                st.markdown("**Suggested Mentor Follow-up Question:**")
                st.warning(follow_up)

            if ev_list:
                st.markdown("**Code Evidence Reference:**")
                for ev in ev_list:
                    st.caption(f"- `{ev.get('filename')}` (lines {ev.get('start_line')}-{ev.get('end_line')})")
