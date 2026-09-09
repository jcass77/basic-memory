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
├── agent-sops/                  # the SOPs that drive the workflow
│   ├── align-basic-memory-skills.sop.md
│   ├── update-basic-memory-ai-assistant-guide.sop.md
│   └── sync-upstream-and-realign.sop.md
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

See the SOPs in `agent-sops/` for the full step-by-step procedures.

## Syncing the fork on upstream

When pulling new upstream changes into a personal fork, follow
`agent-sops/sync-upstream-and-realign.sop.md` rather than a bare `git pull` /
`git rebase upstream/main`. The short version, with the traps that SOP exists to
prevent:

```bash
git fetch upstream
# NOT `git pull` (rebases onto the stale fork) and NOT a bare
# `git rebase upstream/main` (fork-point replays ~150 applied commits):
git rebase --no-fork-point upstream/main

# Prove each drifted skill is "upstream + personalization", nothing missing,
# WITHOUT overwriting manual personalization — compare a throwaway transform of
# the pristine upstream file against the committed local file:
tmp=$(mktemp -d); git show upstream/main:skills/<name>/SKILL.md > "$tmp/SKILL.md"
PYTHONPATH=src/basic_memory/_personalization \
  uv run python -m scripts.align_skills --apply "$tmp/SKILL.md"
diff "$tmp/SKILL.md" skills/<name>/SKILL.md   # expect only personalization variance

# Refresh the lock (benign post-rebase drift) and publish:
python -m scripts.align_skills --write-lock --skills
python -m scripts.align_skills --verify-lock --skills   # expect exit 0
git push --force-with-lease origin main
```

**Do not** run `align_skills --apply` on the real `skills/memory-literary-analysis/SKILL.md`:
its personalization is richer than the deterministic transformer (categories
outside the `SINGULAR_TO_PLURAL` map, preserved `<n-1>` placeholders, and a
manual "Required Conventions" section), so `--apply` would regress it. Re-apply
those parts by hand.
