"""Normalize GitHub data without inferring task completion from checkboxes."""
from __future__ import annotations

import json
import re
from pathlib import Path
from . import identifiers
from . import workflow
from . import delivery_policy
from . import historical_completion

STATUSES = ("idea", "backlog", "todo", "in_progress", "review", "merged")
PRIORITIES = ("high", "medium", "low")
TYPES = ("bug", "feature", "improvement", "research", "operations")
LABELS = {"idea": "Idea", "backlog": "Backlog", "todo": "Todo", "in_progress": "In progress", "review": "Review", "merged": "In master"}
DEFAULT_CONFIG = Path(__file__).with_name("config.json")


def load_config(path=DEFAULT_CONFIG):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("schema_version") not in (2, 3):
        raise ValueError("Expected tracker config schema 2 or 3")
    workflow.validate(config)
    delivery_policy.execution_policy(config)
    if 'task_context_policy' in config:
        delivery_policy.context_module().policy(config)
    if 'process_instructions' in config:
        delivery_policy.process_module().policy(config)
    if 'ci_evidence_policy' in config:
        from .ci_evidence import policy
        policy(config)
    project = config["project"]
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", project["repository"]):
        raise ValueError("Invalid repository")
    if not project.get("base_branch") or not project.get("name"):
        raise ValueError("Project name and base branch are required")
    identifiers.validate(config)
    historical_completion.validate(config)
    if config.get('release_mode', 'legacy') not in ('single', 'legacy'):
        raise ValueError('Unknown release membership mode')
    ids = [m["id"] for m in config["modules"]]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r"[a-z][a-z0-9_-]*", x) for x in ids):
        raise ValueError("Module IDs must be unique stable names")
    if 'unclassified' in ids:
        raise ValueError('Unclassified is reserved for unresolved module classification')
    if any(not isinstance(m.get('name'), str) or not m['name'].strip() or not isinstance(m.get('description'), str) for m in config['modules']):
        raise ValueError('Every module needs a name and description')
    if tuple(config.get("priorities", [])) != PRIORITIES:
        raise ValueError("Priorities must be high, medium, low")
    if not 15 <= config.get("refresh_seconds", 60) <= 3600:
        raise ValueError("Refresh interval must be between 15 and 3600 seconds")
    return config


def names(issue):
    return {x["name"] if isinstance(x, dict) else x for x in issue.get("labels", [])}


def one(labels, prefix, allowed, warnings):
    found = sorted(x[len(prefix):] for x in labels if x.startswith(prefix))
    if len(found) == 1 and found[0] in allowed:
        return found[0]
    if found:
        field = prefix.rstrip(':')
        warnings.append(('Conflicting ' + field + ' labels: ' if len(found)>1 else 'Unknown ' + field + ': ') + ', '.join(found))
    return ""


def dependencies(body, repo):
    return delivery_policy.dependencies(body, repo)


def tasks_from_issues(issues, config, delivery_tasks=None):
    modules = {m["id"] for m in config["modules"]}
    repo = config["project"]["repository"]
    tasks = []
    policy = delivery_policy.policy(config)
    historical = historical_completion.validate(config)
    for issue in sorted(issues, key=lambda x: x["number"]):
        if "pull_request" in issue or "tracker:control" in names(issue):
            continue
        labels, warnings = names(issue), []
        status = one(labels, "status:", [s['id'] for s in workflow.stages(config)], warnings)
        # Transitional read compatibility never hides an unmigrated task.
        if not status:
            old = {x for x in labels if x.startswith("status:")}
            if old in ({"status:next"}, {"status:later"}, {"status:blocked"}):
                status = next((s['id'] for s in workflow.stages(config) if s['phase']=='backlog'), workflow.target(config,'idea'))
            elif old == {"status:shipped"}:
                status = workflow.target(config, 'merged')
            else:
                status = workflow.target(config, 'idea')
                if not old:
                    warnings.append("Needs a status")
        module = one(labels, "module:", modules, warnings)
        if not module:
            warnings.append("Needs a module")
        priority = one(labels, "priority:", PRIORITIES, warnings)
        kind = one(labels, "type:", TYPES, warnings)
        body = issue.get("body") or ""
        context_valid = True
        if 'task_context_policy' in config:
            try:
                delivery_policy.context_module().requirements(body)
            except ValueError as error:
                warnings.append('Invalid task journal: ' + str(error))
                context_valid = False
        task_phase = workflow.phase(config, status)
        archive = 'flag:archived' in labels or issue.get("state") == "closed" and task_phase != "merged"
        if issue.get("state_reason") == "not_planned":
            archive = True
        alias = re.match(r"^([a-z][a-z0-9]*-\d+[a-z]?)\s*:\s*", issue["title"], re.I)
        checks = []
        fence = None
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith(("```", "~~~")):
                marker = stripped[:3]
                fence = None if fence == marker else marker if fence is None else fence
            match = re.match(r"^\s*[-*+]\s+\[([ xX])\]\s+(.+)", line)
            if match and not fence:
                checks.append({"done": match[1].lower() == "x", "title": match[2]})
        milestone = issue.get("milestone")
        included = 'release:included' in labels or config.get('release_mode') != 'single' and 'release:required' in labels
        if config.get('release_mode') != 'single' and "release:required" in labels and not milestone:
            warnings.append("Required task needs a release")
        if task_phase == "merged" and any(not c["done"] for c in checks):
            warnings.append("Completed task has unfinished checklist items")
        tasks.append({
            "number": issue["number"], "id": identifiers.task_id(issue, config),
            "title": issue["title"][alias.end():] if alias else issue["title"],
            "body": re.sub(r"(?m)^_Board id:.*$|^<!-- tracker-(?:origin|request): .* -->$", "", body).strip(),
            "url": f"https://github.com/{repo}/issues/{issue['number']}",
            "status": status, "phase": task_phase, "module": module, "priority": priority, "type": kind,
            "design": "facet:design" in labels, "non_code": "resolution:non_code" in labels,
            "blocked": bool({"flag:blocked", "status:blocked"} & labels),
            # required remains a read-only wire alias for already-open v2 tabs.
            "release": bool(included), "required": bool(included), "initiative": "kind:initiative" in labels,
            "archive": archive, "warnings": warnings, "checks": checks,
            "dependencies": dependencies(body, repo),
            "milestone": milestone["number"] if milestone else None,
            "milestone_title": milestone["title"] if milestone else "",
            "created_at": issue.get("created_at", ""), "updated_at": issue.get("updated_at", ""),
            "origins": re.findall(r'<!-- tracker-origin: (https://github\.com/[\w.-]+/[\w.-]+/issues/[1-9]\d*) -->', body),
        })
        if policy:
            receipt = delivery_policy.summary((delivery_tasks or {}).get(str(issue['number']), {}))
            current = (context_valid and receipt.get('policy') == delivery_policy.fingerprint(config)
                       and delivery_policy.scope_matches(issue, receipt.get('reconciled_scope', delivery_policy.task_scope(issue, config)), config))
            admitted = current and receipt.get('admitted', False)
            verified = current and receipt.get('verified', False)
            required = policy['completion'] != 'reviewed-merge' and not (current and (receipt.get('non_code') or receipt.get('process') and receipt.get('verified')))
            accepted_history = historical_completion.accepted(issue, tasks[-1], historical, receipt)
            tasks[-1].update(complete=accepted_history or task_phase == 'merged' and not archive and admitted and (not required or verified),
                             delivery_state=('historical' if accepted_history else 'not-required' if not required and admitted else receipt.get('state', 'pending') if current else 'pending'),
                             delivery_required=required)
    return tasks


def is_complete(task):
    return bool(task.get('complete', task.get('phase', task.get('status')) == 'merged')) and not task.get('archive', False)


def release_summary(tasks, milestone=None):
    required = [t for t in tasks if (milestone is None or t["milestone"] == milestone) and t["required"] and not t["initiative"]]
    lookup = {key: t for t in tasks for key in (t["id"].lower(), f"#{t['number']}")}
    unresolved = []
    for task in required:
        for dep in task["dependencies"]:
            item = lookup.get(dep.lower())
            if not item or not is_complete(item):
                unresolved.append({"task": task["number"], "dependency": dep})
    complete = sum(is_complete(t) for t in required)
    blocked = sum(t["blocked"] for t in required)
    return {"total": len(required), "complete": complete, "remaining": len(required) - complete,
            "blocked": blocked, "unresolved": unresolved,
            "ready": bool(required) and complete == len(required) and not blocked and not unresolved
                     and not any(t["warnings"] for t in required)}


def payload(issues, config, milestones=(), queue=None):
    import copy
    queue = copy.deepcopy(queue or {})
    from .batch_delivery import finish
    for batch in queue.get('execution', {}).get('batches', []):
        finish(batch, config)
    active = queue.get('execution', {}).get('integration')
    if active:
        finish(active, config)
    tasks = tasks_from_issues(issues, config, (queue or {}).get('delivery_tasks', {}))
    for task in tasks:
        task["todo_at"] = (queue or {}).get("todo_added", {}).get(str(task["number"]), "")
        execution = (queue or {}).get('execution', {}).get('tasks', {}).get(str(task['number']))
        if execution:
            task['execution'] = execution
        timings = copy.deepcopy(queue.get('timing', {}).get('tasks', {}).get(str(task['number']), {}))
        for kind, row in timings.items():
            if row.get('since') and (task['archive'] or kind == 'implementing' and task['phase'] != 'in_progress'
                    or kind == 'reviewing' and task['phase'] != 'review'
                    or kind == 'merging' and task['phase'] not in ('review', 'approved', 'stage')):
                row.update(since=None, partial=True)
        if timings:
            task['timings'] = timings
    releases = {m["number"]: {"number": m["number"], "title": m["title"]} for m in milestones}
    releases.update({t["milestone"]: {"number": t["milestone"], "title": t["milestone_title"]}
                     for t in tasks if t["milestone"] is not None})
    return {"schema_version": 3, "project": config["project"], "modules": config["modules"],
            "workflow": workflow.stages(config),
            "completion_label": config.get("completion_label", "Merged"),
            "refresh_seconds": config.get("refresh_seconds", 60),
            "release_view_label": "Release",
            "default_release": config.get("default_release", ""), "tasks": tasks,
            "release": {"summary": release_summary(tasks), "history": (queue or {}).get('release_history', []),
                        "transitioning": bool((queue or {}).get('release_rollover'))},
            "milestones": [dict(m, summary=release_summary(tasks, m["number"])) for m in releases.values()],
            "timing_as_of": queue.get('timing', {}).get('as_of'), "queue": queue or {}}
