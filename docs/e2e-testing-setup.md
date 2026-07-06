# E2E Testing: Container Backend Setup

`tests/e2e/` uses testcontainers-python (`RabbitMqContainer`) against any
Docker-API-compatible backend. `tests/e2e/conftest.py` auto-detects what's
available — see `docs/decisions/0001-podman-rootless-e2e-backend.md` for
the decision this implements. This guide covers the setup details and
security notes that ADR intentionally doesn't carry.

## Choosing a backend

| Situation | Recommended backend | Setup needed |
|---|---|---|
| macOS | Docker Desktop, Colima, Rancher Desktop, or OrbStack | Install the tool; nothing casablanca-specific |
| Solo-dev Linux box (only account on it) | Either `docker`-group Docker or Podman | `docker`-group risk doesn't apply with no one else to escalate against |
| Shared / multi-user Linux box | Rootless Podman | See below — one-time, sudo-gated |
| CI (GitHub Actions) | Docker (preinstalled on `ubuntu-latest`) | None — untouched by this doc |

**Why Podman on shared boxes:** `docker` group membership is
root-equivalent, not merely "container access" — anyone in it can
`docker run -v /:/host -it alpine chroot /host sh` and get a root shell on
the host. No exploit needed; this is intended Docker functionality. On a
box with more than one account, never add an account to the `docker` group
to work around this — use Podman instead.

## Podman setup (Linux, shared/security-sensitive boxes)

1. **`sudo apt install podman`** — one-time, done by whoever administers
   the box, never by the account that runs tests.

   **Must be the `apt` package, not Pixi/conda-forge's.** Conda-forge's
   `podman` binary fails outright on Ubuntu 23.10+/24.04:
   `kernel.apparmor_restrict_unprivileged_userns=1` (the default) blocks
   any *unconfined* binary from creating a user namespace at all. Ubuntu's
   `apt` package ships `/etc/apparmor.d/podman`, a profile scoped exactly
   to `/usr/bin/podman` that grants only `userns` — the sanctioned, narrow
   escape hatch for this restriction. A conda-forge binary lives at a
   different path and isn't covered by it. `apt install podman` also pulls
   in `uidmap` (`newuidmap`/`newgidmap`, setuid-root helpers a user-space
   package manager can't install — no way to set a setuid bit at
   conda-forge/Pixi install time).

2. **Confirm subuid/subgid provisioning** for your account:
   ```bash
   grep "$USER" /etc/subuid /etc/subgid
   ```
   Usually already present on multi-user boxes. If missing, the box admin
   adds a range (e.g. `sudo usermod --add-subuids 100000-165535
   --add-subgids 100000-165535 "$USER"`).

3. **Nothing else to install.** `tests/e2e/conftest.py` self-manages a
   plain `podman system service` background process — no systemd unit, no
   `loginctl enable-linger`, no lingering session required. It also handles
   `XDG_RUNTIME_DIR` (falls back to `~/.cache/casablanca/podman-run` if the
   inherited value doesn't exist). The service runs with `--time=0` (never
   idles out) and detached — it's a permanent background process once
   started, reused across future runs via its socket file, restarted
   automatically only if that socket goes stale (see troubleshooting).

   `tests/e2e/client_test.py` uses the fully-qualified image name
   (`docker.io/library/rabbitmq:3-management`), so no
   `unqualified-search-registries` config is needed.

4. **Run the tests:**
   ```bash
   pixi run nox -s e2e-3.14
   ```

## Security notes

- **Never add an account to the `docker` group on a shared box** to work
  around a Podman setup problem — it defeats the entire reason Podman was
  chosen there (see table above).
- **Don't disable `kernel.apparmor_restrict_unprivileged_userns` globally**
  to make a conda-forge or other non-`apt` Podman build work. That reopens
  unprivileged user-namespace creation for *every* unconfined process on
  the box, not just Podman — a real, system-wide security regression to
  work around a path-scoping issue. Use the `apt` package instead (it
  ships the correctly-scoped AppArmor profile already).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Error: command required for rootless mode with multiple IDs: exec: "newuidmap": executable file not found in $PATH` | `uidmap` not installed | `sudo apt install podman` (pulls it in) |
| `failed to reexec: Permission denied` | AppArmor blocking unconfined binary from `userns`; usually means a non-`apt` Podman build | Use the `apt`-installed `podman`, not a conda-forge/Pixi one |
| `Failed to obtain podman configuration: lstat /run/user/$UID: no such file or directory` | No full login/lingering session, so `$XDG_RUNTIME_DIR` doesn't exist | Handled automatically by `conftest.py` (falls back to `~/.cache/casablanca/podman-run`); if you hit this running `podman` manually, export `XDG_RUNTIME_DIR` to a writable dir yourself |
| `short-name "..." did not resolve to an alias and no unqualified-search registries are defined` | Running `podman` manually with a short image name | `tests/e2e/client_test.py` already uses the fully-qualified name; for a manual command pass one too (`docker.io/library/rabbitmq:3-management`) |
| `podman system service` exited immediately / `RuntimeError` from `conftest.py` at collection time | Startup failed for some other reason (bad `XDG_RUNTIME_DIR`, AppArmor, uidmap) | `conftest.py` now fails loud with the exact cause instead of silently falling through — run the printed command in the foreground for the underlying error |
| Orphaned container after a crashed (not merely failed) local run, Podman path only | Ryuk (testcontainers' auto-reaper) is disabled on the Podman path — flaky under rootless Podman | `podman ps -a --filter label=org.testcontainers=true -q \| xargs -r podman rm -f` |
| Socket file exists but nothing responds (service was killed uncleanly) | Stale `podman.sock` left behind by a SIGKILL/OOM/reboot | Handled automatically by `conftest.py` (probes the socket, unlinks and restarts the service if dead) |
