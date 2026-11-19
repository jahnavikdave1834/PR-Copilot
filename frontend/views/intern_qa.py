"""View 4: Intern Question and Answer Interface"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List
from ..api_client import BackendClient


def render_intern_qa(client: BackendClient) -> None:
    st.title("Intern Technical Assessment")
    st.markdown("Answer each technical question regarding the design, logic, and edge-cases introduced in this PR.")

    assessment_id = st.session_state.get("current_assessment_id")
    if not assessment_id:
        st.warning("No assessment session active. Please create one on the **New PR Assessment** page or select one from **History**.")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Go to New Assessment"):
                st.session_state["nav_page"] = "New PR Assessment"
                st.rerun()
        return

    # Load assessment details from backend
    with st.spinner("Loading assessment questions..."):
        try:
            assessment = client.get_assessment(assessment_id)
        except Exception as exc:
            st.error(f"Failed to load assessment #{assessment_id}: {exc}")
            return

    questions: List[Dict[str, Any]] = assessment.get("questions", [])
    if not questions:
        st.info("No questions found for this assessment.")
        return

    # Initialize draft answers in session state
    if "answers_draft" not in st.session_state:
        st.session_state["answers_draft"] = {}

    # Pre-populate draft from any existing submitted answers
    for q in questions:
        qid_str = str(q["id"])
        if qid_str not in st.session_state["answers_draft"]:
            if q.get("answer") and q["answer"].get("answer_text"):
                st.session_state["answers_draft"][qid_str] = q["answer"]["answer_text"]
            else:
                st.session_state["answers_draft"][qid_str] = ""

    # Progress bar
    answered_count = sum(1 for q in questions if st.session_state["answers_draft"].get(str(q["id"]), "").strip())
    total_q = len(questions)
    progress_val = answered_count / total_q if total_q > 0 else 0.0

    st.markdown(
        f"""
        <div style="background: #FDFAF4; border: 1px solid #D8CEBD; border-left: 4px solid #1B365D; border-radius: 10px; padding: 14px 20px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 700; color: #0F1E36;">Progress: {answered_count} of {total_q} questions answered</span>
                <span style="font-size: 13px; color: #4A5E78;">Assessment #{assessment_id} • Intern: <code>{assessment.get('intern_id')}</code></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(progress_val)

    st.write("")

    # Question Tabs or List
    q_titles = [f"Q{i+1}: {q.get('category', 'general').capitalize()}" for i, q in enumerate(questions)]
    selected_tab = st.radio("Select Question:", q_titles, horizontal=True)
    selected_idx = q_titles.index(selected_tab)
    q = questions[selected_idx]
    qid_str = str(q["id"])

    category = q.get("category", "comprehension")
    difficulty = q.get("difficulty", "medium")
    evidence = q.get("evidence", [])

    st.markdown('<div class="saas-card">', unsafe_allow_html=True)
    
    # Badges
    st.markdown(
        f"""
        <div style="margin-bottom: 12px;">
            <span class="badge badge-{category}">{category.replace('_', ' ')}</span>
            <span class="badge badge-{difficulty}">{difficulty}</span>
            <span style="font-size: 13px; color: #3B4D66; margin-left: 8px;">Question ID #{qid_str}</span>
        </div>
        <h3 style="color: #0B192C; margin-top: 0; line-height: 1.4;">{q.get('text')}</h3>
        """,
        unsafe_allow_html=True,
    )

    # Evidence references
    if evidence:
        with st.expander("Referenced Code Evidence (Diff Context)", expanded=True):
            for ev in evidence:
                fname = ev.get("filename", "")
                sl = ev.get("start_line")
                el = ev.get("end_line")
                line_info = f"lines {sl}-{el}" if sl and el else "full file"
                st.markdown(f"- File: `{fname}` ({line_info})")

    st.write("")
    st.markdown("#### Your Technical Explanation:")

    draft_key = f"text_area_q_{qid_str}"
    if draft_key not in st.session_state:
        st.session_state[draft_key] = st.session_state["answers_draft"].get(qid_str, "")

    answer_val = st.text_area(
        label="Answer",
        label_visibility="collapsed",
        placeholder="Explain your technical rationale, decisions, edge-cases considered, and relevant implementation details...",
        height=180,
        key=draft_key,
    )
    st.session_state["answers_draft"][qid_str] = answer_val

    st.markdown('</div>', unsafe_allow_html=True)

    # Bottom Actions: Prev / Next / Submit
    bcol1, bcol2, bcol3 = st.columns([1, 1, 2])
    with bcol1:
        if selected_idx > 0:
            if st.button("← Previous Question"):
                pass
    with bcol2:
        if selected_idx < total_q - 1:
            if st.button("Next Question →"):
                pass
    with bcol3:
        if st.button("Submit Assessment for Mentor Evaluation", type="primary", use_container_width=True):
            unanswered = [i + 1 for i, q in enumerate(questions) if not st.session_state["answers_draft"].get(str(q["id"]), "").strip()]
            if unanswered:
                st.warning(f"Note: Questions {unanswered} are currently blank. Submitting now will evaluate incomplete answers.")
            
            with st.spinner("Submitting answers and computing automated rubric evaluation..."):
                try:
                    payload_answers = {
                        str(q["id"]): st.session_state["answers_draft"].get(str(q["id"]), "")
                        for q in questions
                    }
                    res = client.submit_assessment(int(assessment_id), payload_answers)
                    st.session_state["report_data"] = res.get("report")
                    st.success("Assessment submitted successfully! Navigating to results...")
                    st.session_state["nav_page"] = "Assessment Results"
                    st.rerun()
                except Exception as exc:
                    st.error(f"Submission failed: {exc}")
