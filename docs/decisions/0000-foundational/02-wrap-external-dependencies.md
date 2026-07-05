# Wrap external dependencies behind local Protocols and adapters

Date: 2025-12-07
Status: Accepted

## Context

Casablanca depends on third-party broker libraries (`pika`,
`amqpstorm`) whose types, call signatures, and exceptions would otherwise
leak throughout the codebase. Two forces motivated insulating them:

- **Swappability** — the transport library choice is explicitly
  provisional (see
  [01-two-transport-rabbitmq-access.md](01-two-transport-rabbitmq-access.md)),
  so consuming code must not bind directly to a concrete vendor type.
- **Testability** — unit tests must be able to mock the broker at a
  precise, stable seam without a live server
  (see [08-testing-strategy.md](08-testing-strategy.md)).

## Decision

Wrap every external dependency behind a local boundary:

- **Import aliasing.** External symbols are imported under a private
  underscore alias, e.g.
  `from amqpstorm.management import ManagementApi as _ManagementApi`.
  The alias marks the symbol as an external, mockable seam and keeps it out
  of the module's public surface.
- **Local Protocols.** The shape we depend on is declared as a `typing.Protocol`
  in our own code (e.g. `ExchangeApiProto`), not imported from the vendor.
  Consuming code is typed against the Protocol.
- **Adapter classes.** A thin wrapper (e.g. `ExchangeManager`) adapts the
  vendor object to our interface and **re-raises vendor exceptions as our
  own**: `amqpstorm`'s `ApiError` is caught and re-raised as
  `casablanca`'s `ApiError`.

## Options considered

### Use vendor types and exceptions directly

- [pro] Less code; no wrapper layer to maintain.
- [con] Every call site binds to a concrete vendor. Swapping `amqpstorm`
  would ripple everywhere. Tests must patch vendor internals, coupling test
  code to library structure.

### Wrap behind local Protocols + adapters (chosen)

- [pro] Consuming code depends only on our interface; the vendor is a
  detail. Exceptions are ours, so callers never import vendor error types.
  Tests patch at the aliased seam with `autospec`.
- [con] Boilerplate: a Protocol and an adapter per surface, kept in sync
  with the wrapped API by hand.

## Rationale

This is a deliberate, habitual design stance: external dependencies are
always wrapped. Swappability is a concrete benefit here given ADR 01's
provisional library split, but the rule is applied even where swapping is
unlikely, because the mockable-seam and own-exceptions properties pay for
themselves in the test suite regardless.

## Consequences

- A Protocol + adapter pair must be added for each new vendor surface
  (queues, bindings, channels) as the API grows. The e2e
  `test_publisher` already flags one such gap: "TODO: wrap the direct
  channel manipulation in an interface."
- Callers catch `casablanca.ApiError`, never `amqpstorm.ApiError`.
- The wrapper is the enabling mechanism for ADR 01's possible future
  consolidation or injectable backends.
- Adapters must be kept in sync with the wrapped library by hand; a vendor
  signature change surfaces at the adapter, which is the intended single
  point of change.
