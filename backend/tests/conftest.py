"""
Shared pytest fixtures/config for the backend test suite.

Sets a stable SECRET_KEY *before* `auth`/`main` are imported so the suite is
deterministic and never relies on the ephemeral dev fallback.
"""
import os
import sys
from pathlib import Path

# Ensure the flat backend modules (auth, main, ...) are importable.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Deterministic, non-production config for the test process.
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-prod")
os.environ.setdefault("ENVIRONMENT", "development")
