# AGENTS.md — personalization tooling

Operational guidance for AI agents working inside
`src/basic_memory/_personalization/`. For what this directory is, its layout,
and the day-to-day apply commands, see `README.md` alongside this file.

This tooling is **local-only** and is deliberately fenced off from the shipped
product:

- Excluded from the PyPI wheel (`[tool.hatch.build.targets.wheel] exclude` in
  the repo root `pyproject.toml`).
- Omitted from coverage (`*/_personalization/*`), so it never affects the
  repository's 100% coverage gate.
- Not in the repo `testpaths`, so `just test` / the product suite never
  collect these tests.
- Nothing in the shipped `basic_memory` package imports from here, and this
  code must never import from `basic_memory` — the dependency direction is
  one-way and severable.

## Modules

The `scripts` package is imported by putting this directory on `PYTHONPATH`
(`export PYTHONPATH=src/basic_memory/_personalization`); it is not installed and
has no console-script entry points.

| Module | Invocation | Purpose |
|--------|-----------|---------|
| `scripts.conventions` | — | Single source of truth for canonicalization rules |
| `scripts.align_skills` | `python -m scripts.align_skills` | Deterministic guide/skill transformer + lockfile drift detection |
| `scripts.guide_validation` | `python -m scripts.guide_validation` | Validate guides/skills against the conventions |

The transformer and the validator share `scripts.conventions` so that what the
fixer writes is exactly what the checker accepts. Keep that invariant: any new
mechanical convention belongs in `conventions.py`, consumed by both sides.

## Dev workflow

The environment is the basic-memory repo's own `uv` environment; there is no
separate package to install.

Run the tooling's quality gates from the repo root before committing changes to
this directory:

```bash
# Lint + format (repo baseline ruff config; this dir is not otherwise gated)
uv run ruff check src/basic_memory/_personalization
uv run ruff format --check src/basic_memory/_personalization

# Type check (PYTHONPATH so the local `scripts` package resolves)
PYTHONPATH=src/basic_memory/_personalization \
  uv run pyright src/basic_memory/_personalization

# Unit tests — disable the repo's --cov addopts since this code is
# coverage-omitted, and put the package on PYTHONPATH so `scripts` resolves.
PYTHONPATH=src/basic_memory/_personalization \
  uv run python -m pytest src/basic_memory/_personalization/tests -o addopts=""
```

## Coding standards

Follow the repository's house style in the root `AGENTS.md` and
`docs/ENGINEERING_STYLE.md`:

- Python 3.12+, full type annotations, docstrings on modules and public
  functions.
- Validate inputs and fail fast; use context managers for I/O.
- Package-qualified imports only (e.g. `from scripts.conventions import ...`).
- Determinism is the point of this tooling: transforms must be idempotent, and
  the checker/fixer must not drift. Add a regression test for any convention
  change and prove idempotency (`--check` after `--apply` reports no changes).
- Do not add third-party dependencies. The `scripts` package is intentionally
  dependency-free (standard library only) so it runs in any checkout.
- Never import from `basic_memory`; this tooling must stay severable from the
  shipped package.

## Standard Operating Procedures (`agent-sops/`)

Multi-step workflows with RFC 2119 constraints:

- `align-basic-memory-skills.sop.md` — align the git-tracked skills
  (`skills/memory-*/SKILL.md`) to the preference conventions, with lockfile
  drift detection.
- `update-basic-memory-ai-assistant-guide.sop.md` — regenerate the personalized
  guides (`docs/ai-assistant-guide-extended.md` and
  `src/basic_memory/mcp/resources/ai_assistant_guide.md`) from upstream.
- `sync-upstream-and-realign.sop.md` — rebase a personal fork on `upstream/main`
  (avoiding the `git pull` / fork-point traps), verify re-alignment
  non-destructively, regenerate the lockfile, and force-with-lease push to the
  fork.

## Preference source

`config/user-preferences.md` is the authoring-preference source the SOPs read
(kebab-case titles, plural observation categories, find_replace-first editing,
relations-to-existing-notes-only, controlled observation categories). Update it
there; both SOPs derive their alignment decisions from it.
