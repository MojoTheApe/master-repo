"""Signed GitHub deliveries schedule repository reads; payloads never replace Issues."""
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import signal
import threading
import time
from .cached_github import CachedGitHub
from .sync_state import SyncState, exclusive_lock
from .workspace import load_workspace, sync_workspace

MAX_BODY = 2 * 1024 * 1024


class Receiver:
    def __init__(self, registry, state, secret):
        if len(secret) < 32:
            raise ValueError('Use a random webhook secret of at least 32 bytes')
        self.registry, self.state, self.secret = registry, state, secret
        self.repositories = {p['repository'].lower(): p for p in registry['projects']}

    def receive(self, headers, body):
        signature = headers.get('X-Hub-Signature-256', '')
        expected = 'sha256=' + hmac.new(self.secret, body, hashlib.sha256).hexdigest()
        if not re.fullmatch(r'sha256=[a-f0-9]{64}', signature) or not hmac.compare_digest(signature, expected):
            return 401
        if len(body) > MAX_BODY:
            return 413
        if headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            return 415
        delivery, event = headers.get('X-GitHub-Delivery', ''), headers.get('X-GitHub-Event', '')
        if not re.fullmatch(r'[a-zA-Z0-9-]{16,80}', delivery):
            return 400
        try:
            payload = json.loads(body)
            repo = payload['repository']['full_name'].lower()
            project = self.repositories.get(repo)
            if project is None:
                return 403
            action = payload.get('action', '')
            identifiers = []
            if event == 'issues':
                if not isinstance(payload.get('issue', {}).get('number'), int):
                    return 400
                if action in {'opened', 'edited', 'deleted', 'transferred', 'closed', 'reopened',
                              'labeled', 'unlabeled', 'milestoned', 'demilestoned', 'typed', 'untyped'}:
                    # A transfer affects both repositories and may introduce a deep-link route.
                    identifiers = [p['id'] for p in self.registry['projects']] if action == 'transferred' else [project['id']]
            elif event in ('milestone', 'label') and action in {'created', 'edited', 'deleted', 'opened', 'closed'}:
                identifiers = [project['id']]
            elif event == 'push' and payload.get('ref') in ('refs/heads/' + project['base_branch'], 'refs/heads/tracker-state'):
                identifiers = [project['id']]
            elif event != 'ping':
                # Valid but irrelevant deliveries are still deduplicated, without a refresh.
                pass
        except (ValueError, KeyError, TypeError, AttributeError):
            return 400
        inserted = self.state.accept(delivery, project['id'], event, identifiers)
        return 202 if inserted else 200


class Worker:
    def __init__(self, workspace, output, state, command=None, interval=900, refresh=sync_workspace):
        if not 60 <= interval <= 900:
            raise ValueError('Reconciliation interval must be 60–900 seconds')
        self.workspace, self.output, self.state = workspace, output, state
        self.command, self.interval, self.refresh = command, interval, refresh
        self.identifiers = [p['id'] for p in load_workspace(workspace)['projects']]
        state.register(self.identifiers)
        self.next_reconcile = 0
        self.heartbeat = time.monotonic()
        self.started = None

    def step(self):
        self.heartbeat = time.monotonic()
        periodic = self.state.clock() >= self.next_reconcile
        if periodic:
            self.state.enqueue(self.identifiers, full=True)
            self.state.prune()
            self.next_reconcile = self.state.clock() + self.interval
        pending = self.state.due(self.identifiers)
        if not pending:
            return False
        self.started = time.monotonic()
        try:
            # Unconditional reconciliation also repairs collection pagination after
            # missing notifications. Event reads use ETags page by page.
            repository_ids = {p['repository']: p['id'] for p in load_workspace(self.workspace)['projects']}
            full = {p['id'] for p in pending if p['full_generation'] > p['completed']}
            factory = lambda repo: CachedGitHub(repo, self.state, self.command, conditional=repository_ids[repo] not in full)
            result = self.refresh(self.workspace, self.output, command=self.command,
                                  api_factory=factory, project_ids=[p['id'] for p in pending],
                                  freshness_seconds=self.interval + 180)
            selected = {p['id'] for p in pending}
            outcomes = {p['id']: p['ok'] for p in result['projects'] if p['id'] in selected}
            for project in pending:
                self.state.finish(project['id'], project['generation'], outcomes.get(project['id'], False))
            self.state.count('refresh_batches')
            print(json.dumps({'event': 'refresh', 'projects': outcomes, 'reconciliation': periodic}), flush=True)
        except Exception:
            for project in pending:
                self.state.finish(project['id'], project['generation'], False)
            self.state.count('worker_errors')
            # GitHub/output failures must never echo raw response bodies or credentials.
            print('Refresh failed; pending work retained for retry', flush=True)
        finally:
            self.heartbeat = time.monotonic()
            self.started = None
        return True

    def healthy(self):
        return time.monotonic() - (self.started or self.heartbeat) < (600 if self.started else 15)

    def run(self, stop):
        while not stop.is_set():
            self.step()
            stop.wait(1)


def handler(receiver, worker):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'Tracker'
        sys_version = ''

        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def reply(self, status, body=b''):
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/healthz':
                self.reply(200 if worker.healthy() else 503, b'{"service":"tracker-events"}')
            else:
                self.reply(404)

        def do_POST(self):
            if self.path != '/github/webhook':
                self.reply(404)
                return
            sizes = self.headers.get_all('Content-Length', [])
            if len(sizes) != 1 or not re.fullmatch(r'[0-9]{1,9}', sizes[0]) or self.headers.get('Transfer-Encoding'):
                self.reply(400)
                return
            size = int(sizes[0])
            if size > MAX_BODY:
                self.reply(413)
                return
            try:
                body = self.rfile.read(size)
                if len(body) != size:
                    self.reply(400)
                    return
                self.reply(receiver.receive(self.headers, body))
            except (OSError, ValueError):
                self.reply(400)
            except Exception:
                # No 2xx acknowledgment if durable acceptance failed.
                self.reply(503)

        def log_message(self, *args):
            pass
    return Handler


def serve(workspace, output, state_dir, secret_file, *, command=None, host='127.0.0.1', port=8787, interval=900):
    output, state_dir, secret_file = Path(output).resolve(), Path(state_dir).resolve(), Path(secret_file).resolve()
    if state_dir.is_relative_to(output) or secret_file.is_relative_to(output):
        raise ValueError('Private synchronization state and secret must be outside public output')
    if secret_file.stat().st_mode & 0o077:
        raise ValueError('Webhook secret file must be private (mode 0600)')
    state = SyncState(state_dir)
    with exclusive_lock(state_dir / 'service.lock'):
        worker = Worker(workspace, output, state, command, interval)
        receiver = Receiver(load_workspace(workspace), state, secret_file.read_bytes().strip())
        server = ThreadingHTTPServer((host, port), handler(receiver, worker))
        server.timeout = 1
        stop = threading.Event()
        previous = {sig: signal.signal(sig, lambda *_: stop.set()) for sig in (signal.SIGTERM, signal.SIGINT)}
        thread = threading.Thread(target=worker.run, args=(stop,), name='tracker-refresh')
        thread.start()
        try:
            while not stop.is_set():
                if not thread.is_alive():
                    raise RuntimeError('Refresh worker stopped; restart required')
                server.handle_request()
        finally:
            stop.set()
            server.server_close()
            thread.join()
            for sig, callback in previous.items():
                signal.signal(sig, callback)
