# Exchange tap: exclusive server-named queue bound to an existing exchange

Date: 2026-07-06
Status: Proposed

## Context

The `listen` CLI command (the first real operator-facing sub-command, see
[07-cli-on-bat-scaffold.md](0000-foundational/07-cli-on-bat-scaffold.md))
must observe messages flowing through an exchange and print them as they
pass. The record path defined in
[04-record-replay-scope.md](0000-foundational/04-record-replay-scope.md)
has the same need: it "binds a fresh queue to the target exchange —
recording is observational and must avoid disturbing the application's own
consumers." ADR 04 fixes the *scope* (attach to existing topology, do not
rebuild it) but not the *mechanism* of attachment.

The mechanism must satisfy:

- **Observational** — a tap must never compete with the application's real
  consumers for messages. Consuming from an application queue would steal
  deliveries.
- **Self-cleaning** — a monitoring session that ends (including by crash or
  Ctrl-C) must not leave topology behind on the broker, and must not
  accumulate unconsumed messages while no listener is attached.
- **Concurrent-safe** — two operators tapping the same exchange at once
  must each get their own copy of the stream, without name collisions.

## Decision

A tap attaches to an existing exchange by declaring its own
**server-named, exclusive queue** and binding it to the target exchange:

- `queue_declare(queue='', exclusive=True)` — the empty name asks the
  broker to generate a unique queue name; `exclusive=True` restricts the
  queue to this connection and the broker deletes it automatically when
  the connection closes.
- `queue_bind(queue=<server-named>, exchange=<target>, routing_key=<key>)`
  — the binding key is caller-supplied; its semantics depend on the
  exchange type (ignored by `fanout`, exact-match for `direct`, pattern
  for `topic`).
- The tap **does not declare the exchange**. Per ADR 04 the operator owns
  the topology; tapping a non-existent exchange is an error surfaced to
  the user, not silently repaired.

The upcoming `Reader` class implements this mechanism, and the record path
(ADR 04) is expected to reuse it.

## Options considered

### Consume from an existing application queue

- [pro] No new topology at all; simplest possible attach.
- [con] Destructive observation: every message the tap consumes is a
  message the application's consumer never sees. Round-robin delivery
  splits the stream between tap and application unpredictably.
- [con] Requires the operator to know internal queue names rather than the
  exchange, which is the natural monitoring surface.

### Named, durable monitor queue

- [pro] Survives reconnects; a recording session can resume where it left
  off.
- [con] Leaks topology: the queue outlives the session and must be cleaned
  up by hand. While no listener is attached it accumulates every message
  published to the exchange, growing without bound on the broker.
- [con] Fixed name collides when two operators monitor the same exchange.

### Server-named exclusive queue (chosen)

- [pro] Broker-generated name cannot collide; each tap gets an independent
  copy of the stream.
- [con] Live-only: messages published before the tap attaches, or after it
  disconnects, are never seen. Acceptable — a monitor observes from "now",
  and ADR 04 already scopes recording as attach-and-stream, not replay of
  broker history.
- [pro] Exclusive queues are deleted by the broker on connection close —
  crash, Ctrl-C, and clean exit all leave zero residue, with no cleanup
  code path to maintain.

## Rationale

The tap exists to *observe without disturbing* — that rules out consuming
from application queues outright. Between a durable monitor queue and an
exclusive server-named one, the exclusive queue wins on every property the
use case actually has: monitoring is inherently a live, session-scoped
activity, so durability buys nothing while costing unbounded broker growth
and manual cleanup. Letting the broker own both the queue's name and its
lifetime is the smallest mechanism that is simultaneously observational,
self-cleaning, and concurrent-safe. This also keeps the tap consistent
with ADR 04's stance that Casablanca attaches to topology it does not own.

## Consequences

- The `Reader` (and later the recorder) sees only messages published while
  its connection is open. Tests and docs must sequence
  "attach, then publish" — publishing first drops the message silently
  (fanout with no bound queue routes nowhere).
- The binding key's meaning varies by exchange type; the CLI must document
  that `--routing-key` is a *binding* key (`#` catches everything on a
  `topic` exchange; the value is ignored on `fanout`).
- Tapping a missing exchange fails loudly; `listen` gains a natural
  precondition error instead of a silent no-message hang.
- One tap = one connection-scoped queue: long-lived monitoring across
  reconnects would need a different mechanism (the rejected durable
  queue), which would require a superseding ADR if that use case appears.
