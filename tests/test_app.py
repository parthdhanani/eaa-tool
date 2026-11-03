"""Offline tests for the Flask app. No Node, scorm-kit or network required."""
import io
import shutil
import subprocess

import pytest
from conftest import build_zip, real_scorm_kit


def _post(client, data: bytes, name="course.zip"):
    return client.post(
        "/scan",
        data={"package": (io.BytesIO(data), name)},
        content_type="multipart/form-data",
    )


def test_index_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"<html" in r.data and b"/scan" in r.data


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.data == b"ok"


def test_scan_fixture_report(client, course_zip, app_module):
    r = _post(client, course_zip)
    assert r.status_code == 200, r.get_json()
    d = r.get_json()
    # 4 errors, 2 warnings -> 100 - 40 - 6
    assert d["blocking"] == 4 and d["advisory"] == 2
    assert d["score"] == 54 and d["verdict"] == "work needed"
    assert d["files_scanned"] == 1 and d["files_affected"] == 1
    # 2+2+3+5+3+3 minutes from wcag_map
    assert d["remediation_minutes"] == 18
    scs = [c["wcag"] for c in d["criteria"]]
    # Blocking groups sort first, then by criterion number.
    assert scs == ["1.1.1", "2.4.2", "3.1.1", "4.1.2", "2.4.4", "2.4.6"]
    assert all(c["severity"] == "error" for c in d["criteria"][:4])
    # Session dir is removed after scoring.
    assert list(app_module.SESSIONS.iterdir()) == []


def test_scan_without_file(client):
    r = client.post("/scan", data={}, content_type="multipart/form-data")
    assert r.status_code == 400
    assert "No SCORM package" in r.get_json()["error"]


def test_scan_rejects_non_zip(client, app_module):
    r = _post(client, b"this is not a zip file", name="notes.zip")
    assert r.status_code == 400
    assert "does not look like" in r.get_json()["error"]
    assert list(app_module.SESSIONS.iterdir()) == []


def test_scan_rejects_oversize(client, course_zip, app_module, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_B", 10)
    r = _post(client, course_zip)
    assert r.status_code == 413
    assert "MB limit" in r.get_json()["error"]


def test_scan_engine_failure_is_reported(client, course_zip, monkeypatch):
    monkeypatch.setenv("FAKE_ENGINE_MODE", "empty")
    r = _post(client, course_zip)
    assert r.status_code == 500
    assert "engine exploded" in r.get_json()["error"]


def test_scan_timeout(client, course_zip, app_module, monkeypatch):
    def boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="a11y", timeout=60)
    monkeypatch.setattr(app_module.subprocess, "run", boom)
    r = _post(client, course_zip)
    assert r.status_code == 504


def test_busy_when_session_cap_reached(client, course_zip, app_module, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_SESSIONS", 2)
    for i in range(2):
        (app_module.SESSIONS / f"live-{i}").mkdir()
    r = _post(client, course_zip)
    assert r.status_code == 503


def test_build_report_clean_package(app_module):
    d = app_module.build_report([], 3)
    assert d["score"] == 100 and d["verdict"] == "compliant"
    assert d["criteria"] == [] and d["remediation_minutes"] == 0


def test_build_report_score_floor_and_unmapped_rule(app_module):
    findings = [{"rule": "brand-new-rule", "sev": "error", "file": "a.html"}] * 12
    d = app_module.build_report(findings, None)
    assert d["score"] == 0 and d["verdict"] == "not compliant"
    assert d["criteria"][0]["wcag"] == "4.1.1"  # fallback criterion
    assert len(d["criteria"][0]["items"]) == 12


@pytest.mark.skipif(real_scorm_kit() is None or shutil.which("node") is None,
                    reason="set SCORM_KIT_REAL=/path/to/scorm-kit/bin/scorm-kit.js to run")
def test_scan_with_real_engine(client, app_module, monkeypatch):
    monkeypatch.setattr(app_module, "NODE", shutil.which("node"))
    monkeypatch.setattr(app_module, "SCORM_KIT", real_scorm_kit())
    r = _post(client, build_zip())
    assert r.status_code == 200, r.get_json()
    d = r.get_json()
    assert d["blocking"] == 4 and d["advisory"] == 2 and d["files_scanned"] == 1
