"""Helper script to run pytest with the project root on PYTHONPATH."""

import os
import sys
import subprocess
from pathlib import Path

# Add kg_demo to sys.path and PYTHONPATH
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))
os.environ["PYTHONPATH"] = str(project_root) + os.pathsep + os.environ.get("PYTHONPATH", "")

# Run pytest in quiet mode
exit_code = subprocess.call([sys.executable, "-m", "pytest", "-v"], cwd=str(project_root))
sys.exit(exit_code)
