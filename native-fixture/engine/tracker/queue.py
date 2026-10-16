"""One execution slot and explicit Todo batches, using GitHub SHA compare-and-swap."""
from __future__ import annotations
import base64
import json
import uuid
from urllib.parse import quote
from .github import APIError, file_bytes
from .model import names, tasks_from_issues, is_complete
from .sync import now
from .workflow import target
from .identifiers import task_id

BRANCH = "tracker-state"
FILE = ".tracker-state.json"


def empty():
    return {"schema_version": 1, "active": None, "run": None, "todo_order": [], "todo_added": {}}


class StateStore:
    def __init__(self, api, base_branch):
        self.api, self.base = api, base_branch
        self.path = api.root + "/contents/" + FILE

    def read(self, optional=False):
        row = self.api.request(self.path + "?ref=" + BRANCH, optional=optional)
        if row is None:
            return empty(), None
        value = json.loads(file_bytes(self.api.request, self.api.root, row))
        from .delivery_policy import state_schema
        if state_schema(value) not in (1, 2) or not isinstance(value.get("todo_order"), list):
            raise ValueError("Invalid shared tracker state; inspect it before continuing")
        return value, row["sha"]

    def write(self, state, sha):
        from .delivery_policy import state_schema
        state_schema(state)
        if sha is None:
            ref = self.api.request(self.api.root + "/git/ref/heads/" + BRANCH, optional=True)
            if ref is None:
                base = self.api.request(self.api.root + "/git/ref/heads/" + quote(self.base, safe=""))
                try:
                    self.api.request(self.api.root + "/git/refs", "POST",
                                     {"ref": "refs/heads/" + BRANCH, "sha": base["object"]["sha"]})
                except APIError as error:
                    if error.status != 422:
                        raise
        request = {"message": "Update tracker execution state [skip ci]", "branch": BRANCH,
                   "content": base64.b64encode(json.dumps(state, indent=2).encode()).decode()}
        if sha:
            request["sha"] = sha
        try:
            self.api.request(self.path, "PUT", request)
        except APIError as error:
            if error.status in (409, 422):
                raise ValueError("Tracker state changed in another session; reload before retrying") from None
            # A timeout may have committed. Keep the slot reserved; explicit resume recovers it.
            raise


def public_state(state):
    from .delivery_policy import summary, state_schema
    # Existing snapshot callers supply partial legacy projection inputs (including
    # {}). Canonical store reads and explicit protocol/ownership fields remain
    # strict; a malformed fence cannot enter through this compatibility bridge.
    schema = (state_schema(state) if any(k in state for k in ('schema_version', 'maintenance', 'execution')) else 1)
    active = state.get("active")
    result = {"active": {k: active[k] for k in ("issue", "started_at")} if active else None,
            "run": state.get("run"), "todo_order": state.get("todo_order", []), "todo_added": state.get("todo_added", {}),
            "release_history": state.get('release_history', []), "release_rollover": bool(state.get('release_rollover')),
            "delivery_tasks": {n: summary(r) for n, r in state.get('delivery_workflow', {}).get('tasks', {}).items()}}
    if schema == 2:
        from .execution import public
        result['execution'] = public(state['execution'], state.get('delivery_workflow', {}))
    if state.get('maintenance'):
        from .maintenance import busy
        result['maintenance'] = {'admission_paused': True, 'state': 'draining' if busy(state) else 'idle',
                                 'reserved_at': state['maintenance']['reserved_at']}
    from .timing import project
    result['timing'] = project(state)
    return result


def legacy(state):
    from .delivery_policy import state_schema
    if state_schema(state) != 1:
        raise ValueError('Use execution commands for parallel ownership; legacy queue commands cannot change its state')


def dependency_problems(task, tasks):
    lookup = {key: t for t in tasks for key in (t["id"].lower(), f"#{t['number']}")}
    return [dep for dep in task["dependencies"] if dep.lower() not in lookup
            or not is_complete(lookup[dep.lower()])]


def ordered_todo(tasks, manual=()):
    positions = {number: index for index, number in enumerate(manual)}
    priority = {"high": 0, "medium": 1, "low": 2, "": 1}
    return sorted((t for t in tasks if t.get("phase", t["status"]) == "todo" and not t["archive"] and not t["initiative"]),
                  key=lambda t: (positions.get(t["number"], len(positions)), priority[t["priority"]],
                                 t.get("todo_at") or t["created_at"], t["number"]))


def begin(store, tasks):
    state, sha = store.read(optional=True)
    legacy(state)
    from .delivery_policy import admission_open
    admission_open(state)
    if state.get("active") or (state.get("run") and state["run"]["state"] == "running"):
        raise ValueError("An execution or batch already exists; use queue next/resume")
    for task in tasks:
        task["todo_at"] = state.get("todo_added", {}).get(str(task["number"]), "")
    ids = [t["number"] for t in ordered_todo(tasks, state["todo_order"])]
    if not ids:
        raise ValueError("No Todo tasks to snapshot")
    state["run"] = {"id": uuid.uuid4().hex, "state": "running", "issues": ids, "started_at": now()}
    store.write(state, sha)
    return state["run"]


def start(api, config, store, number, resume=False, execution_args=None):
    if config.get('execution_policy'):
        from . import execution
        return execution.start(api, config, store, number, execution_args)
    state, sha = store.read(optional=True)
    legacy(state)
    active = state.get("active")
    if active and (active["issue"] != number or not resume):
        raise ValueError(f"#{active['issue']} owns the execution slot. Resume it explicitly or release it after review.")
    if resume and not active:
        raise ValueError("No execution to resume; start the task normally")
    if not active:
        from .delivery_policy import admission_open
        admission_open(state)
    tasks = tasks_from_issues(api.issues(), config, state.get('delivery_workflow',{}).get('tasks',{}))
    task = next((t for t in tasks if t["number"] == number), None)
    if task is None:
        # GitHub's collection can briefly lag a successful create. Verify the exact
        # Issue directly; never infer absence or repeat its creation from the list.
        direct = tasks_from_issues([api.issue(number)], config, state.get('delivery_workflow',{}).get('tasks',{}))
        task = direct[0] if direct else None
        if task: tasks.append(task)
    if not task or task["archive"] or task.get("phase", task["status"]) == "merged" or task["initiative"]:
        raise ValueError("Choose an open, unfinished leaf task")
    if task["blocked"] or dependency_problems(task, tasks):
        raise ValueError("Task is blocked or has unfinished dependencies")
    if task["warnings"] or not task['module'] or not task['type']:
        raise ValueError("Resolve task metadata warnings before starting")
    reservation_changed = not active
    if not active:
        state["active"] = {"issue": number, "started_at": now()}
    elif active.get('timing_finished_at'):
        active['started_at'] = now()
        active.pop('timing_finished_at')
        reservation_changed = True
    from .timing import end_observations
    reservation_changed = end_observations(state, number) or reservation_changed
    if str(number) in config.get('historical_completion', {}).get('tasks', {}):
        row = state.setdefault('delivery_workflow', {}).setdefault('tasks', {}).setdefault(str(number), {})
        if not row.get('historical_revoked'):
            row['historical_revoked'] = True
            reservation_changed = True
    if reservation_changed:
        store.write(state, sha)
    # Reserve first. On an uncertain API result, retain the reservation for explicit resume.
    issue = api.issue(number)
    latest = tasks_from_issues([issue], config)[0]
    if latest["archive"] or latest.get("phase", latest["status"]) == "merged" or latest["blocked"] or latest["warnings"] or dependency_problems(latest, tasks):
        raise ValueError("Task changed before the status write; inspect it and resume explicitly")
    api.labels(number, {"status:" + target(config, "in_progress")}, {n for n in names(issue) if n.startswith("status:")})
    return {"issue": number, "id": task_id(issue, config), "status": target(config, "in_progress"), "instruction": "Status verified. Implementation may begin."}


def release(store, number):
    state, sha = store.read(optional=True)
    legacy(state)
    if state.get("active") and state["active"]["issue"] != number:
        raise ValueError("Another task owns the execution slot")
    if state.get("active"):
        from .timing import end_work
        end_work(state, number)
        state["active"] = None
        store.write(state, sha)


def next_task(api, config, store):
    state, sha = store.read(optional=True)
    legacy(state)
    if state.get("active"):
        raise ValueError(f"Finish or explicitly resume #{state['active']['issue']} first")
    run = state.get("run")
    if not run or run["state"] != "running":
        raise ValueError("Start an explicit batch with queue begin")
    tasks = tasks_from_issues(api.issues(), config, state.get('delivery_workflow',{}).get('tasks',{}))
    lookup = {t["number"]: t for t in tasks}
    waiting = []
    for number in run["issues"]:
        task = lookup.get(number)
        if task and (task["archive"] or is_complete(task)):
            continue
        if not task or task.get("phase", task["status"]) != "todo" or task["blocked"] or task["warnings"] or dependency_problems(task, tasks):
            waiting.append(number)
            continue
        return start(api, config, store, number)
    if waiting:
        return {"state": "waiting", "issues": waiting, "instruction": "Blocked, missing or moved tasks require review. No Backlog tasks were added."}
    run["state"] = "complete"
    run["completed_at"] = now()
    store.write(state, sha)
    return run
