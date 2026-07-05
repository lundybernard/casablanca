# Architecture Decision Records

Significant architectural decisions for Casablanca. Read the relevant ADRs
before proposing changes to core behaviour.

- **Format.** Each ADR uses the canonical format (Context / Decision /
  Options considered / Rationale / Consequences). Use the `adr-write` skill
  for a single record and `adr-directory` for a multi-decision PR.
- **Immutability.** ADRs are not edited once accepted; supersede them with a
  new record and update the status of the old one.
- **Numbering.** Grouped decisions live in `NNNN-topic/` directories with
  their own `README.md` index. The `0000-foundational/` group predates the
  numbering system and uses two-digit local prefixes.

| # | Topic | Status |
| ---- | ----- | ------ |
| 0000 | [Foundational decisions](0000-foundational/README.md) | Accepted |
