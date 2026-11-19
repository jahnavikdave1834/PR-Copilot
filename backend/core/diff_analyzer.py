from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from ..schemas.github import PullRequestFullResponse, FileChange
from ..schemas.diff import FileDiffContext, PRContext, detect_language

# Keywords that often indicate edge‑case handling or potential bugs
EDGE_KEYWORDS = {
    "try",
    "except",
    "finally",
    "raise",
    "assert",
    "with",
    "open",
    "close",
    "cleanup",
    "validate",
    "error",
    "exception",
    "resource",
    "timeout",
    "null",
    "None",
    "undef",
}

class _PythonASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions: Set[str] = set()
        self.classes: Set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes.add(node.name)
        self.generic_visit(node)

def _extract_python_entities(source: str) -> Tuple[Set[str], Set[str]]:
    """Parse a Python source fragment and return (functions, classes).
    If parsing fails (e.g., incomplete snippet) we fall back to an empty set.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set(), set()
    visitor = _PythonASTVisitor()
    visitor.visit(tree)
    return visitor.functions, visitor.classes

def _lines_from_patch(patch: str | None) -> Tuple[List[str], List[str]]:
    """Return two lists: added lines (without leading '+') and removed lines (without '-')
    from a unified diff patch. Header lines (---, +++, @@) are ignored.
    """
    added: List[str] = []
    removed: List[str] = []
    if not patch:
        return added, removed
    for line in patch.splitlines():
        if line.startswith("@@") or line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("+") and not line.startswith("++"):
            added.append(line[1:])
        elif line.startswith("-") and not line.startswith("--"):
            removed.append(line[1:])
    return added, removed

def analyze_pr(pr: PullRequestFullResponse) -> PRContext:
    """Analyze a fully‑fetched PR and produce a structured diff context.
    The function is deliberately lightweight – it only uses the Python ``ast``
    module for Python files. For other languages we leave the function/class lists
    empty and rely on language detection.
    """
    file_contexts: List[FileDiffContext] = []
    total_added = 0
    total_removed = 0
    concept_set: Set[str] = set()
    edge_cases: Set[str] = set()

    for f in pr.files:
        # Basic stats from the API
        added = f.additions
        removed = f.deletions
        total_added += added
        total_removed += removed

        language = detect_language(f.filename)
        added_funcs: List[str] = []
        removed_funcs: List[str] = []
        added_classes: List[str] = []
        removed_classes: List[str] = []

        if language == "python":
            added_lines, removed_lines = _lines_from_patch(f.patch)
            # Join lines to form snippets for AST parsing
            added_src = "\n".join(added_lines)
            removed_src = "\n".join(removed_lines)
            add_funcs, add_classes = _extract_python_entities(added_src)
            rem_funcs, rem_classes = _extract_python_entities(removed_src)
            added_funcs = sorted(add_funcs)
            removed_funcs = sorted(rem_funcs)
            added_classes = sorted(add_classes)
            removed_classes = sorted(rem_classes)
            # Collect concepts (function/class names) for heuristics
            concept_set.update(added_funcs)
            concept_set.update(removed_funcs)
            concept_set.update(added_classes)
            concept_set.update(removed_classes)
            # Edge‑case detection – simple keyword scan in added/removed source
            for snippet in (added_src, removed_src):
                for kw in EDGE_KEYWORDS:
                    if re.search(r"\b" + re.escape(kw) + r"\b", snippet, flags=re.IGNORECASE):
                        edge_cases.add(kw)
        # Build per‑file context
        file_ctx = FileDiffContext(
            filename=f.filename,
            language=language,
            added_lines=added,
            removed_lines=removed,
            added_functions=added_funcs,
            removed_functions=removed_funcs,
            added_classes=added_classes,
            removed_classes=removed_classes,
        )
        file_contexts.append(file_ctx)

    pr_context = PRContext(
        total_files=len(pr.files),
        total_added=total_added,
        total_removed=total_removed,
        files=file_contexts,
        important_concepts=sorted(concept_set),
        potential_edge_cases=sorted(edge_cases),
    )
    return pr_context
