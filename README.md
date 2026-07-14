# EAA / WCAG Accessibility Checker for SCORM

Upload a SCORM package (`.zip`), get back a WCAG 2.2 conformance report: score, blocking vs advisory findings, and a plain-language fix for every issue — grouped by success criterion, with a rough remediation-time estimate.

Built for the [EU Accessibility Act](https://ec.europa.eu/social/main.jsp?catId=1202) (in force since June 2025), which points at EN 301 549 → WCAG 2.2 Level A/AA. Every rule this tool checks is mapped to a specific success criterion so a compliance report is traceable, not just a pass/fail badge.

## What it checks

Rules run through [scorm-kit](https://github.com/parthdhanani/scorm-kit)'s `a11y` engine and are mapped in [`wcag_map.py`](wcag_map.py) to WCAG criteria — missing `lang`/`title`, image alt-text problems (missing, filename-as-alt, redundant), missing video captions / audio transcripts, heading structure (skipped levels, missing `h1`), link and button naming, form labels, keyboard-operability of custom clickable elements, focus order, iframe titles, table headers, and ARIA validity.

## Usage

```bash
pip install -r requirements.txt
python app.py            # dev server on :5051
# or: gunicorn app:app --bind 0.0.0.0:5051
```

Requires Node.js — the tool shells out to `scorm-kit`'s `a11y` command as its scanning engine (path configurable via `SCORM_KIT` env var).

Open the page, drop a SCORM `.zip`, get a report: overall score, verdict (compliant / minor gaps / work needed / not compliant), and every finding grouped by WCAG success criterion with a plain-language fix.

## Stack

Flask · Node.js (scorm-kit engine) · WCAG 2.2 / EN 301 549

## Deployment

Ships with a systemd unit (`eaa-tool.service`) behind gunicorn. Sessions are ephemeral — uploaded packages live under `/tmp` with a 15-minute TTL and are deleted immediately after scoring.
