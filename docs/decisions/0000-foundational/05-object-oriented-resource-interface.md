# Object-oriented resource interface: object handles, lazy lifecycle, keyed cache

Date: 2025-12-07
Status: Accepted (implementation provisional)

## Context

Broker resources — connections, channels, exchanges — have to be created,
addressed, and reused. The Python API style for how callers reach those
resources is a foundational choice: it shapes how every higher layer and
test interacts with the client.

Two style preferences drove the design:

- Treat resources as **objects**, not as verbs on a manager. An exchange is
  a thing you hold a handle to, not an operation you perform.
- Build expensive resources **lazily** and reuse them, avoiding redundant
  connections and round-trips to the broker.

## Decision

- **Handles as objects.** A resource is reached as an object you index or
  hold, e.g. `client.exchanges['my-exchange']` returns an `Exchange`
  handle, rather than an imperative `client.exchange('my-exchange')` call.
  `client.exchanges['x']` reads as "the exchange x"; `client.exchange('x')`
  would read as "perform exchange on x."
- **Lazy lifecycle via `cached_property`.** Connection → channel →
  management API are built on first access and cached:
  `_connection` opens the `pika` `BlockingConnection`, `_channel` derives
  from it, `manager` builds the `RabbitMQManager`. Nothing connects until
  something is needed.
- **Keyed factory-cache for named resources.** `client.exchanges` is an
  `_ExchangeCache` (a `dict` subclass) fed by an `_ExchangeFactory`. On a
  cache miss, `__missing__` calls the factory to build the `Exchange`
  (injecting the shared `ExchangeManager`), stores it, and returns it. The
  same name yields the same object, and no broker round-trip is spent
  re-fetching a handle already held.

The concrete implementation (dict subclass with `__missing__`) is recorded
as **provisional** and open to reconsideration; the *interface style* is
the durable decision.

## Options considered

### Imperative methods on the client/manager

- [pro] Conventional and explicit; no factory or cache machinery.
- [con] Reads as an action, not a handle. Returns fresh objects unless the
  caller manages identity, inviting redundant round-trips and duplicate
  state.

### Eager construction of connections/resources

- [pro] Failures surface immediately at construction.
- [con] Connects even when unused (e.g. a CLI `--help` run, or a test that
  never touches the broker). Couples object creation to live I/O.

### Object handles + lazy `cached_property` + keyed cache (chosen)

- [pro] Resources read as objects; nothing connects until used; named
  handles are deduplicated and cheap to re-access. Lazy seams are also
  clean mock points for unit tests.
- [con] More machinery (factory + cache + `__missing__`); cache lifetime
  and invalidation become concerns the implementation must own.

## Rationale

This is a deliberate personal interface style — objects should behave like
objects — combined with the practical win of lazy construction and caching
to avoid extra broker traffic. The `cached_property` lazy state-machine is
applied consistently across the client's resource graph, which also makes
each seam individually patchable in tests.

## Consequences

- Cache lifetime/invalidation is the implementation's responsibility: a
  cached `Exchange` handle could outlive a server-side delete, so `exists`
  is checked against the broker rather than inferred from cache membership.
- The lazy `cached_property` chain means construction never fails — the
  first *use* does — which tests and callers must account for.
- The dict-subclass-with-`__missing__` mechanism may be replaced; callers
  should depend on the `client.exchanges['name']` access shape, not on the
  cache's concrete type.
