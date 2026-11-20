"""Custom styling for the Streamlit PR Understanding Copilot UI.
Design Language: Elegant Warm Beige & Deep Navy Blue SaaS Theme.
Strictly emoji-free, high-contrast, fully visible sidebar and accessible controls.
"""

CSS_THEME = """
<style>
    /* Global Typography & Font Styling */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #F7F4EE !important;
        color: #0F1E36 !important;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #0F1E36 !important;
        font-weight: 700 !important;
    }
    
    p, span, label, div {
        color: #0F1E36;
    }

    /* Top App Header & Container */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px !important;
    }

    /* ========================================================
       SIDEBAR & NAVIGATION STYLING (HIGH-CONTRAST BEIGE & NAVY)
       ======================================================== */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {
        background-color: #EAE4D8 !important;
        border-right: 1px solid #D8CEBD !important;
    }

    /* Force all base text in sidebar to deep navy */
    section[data-testid="stSidebar"] *,
    [data-testid="stSidebarContent"] *,
    [data-testid="stSidebarUserContent"] * {
        color: #0F1E36 !important;
    }

    /* Sidebar Radio Navigation Container */
    section[data-testid="stSidebar"] div[data-testid="stRadio"],
    [data-testid="stSidebarContent"] div[data-testid="stRadio"] {
        background-color: transparent !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"],
    [data-testid="stSidebarContent"] div[data-testid="stRadio"] > div[role="radiogroup"] {
        gap: 6px !important;
    }

    /* Radio item container - Crisp Beige card */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label,
    [data-testid="stSidebarContent"] div[data-testid="stRadio"] label {
        background-color: #F4EFE6 !important;
        border: 1px solid #D8CEBD !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        margin-bottom: 4px !important;
        cursor: pointer !important;
        transition: all 0.15s ease-in-out !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Radio item text: Must be 100% visible deep navy */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label p,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label span,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label div,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebarContent"] div[data-testid="stRadio"] label p,
    [data-testid="stSidebarContent"] div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
        color: #0F1E36 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        line-height: 1.4 !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* Hover state */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover,
    [data-testid="stSidebarContent"] div[data-testid="stRadio"] label:hover {
        background-color: #DFD5C6 !important;
        border-color: #1B365D !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover p,
    [data-testid="stSidebarContent"] div[data-testid="stRadio"] label:hover p {
        color: #1B365D !important;
    }

    /* Active / Checked radio item: Solid Navy Blue card with Beige/White text */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked),
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-checked="true"],
    [data-testid="stSidebarContent"] div[data-testid="stRadio"] label:has(input:checked),
    [data-testid="stSidebarContent"] div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: #0F1E36 !important;
        border-color: #0F1E36 !important;
        box-shadow: 0 2px 4px rgba(15, 30, 54, 0.2) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) p,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) span,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) div,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-checked="true"] p,
    [data-testid="stSidebarContent"] div[data-testid="stRadio"] label:has(input:checked) p,
    [data-testid="stSidebarContent"] div[data-testid="stRadio"] label:has(input:checked) [data-testid="stMarkdownContainer"] p {
        color: #FDFAF4 !important;
        font-weight: 700 !important;
    }

    /* Radio circle accent */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] input[type="radio"]:checked + div {
        background-color: #1B365D !important;
        border-color: #1B365D !important;
    }

    /* Sidebar Expander */
    section[data-testid="stSidebar"] [data-testid="stExpander"],
    [data-testid="stSidebarContent"] [data-testid="stExpander"] {
        background-color: #F4EFE6 !important;
        border: 1px solid #D8CEBD !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary,
    [data-testid="stSidebarContent"] [data-testid="stExpander"] summary {
        color: #0F1E36 !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover,
    [data-testid="stSidebarContent"] [data-testid="stExpander"] summary:hover {
        color: #1B365D !important;
    }

    /* ========================================================
       CARDS & HERO BANNER (BEIGE & NAVY BLUE PALETTE)
       ======================================================== */
    .saas-card {
        background-color: #FDFAF4;
        border: 1px solid #D8CEBD;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 1px 4px rgba(15, 30, 54, 0.05);
        transition: all 0.2s ease-in-out;
    }
    .saas-card:hover {
        border-color: #1B365D;
        box-shadow: 0 4px 12px rgba(27, 54, 93, 0.08);
    }
    
    .saas-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
        border-bottom: 1px solid #EAE4D8;
        padding-bottom: 12px;
    }

    /* Hero Banner: Deep Navy Background, Warm Beige Text */
    .hero-banner {
        background: linear-gradient(135deg, #0F1E36 0%, #1B365D 100%);
        color: #FDFAF4;
        border-radius: 12px;
        padding: 28px 32px;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(15, 30, 54, 0.15);
        border: 1px solid #2C4A70;
    }
    .hero-title {
        font-size: 26px;
        font-weight: 800;
        margin-bottom: 8px;
        color: #FDFAF4 !important;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 14px;
        color: #D8CEBD !important;
        line-height: 1.5;
    }
    .hero-pill {
        background: rgba(253, 250, 244, 0.12);
        border: 1px solid rgba(216, 206, 189, 0.3);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        color: #FDFAF4 !important;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* Metric Boxes */
    .metric-box {
        background: #F0EAE0;
        border: 1px solid #DCD2C2;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(15, 30, 54, 0.03);
    }
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        color: #0F1E36;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 12px;
        font-weight: 600;
        color: #4A5E78;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }

    /* ========================================================
       BUTTONS & CONTROLS (NAVY PRIMARY, BEIGE SECONDARY)
       ======================================================== */
    /* Primary buttons */
    button[data-testid="baseButton-primary"],
    .stButton > button[kind="primary"] {
        background-color: #EA580C !important;
        border: 1px solid #C2410C !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 6px rgba(234, 88, 12, 0.3) !important;
        transition: all 0.15s ease-in-out !important;
    }
    button[data-testid="baseButton-primary"] *,
    .stButton > button[kind="primary"] *,
    button[data-testid="baseButton-primary"] p,
    .stButton > button[kind="primary"] p,
    button[data-testid="baseButton-primary"] div,
    .stButton > button[kind="primary"] div,
    button[data-testid="baseButton-primary"] span,
    .stButton > button[kind="primary"] span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 15px !important;
    }
    button[data-testid="baseButton-primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        background-color: #C2410C !important;
        border-color: #9A3412 !important;
        box-shadow: 0 4px 12px rgba(234, 88, 12, 0.45) !important;
    }
    button[data-testid="baseButton-primary"]:hover *,
    .stButton > button[kind="primary"]:hover * {
        color: #FFFFFF !important;
    }

    /* Secondary / standard buttons */
    button[data-testid="baseButton-secondary"],
    .stButton > button {
        background-color: #F4EFE6 !important;
        color: #0F1E36 !important;
        border: 1px solid #D8CEBD !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.15s ease-in-out !important;
    }
    button[data-testid="baseButton-secondary"]:hover,
    .stButton > button:hover {
        background-color: #EAE4D8 !important;
        border-color: #1B365D !important;
        color: #1B365D !important;
    }

    /* Form Inputs & Select Boxes */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background-color: #FDFAF4 !important;
        color: #0F1E36 !important;
        border: 1px solid #D8CEBD !important;
        border-radius: 8px !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #1B365D !important;
        box-shadow: 0 0 0 1px #1B365D !important;
    }

    /* Progress Bar */
    .stProgress > div > div > div > div {
        background-color: #1B365D !important;
    }

    /* Tabs Styling */
    button[data-baseweb="tab"] {
        color: #4A5E78 !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #1B365D !important;
        border-bottom-color: #1B365D !important;
    }

    /* ========================================================
       BADGES & STATUS PILLS (NAVY & BEIGE HARMONIZED)
       ======================================================== */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        text-transform: capitalize;
        margin-right: 6px;
    }
    .badge-comprehension { background-color: #E2E8F0; color: #0F1E36; border: 1px solid #CBD5E1; }
    .badge-reasoning { background-color: #EAE4D8; color: #0F1E36; border: 1px solid #D8CEBD; }
    .badge-decision { background-color: #E8EDF5; color: #1B365D; border: 1px solid #C8D4E5; }
    .badge-edge_case { background-color: #F5EBEB; color: #8C2424; border: 1px solid #E5C8C8; }
    .badge-debugging { background-color: #EBF1F7; color: #1B365D; border: 1px solid #CADBEB; }
    .badge-concept { background-color: #EAE4D8; color: #0F1E36; border: 1px solid #D8CEBD; }

    .badge-easy { background-color: #EBF5EE; color: #1A5632; border: 1px solid #C4E2CB; }
    .badge-medium { background-color: #F5EFE3; color: #7A5318; border: 1px solid #E5D5BA; }
    .badge-hard { background-color: #F8EBEB; color: #8C2424; border: 1px solid #E5C8C8; }

    /* Concept & Rubric Pills */
    .pill-concept {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px 4px 2px 0;
    }
    .pill-correct {
        background-color: #EBF5EE;
        border: 1px solid #C4E2CB;
        color: #1A5632;
    }
    .pill-missing {
        background-color: #F5EFE3;
        border: 1px solid #E5D5BA;
        color: #7A5318;
    }
    .pill-misconception {
        background-color: #F8EBEB;
        border: 1px solid #E5C8C8;
        color: #8C2424;
    }

    /* Status Pills */
    .status-pill {
        display: inline-flex;
        align-items: center;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .status-completed {
        background-color: #EBF5EE;
        color: #1A5632;
        border: 1px solid #C4E2CB;
    }
    .status-in-progress {
        background-color: #E8EDF5;
        color: #1B365D;
        border: 1px solid #CADBEB;
    }

    /* Pure CSS Indicator Dots (no emojis) */
    .indicator-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .indicator-online {
        background-color: #1B365D;
        box-shadow: 0 0 6px rgba(27, 54, 93, 0.4);
    }
    .indicator-offline {
        background-color: #8C2424;
        box-shadow: 0 0 6px rgba(140, 36, 36, 0.4);
    }
</style>
"""
