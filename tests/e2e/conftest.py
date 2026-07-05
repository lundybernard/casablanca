import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

_RUNTIME_DIR = Path.home() / '.cache' / 'casablanca' / 'podman-run'
_SOCK = _RUNTIME_DIR / 'podman.sock'


def _socket_is_live(path: Path) -> bool:
    probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        probe.connect(str(path))
        return True
    except OSError:
        return False
    finally:
        probe.close()


def pytest_configure(config):
    if os.environ.get('DOCKER_HOST'):
        return

    if not shutil.which('podman'):
        # No Podman on this box - defer entirely to testcontainers' own
        # docker-py detection (Docker Desktop, Colima, Rancher Desktop,
        # OrbStack, a docker-group Docker install, whatever's actually
        # there). Leave DOCKER_HOST unset so docker.from_env() runs its
        # normal search; nothing Podman-specific applies.
        return

    # podman needs a *working* XDG_RUNTIME_DIR for everything (storage
    # locks, config, not just our socket) - the inherited value may point
    # at a login-session dir (e.g. /run/user/$UID) that doesn't exist when
    # there's no full login/lingering session, so existence is checked, not
    # just presence.
    runtime_dir = os.environ.get('XDG_RUNTIME_DIR')
    if not runtime_dir or not Path(runtime_dir).is_dir():
        os.environ['XDG_RUNTIME_DIR'] = str(_RUNTIME_DIR)

    _RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    if _SOCK.exists() and not _socket_is_live(_SOCK):
        # Left behind by a service killed without a clean shutdown (SIGKILL,
        # OOM, host reboot) - nothing is listening on it, so it must be
        # cleared before podman can bind a fresh one at the same path.
        _SOCK.unlink()

    if not _SOCK.exists():
        proc = subprocess.Popen(
            ['podman', 'system', 'service', f'unix://{_SOCK}', '--time=0'],
            start_new_session=True,
        )
        for _ in range(50):  # ~5s
            if _SOCK.exists():
                break
            if proc.poll() is not None:
                raise RuntimeError(
                    f'podman system service exited immediately '
                    f'(code {proc.returncode}) - run it in the foreground '
                    f'for the real error: podman system service '
                    f'unix://{_SOCK} --time=0'
                )
            time.sleep(0.1)
        else:
            raise RuntimeError(
                f'podman system service did not create {_SOCK} in time'
            )

    os.environ['DOCKER_HOST'] = f'unix://{_SOCK}'
    os.environ.setdefault('TESTCONTAINERS_RYUK_DISABLED', 'true')
    print(f'[conftest] using rootless Podman socket at {_SOCK}')
