import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import nox

_ENVDIR = os.path.expanduser('~/.cache/nox/casablanca')
_SENTINEL = os.path.join(_ENVDIR, '.last_rebuild')
_MAX_AGE = 86400  # 24 hours

def _stale():
    if not os.path.exists(_SENTINEL):
        return True
    return time.time() - os.path.getmtime(_SENTINEL) > _MAX_AGE

if _stale():
    shutil.rmtree(_ENVDIR, ignore_errors=True)
    os.makedirs(_ENVDIR, exist_ok=True)
    open(_SENTINEL, 'w').close()

nox.options.default_venv_backend = 'uv'
nox.options.envdir = _ENVDIR
nox.options.reuse_existing_virtualenvs = True

# pika / amqpstorm are C extensions; no pypy. free-threading variants included.
CPYTHON_VERSIONS = ['3.10', '3.11', '3.12', '3.13', '3.13t', '3.14', '3.14t']
TYPECHECK_VERSIONS = ['3.10', '3.11', '3.12', '3.13', '3.14']  # CPython stable; free-threading adds no type-system variation
PYTHON_VERSIONS = CPYTHON_VERSIONS


@nox.session(python=PYTHON_VERSIONS)
def unit(session):
    session.install('coverage', 'pytest', 'pytest-cov')
    session.env['COVERAGE_FILE'] = f'.cache/.coverage.{session.python}'
    session.install('.')
    session.run('pytest', 'casablanca')


@nox.session(python=PYTHON_VERSIONS)
def e2e(session):
    # testcontainers spins up a RabbitMQ docker container; skip where docker
    # is unavailable (e.g. free-threaded Windows, where pywin32 also has no
    # wheel). integration tests need no containers, so they stay separate.
    if not shutil.which('docker'):
        session.skip('docker unavailable')
    session.install('coverage', 'pytest', 'pytest-cov', 'testcontainers')
    session.install('.')
    session.run('pytest', '--no-cov', 'tests/e2e')


@nox.session(python=TYPECHECK_VERSIONS)
def typecheck(session):
    session.install(
        'mypy', 'types-requests', 'types-PyYAML', 'types-pika-ts',
    )
    session.install('.')
    # tests/ holds only e2e, which needs pytest + testcontainers (e2e group);
    # those aren't in the typecheck group, so e2e is not type-checked. Add
    # tests/<dir> here when non-e2e (e.g. integration) test code lands.
    session.run('mypy', 'casablanca')


def _summarize_failure(output: str) -> str:
    lines = [l for l in output.splitlines() if not l.startswith('nox > ')]

    # pytest test failures: show short summary section
    for i, line in enumerate(lines):
        if 'short test summary info' in line:
            return '\n'.join(lines[i:])

    summary = []
    # coverage miss rows: "some/file.py  117  2  98%  242-243"
    summary.extend(l for l in lines if re.match(r'\S+\.py\s+\d+\s+[1-9]\d*\s', l))
    # FAIL coverage line and INTERNALERROR root-cause lines
    for l in lines:
        if l.startswith('FAIL') or (
            l.startswith('INTERNALERROR') and ('Error:' in l or 'Exception:' in l)
        ):
            summary.append(l)
    # pytest result summary line
    result = next((l for l in lines if re.match(r'={3,}.*\d+ (passed|failed|error)', l)), None)
    if result:
        summary.append(result)

    return '\n'.join(summary) if summary else '\n'.join(lines[-10:])


@nox.session
def parallel(session):
    quiet = '-q' in session.posargs

    listing = subprocess.run(
        ['nox', '-l'], capture_output=True, text=True, check=True,
    )
    sessions = [
        line.split()[1]
        for line in listing.stdout.splitlines()
        if line.startswith(('* ', '- ')) and line.split()[1] != 'parallel'
    ]

    def run_one(name):
        r = subprocess.run(
            ['nox', '-s', name, '-r'],
            capture_output=True, text=True,
        )
        return name, r.returncode, r.stdout + r.stderr

    results = []
    workers = min(len(sessions), os.cpu_count() or 1)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_one, s): s for s in sessions}
        for fut in as_completed(futures):
            name, rc, output = fut.result()
            results.append((name, rc, output))
            print(f"{'OK  ' if rc == 0 else 'FAIL'}: {name}")

    failed = [(n, o) for n, rc, o in results if rc != 0]
    if quiet:
        groups: dict[frozenset[str], tuple[list[str], str]] = {}
        for name, output in failed:
            body = _summarize_failure(output)
            key = frozenset(l for l in body.splitlines() if l.startswith('FAILED '))
            if key not in groups:
                groups[key] = ([], body)
            groups[key][0].append(name)
        for names, body in groups.values():
            print(f'\n=== {", ".join(names)} ===\n{body}')
    else:
        for name, output in failed:
            print(f'\n=== {name} ===\n{output}')

    if failed:
        session.error(f'{len(failed)} session(s) failed')


@nox.session(python='3.13')
def lint(session):
    session.install('flake8')
    session.run(
        'flake8', 'casablanca', 'tests',
        '--count', '--select=E9,F63,F7,F82', '--show-source', '--statistics',
    )
    session.run(
        'flake8', 'casablanca', 'tests',
        '--count', '--exit-zero', '--statistics',
    )
