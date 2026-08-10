"""Make the scripts/ directory importable so the test suite runs under any
invocation form (`pytest tests/`, `pytest`, `python -m pytest tests/`).

The scripts import each other as plain modules (e.g. `import apply_user_lists
as sync`), so scripts/ must be on sys.path regardless of how pytest is
launched or where the CWD is.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
