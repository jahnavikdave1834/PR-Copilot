"""View 2: New PR Assessment"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict
from ..api_client import BackendClient


def render_new_assessment(client: BackendClient) -> None:
    st.title("Start New PR Assessment")
    st.markdown(
        "Connect a GitHub repository pull request to run AST diff analysis and generate targeted technical evaluation questions."
    )

    # Initialize widget defaults in session_state to avoid Streamlit value conflict warnings
    st.session_state.setdefault(
        "input_repo_url",
        "https://github.com/jahnavikdave1834/Knowledge-Graphs-on-Multilingual-Fake-News-Detection",
    )
    st.session_state.setdefault("input_pr_number", 1)
    st.session_state.setdefault("input_intern_id", "jahnavikdave1834@gmail.com")

    with st.container():
        st.markdown('<div class="saas-card">', unsafe_allow_html=True)
        st.subheader("1. Assessment Target Configuration")

        # Quick sample fill
        col_btn1, col_btn2, col_btn3 = st.columns([1.8, 1.4, 1.4])
        with col_btn1:
            if st.button("Use Knowledge-Graphs (PR #1)", help="Target repository: Knowledge-Graphs", type="primary"):
                st.session_state["input_repo_url"] = "https://github.com/jahnavikdave1834/Knowledge-Graphs-on-Multilingual-Fake-News-Detection"
                st.session_state["input_pr_number"] = 1
                st.session_state["input_intern_id"] = "jahnavikdave1834@gmail.com"
                st.rerun()
        with col_btn2:
            if st.button("Use PR-Copilot (PR #1)", help="Target repository: PR-Copilot"):
                st.session_state["input_repo_url"] = "https://github.com/jahnavikdave1834/PR-Copilot"
                st.session_state["input_pr_number"] = 1
                st.session_state["input_intern_id"] = "jahnavikdave1834@gmail.com"
                st.rerun()
        with col_btn3:
            if st.button("Use Sample PR (FastAPI)", help="Fill with sample open-source PR"):
                st.session_state["input_repo_url"] = "https://github.com/fastapi/fastapi"
                st.session_state["input_pr_number"] = 1
                st.session_state["input_intern_id"] = "intern_alex@company.com"
                st.rerun()

        repo_url = st.text_input(
            "GitHub Repository HTTPS URL",
            placeholder="https://github.com/owner/repository",
            key="input_repo_url",
        )

        col_pr, col_intern = st.columns(2)
        with col_pr:
            pr_number = st.number_input(
                "Pull Request Number",
                min_value=1,
                step=1,
                key="input_pr_number",
            )
        with col_intern:
            intern_id = st.text_input(
                "Intern Identifier (Email or Handle)",
                placeholder="e.g. dev_jane@example.com",
                key="input_intern_id",
            )

        st.write("")
        # Action button to preview PR
        btn_preview = st.button("Fetch PR Preview", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Handle Fetch PR Preview
    if btn_preview:
        if not repo_url or not intern_id:
            st.error("Please provide both a repository URL and an Intern Identifier.")
        else:
            with st.spinner("Connecting to GitHub REST API and retrieving PR metadata..."):
                try:
                    pr_data = client.fetch_pr(repo_url, int(pr_number))
                    st.session_state["current_pr"] = pr_data
                    st.session_state["preview_fetched"] = True
                    st.success("Successfully fetched PR metadata from GitHub!")
                except Exception as exc:
                    st.error(f"Failed to fetch PR: {exc}")
                    st.session_state["preview_fetched"] = False

    # Display PR Preview Card if available
    pr_data = st.session_state.get("current_pr")
    if pr_data:
        st.write("")
        st.markdown('<div class="saas-card">', unsafe_allow_html=True)
        st.subheader("2. Pull Request Preview")

        repo_info = pr_data.get("repository", {})
        pr_info = pr_data.get("pull_request", {})
        files = pr_data.get("files", [])
        commits = pr_data.get("commits", [])

        st.markdown(f"### **{pr_info.get('title', 'Untitled PR')}**")
        st.caption(f"Authored by **@{pr_info.get('author', 'unknown')}** • State: `{pr_info.get('state', 'unknown')}`")

        # Metric badges
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            st.metric("Repository", f"{repo_info.get('owner')}/{repo_info.get('name')}")
        with mcol2:
            st.metric("Changed Files", len(files))
        with mcol3:
            additions = sum(f.get("additions", 0) for f in files)
            st.metric("Additions", f"+{additions}")
        with mcol4:
            deletions = sum(f.get("deletions", 0) for f in files)
            st.metric("Deletions", f"-{deletions}")

        if pr_info.get("body"):
            with st.expander("PR Description", expanded=False):
                st.markdown(pr_info.get("body"))

        st.write("")
        st.markdown("#### Ready to Generate AI Assessment")
        st.markdown(
            "This will parse code diffs with AST analysis, extract functions and edge-case patterns, and query the Groq LLM to build 5-8 targeted questions."
        )

        col_gen, col_view = st.columns([2, 1])
        with col_gen:
            if st.button("Generate Assessment & Technical Questions", type="primary", use_container_width=True):
                with st.spinner("Analyzing diff AST and generating grounded questions via Groq LLM..."):
                    try:
                        res = client.generate_assessment(repo_url, int(pr_number), intern_id)
                        st.session_state["current_assessment_id"] = res["assessment_id"]
                        st.session_state["assessment_data"] = res
                        st.session_state["answers_draft"] = {}
                        st.success(f"Assessment #{res['assessment_id']} created with {len(res.get('questions', []))} questions!")
                        st.session_state["nav_page"] = "Intern Q&A Interface"
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Assessment generation failed: {exc}")

        with col_view:
            if st.button("Inspect Diffs & Code Changes →", use_container_width=True):
                st.session_state["nav_page"] = "PR Details & Changes"
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
