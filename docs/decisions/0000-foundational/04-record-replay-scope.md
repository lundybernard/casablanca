# Record/replay scope: no topology rebuild, full-speed replay

Date: 2025-12-07
Status: Accepted

## Context

"Record and replay RabbitMQ messages" could mean many things, from a thin
message tap to a full broker-state snapshot-and-restore tool. The scope of
the first iteration must be pinned down, because it determines what the
capture format carries (see
[03-capture-format.md](03-capture-format.md)) and how much of the broker's
topology Casablanca is responsible for.

The primary use case is writing end-to-end tests for applications that use
RabbitMQ: capture a representative message stream once, replay it into a
test broker on demand.

## Decision

Scope the first iteration deliberately narrowly:

- **Record** by pointing Casablanca at an exchange that **already exists**.
  It binds a *new* queue to that exchange and attaches a handler that
  records messages off that queue into a recording file.
- **Replay** by publishing recorded messages to an exchange (creating it if
  needed, or publishing to an existing one). Replay uses each record's
  stored `routing_key` and `exchange`.
- **Do not rebuild topology.** Casablanca does not snapshot or recreate the
  full exchange/queue/binding graph. The operator is responsible for the
  topology under test; Casablanca attaches to it.
- **No timing fidelity.** Messages replay at full speed in recorded order.
  Original inter-message timing is not captured or reproduced.

## Options considered

### Full topology snapshot and restore

- [pro] A recording would be self-contained: replay could stand up the
  entire broker layout from scratch.
- [con] Large scope; duplicates infrastructure-as-code/broker-definition
  tooling RabbitMQ already provides. Not needed for the e2e-testing use
  case, where the application under test declares its own topology.

### Timing-faithful replay

- [pro] Could reproduce load patterns and timing-sensitive behaviour.
- [con] Requires capturing timestamps and a scheduler on replay. For most
  testing scenarios full-speed is sufficient; timing adds cost with no
  immediate payoff.

### Attach-to-existing, full-speed (chosen)

- [pro] Smallest thing that serves e2e testing: tap an existing exchange,
  capture a stream, fire it back fast. Minimal moving parts.
- [con] Recordings are not self-contained — replaying assumes a compatible
  exchange exists or can be created. No load/timing reproduction.

## Rationale

The product boundary is set by the primary use case. For e2e tests, the
application under test owns its topology; Casablanca only needs to inject a
known message stream, and full-speed delivery is enough to exercise message
handling. Excluding topology rebuild and timing keeps the first iteration
small and focused, and both can be added later without invalidating the
attach-and-stream model.

## Consequences

- Replay targets must exist or be creatable; a recording is not a complete
  broker definition.
- The record path binds a fresh queue to the target exchange — recording is
  observational and must avoid disturbing the application's own consumers.
- Timing-sensitive behaviour cannot be reproduced yet; adding it later
  means extending the capture format (ADR 03) and adding a replay
  scheduler. Both are flagged as future work, not v1.
- `--delay` / `--parallel-workers` style controls described in the README
  are replay-pacing conveniences layered on top of full-speed delivery, not
  reconstruction of recorded timing.
