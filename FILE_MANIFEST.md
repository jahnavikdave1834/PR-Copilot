# PR Understanding Copilot - File Manifest & Architecture

## System Architecture

```mermaid
flowchart TD
    subgraph Frontend [Streamlit Frontend (app.py)]
        F1[Home Dashboard]
        F2[New PR Assessment]
        F3[PR Details & Code Changes]
        F4[Intern Q&A Interface]
        F5[Assessment Results]
        F6[Mentor Dashboard]
        F7[Assessment History]
    end

    Frontend -->|HTTP REST Client: api_client.py| API

    subgraph Backend [FastAPI Backend (main.py)]
        API[API Routers]
        API --> B1[Health: /api/health]
        API --> B2[GitHub: /api/github/fetch-pr]
        API --> B3[Assessment: /api/assessment/*]
        API --> B4[Reports: /api/reports/*]

        B2 --> C[GitHub Service & Client]
        C --> C1[GitHub REST API]

        B3 --> D[Diff Analyzer: Python AST]
        B3 --> E[Question Service: Groq LLM]
        B3 --> F[Evaluation Service: Rubric Engine]
        B3 --> G[Report Service: Aggregator]
        B3 --> H[SQLite Persistence: database.py]
    end
```

---

## Complete Project Manifest

### Frontend (Streamlit)
- **`frontend/app.py`**: Streamlit application entry point featuring professional SaaS styling, session state management, active session tracking, and routing across all 7 views.
- **`frontend/api_client.py`**: Dedicated HTTP client using `httpx` for connecting to the FastAPI backend without making direct GitHub or LLM requests.
- **`frontend/styles.py`**: High-contrast Warm Beige and Deep Navy Blue SaaS design system, emoji-free typography, fully visible sidebar navigation, and accessible controls.
- **`frontend/views/home.py`**: View 1 — Home dashboard showing live backend health, high-level KPIs, quick action cards, and recent activity.
- **`frontend/views/new_assessment.py`**: View 2 — New PR assessment page with repo URL/PR number input, instant PR preview cards, and one-click AI assessment creation.
- **`frontend/views/pr_details.py`**: View 3 — PR inspection view showing file diffs with unified patches, commit histories, and review comments.
- **`frontend/views/intern_qa.py`**: View 4 — Intern technical interrogation interface with progress tracking, category/difficulty badges, referenced code evidence, and draft persistence.
- **`frontend/views/results.py`**: View 5 — Assessment results page with overall score banners, Altair category proficiency bar charts, strengths, gaps, and question-by-question rubric feedback.
- **`frontend/views/mentor_dashboard.py`**: View 6 — Mentor oversight dashboard showing cohort pass rates, intern filtering, misconception detection, and JSON exports.
- **`frontend/views/history.py`**: View 7 — Searchable and filterable archive of all historical assessments with one-click resumption and report inspection.

### Backend Application Entry & Configuration
- **`backend/main.py`**: FastAPI application entry point with CORS middleware, lifespan events, and router registrations.
- **`backend/config/settings.py`**: Pydantic BaseSettings configuration management loading environment variables from `.env`.
- **`backend/logger/logger.py`**: Loguru structured logging configuration with console and file sinks.
- **`backend/db/database.py`**: SQLAlchemy SQLite database models (`Intern`, `Assessment`, `QuestionRecord`, `AnswerRecord`, `EvaluationRecord`, `ReportRecord`).

### Schemas (Pydantic Models)
- **`backend/schemas/github.py`**: Structured representations for repository info, PR metadata, file changes with patches, commits, and review comments.
- **`backend/schemas/diff.py`**: AST-based code analysis models (`FileDiffContext`, `PRContext`, language detection).
- **`backend/schemas/question.py`**: Question generation schema with categories, difficulties, evidence references, and expected concepts.
- **`backend/schemas/evaluation.py`**: Answer evaluation schema with score, rubric criteria, feedback, correct concepts, missing concepts, misconceptions, and follow-ups.

### Core Modules & Services
- **`backend/core/github_client.py`**: Async HTTP client for GitHub REST API using `httpx` with pagination, rate-limit back-off handling, and error mapping.
- **`backend/core/diff_analyzer.py`**: Diff parsing and Python AST analysis for added/modified functions, classes, and edge-case keyword detection.
- **`backend/core/llm_client.py`**: Async Groq client for LLM chat completions (`mixtral-8x7b-32768`).
- **`backend/services/github_service.py`**: Service layer encapsulating PR validation, normalization, and fetch workflows.
- **`backend/services/question_service.py`**: AI question generation service querying Groq LLM with robust JSON array extraction and Pydantic validation.
- **`backend/services/evaluation_service.py`**: Intern answer scoring engine evaluating concepts, deductions for omissions, and misconception penalties.
- **`backend/services/report_service.py`**: Report generator compiling total scores, category breakdown, strengths, knowledge gaps, and mentor recommendations.

### API Routes
- **`backend/api/health.py`**: `GET /api/health` - Service heartbeat check.
- **`backend/api/github.py`**: `POST /api/github/fetch-pr` - Fetches PR details, commits, files, and comments.
- **`backend/api/assessment.py`**:
  - `POST /api/assessment/generate` - Runs diff analysis and question generation, stores assessment session.
  - `POST /api/assessment/submit` - Evaluates submitted intern answers and compiles mentor report.
  - `GET /api/assessment/{assessment_id}` - Retrieves assessment session with questions and submitted evaluations.
  - `GET /api/assessments` - Lists all assessments with completion and score summaries.
- **`backend/api/reports.py`**: `GET /api/reports/{assessment_id}` - Retrieves or generates finalized mentor report.

### Test Suite (`tests/`)
- **`tests/test_diff_analyzer.py`**: Patch parsing, AST entity extraction, and edge-case detection.
- **`tests/test_github_integration.py`**: URL normalization, mocked GitHub client integration, and health endpoint.
- **`tests/test_github_service.py`**: Service-level error propagation and normalization.
- **`tests/test_question_service.py`**: Question schema validation, LLM response parsing, and error handling.
- **`tests/test_evaluation_service.py`**: Scoring rubric, concept matching, and misconception detection.
- **`tests/test_persistence_and_reports.py`**: Database ORM relationships and report generation logic.
- **`tests/test_api_endpoints.py`**: FastAPI integration tests across all lifecycle endpoints.
- **`tests/test_frontend.py`**: Unit tests for frontend API client communication with FastAPI and automated Streamlit `AppTest` regression tests across all 7 views.
