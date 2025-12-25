"""Pytest config.

Ensures the repository root is importable so `import beam1010` works when running
`pytest` without installing the package.

This repo intentionally keeps things lightweight (no packaging step required).
"""

from __future__ import annotations

import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
