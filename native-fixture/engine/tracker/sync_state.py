"""Private, disposable read cache and durable refresh inbox; never task authority."""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import time


@contextmanager
def exclusive_lock(path):
    # Hosting is POSIX. Import locally so the portable agent CLI still works on Windows.
    import fcntl
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another synchronization process owns this directory') from None
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


class SyncState:
    def __init__(self, directory, clock=time.time):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        directory.chmod(0o700)
        self.path, self.clock = directory / 'sync.sqlite3', clock
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS deliveries (
                    id TEXT PRIMARY KEY, project TEXT, event TEXT, received REAL);
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY, generation INTEGER NOT NULL DEFAULT 0,
                    completed INTEGER NOT NULL DEFAULT 0, due REAL NOT NULL DEFAULT 0,
                    full_generation INTEGER NOT NULL DEFAULT 0,
                    retry REAL NOT NULL DEFAULT 0, failures INTEGER NOT NULL DEFAULT 0,
                    success REAL NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS cache (
                    path TEXT PRIMARY KEY, etag TEXT, body TEXT NOT NULL,
                    next TEXT, touched REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS counters (name TEXT PRIMARY KEY, value INTEGER);
                CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value REAL);
            ''')
        self.path.chmod(0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def register(self, identifiers):
        with self.connect() as db:
            db.executemany('INSERT OR IGNORE INTO projects(id) VALUES (?)', ((i,) for i in identifiers))

    def _enqueue(self, db, identifiers, delay, full=False):
        for identifier in identifiers:
            # Bound coalescing from the first event; endless edits cannot starve a refresh.
            db.execute('''UPDATE projects SET due=CASE WHEN generation=completed THEN ? ELSE min(due,?) END,
                       full_generation=CASE WHEN ? THEN generation+1 ELSE full_generation END,
                       generation=generation+1 WHERE id=?''',
                       (self.clock() + delay, self.clock() + delay, full, identifier))

    def enqueue(self, identifiers, delay=0, full=False):
        with self.connect() as db:
            self._enqueue(db, identifiers, delay, full)

    def accept(self, delivery, project, event, identifiers, delay=3):
        with self.connect() as db:
            inserted = db.execute('INSERT OR IGNORE INTO deliveries VALUES (?,?,?,?)',
                                  (delivery, project, event, self.clock())).rowcount
            if inserted:
                self._enqueue(db, identifiers, delay)
            return bool(inserted)

    def due(self, identifiers):
        allowed = set(identifiers)
        if self.blocked_until() > self.clock():
            return []
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                'SELECT * FROM projects WHERE generation>completed AND due<=? AND retry<=? ORDER BY due,id',
                (self.clock(), self.clock())) if row['id'] in allowed]

    def finish(self, identifier, generation, success):
        with self.connect() as db:
            if success:
                # Events accepted during the fetch retain a newer pending generation.
                db.execute('UPDATE projects SET completed=?,success=?,failures=0,retry=0 WHERE id=?',
                           (generation, self.clock(), identifier))
            else:
                row = db.execute('SELECT failures FROM projects WHERE id=?', (identifier,)).fetchone()
                failures = row['failures'] + 1
                delay = min(900, 30 * 2 ** min(failures - 1, 5))
                db.execute('UPDATE projects SET failures=?,retry=? WHERE id=?',
                           (failures, self.clock() + delay, identifier))

    def cached(self, path):
        with self.connect() as db:
            row = db.execute('SELECT * FROM cache WHERE path=?', (path,)).fetchone()
            if not row:
                return None
            try:
                return dict(row, value=json.loads(row['body']))
            except ValueError:
                db.execute('DELETE FROM cache WHERE path=?', (path,))
                return None

    def cache(self, path, etag, value, next_path):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?,?,?)',
                       (path, etag, json.dumps(value), next_path, self.clock()))

    def forget(self, path):
        with self.connect() as db:
            db.execute('DELETE FROM cache WHERE path=?', (path,))

    def count(self, name):
        with self.connect() as db:
            db.execute('INSERT INTO counters VALUES (?,1) ON CONFLICT(name) DO UPDATE SET value=value+1', (name,))

    def block_until(self, timestamp):
        with self.connect() as db:
            db.execute("INSERT INTO settings VALUES ('blocked_until',?) ON CONFLICT(name) DO UPDATE SET value=max(value,excluded.value)", (timestamp,))

    def blocked_until(self):
        with self.connect() as db:
            row = db.execute("SELECT value FROM settings WHERE name='blocked_until'").fetchone()
            return row['value'] if row else 0

    def prune(self):
        with self.connect() as db:
            db.execute('DELETE FROM deliveries WHERE received<?', (self.clock() - 30 * 86400,))
            db.execute('DELETE FROM cache WHERE touched<?', (self.clock() - 30 * 86400,))

    def metrics(self):
        with self.connect() as db:
            return {'counters': dict(db.execute('SELECT name,value FROM counters')),
                    'deliveries': db.execute('SELECT count(*) FROM deliveries').fetchone()[0],
                    'projects': [dict(row) for row in db.execute('SELECT * FROM projects ORDER BY id')],
                    'blocked_until': self.blocked_until()}
