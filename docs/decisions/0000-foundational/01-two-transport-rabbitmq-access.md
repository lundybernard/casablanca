# Two-transport RabbitMQ access: AMQP for messaging, HTTP management for topology

Date: 2025-12-07
Status: Accepted (provisional)

## Context

Casablanca records and replays RabbitMQ messages. Two distinct kinds of
interaction with the broker are required:

1. **Message I/O** — publishing and consuming messages on queues (the
   record and replay hot path).
2. **Topology administration** — listing, declaring, and deleting
   exchanges (and, later, queues and bindings) so that recordings can be
   bound to existing exchanges and replays can target them.

The AMQP protocol (port 5672) can publish, consume, and *declare*
exchanges/queues, but it offers no introspection: there is no way over
AMQP to *list* or *inspect* existing topology. The RabbitMQ HTTP
management API (port 15672) provides that introspection.

No single client library was an obvious fit for both jobs at the time the
client layer was built.

## Decision

Use two libraries, split by transport:

- `pika` for AMQP message I/O on port 5672 (`RabbitmqClient`).
- `amqpstorm.management` for the HTTP management API on port 15672
  (`RabbitMQManager`, `ExchangeManager`) — list / declare / delete.

This is recorded as **provisional**. The split is not yet justified by a
hard technical constraint; it emerged from picking the best tool for each
job as the layers were built. We deliberately keep the door open to
consolidating onto a single library, or to exposing the transport as an
injectable backend, once the record/replay core forces the question.

## Options considered

### Single library — `pika` only

- [pro] One dependency, one connection model, one mental model.
- [con] No topology introspection. Listing/inspecting exchanges (needed to
  avoid duplicate declares and to verify state) is not expressible over
  AMQP alone.

### Single library — `amqpstorm` only

- [pro] `amqpstorm` speaks both AMQP and the management API, so one
  dependency could in principle cover both jobs.
- [con] We already depended on `pika`'s encode/decode machinery for message
  handling, and the messaging path was built on it first. Rewriting the
  hot path onto `amqpstorm` was unjustified churn at this stage.

### Two libraries split by transport (chosen)

- [pro] Each job uses the library best suited to it; management
  introspection is available immediately.
- [con] Two dependencies, two connection models, two ports to configure.
  The reason for keeping *both* is not yet proven and may not survive
  contact with the record/replay core.

## Rationale

Topology introspection is a real requirement (we must list exchanges to
avoid duplicate declares — see the e2e `test_creating_an_exchange`), and
AMQP cannot provide it, so *some* management-API access is non-negotiable.
`amqpstorm` was the chosen management client. The messaging path was
already on `pika` and used its encoding machinery, so it stayed there.

Honesty note: this is "best tool for each job, decided as we went," not a
conclusion reached from first principles. We are recording it now so the
provisionality is explicit rather than ossifying by accident.

## Consequences

- Two broker ports must be configured (`port` 5672, `adminport` 15672) and
  carried through config and tests.
- The management seam is isolated behind a Protocol (see
  [02-wrap-external-dependencies.md](02-wrap-external-dependencies.md)),
  which is what makes a future consolidation or injectable-backend swap
  tractable without touching `Exchange`/client code.
- Revisit when the record/replay core is built: if `amqpstorm` (or `pika`)
  can cover both transports cleanly, collapse to one, or introduce an
  explicit backend interface. This ADR should be superseded, not edited,
  when that happens.
