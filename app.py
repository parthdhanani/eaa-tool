from flask import Flask, request, jsonify, render_template
from pathlib import Path
import uuid, os, sys, shutil, threading, time, subprocess, json, re

sys.path.insert(0, os.path.dirname(__file__))
import wcag_map

app = Flask(__name__)

SESSIONS     = Path('/tmp/eaa_tool_sessions')
MAX_AGE_S    = 900               # 15-min TTL
MAX_SESSIONS = 15
MAX_FILE_MB  = 80
MAX_FILE_B   = MAX_FILE_MB * 1024 * 1024
app.config['MAX_CONTENT_LENGTH'] = (MAX_FILE_MB + 10) * 1024 * 1024

# Path to the scorm-kit CLI (the a11y engine). Override with SCORM_KIT env var.
SCORM_KIT = os.environ.get(
    'SCORM_KIT',
    str(Path.home() / 'AI_Space' / 'autonomous_lab' / 'scorm-kit' / 'bin' / 'scorm-kit.js')
)
NODE = os.environ.get('NODE_BIN', 'node')

SESSIONS.mkdir(exist_ok=True)

# Purge anything stale from a previous run.
_cutoff = time.time() - MAX_AGE_S
for _d in list(SESSIONS.iterdir()):
    try:
        if _d.is_dir() and _d.stat().st_mtime < _cutoff:
            shutil.rmtree(_d, ignore_errors=True)
    except Exception:
        pass


def _cleanup_loop():
    while True:
        time.sleep(300)
        cut = time.time() - MAX_AGE_S
        for d in SESSIONS.iterdir():
            try:
                if d.is_dir() and d.stat().st_mtime < cut:
                    shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass

threading.Thread(target=_cleanup_loop, daemon=True).start()


def _session_cap():
    cut = time.time() - MAX_AGE_S
    for d in list(SESSIONS.iterdir()):
        try:
            if d.is_dir() and d.stat().st_mtime < cut:
                shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass
    count = sum(1 for d in SESSIONS.iterdir() if d.is_dir())
    if count >= MAX_SESSIONS:
        return jsonify({'error': 'Server is busy. Try again in a few minutes.'}), 503
    return None


def _is_zip(path: Path) -> bool:
    try:
        with open(path, 'rb') as fh:
            return fh.read(2) == b'PK'
    except Exception:
        return False


def _run_a11y(zip_path: Path):
    """Return (findings, files_scanned). Raises on engine failure."""
    j = subprocess.run([NODE, SCORM_KIT, 'a11y', str(zip_path), '--json'],
                       capture_output=True, text=True, timeout=60)
    if not j.stdout.strip():
        raise RuntimeError((j.stderr or 'a11y engine returned nothing').strip().split('\n')[-1])
    findings = json.loads(j.stdout).get('findings', [])

    # Second pass (text) just to read the "across N HTML file(s)" count.
    t = subprocess.run([NODE, SCORM_KIT, 'a11y', str(zip_path)],
                       capture_output=True, text=True, timeout=60)
    m = re.search(r'across (\d+) HTML file', t.stdout or '')
    files_scanned = int(m.group(1)) if m else None
    return findings, files_scanned


def build_report(findings, files_scanned):
    errors = sum(1 for f in findings if f.get('sev') == 'error')
    warns  = sum(1 for f in findings if f.get('sev') == 'warn')
    score  = max(0, 100 - 10 * errors - 3 * warns)
    verdict = ('compliant' if score >= 90 else
               'minor gaps' if score >= 70 else
               'work needed' if score >= 40 else 'not compliant')

    # Group by WCAG criterion, annotate, and total the remediation estimate.
    groups, total_minutes = {}, 0
    for f in findings:
        meta = wcag_map.annotate(f.get('rule', ''))
        total_minutes += meta['fix_minutes']
        key = meta['wcag']
        g = groups.setdefault(key, {
            'wcag': meta['wcag'], 'wcag_name': meta['wcag_name'],
            'level': meta['level'], 'fix': meta['fix'],
            'severity': f.get('sev'), 'items': [],
        })
        if f.get('sev') == 'error':
            g['severity'] = 'error'
        g['items'].append({
            'rule': f.get('rule'), 'msg': f.get('msg'),
            'file': f.get('file'), 'line': f.get('line'),
            'detail': f.get('detail', ''), 'sev': f.get('sev'),
        })

    grouped = sorted(groups.values(),
                     key=lambda g: (0 if g['severity'] == 'error' else 1, g['wcag']))
    affected = sorted({f.get('file') for f in findings if f.get('file')})

    return {
        'score': score, 'verdict': verdict,
        'blocking': errors, 'advisory': warns,
        'files_scanned': files_scanned, 'files_affected': len(affected),
        'remediation_minutes': total_minutes,
        'criteria': grouped,
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    return 'ok', 200


@app.route('/scan', methods=['POST'])
def scan():
    cap = _session_cap()
    if cap:
        return cap

    pkg = request.files.get('package')
    if not pkg:
        return jsonify({'error': 'No SCORM package uploaded.'}), 400

    sid = str(uuid.uuid4())
    sdir = SESSIONS / sid
    sdir.mkdir()
    zpath = sdir / 'course.zip'
    try:
        pkg.save(str(zpath))
        if zpath.stat().st_size > MAX_FILE_B:
            return jsonify({'error': f'Package exceeds the {MAX_FILE_MB} MB limit.'}), 413
        if not _is_zip(zpath):
            return jsonify({'error': 'That does not look like a SCORM .zip package.'}), 400
        findings, files_scanned = _run_a11y(zpath)
        return jsonify(build_report(findings, files_scanned))
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Analysis timed out. Is the package very large?'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        shutil.rmtree(sdir, ignore_errors=True)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5051)))
