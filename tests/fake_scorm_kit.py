"""Offline stand-in for the scorm-kit CLI, used only by the test suite.

The app shells out to ``$NODE_BIN $SCORM_KIT a11y <zip> [--json]``. The tests
point NODE_BIN at the Python interpreter and SCORM_KIT at this file, so the
real subprocess + JSON parsing path in app.py runs without Node or scorm-kit.

The canned findings below are what the real scorm-kit a11y engine reports for
tests/fixtures/course/index.html. Set FAKE_ENGINE_MODE=empty to simulate an
engine that crashes and prints nothing to stdout.
"""
import json
import os
import sys

FINDINGS = [
    {"rule": "doc-no-lang", "sev": "error", "msg": "<html> missing lang attribute",
     "file": "index.html", "line": 2, "detail": ""},
    {"rule": "doc-no-title", "sev": "error", "msg": "no <title> element",
     "file": "index.html", "line": 1, "detail": ""},
    {"rule": "img-no-alt", "sev": "error", "msg": "<img> missing alt attribute (use alt=\"\" for decorative)",
     "file": "index.html", "line": 6, "detail": "<img src=\"photo.png\">"},
    {"rule": "heading-no-h1", "sev": "warn", "msg": "HTML has headings but no <h1>",
     "file": "index.html", "line": 5, "detail": ""},
    {"rule": "link-generic-text", "sev": "warn", "msg": "link text is generic (\"click here\" / \"read more\")",
     "file": "index.html", "line": 7, "detail": "\"click here\""},
    {"rule": "button-no-name", "sev": "error", "msg": "<button> has no accessible name",
     "file": "index.html", "line": 8, "detail": ""},
]


def main(argv):
    if os.environ.get("FAKE_ENGINE_MODE") == "empty":
        print("Error: engine exploded", file=sys.stderr)
        return 2
    if len(argv) < 2 or argv[0] != "a11y":
        print("usage: a11y <zip> [--json]", file=sys.stderr)
        return 64
    if "--json" in argv:
        print(json.dumps({"findings": FINDINGS}, indent=2))
    else:
        errors = sum(1 for f in FINDINGS if f["sev"] == "error")
        warns = sum(1 for f in FINDINGS if f["sev"] == "warn")
        print(f"{errors} error(s), {warns} warning(s) across 1 HTML file(s).")
    return 2 if FINDINGS else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
