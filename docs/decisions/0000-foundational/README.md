# Foundational Decisions

Decisions made before Casablanca adopted Architecture Decision Records.
Reconstructed from source, git history, and project documentation, and
confirmed with the author.

These predate the global ADR numbering system; they use a two-digit
local prefix and are ordered most-fundamental first (each builds on the
ones above it). Status is `Accepted`; dates are approximate, taken from
the relevant commits in the December 2025 RabbitMQ build.

| # | Title | Status |
| - | ----- | ------ |
| 01 | [Two-transport RabbitMQ access](01-two-transport-rabbitmq-access.md) | Accepted (provisional) |
| 02 | [Wrap external dependencies behind local Protocols and adapters](02-wrap-external-dependencies.md) | Accepted |
| 03 | [Capture format: JSON-lines, one queue stream per file](03-capture-format.md) | Accepted |
| 04 | [Record/replay scope: no topology rebuild, full-speed replay](04-record-replay-scope.md) | Accepted |
| 05 | [Object-oriented resource interface](05-object-oriented-resource-interface.md) | Accepted (impl provisional) |
| 06 | [Layered configuration via batconf](06-layered-configuration-batconf.md) | Accepted |
| 07 | [CLI on the BAT scaffold](07-cli-on-bat-scaffold.md) | Accepted |
| 08 | [Testing strategy](08-testing-strategy.md) | Accepted |
| 09 | [Runtime and concurrency policy](09-runtime-and-concurrency-policy.md) | Accepted |
