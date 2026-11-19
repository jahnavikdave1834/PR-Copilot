"""PR Understanding Copilot - Streamlit Application Entry Point."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

# Add current directory to path
root_dir = Path(__file__).parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Delegate to frontend/app.py
target_script = root_dir / "frontend" / "app.py"
runpy.run_path(str(target_script), run_name="__main__")
