# Contributing to Blackbox

Everything you need to know to work on this repo. The toolchain is self-enforcing: if the local hooks pass, CI passes.

## Toolchain

* **uv** is the package manager. No poetry, no pip-tools, no requirements.txt.
* **ruff** does linting + formatting + import sorting. No flake8, no isort, no black.
* **pre-commit** is the local quality gate.
* **pytest** is the test runner. Coverage and testdox output are enabled by default via `pyproject.toml`.

## First-time setup

```bash
uv sync                                          # install runtime + dev deps into .venv
uv run pre-commit install                        # install the per-commit hook
uv run pre-commit install --hook-type pre-push   # install the pre-push gate
```

After this, every commit gets linted and every push runs the full test suite locally before anything reaches the remote.

## Running things

| what | command |
| --- | --- |
| run the CLI | `uv run blackbox` |
| run tests | `uv run pytest` |
| lint + format | `uv run ruff check --fix . && uv run ruff format .` |
| run all hooks against everything | `uv run pre-commit run --all-files` |
| audit runtime deps for CVEs | `uv run pip-audit` |
| add a runtime dep | `uv add <package>` |
| add a dev dep | `uv add --dev <package>` |
| upgrade locked deps | `uv lock --upgrade` |

## CI mirror

The pre-push hook runs the full pytest suite. CI runs:

1. `lint.yaml` — `pre-commit run --all-files`
2. `tests.yaml` — pytest matrix on Python 3.11–3.13 + a `min-versions` job that resolves every direct dep to its lowest allowed version
3. `security.yaml` — `pip-audit` against the runtime dep graph, weekly + on every PR

If the pre-push hook isn't available in your environment, run these three by hand before opening a PR:

```bash
uv run pre-commit run --all-files
uv run pytest
uv run pip-audit
```

## Writing code

* Match the existing style. Ruff config lives in `pyproject.toml` under `[tool.ruff]`.
* No new top-level dependencies without a clear justification. Prefer the standard library.
* Subprocess calls go through `blackbox.utils.commands.run_command`. Don't sprinkle `subprocess.run(..., shell=True)` around the codebase.
* Backup handlers live under `blackbox/handlers/`. New databases extend `BlackboxDatabase`, new storage backends extend `BlackboxStorage`, new notifiers extend `BlackboxNotifier`.

## Releasing

Releases are cut by publishing a GitHub Release with a tag like `v3.0.0`. The `publish.yaml` workflow:
1. Strips the leading `v` and runs `uv version <X.Y.Z>` to bump `pyproject.toml`.
2. Builds the sdist and wheel with `uv build`.
3. Commits the version bump back to `main`.
4. Publishes to PyPI via Trusted Publishing (OIDC, no token).
5. Builds and pushes the Docker image with `latest`, `vX.Y.Z`, `vX.Y`, and `vX` tags.
