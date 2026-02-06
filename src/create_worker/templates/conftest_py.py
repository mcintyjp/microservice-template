CONTENT = """\
\"\"\"Pytest configuration.\"\"\"

import sys
from pathlib import Path

# Add src/ to path so actions and services are importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
"""
