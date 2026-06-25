# Capture format: JSON-lines, one queue stream per file

Date: 2025-12-07
Status: Accepted

## Context

The core purpose of Casablanca is to record messages off a RabbitMQ queue
and replay them later — primarily to write end-to-end tests for
applications that use RabbitMQ. A persisted recording needs a format that:

- preserves enough of each message to faithfully republish it,
- treats the payload as opaque (payloads range from plain text to JSON to
  binary — a prime case is serialized dataframes),
- streams well (recordings can be long; we should not need the whole file
  in memory to read or write it).

At the time of this decision, none of the record/replay code existed yet;
this ADR fixes the data model the implementation must target.

## Decision

Persist recordings as **JSON-lines**: one JSON object per line, one file
per recorded queue stream.

Each line is a `MessageRecord` with these fields:

- `body_str` — the message payload. The payload is treated as opaque
  content; Casablanca does not interpret it.
- `properties` — the AMQP message properties, wrapped by a
  `MessageProperties` class that serializes the `pika` properties to a
  dumpable `dict`.
- `routing_key` — required to faithfully republish the message to an
  exchange on replay.
- `exchange` — the exchange the message was associated with.

Timing is **not** captured in this iteration (see
[04-record-replay-scope.md](04-record-replay-scope.md)); replay is
full-speed.

## Options considered

### Single JSON array per file

- [pro] One well-formed JSON document; trivial to load with `json.load`.
- [con] Not streamable — the writer must hold/!rewrite the array and the
  reader must parse the whole file. Poor fit for long recordings.

### Binary / pickle

- [pro] Compact; preserves arbitrary Python objects directly.
- [con] Opaque, not human-inspectable, version-fragile, and unsafe to load
  from untrusted sources. Overkill given payloads are already bytes/strings.

### JSON-lines, one queue per file (chosen)

- [pro] Streamable (read/write a line at a time), append-friendly,
  human-inspectable, language-agnostic. One file per queue keeps streams
  cleanly separated.
- [con] Binary payloads must be encoded into a JSON-safe string form within
  `body_str`; the per-message envelope carries some overhead vs. raw bytes.

## Rationale

E2E testing is the primary use, so recordings must be easy to inspect and
diff, and easy to produce/consume incrementally. JSON-lines gives
streamability and inspectability at once. Storing `routing_key` and
`exchange` alongside the opaque `body_str` is the minimum needed to
republish faithfully; `properties` (via `MessageProperties`) preserves
content-type and headers so a typed payload such as a dataframe survives
the round trip. Wrapping the payload as an opaque string keeps the format
content-agnostic, which is a hard requirement.

## Consequences

- `MessageRecord` and `MessageProperties` are the canonical
  serialization types; record and replay both bind to them.
- Binary payloads require an encoding decision inside `body_str` (e.g.
  base64) so they remain JSON-safe; this must be settled when the record
  path is implemented.
- Because timing is not stored, recordings cannot later reproduce original
  cadence without a format revision; adding timing would extend the
  envelope (a forward-compatible change, since unknown/added fields don't
  break a line-oriented reader).
- One file per queue means a multi-queue capture produces multiple files,
  which the CLI/API must orchestrate.
