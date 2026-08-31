# Personalization tooling (local-only, not shipped)

This directory holds SOP-driven tooling that aligns the Basic Memory AI
assistant guides and agent skills with a set of local authoring preferences
(kebab-case titles, plural observation categories, find_replace-first editing,
relations-to-existing-notes-only, controlled observation categories).

It lives under `src/basic_memory/` only for convenient in-tree reference from a
checkout. **It is not part of the shipped product:**

- Excluded from the PyPI wheel via `[tool.hatch.build.targets.wheel] exclude`
  in the repo root `pyproject.toml`.
- Omitted from coverage (`*/_personalization/*`) so it never affects the 100%
  coverage gate.
- Its `tests/` are not in the repo `testpaths`, so the product test run does
  not collect them.

Nothing in the shipped `basic_memory` package imports from here.

## Layout

```
_personalization/
├── scripts/                     # deterministic transformer + validator
│   ├── conventions.py           # single source of truth for the conventions
│   ├── align_skills.py          # applies the conventions (dry-run/apply/check/lock)
│   └── guide_validation.py      # validates guides/skills against the conventions
├── agent-sops/                  # the two SOPs that drive the workflow
│   ├── align-basic-memory-skills.sop.md
│   └── update-basic-memory-ai-assistant-guide.sop.md
├── config/
│   └── user-preferences.md      # the preference source the SOPs read
├── tests/                       # unit tests for scripts/ (run manually)
└── skills-alignment-lock.json   # SHA-256 manifest for overwrite/drift detection
```

## What gets aligned

| Target | Location (repo-relative) |
|--------|--------------------------|
| Extended guide | `docs/ai-assistant-guide-extended.md` |
| Abridged guide | `src/basic_memory/mcp/resources/ai_assistant_guide.md` |
| Skills | `skills/memory-*/SKILL.md` |

## Running

Run from the repo root with this directory on `PYTHONPATH`:

```bash
export PYTHONPATH=src/basic_memory/_personalization

# Validate the guides (defaults to the two guide targets above)
python -m scripts.guide_validation

# Validate the in-repo skills
python -m scripts.guide_validation --skills

# Preview skill alignment (dry-run is the default)
python -m scripts.align_skills --skills

# Apply, then confirm idempotency and refresh the lockfile
python -m scripts.align_skills --apply --skills
python -m scripts.align_skills --check --skills
python -m scripts.align_skills --write-lock --skills

# Detect upstream overwrites since the last alignment
python -m scripts.align_skills --verify-lock --skills
```

Run the tests manually (the repo's `--cov` addopts must be disabled since this
code is coverage-omitted):

```bash
python -m pytest src/basic_memory/_personalization/tests -o addopts=""
```

See the two SOPs in `agent-sops/` for the full step-by-step alignment
procedures.
