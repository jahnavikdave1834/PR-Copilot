"""View 3: PR Details and Code Changes"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List
from ..api_client import BackendClient


def render_pr_details(client: BackendClient) -> None:
    st.title("PR Details & Code Changes")
    st.markdown("Inspect file diffs, unified patches, commit logs, and review comments.")

    pr_data = st.session_state.get("current_pr")

    # If no PR is in session state, allow fetching directly
    if not pr_data:
        st.info("No active PR loaded in session. You can load one below:")
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            repo_input = st.text_input("Repository HTTPS URL", value="https://github.com/fastapi/fastapi")
        with col2:
            pr_num_input = st.number_input("PR #", value=1, min_value=1)
        with col3:
            st.write("")
            st.write("")
            if st.button("Fetch PR"):
                with st.spinner("Fetching..."):
                    try:
                        pr_data = client.fetch_pr(repo_input, int(pr_num_input))
                        st.session_state["current_pr"] = pr_data
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                        return
        if not pr_data:
            return

    repo_info = pr_data.get("repository", {})
    pr_info = pr_data.get("pull_request", {})
    files: List[Dict[str, Any]] = pr_data.get("files", [])
    commits: List[Dict[str, Any]] = pr_data.get("commits", [])
    reviews: List[Dict[str, Any]] = pr_data.get("reviews", [])

    # PR Overview Header
    st.markdown(
        f"""
        <div class="saas-card">
            <div class="saas-card-header">
                <div>
                    <h3 style="margin: 0; color: #0B192C;">{pr_info.get('title')}</h3>
                    <p style="margin: 4px 0 0 0; color: #3B4D66; font-size: 13px;">
                        {repo_info.get('owner')}/{repo_info.get('name')} • PR #{pr_info.get('number')} by <strong>@{pr_info.get('author')}</strong>
                    </p>
                </div>
                <div>
                    <span class="status-pill status-completed">{pr_info.get('state', '').upper()}</span>
                </div>
            </div>
            <div style="color: #0B192C; font-size: 14px; line-height: 1.6;">
                {pr_info.get('body') or '<em>No description provided in PR body.</em>'}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_files, tab_commits, tab_reviews = st.tabs([
        f"Changed Files ({len(files)})",
        f"Commits ({len(commits)})",
        f"Review Comments ({len(reviews)})",
    ])

    with tab_files:
        if not files:
            st.info("No file changes recorded for this PR.")
        else:
            for idx, f in enumerate(files):
                fname = f.get("filename", "")
                status = f.get("status", "modified")
                adds = f.get("additions", 0)
                dels = f.get("deletions", 0)
                patch = f.get("patch", "")

                with st.expander(f"**{fname}**  (`+{adds}` / `-{dels}`) - *{status}*", expanded=(idx == 0)):
                    if patch:
                        st.code(patch, language="diff")
                    else:
                        st.caption("No patch available (binary file or change omitted).")

    with tab_commits:
        if not commits:
            st.info("No commit records found.")
        else:
            for c in commits:
                sha = c.get("sha", "")[:7]
                author = c.get("author_name") or "Unknown"
                msg = c.get("message", "").strip().split("\n")[0]
                date = c.get("date", "")
                st.markdown(
                    f"""
                    <div style="padding: 10px 14px; border-bottom: 1px solid #DDD6C8; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <code>{sha}</code> <strong>{msg}</strong>
                            <div style="font-size: 12px; color: #3B4D66; margin-top: 2px;">{author} • {date}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_reviews:
        if not reviews:
            st.info("No review comments attached to this PR.")
        else:
            for r in reviews:
                user = r.get("user", "reviewer")
                body = r.get("body", "")
                path = r.get("path")
                created = r.get("created_at", "")
                with st.container():
                    st.markdown(f"**@{user}** on `{path or 'General'}` *({created})*:")
                    st.markdown(f"> {body}")
                    st.divider()
