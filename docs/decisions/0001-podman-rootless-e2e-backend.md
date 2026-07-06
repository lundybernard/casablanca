# Local e2e container backend: support both rootless Podman and Docker/compatible tools; CI unchanged

Date: 2026-07-04
Status: Proposed

## Context

`08-testing-strategy.md` (`docs/decisions/0000-foundational/08-testing-strategy.md`,
Accepted) already locks in testcontainers-python
(`RabbitMqContainer('docker.io/library/rabbitmq:3-management')` in
`tests/e2e/client_test.py`)
as the e2e mechanism. This ADR does not revisit that choice — it decides how
those containers get run locally, across dev machines that don't all share
the same constraints (shared multi-user Linux boxes, solo-dev Linux boxes,
macOS, CI).

The forcing case: on a shared Linux box, an unprivileged test-runner account
can't be given Docker access, because `docker`-group membership is
root-equivalent, not merely "container access" — this ruled out "just add
the test user to the `docker` group" as an option there. Rootless Podman
avoids that. But not every dev machine has that constraint, and Podman
itself turned out to carry its own real, box-level setup requirements
(detailed in `docs/e2e-testing-setup.md`, not here) — so this ADR settles on
supporting **both** backends, auto-detected, rather than mandating one
globally.

testcontainers-python already speaks the same Docker-compatible API either
way, so this is purely a local backend-selection decision, not a
testing-framework change.

## Decision

- **`tests/e2e/conftest.py` auto-detects the backend** in
  `pytest_configure`, before any test module imports `testcontainers`:
  1. If `DOCKER_HOST` is already set explicitly, defer to it.
  2. Else, if a `podman` binary is on `PATH`, use rootless Podman —
     self-managed, no systemd/lingering dependency.
  3. Else, do nothing and let testcontainers' own docker-py detection run
     normally (Docker Desktop, Colima, Rancher Desktop, OrbStack, or a
     plain `docker`-group install).
  It prints one line identifying which path activated — this must never be
  silent magic to a contributor debugging a container failure.
- **Podman is the recommended backend specifically for shared,
  multi-user, security-sensitive Linux boxes**; plain Docker or any
  Docker-API-compatible tool is fully supported and requires zero
  casablanca-specific setup, and is the simpler default everywhere else
  (macOS, solo-dev Linux, CI).
- **`noxfile.py`'s `e2e` session** accepts either `docker` or `podman` on
  `PATH` so a box with only one of the two isn't incorrectly skipped.
- **CI is unchanged and remains the gate of record** — GitHub Actions
  `ubuntu-latest` runners are ephemeral, single-tenant VMs, already
  preinstalled with Docker; local backend choice doesn't affect it.
- **Multi-service topologies, when needed, use testcontainers' `Network` +
  multiple-`DockerContainer` API**, not `DockerCompose` — that wrapper
  shells out to a `docker compose` CLI that doesn't exist on a
  Podman-only box, so it would silently break one of the two supported
  backends.
- Podman setup steps, the AppArmor/uidmap system requirements behind
  "why `apt`, not Pixi," security recommendations, and troubleshooting all
  live in **`docs/e2e-testing-setup.md`** — kept out of this ADR so the
  decision record doesn't drift out of sync with operational detail.

## Options considered

### Support both Podman (rootless) and Docker/compatible, auto-detected (chosen)

- [pro] Matches actual constraints per box instead of one global policy.
- [pro] Zero extra code for the Docker/compatible path — testcontainers'
  existing detection already covers it; `conftest.py` only needs to know
  when to step aside.
- [con] Two backends can drift apart over time (image/networking edge
  cases) — mitigated by CI staying the single gate of record regardless of
  what a contributor runs locally.

### Podman-only

- [pro] One backend, one code path.
- [con] Turned out to require its own non-trivial, sudo-gated system setup
  on current Ubuntu (see `docs/e2e-testing-setup.md`) — forcing that tax
  onto every dev regardless of whether their box has the multi-user risk
  Podman exists to solve.

### Docker rootless mode

- [pro] Identical CLI/config/compose tooling to classic Docker.
- [con] Still a persistent per-user daemon with its own install path,
  for no isolation benefit over Podman on the boxes where isolation
  actually matters.

### Docker, unprivileged user added to `docker` group, everywhere

- [pro] Zero new install anywhere.
- [con] Root-equivalent by design — a real problem specifically on
  shared/multi-user boxes. Rejected as the *only* option, though it's fine
  on boxes where that risk doesn't apply.

### Switch away from testcontainers-python (e.g. Dagger, pytest-docker)

- [con] Solves a backend problem by replacing a working, still-current
  framework; `08-testing-strategy.md` already committed to testcontainers.
  Rejected — out of scope for what is actually a backend/access-model
  problem.

## Rationale

Docker-group root-equivalence is only a *relevant* risk on boxes where
another account exists to escalate against — treating "rootless Podman
everywhere" as the universal answer ignored that Podman isn't free either,
and that cost only pays for itself where the risk it addresses actually
applies. Auto-detecting the backend lets each box's real constraints decide
without making every contributor pay a setup tax for a risk that doesn't
apply to their machine. CI is untouched either way, since its isolation
comes from the ephemeral VM boundary and already gates `main` regardless of
local backend choice.

## Consequences

- Contributors on shared/security-sensitive Linux boxes follow the Podman
  setup in `docs/e2e-testing-setup.md`, once per box.
- Contributors on macOS, CI, or solo-dev Linux boxes need nothing
  casablanca-specific — `conftest.py` steps aside when no `podman` binary
  is present.
- `08-testing-strategy.md` also names `feature_tests/` as a testcontainers
  consumer; today it holds no live tests, so it's out of scope here.
  `tests/e2e/conftest.py`'s auto-detection is scoped to `tests/e2e/` only —
  if `feature_tests/` becomes live again, it needs the same treatment or it
  silently won't pick up either backend.
- Future multi-service e2e tests must use testcontainers' `Network` +
  `DockerContainer` API; `DockerCompose` is a known non-option.
- This ADR does not change `.github/workflows/tests.yml` or CI behavior;
  CI remains the gate of record.
