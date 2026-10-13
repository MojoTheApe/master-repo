# Project Workflow source and team distribution

Master Repo owns the canonical `.agents/skills/project-workflow/` directory.
The team's [AI Skills library](https://github.com/MojoTheApe/ai-skills) publishes a
read-only mirror and packages it as a Codex plugin. Library-owned skills, including
Agency Builder and AIO, are authored directly in AI Skills; they need no project copy.

When changing standards, templates, process guidance, compatibility or their
implementation, assess the effect on Project Workflow. Update the skill and its
affected references in the same PR when instructions change. Otherwise record a
concrete reason why the existing skill still applies. Use these exact PR-body lines:

```text
Project Workflow impact: updated
Project Workflow reason: Explain the changed instruction and why it is needed.
```

Or select `no-impact` with a concrete reason. CI requires one assessment and checks
whether a declared skill update exists. Independent review evaluates its meaning;
CI does not interpret architecture or generate skill prose.

After reviewed main integration, the library checks this source periodically,
copies the complete directory at an immutable approved revision, validates its
contents and applies it through an automated library PR. The library generates a
new plugin version when its contents change. Employee updaters receive it through
their configured Codex catalog; source credentials remain in the library's CI.
The current source is public, so synchronization needs no token with cross-repository
write access. The source repository does not push into the private library.

Consumer descriptors, standards pins, Tracker engines and deployment settings are
unchanged. A new navigation skill continues to follow each project's adopted rules.
This distribution is not a standard release, consumer upgrade or runtime deployment.
