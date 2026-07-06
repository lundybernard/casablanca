<!--
Project todo list. Same item format/hierarchy as the global system
(~/todo/SCHEMA.md), simplified:
- [CAT:name] replaces category-per-file.
- No DUE/BUMPED/REPEAT — priority alone drives order, one-time tasks.
- No time-window filtering, no daily bump.
- P: priority, higher = more urgent. LOE: 1/2/3/5/8 effort. TAGS: optional.

Purpose: catch things noticed mid-development that are out of scope for
the current change, so they aren't lost or forced in prematurely.

On completion: log to completed.md, remove block from Open section.
-->

## Open

- [ ] Allow Publisher to use non-blocking channel types (not just pika BlockingChannel) [CAT:feature] [P:3] [LOE:3]
      Publisher currently typed to `_BlockingChannel`. Generalize once a
      non-blocking use case shows up (e.g. SelectConnection/async channel).

- [ ] Extend rootless-Podman conftest auto-detection to feature_tests/ [CAT:infra] [P:2] [LOE:1]
      tests/e2e/conftest.py (see ADR 0001) only covers tests/e2e/. If
      feature_tests/ becomes live again it needs the same DOCKER_HOST /
      TESTCONTAINERS_RYUK_DISABLED auto-detection or Podman won't be picked
      up there.

- [ ] Write fix for pixi#3741 upstream [CAT:oss] [P:3] [LOE:5]
      github.com/prefix-dev/pixi issue #3741 - repodata shard cache files
      written 0600 (ignores umask), breaks shared multi-user cache dirs.
      Confirmed on this box; worked around locally via chmod in
      /projects/.envrc. rattler#43/PR#1003 (layered cache) is unrelated -
      different problem, already merged. No PR against pixi/rattler yet.
