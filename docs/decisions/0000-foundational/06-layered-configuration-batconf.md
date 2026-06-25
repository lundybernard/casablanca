# Layered configuration via batconf: CLI > env > ini

Date: 2025-12-07
Status: Accepted

## Context

Casablanca runs in several contexts — local development, CI/e2e, and (in
future) as a CLI against live brokers. Each context supplies broker
connection details differently: a developer edits a file, CI injects
environment variables, an operator passes command-line flags. Configuration
must resolve consistently across all three from a single schema.

## Decision

Use `batconf` to compose configuration from a **prioritized list of
sources**, highest priority first:

1. **CLI arguments** (`NamespaceConfig` over the parsed argparse namespace)
2. **Environment variables** (`EnvConfig`)
3. **Config file** (`IniConfig`, `config.ini` by default)

A single `ConfigSchema` dataclass defines the shape (`rabbitmq`,
`loglevel`); `get_config()` builds the `SourceList` and returns a
`Configuration` rooted at the `casablanca` path. A source contributes a
value only if higher-priority sources did not.

**`config.ini` is the canonical config-file format.** Earlier YAML examples
(`example.config.yaml`) are dropped to avoid the extra YAML dependency.

## Options considered

### A single source (file only, or env only)

- [pro] Simplest to reason about; one place to look.
- [con] Cannot serve dev, CI, and CLI at once. Forces awkward overrides
  (e.g. editing committed files in CI, or exporting everything locally).

### Bespoke layering logic

- [pro] No external config dependency.
- [con] Reinvents source precedence, type coercion, and nested-path
  resolution that `batconf` already provides and that is shared with the
  author's other projects.

### batconf prioritized SourceList — CLI > env > ini (chosen)

- [pro] One schema, three sources, deterministic precedence. Matches how the
  three contexts actually supply config: flags win for one-off operator
  overrides, env for CI, file for local defaults.
- [con] Adds the `batconf` dependency and its conventions; contributors must
  learn the source-list model.

### YAML config files

- [pro] More expressive/nested than ini; familiar to many.
- [con] Pulls in a YAML parser dependency for no benefit at this config
  size. Dropped in favour of `config.ini`.

## Rationale

`batconf` is the author's configuration library and is reused here rather
than hand-rolling precedence. Standardising on ini removes the YAML
dependency — this part is confirmed.

The CLI > env > ini ordering maps cleanly onto how the three contexts
supply config: command-line flags are the most specific and deliberate, so
they win; environment variables suit CI injection; the ini file holds local
defaults. **Inference, not confirmed:** whether this ordering was chosen
deliberately for that reason or inherited as `batconf`'s default was not
established; the precedence itself is a code fact (`get_config()` builds the
source list in that order), the motivation above is a post-hoc reading.

## Consequences

- `config.ini` is the file format going forward; YAML examples should be
  removed or converted (`example.config.yaml`, README references to
  `config.yaml`).
- New configuration is added by extending `ConfigSchema`; all three sources
  resolve it automatically.
- Tests wire config through `get_config()` (see the e2e suite overriding
  `cfg.rabbitmq` from container info), keeping production and test
  resolution paths identical.
- The `batconf` dependency is mandatory (declared in `pyproject.toml`),
  unlike the optional dev/docs groups.
