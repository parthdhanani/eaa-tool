import io
import os
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TESTS = Path(__file__).resolve().parent
FIXTURE_COURSE = TESTS / "fixtures" / "course"

sys.path.insert(0, str(ROOT))


def build_zip(src_dir: Path = FIXTURE_COURSE) -> bytes:
    """Zip a fixture folder in memory (keeps binary .zip files out of git)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(src_dir.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(src_dir).as_posix())
    return buf.getvalue()


@pytest.fixture
def app_module(tmp_path, monkeypatch):
    import app as app_mod

    sessions = tmp_path / "sessions"
    sessions.mkdir()
    monkeypatch.setattr(app_mod, "SESSIONS", sessions)
    # Route the a11y engine to the offline fake unless a real scorm-kit is given.
    monkeypatch.setattr(app_mod, "NODE", sys.executable)
    monkeypatch.setattr(app_mod, "SCORM_KIT", str(TESTS / "fake_scorm_kit.py"))
    monkeypatch.delenv("FAKE_ENGINE_MODE", raising=False)
    app_mod.app.config["TESTING"] = True
    return app_mod


@pytest.fixture
def client(app_module):
    return app_module.app.test_client()


@pytest.fixture
def course_zip() -> bytes:
    return build_zip()


def real_scorm_kit():
    """Path to a real scorm-kit CLI for the optional integration test, or None."""
    p = os.environ.get("SCORM_KIT_REAL")
    return p if p and Path(p).is_file() else None
