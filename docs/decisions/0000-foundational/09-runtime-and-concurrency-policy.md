# Runtime and concurrency policy: Python 3.10–3.14, free-threading as a deferred constraint

Date: 2025-12-07
Status: Accepted

## Context

Casablanca's replay path is intended to support parallel workers for
high-throughput delivery (the README describes `--parallel-workers`).
Python's free-threaded (no-GIL) builds change the concurrency story for such
workloads. The project must state, up front, which Python runtimes it
targets and whether free-threading is a real constraint on the design or
merely an aspiration.

## Decision

- **Target Python 3.10 through 3.14.** `requires-python = '>=3.10'`, with
  classifiers for 3.10–3.14.
- **Free-threading is a real design goal, deferred.** The "Free Threading"
  classifier is declared intentionally. For now the constraint is the weak
  form: **the code must not break under free-threaded Python.** Actively
  *exploiting* no-GIL parallelism (e.g. in the parallel-replay path) is
  deferred until the record/replay core exists.

## Options considered

### Pin to a single Python version

- [pro] Simplest support matrix; can use the newest syntax freely.
- [con] Too narrow for a developer tool meant to slot into many projects'
  CI; forecloses the free-threading direction.

### Claim free-threading support now, build for it now

- [pro] Forces no-GIL-correct design from day one.
- [con] Premature: the concurrent path (parallel replay) does not exist yet.
  Designing for it before the core is built is speculative and would slow
  delivery of the actual product.

### Broad version support, free-threading deferred (chosen)

- [pro] Wide compatibility for a tool used across many environments;
  free-threading kept as an explicit, on-the-record goal without blocking
  current work. Avoids designing in anti-no-GIL patterns now.
- [con] The free-threading claim is partly aspirational until verified;
  "doesn't break" must be checked, and full exploitation is future work.

## Rationale

Casablanca is a developer/testing tool expected to run in diverse
environments, so broad version support is worth the cost. Free-threading is
genuinely on the roadmap because the replay path is inherently parallel, but
committing engineering to it before the core exists would be premature. The
honest current position is "keep the door open and don't regress," not
"optimized for no-GIL."

## Consequences

- CI should include a free-threaded interpreter to verify the "does not
  break" guarantee as the codebase grows.
- The parallel-replay implementation, when built, must be designed to be
  free-threading-safe and is the place where no-GIL is actually exploited.
- New dependencies should be checked for free-threading compatibility before
  adoption, since an incompatible mandatory dependency would undermine the
  goal.
- Code may use Python 3.10+ syntax (e.g. `X | None` unions) but must not
  rely on features newer than 3.10 without raising the floor.
