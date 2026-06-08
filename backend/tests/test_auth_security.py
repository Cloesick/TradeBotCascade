"""
Tests for the SECRET_KEY env handling, bcrypt password hashing, and JWT
round-trips. These lock in the two security fixes:

  1. SECRET_KEY is loaded from the environment (stable across restarts),
     fails fast in production when unset, and only falls back to an ephemeral
     key in development.
  2. Password hashing uses bcrypt directly (no passlib), so the backend imports
     and authenticates cleanly.
"""
import os
import subprocess
import sys
from pathlib import Path

import auth
from auth import PasswordHash, TokenManager, UserRole, user_db

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _run_import(env_overrides, cwd):
    """Import `auth` in a fresh subprocess with a controlled environment.

    Runs in an isolated working dir (so load_dotenv() can't pick up the repo's
    backend/.env) with PYTHONPATH pointed at the backend package. Returns
    (returncode, stdout, stderr). Used to exercise the import-time SECRET_KEY
    branching that can't be re-triggered within one process.
    """
    env = {k: v for k, v in os.environ.items() if k not in ("SECRET_KEY", "ENVIRONMENT")}
    env["PYTHONPATH"] = str(BACKEND_DIR)
    env.update(env_overrides)
    code = (
        "import auth; "
        "print('KEY_LEN', len(auth.SECRET_KEY)); "
        "print('ALGO', auth.ALGORITHM)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


# --------------------------------------------------------------------------- #
# SECRET_KEY environment handling
# --------------------------------------------------------------------------- #

def test_secret_key_loaded_from_env():
    """The configured SECRET_KEY (from conftest) is used verbatim."""
    assert auth.SECRET_KEY == os.environ["SECRET_KEY"]
    assert auth.ALGORITHM == "HS256"


def test_production_without_secret_key_fails_fast(tmp_path):
    """ENVIRONMENT=production + no SECRET_KEY must refuse to start.

    Runs in an isolated cwd so the repo's backend/.env can't supply a key.
    """
    rc, out, err = _run_import({"ENVIRONMENT": "production"}, cwd=tmp_path)
    assert rc != 0, f"expected failure, got success: {out}"
    assert "SECRET_KEY" in err and "required in production" in err


def test_development_without_secret_key_uses_fallback(tmp_path):
    """Dev with no SECRET_KEY still boots with a generated key."""
    rc, out, err = _run_import({"ENVIRONMENT": "development"}, cwd=tmp_path)
    assert rc == 0, err
    assert "KEY_LEN" in out
    key_len = int(out.split("KEY_LEN")[1].split()[0])
    assert key_len > 0


def test_secret_key_stable_across_restarts():
    """Same SECRET_KEY across two imports => a token from one verifies in the
    other. (Different ephemeral keys would fail to validate.)"""
    token = TokenManager.create_access_token({"sub": "admin", "role": "admin"})
    code = (
        "import sys; from auth import TokenManager; "
        "td = TokenManager.verify_token(sys.argv[1]); "
        "print('OK' if td and td.username == 'admin' else 'FAIL')"
    )
    env = {k: v for k, v in os.environ.items()}
    env["SECRET_KEY"] = auth.SECRET_KEY
    proc = subprocess.run(
        [sys.executable, "-c", code, token],
        cwd=str(BACKEND_DIR), env=env, capture_output=True, text=True,
    )
    assert proc.stdout.strip() == "OK", proc.stderr


# --------------------------------------------------------------------------- #
# Password hashing (bcrypt, used directly)
# --------------------------------------------------------------------------- #

def test_password_hash_roundtrip():
    h = PasswordHash.hash_password("Admin123!")
    assert h.startswith("$2"), "expected a bcrypt hash"
    assert PasswordHash.verify_password("Admin123!", h)
    assert not PasswordHash.verify_password("WrongPass1", h)


def test_password_hash_is_salted():
    """Two hashes of the same password differ (random salt)."""
    assert PasswordHash.hash_password("Admin123!") != PasswordHash.hash_password("Admin123!")


def test_long_password_does_not_crash():
    """>72-byte passwords are handled (bcrypt's limit) without raising."""
    long_pw = "A1b" * 40  # 120 bytes
    h = PasswordHash.hash_password(long_pw)
    assert PasswordHash.verify_password(long_pw, h)


def test_verify_handles_malformed_hash():
    assert PasswordHash.verify_password("whatever", "not-a-real-hash") is False


def test_default_admin_authenticates():
    user = user_db.authenticate_user("admin", "Admin123!")
    assert user is not None
    assert user.role == UserRole.ADMIN


# --------------------------------------------------------------------------- #
# JWT token round-trips
# --------------------------------------------------------------------------- #

def test_access_token_roundtrip():
    token = TokenManager.create_access_token({"sub": "admin", "role": "admin"})
    td = TokenManager.verify_token(token, token_type="access")
    assert td is not None and td.username == "admin"


def test_token_type_is_enforced():
    """An access token must not validate as a refresh token, and vice versa."""
    access = TokenManager.create_access_token({"sub": "admin", "role": "admin"})
    refresh = TokenManager.create_refresh_token({"sub": "admin", "role": "admin"})
    assert TokenManager.verify_token(access, token_type="refresh") is None
    assert TokenManager.verify_token(refresh, token_type="access") is None


def test_tampered_token_rejected():
    token = TokenManager.create_access_token({"sub": "admin", "role": "admin"})
    tampered = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
    assert TokenManager.verify_token(tampered) is None
