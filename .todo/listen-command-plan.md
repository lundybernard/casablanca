# Plan: `casablanca listen` — monitor messages through an exchange

Status: planned, not started. Written 2026-07-06.
First real user-facing CLI sub-command; first piece of the operator CLI.

## Goal

```
casablanca listen <exchange> [--routing-key KEY] [--count N]
```

Attach a reader to an exchange and print each message body to stdout as it
passes through. Runs until Ctrl-C, or exits after `N` messages when
`--count` is given (`--count` also makes the e2e test bounded and
deterministic).

## Decisions already made

- **Attach mechanism**: server-named exclusive queue bound to the target
  exchange — see ADR
  [0002-exchange-tap-exclusive-queue.md](../docs/decisions/0002-exchange-tap-exclusive-queue.md)
  (Proposed; accept with this PR). The reader does *not* declare the
  exchange (ADR 04: operator owns topology).
- **API shape** (approved in design discussion):

  ```python
  reader = client.new_reader(exchange='my.exchange', routing_key='#')
  reader.run(on_message=print)   # blocks; count/interrupt stops it
  ```

  Mirrors the `new_publisher` / `Publisher` precedent in `client.py`.

## ADR fit (reviewed 2026-07-06)

- **01 two-transport** — listen is message I/O → AMQP/`pika` side. Fits.
- **02 wrap-external-deps** — `Reader` wraps `channel.consume(...)`;
  mock at the underscore-aliased seam. The e2e `test_publisher` TODO
  ("wrap the direct channel manipulation") also covers the
  `queue_declare`/`queue_bind` calls Reader needs — Reader wraps them
  internally, shrinking that gap.
- **04 record/replay scope** — tap mechanism is the same one the future
  record path needs; building it for listen is a stepping stone, not a
  detour.
- **05 OO resource interface** — reader handle built by the client
  factory method; lazy channel via existing `cached_property` chain.
- **07 CLI on BAT scaffold** — `listen` becomes the first real
  sub-command (module-level sub-CLI pattern per the `example` module).
- **08 testing strategy** — **amended 2026-07-06**: original record
  missed the in-process integration layer (`tests/integration/` — real
  internal collaborators, only vendor seams stubbed, no fake broker).
  Amended in place rather than superseded (early-stage exception,
  applied sparingly). Plan below follows the amended record.
- **09 runtime** — blocking consume is fine; parallel consumption out of
  scope.

**New ADR needed: yes — written.** ADR 0002 records the tap mechanism
(was undocumented). ADR 08 amended with the integration layer.

## Prerequisites (before Loop 1)

### 1. Scaffold residue blocks stdout

`Commands.set_log_level` prints `conf` and `log.level` to stdout on every
CLI run (flagged as residue in ADR 07 Consequences). `listen`'s contract
*is* its stdout — the e2e test asserts on it — so this residue breaks the
feature. Remove the two `print()` calls (own RED/GREEN cycle: fix the
existing `cli_test.py` expectations first).

### 2. Backfill the integration layer (new `tests/integration/`)

The listen descent is e2e → integration → unit; the integration rung
does not exist yet. Build it against the *existing, green* surface first
(characterization — no design risk), so the feature loops extend a
proven harness instead of inventing one mid-descent:

- `tests/integration/client_test.py` — Client's public contract with
  real internal collaborators (Publisher, Exchange, ExchangeManager)
  wired together; patch **only** the underscore vendor aliases
  (`casablanca.client._BlockingConnection`,
  `casablanca.manager._ManagementApi`) with `autospec`, minimal stub
  returns. State verification. Cover: `from_config`, `publish`,
  `read_one`, `get_queue_length`, `new_publisher`, `exchanges` cache,
  `manager`.
- `tests/integration/lib_test.py` — pattern stub for `lib`'s contract
  (only `hello_world` today; real value arrives with `lib.listen`).

No fake broker: stubs encode our vendor assumptions, `autospec` pins
signatures, the e2e layer proves the assumptions against real RabbitMQ
(ADR 08 as amended). Own commit, separate from feature work.

## TDD plan — outside-in N-loop

One requirement per cycle; red for the right reason before green;
refactor only when green. Layers per `/tdd` + `/python-style` and
ADR 08 (as amended): e2e in `tests/e2e/`, integration in
`tests/integration/` (real internals, stubbed vendor seams), units
co-located in `casablanca/tests/`.

### Loop 1 — outer red: e2e CLI test

`tests/e2e/cli_test.py` (new file; reuse the session `rabbitmq` fixture —
move/share it via `tests/e2e/conftest.py` if needed):

1. Declare exchange via `client.exchanges[ex].declare()` (operator-owned
   topology; listen must find it existing).
2. Spawn `casablanca listen <ex> --routing-key <key> --count 2` as a
   subprocess. Config reaches it via `CASABLANCA_RABBITMQ_*` env vars
   (batconf `EnvConfig` — verified working). Include `PORT`/`ADMINPORT`
   from the container.
3. Wait for a readiness line on stdout (e.g. `listening on <ex>`,
   flushed) — binding must exist *before* publishing or messages route
   nowhere (ADR 0002 consequence).
4. Publish two text messages via `client.new_publisher(...)`.
5. Assert: process exits 0 within timeout; stdout contains both bodies.

Red for the right reason: argparse error — no `listen` command.

### Loop 2 — descend: lib e2e test

`tests/e2e/lib_test.py` (new): `lib.listen(...)` exercised as a library
consumer would, against the real container — declare exchange, run
`lib.listen` with `count` bounded (in a thread, or capture stdout via
`capsys`), publish, assert printed bodies. This is the public-API
behavioral contract: `listen` must be usable from Python without the
CLI (BAT principle — functions are the public API, CLI is one consumer).

Red: `AttributeError` — `lib.listen` does not exist.

### Loop 3 — descend: CLI layer unit tests

`casablanca/tests/cli_test.py`:

- `argparser()` parses `listen <exchange> --routing-key K --count N`
  into the expected namespace; `func` bound to `Commands.listen`.
- `Commands.listen` calls `lib.listen(cfg, exchange=..., routing_key=...,
  count=...)` — patch `lib.listen` at the `casablanca.cli` import seam,
  extend `validate_commands` / `test_commands` for the new command.

Implementation: sub-command wired in `cli.py` (own module sub-CLI only if
listen grows sub-commands — YAGNI says flat parser entry for now),
`Commands.listen` staticmethod delegating to `lib.listen`.

### Loop 4 — descend: lib integration test

`tests/integration/lib_test.py` (backfilled in prerequisite 2):
`lib.listen` contract with the *real* Client/Reader wired together,
vendor seams stubbed — `_BlockingConnection`'s mock channel configured
so `queue_declare` returns a server-named queue frame and `consume`
yields message tuples; assert the bodies are printed and the run
terminates at `count`. State verification — no call-order assertions
on internals.

### Loop 5 — descend: lib layer unit tests

`casablanca/tests/lib_test.py` (new — `lib.py` currently has only
`hello_world`). `lib.listen(cfg, exchange, routing_key, count)`:

- builds `RabbitmqClient.from_config(cfg.rabbitmq)` (patch
  `RabbitmqClient` at the `casablanca.lib` seam),
- prints the readiness line,
- calls `client.new_reader(exchange=..., routing_key=...)` and
  `reader.run(on_message=print, count=count)` (exact split of
  count-vs-callback responsibility settled when the test is written —
  test-first designs the signature).

`lib.py` stays thin: readable orchestration only, logic lives in Reader.

### Loop 6 — descend: client integration test

`tests/integration/client_test.py` (backfilled in prerequisite 2) gains
the `new_reader` / `Reader` contract: real Client + Reader against the
stubbed vendor channel — declaring the exclusive server-named queue,
binding it, consuming, callback per body, stop at count (ADR 0002
mechanism, verified as observable state/returns).

### Loop 7 — descend: client layer unit tests

`casablanca/tests/client_test.py`:

- `test_new_reader` — mirrors `test_new_publisher`: constructs `Reader`
  with the client's `_channel` and args, returns the instance.
- `ReaderTests` — one `test_<attr>` per public attribute, subTests per
  code path, `create_autospec(_BlockingChannel)` like `PublisherTests`:
  - declares server-named exclusive queue
    (`queue_declare(queue='', exclusive=True)`), binds the broker-returned
    name to the exchange with the routing key (ADR 0002),
  - `run(on_message)` iterates `channel.consume(...)`, invokes callback
    per body,
  - stops after `count` messages: `channel.cancel()`,
  - `KeyboardInterrupt` during consume → `cancel()` + clean exit
    (Ctrl-C path).

Implementation in `client.py` beside `Publisher`. `pika`'s
`channel.consume` generator (pull style) over `basic_consume` callback
(push style): unit tests iterate a plain mocked iterable, no
`start_consuming` loop to fake, and `cancel()` is the documented exit.

### Loop 8 — ascend & refactor

Green each layer bottom-up: units → integration → lib e2e → CLI e2e.
Full gate: `nox -s parallel -- -q` (100% unit coverage enforced).
Refactor pass while green — candidates: shared readiness-line constant,
`Publisher` / `Reader` symmetry.

## Out of scope (goes to todo.md if it itches)

- Message properties/headers in output (plain bodies only — "text-only,
  nothing fancy").
- Output formats (JSON lines etc.) — that's the recorder's job, ADR 03.
- Reconnect/resume (rejected durable-queue option, ADR 0002).
- Non-blocking channel types (already in todo.md for Publisher).

## Acceptance

- `casablanca listen <ex> --count 2` prints two published bodies, exit 0.
- `lib.listen(...)` does the same as a plain library call (no CLI).
- Ctrl-C exits cleanly, no traceback, broker left clean (exclusive queue
  auto-deleted).
- `tests/integration/` exists with Client + lib contracts (backfill plus
  the listen additions), in-process only, no container required.
- All layers green, coverage gate holds, ADR 0002 flipped to Accepted on
  merge.
