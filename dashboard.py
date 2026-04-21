"""
Phase 12: Real-time web dashboard to watch the agent live.

Auto-starts when main.py is run with --dashboard.
Can also be imported and used directly:
    from dashboard import start_dashboard, emit_event, emit_screenshot
"""
from __future__ import annotations
import base64
import io
import threading
import time

_socketio = None
_app = None


def create_app():
    global _app, _socketio
    try:
        from flask import Flask, render_template_string
        from flask_socketio import SocketIO
    except ImportError:
        raise ImportError(
            "Dashboard requires: pip install flask flask-socketio"
        )

    _app = Flask(__name__)
    _app.config["SECRET_KEY"] = "cua-dashboard-secret"
    _socketio = SocketIO(_app, cors_allowed_origins="*", async_mode="threading")

    @_app.route("/")
    def index():
        return render_template_string(_DASHBOARD_HTML)

    return _app, _socketio


def emit_event(event: str, data: dict):
    """Broadcast an event to all connected dashboard clients."""
    if _socketio:
        _socketio.emit(event, data)


def emit_screenshot(img_pil):
    """Send a compressed screenshot to the dashboard."""
    if not _socketio:
        return
    buf = io.BytesIO()
    thumb = img_pil.copy()
    thumb.thumbnail((960, 540))
    thumb.save(buf, format="JPEG", quality=70)
    _socketio.emit("screenshot", {"data": base64.b64encode(buf.getvalue()).decode()})


def start_dashboard(host: str = "127.0.0.1", port: int = 7860,
                    open_browser: bool = True) -> str:
    """Start the dashboard server in a background thread. Returns URL."""
    create_app()

    def _run():
        _socketio.run(_app, host=host, port=port,
                      allow_unsafe_werkzeug=True, log_output=False)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    time.sleep(1.5)

    url = f"http://{host}:{port}"
    print(f"📊 Dashboard → {url}")

    if open_browser:
        import webbrowser
        webbrowser.open(url)

    return url


# ---------------------------------------------------------------------------
# Embedded HTML/JS dashboard
# ---------------------------------------------------------------------------

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Computer-Using Agent — Live Dashboard</title>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#0f0f0f;color:#e0e0e0;font-family:'Courier New',monospace;height:100vh;display:flex;flex-direction:column}
  header{background:#1a1a2e;padding:12px 20px;display:flex;align-items:center;gap:14px;border-bottom:1px solid #2a2a3e}
  header h1{font-size:1rem;color:#7eb8f7;white-space:nowrap}
  #badge{padding:3px 10px;border-radius:20px;font-size:.7rem;background:#222;color:#666}
  #badge.running{background:#0d1f0d;color:#4caf50}
  #badge.done{background:#0d0d1f;color:#7eb8f7}
  #badge.error{background:#1f0d0d;color:#f44336}
  #goal{font-size:.82rem;color:#aaa;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .main{display:flex;flex:1;overflow:hidden}
  .screen{flex:1;display:flex;align-items:center;justify-content:center;background:#111;padding:10px}
  #screen-img{max-width:100%;max-height:100%;border:1px solid #2a2a3e;border-radius:3px;object-fit:contain}
  .sidebar{width:340px;display:flex;flex-direction:column;border-left:1px solid #1e1e1e}
  .sb-header{background:#1a1a2e;padding:7px 12px;font-size:.7rem;color:#7eb8f7;border-bottom:1px solid #2a2a3e;letter-spacing:.05em}
  #log{flex:1;overflow-y:auto;padding:8px;font-size:.72rem;line-height:1.5}
  .entry{padding:5px 8px;border-radius:3px;margin-bottom:3px;border-left:3px solid #333}
  .entry.step{border-color:#4caf50;background:#0d1a0d}
  .entry.blocked{border-color:#f44336;background:#1a0d0d}
  .entry.done{border-color:#7eb8f7;background:#0d0d1a}
  .entry.error{border-color:#ff9800;background:#1a130d}
  .entry.info{border-color:#444;background:#141414}
  .entry.rollback{border-color:#e040fb;background:#1a0d1a}
  .ts{color:#444;font-size:.62rem;margin-right:4px}
  .badge-type{font-weight:700;margin-right:5px}
  .details{color:#555;font-size:.65rem;margin-top:2px}
  #footer{padding:7px 12px;background:#111;border-top:1px solid #1e1e1e;font-size:.7rem;color:#555;display:flex;gap:16px}
  .dot{width:7px;height:7px;border-radius:50%;background:#4caf50;display:inline-block;margin-right:5px;animation:pulse 1.4s infinite}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
</style>
</head>
<body>
<header>
  <h1>🤖 Computer-Using Agent</h1>
  <span id="badge">Waiting...</span>
  <span id="goal">No active session</span>
</header>
<div class="main">
  <div class="screen">
    <img id="screen-img" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" alt="Screen capture">
  </div>
  <div class="sidebar">
    <div class="sb-header">ACTION LOG</div>
    <div id="log"></div>
    <div id="footer">
      <span id="steps">Steps: 0</span>
      <span id="provider">Provider: —</span>
      <span id="session">Session: —</span>
    </div>
  </div>
</div>
<script>
const socket = io();
const log = document.getElementById('log');
const img = document.getElementById('screen-img');
const badge = document.getElementById('badge');
const goalEl = document.getElementById('goal');
const stepsEl = document.getElementById('steps');
const providerEl = document.getElementById('provider');
const sessionEl = document.getElementById('session');
let stepCount = 0;

function ts() {
  return new Date().toLocaleTimeString();
}

function addLog(type, msg, detail='') {
  const d = document.createElement('div');
  d.className = 'entry ' + type;
  d.innerHTML = '<span class="ts">'+ts()+'</span>'
    + '<span class="badge-type">'+type.toUpperCase()+'</span>' + msg
    + (detail ? '<div class="details">'+detail+'</div>' : '');
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}

socket.on('screenshot', d => { img.src = 'data:image/jpeg;base64,' + d.data; });

socket.on('session_start', d => {
  goalEl.textContent = '🎯 ' + d.goal;
  badge.textContent = '● Running';
  badge.className = 'running';
  stepCount = 0;
  log.innerHTML = '';
  providerEl.textContent = 'Provider: ' + d.provider + ' / ' + d.model;
  sessionEl.textContent = 'Session: ' + d.session_id;
  addLog('info', '<span class="dot"></span>Session started');
});

socket.on('step', d => {
  stepCount++;
  stepsEl.textContent = 'Steps: ' + stepCount + (d.max_steps ? ' / ' + d.max_steps : '');
  addLog('step', 'Step ' + d.step + ': ' + d.type, d.reasoning || '');
});

socket.on('blocked', d => { addLog('blocked', 'BLOCKED', d.reason || ''); });

socket.on('rollback', d => { addLog('rollback', 'ROLLBACK triggered', d.reason || ''); });

socket.on('done', d => {
  badge.textContent = '✓ Done';
  badge.className = 'done';
  addLog('done', 'Goal complete! ' + d.steps + ' steps | status: ' + d.status);
});

socket.on('error', d => {
  badge.textContent = '✗ Error';
  badge.className = 'error';
  addLog('error', d.message || 'Unknown error');
});

socket.on('connect', () => { addLog('info', '<span class="dot"></span>Dashboard connected'); });
socket.on('disconnect', () => { addLog('info', 'Disconnected from agent'); });
</script>
</body>
</html>"""
