"""
Tests that TLS certificate verification is NOT disabled for outbound HTTP.

Locks in the fix that removed `verify=False`, `urllib3.disable_warnings(...)`,
and the process-wide `ssl._create_unverified_context` monkeypatch from main.py.
"""
import ssl
from pathlib import Path

MAIN_PY = Path(__file__).resolve().parents[1] / "main.py"


def test_main_source_has_no_tls_bypass():
    src = MAIN_PY.read_text(encoding="utf-8")
    assert "verify=False" not in src, "verify=False must not be reintroduced"
    assert "disable_warnings" not in src, "urllib3.disable_warnings must not return"
    assert "_create_unverified_context" not in src, "do not disable SSL verification globally"


def test_alpha_vantage_session_verifies_tls():
    import main
    # requests.Session defaults verify to True; ensure nothing flipped it off.
    assert main.av_session.verify is not False


def test_global_ssl_context_not_monkeypatched():
    """The process-wide default HTTPS context should still verify certs."""
    ctx = ssl.create_default_context()
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True
