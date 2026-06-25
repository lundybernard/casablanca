# CLI on the BAT scaffold

Date: 2025-12-07
Status: Accepted

## Context

Casablanca ships a command-line entry point (`casablanca = casablanca.cli:BATCLI`)
and is intended to grow into a tool for interacting with live RabbitMQ
services — driving record/replay, and supporting manual testing and live
demos against containerized brokers.

Rather than design a CLI from scratch, the project is scaffolded from the
author's reusable "BAT" CLI template, which establishes a consistent
structure across the author's tools.

## Decision

Adopt the BAT scaffold for the CLI:

- **`BATCLI` entry point** — parses args, builds config via `get_config()`,
  sets log level, dispatches to the function bound to the parsed
  sub-command.
- **Static `Commands` class** — sub-commands are static methods on a
  `Commands` class; argparse `set_defaults(func=...)` binds each parser to
  its handler.
- **Modular sub-CLIs** — a sub-command can be a self-contained argparse
  parser contributed from its own module and attached via `parents=[...]`.
  The `example` module currently demonstrates the sub-CLI pattern. (Whether
  it is retained long-term as a copy-me template or eventually removed was
  not confirmed; see Consequences.)
- **Nested argparse namespace** — `NestedNameSpace` lets flags target
  dotted config paths (e.g. `casablanca.loglevel`), feeding the config
  layer (see [06-layered-configuration-batconf.md](06-layered-configuration-batconf.md)).

## Options considered

### Hand-rolled argparse, no template

- [pro] No inherited conventions or unused scaffolding.
- [con] Reinvents sub-command dispatch, config wiring, and log-level
  handling that the BAT template already standardises across the author's
  tools.

### A third-party CLI framework (e.g. click/typer)

- [pro] Ergonomic decorators, less boilerplate.
- [con] New dependency and a different idiom from the author's other BAT-
  based tools; the scaffold already integrates with `batconf` and the
  nested-namespace config path.

### BAT scaffold (chosen)

- [pro] Consistent structure with the author's other tools; config, logging,
  and modular sub-CLI patterns come built in. The `example` module documents
  the extension pattern by example.
- [con] Carries template scaffolding that must be built out or cleaned up;
  some artifacts arrive stale and need attention before they work.

## Rationale

The CLI is expected to become a real operator tool (live-service
interaction, demos), so starting from the proven BAT structure is cheaper
than designing dispatch/config/logging from scratch and keeps Casablanca
consistent with the author's other tools — this is the confirmed rationale.
The fate of the `example` sub-CLI (kept as a copy-me template vs. removed as
scaffolding) is an open question flagged in Consequences, not a settled
decision.

## Consequences

- **Open question:** decide the `example` module's fate — retain it as a
  pattern reference that new sub-commands copy, or delete it as scaffolding
  once a real sub-command exists. Until decided, it serves as the working
  example of the sub-CLI shape.
- **Scaffold cleanup is owed.** Template artifacts inherited from BAT are
  stale and must be fixed as the CLI is built out — notably the container
  setup, which still references the old `bat` project rather than
  `casablanca`:
  - `dockerfile` uses `python:3.8-alpine`, runs
    `python -m unittest discover bat.tests`, and `CMD ["start"]` — none of
    which match this project (Python 3.10–3.14, pytest, no `bat` package, no
    `start` command).
  - The docker setup is intended for future containerized tests and live
    demos (see test/runtime ADRs) and must be updated to target
    `casablanca` before it works again.
- `set_log_level` currently prints debug output (`print(conf)`,
  `print(log.level)`) — scaffold residue to clean up.
