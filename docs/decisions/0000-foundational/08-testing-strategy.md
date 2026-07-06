# Testing strategy: 100% unit coverage, import-seam mocking, in-process integration, testcontainers e2e

Date: 2025-12-12
Amended: 2026-07-06 — added the in-process integration layer, missed in
the original record (edited in place rather than superseded; the project
is early enough that amendment beats a superseding record, applied
sparingly)
Status: Accepted

## Context

Casablanca talks to an external broker, so its tests must distinguish logic
that can be verified in isolation from behaviour that only a live RabbitMQ
can confirm. The project also enforces a strict quality bar and wants tests
that are fast by default but able to exercise the real broker when needed.

## Decision

A layered test strategy with a hard coverage gate:

- **100% unit coverage gate.** `fail_under = 100` in `pyproject.toml`. Unit
  tests must cover every line; the build fails otherwise. Coverage is
  measured over `casablanca` with term + xml reports.
- **Co-located unit tests.** Unit tests live beside the code under
  `casablanca/tests/` (e.g. `manager_test.py` for `manager.py`). They
  require **no** live broker.
- **Mock at the import seam with `autospec`.** Tests patch the
  underscore-aliased external symbols (e.g. `casablanca.manager._ManagementApi`)
  using `patch(..., autospec=True)`, set up in `setUp` and torn down via
  `addCleanup`. This pins mocks to the real vendor signature and exploits
  the seams established in
  [02-wrap-external-dependencies.md](02-wrap-external-dependencies.md).
- **In-process integration tests: real modules, mocked vendor seams.**
  `tests/integration/` exercises each module's public contract with its
  *real* internal collaborators wired together (Client + Publisher +
  Exchange + ExchangeManager); **only** the underscore-aliased vendor
  symbols (`_BlockingConnection`, `_ManagementApi`, …) are patched, with
  `autospec`, configured with minimal stub returns. No fake broker is
  built — reimplementing AMQP routing would amount to testing `pika`,
  which is not our responsibility; the e2e layer validates the vendor
  assumptions the stubs encode. State/return-value verification
  (Detroit style), one test per public attribute/method, subTests per
  code path. Runs fully in-process, no container.
- **Outside-in e2e/feature tests against a real broker.** `tests/e2e/` and
  `feature_tests/` spin up RabbitMQ via `testcontainers`
  (`RabbitMqContainer('rabbitmq:3-management')`) and exercise the real
  publish/consume/management paths.
- **Inheritable shared test bodies.** Common API assertions live in a
  reusable mixin (`CommonAPITest`) so the same checks run against both a
  local service and a containerized one.
- **House test idioms.** `unittest.TestCase` with `t` as the instance
  parameter (not `self`), `subTest` per code path, and pytest configured to
  collect `*_test.py` / `*Tests` classes.

## Options considered

### A single mixed test suite requiring a live broker

- [pro] Tests exercise real behaviour end to end; no mocking.
- [con] Slow, requires infrastructure to run anything, and can't pinpoint
  logic errors. Unsuitable as the default inner-loop suite.

### Unit tests only, no e2e

- [pro] Fast; no container/runtime dependency.
- [con] Never verifies the integration with the real broker — exactly where
  a record/replay tool is most likely to break.

### In-process fake broker for the middle layer

- [pro] Integration tests could verify routing behaviour (bindings,
  routing keys) without a container.
- [con] A faithful fake reimplements AMQP semantics — large maintenance
  surface, and its correctness itself needs testing. Verifying vendor
  behaviour is `pika`/`amqpstorm`'s job, confirmed by the e2e layer.

### Layered: 100%-covered units + seam-mocked integration + testcontainers e2e (chosen)

- [pro] Fast, total-coverage inner loop with mocked seams, plus real-broker
  confidence on demand. The coverage gate forces every branch to be
  exercised; the seams from ADR 02 make mocking precise.
- [pro] The integration layer catches cross-module wiring errors units
  cannot see (units mock the very collaborators integration wires
  together), still without container cost.
- [con] The 100% gate has upkeep cost and can pressure toward trivial tests;
  e2e needs Docker/testcontainers available.
- [con] Seam stubs encode our assumptions about vendor behaviour and can
  drift; `autospec` pins signatures and e2e pins semantics, but the drift
  window between e2e runs is real.

## Rationale

The wrapped-dependency seams (ADR 02) make a 100% unit gate achievable
without a live broker, because every external call is mockable at a stable
point. `autospec` keeps those mocks honest against vendor signatures. The
integration layer reuses the same seams one level up: everything inside
the package is real, only the vendor boundary is stubbed, giving the
outside-in descent (e2e → integration → unit) its middle rung without a
fake broker whose fidelity we would then have to test. The
testcontainers layer covers what mocks cannot — actual AMQP and management
behaviour — which is essential for a tool whose whole job is moving real
messages. The 100% gate is a deliberate, non-negotiable foundation while the
codebase is small and the discipline is cheap to maintain.

## Consequences

- New code ships with unit tests or the build fails; `common_api_tests.py`
  is excluded from coverage as a shared mixin, not a test module.
- Mocks patch the aliased seam, so they depend on ADR 02's wrapping holding;
  un-wrapped direct vendor calls (e.g. the channel manipulation flagged in
  the e2e `test_publisher`) are harder to unit-test and should be wrapped.
- Modules acquire integration tests in `tests/integration/` as they are
  touched; `client.py` and `lib.py` are the first (backfilled as a
  prerequisite of the `listen` feature). A behaviour assumed of the
  vendor in an integration stub should have an e2e test somewhere that
  demonstrates it for real.
- e2e/feature tests require a working Docker/testcontainers environment;
  containerized test runs are also why the `dockerfile` (ADR 07) must be
  brought up to date.
- Test idioms (`t`, `subTest`, `*_test.py`) are conventions contributors
  must follow for collection and consistency.
