# Align Basic Memory Skills

## Overview

This SOP aligns the git-tracked Basic Memory agent skills (`skills/memory-*/SKILL.md` in this repository) with user preferences, mirroring the guide-alignment mechanism used for the personalized AI assistant guides. Skills are instruction files that teach agents how to use Basic Memory's MCP tools; because several of them describe note authoring, they can contradict the conventions in `user-preferences.md` (kebab-case titles, plural categories, find_replace-first editing, relations-to-existing-notes-only, controlled observation categories).

Skills are aligned **in-place** in this repository's `skills/` directory. Because pulling upstream skill updates can overwrite these files, this SOP produces a checksum manifest so later runs can detect upstream overwrites and re-align.

Two classes of violation are handled differently:
- **Mechanical violations** (Title Case, singular categories, invalid permalink punctuation) are fixed deterministically by `scripts.align_skills`, which shares its canonicalization with the validator (`scripts.conventions`).
- **Content contradictions** (a skill that teaches "categories are arbitrary" or positively encourages forward references) cannot be fixed by transforms and MUST be routed to a content-rewrite decision rather than silently transformed.

## Parameters

- **preferences_path** (optional, default: "src/basic_memory/_personalization/config/user-preferences.md"): Path to the user preferences file
- **skills_glob** (optional, default: "skills/memory-*/SKILL.md"): Glob matching the git-tracked skill files to align in this repository
- **output_dir** (optional, default: "src/basic_memory/_personalization/.scratchpad/align-basic-memory-skills"): Directory for SOP output artifacts
- **lock_path** (optional, default: "src/basic_memory/_personalization/skills-alignment-lock.json"): Path to the git-tracked alignment lockfile, mirroring the `skills-lock.json` convention used by the skills sync tooling

**Constraints for parameter acquisition:**
- If all required parameters are already provided, You MUST proceed to the Steps
- If any required parameters are missing, You MUST ask for them before proceeding
- When asking for parameters, You MUST request all parameters in a single prompt
- When asking for parameters, You MUST use the exact parameter names as defined
- You MUST validate that `preferences_path` exists before proceeding
- You MUST expand `~` in `skills_glob` before use
- You MUST confirm successful acquisition of all parameters before proceeding

## Steps

### 1. Setup

Load current user preferences and enumerate the installed skills to align.

**Constraints:**
- You MUST read user preferences using `fs_read(path=preferences_path)` because alignment decisions derive from them
- You MUST expand `skills_glob` and list every matching `SKILL.md` file
- You MUST create the output directory if it does not exist using `execute_bash(command="mkdir -p {output_dir}")`
- You MUST NOT proceed if preferences cannot be loaded because alignment requires the preference source
- You SHOULD report the count and names of matched skills to the user before continuing

### 2. Baseline Validation

Run the validation script against all matched skills to establish a baseline and classify violations.

**Constraints:**
- You MUST run `python -m scripts.guide_validation --skills` to validate all installed skills
- You MUST record the per-skill error and warning counts to `{output_dir}/skills-baseline.json`
- You MUST separately track the `content-contradictions` check results because those require a content-rewrite decision, not a mechanical transform
- You SHOULD classify each skill as one of: clean (0 errors), mechanical-only, or content-contradiction

### 3. Analyze Violations

For each skill with violations, determine which are mechanical and which are content contradictions.

**Constraints:**
- You MUST classify violations into two groups, because only the first is fixed by the deterministic transformer:
  - **Deterministically transformable** (handled by `scripts.align_skills` in Step 5):
    - Naming conventions (Title Case wiki-links, `identifier=`, `title=`, `memory://` URLs → kebab-case), including acronym-first names such as `API Design`
    - Category conventions (singular → plural)
  - **Manual / content judgment** (NOT performed by the transformer — resolve by hand or route to Step 6):
    - Edit operation preferences (append-first → find_replace-first where appropriate)
    - Forward reference wording
- You MUST treat any `content-contradictions` violation as requiring a content decision, specifically:
  - A skill statement that observation categories are arbitrary / free-form / unlimited, which contradicts the controlled-category preference
  - Positive forward-reference encouragement (e.g. "valid — BM will resolve it", "create target notes if they don't exist yet"), which contradicts the relations-to-existing-notes-only preference
- You MUST NOT rewrite illustrative domain fixtures that are clearly examples rather than instructions unless they violate a mechanical convention, because gratuitous edits reduce fidelity to upstream

### 4. Document Findings

Record the analysis and a per-skill task list.

**Constraints:**
- You MUST create `{output_dir}/skills-contradictions.md` documenting, per skill, the mechanical violations and any content contradictions with specific line references
- You MUST create `{output_dir}/skills-resolution-tasks.md` with a markdown checkbox list grouped by skill
- You MUST clearly separate mechanical tasks (auto-fixable) from content-decision tasks (require rewrite or an explicit accept/skip decision)

### 5. Execute Mechanical Alignment

Apply deterministic transforms to fix mechanical violations in each skill, in-place, using the committed transformer script.

**Constraints:**
- You MUST use `scripts.align_skills` to apply mechanical transforms because it is deterministic, reviewable, idempotent, and shares its canonicalization (`scripts.conventions`) with the validator, so what it writes is exactly what the validator accepts
- You MUST first preview changes with `python -m scripts.align_skills --skills` (dry-run is the default mode) and review the unified diff
- You MUST then apply with `python -m scripts.align_skills --apply --skills`
- You MUST NOT hand-write `sed` or ad-hoc `str_replace` transforms for the mechanical conventions because those are non-reproducible and previously introduced artifacts (e.g. a trailing comma left in a kebab permalink)
- The transformer skips the YAML frontmatter block in code, so You do not need a separate safeguard for `name`/`description`; You MUST still confirm frontmatter is unchanged in Step 8
- The transformer applies ONLY the two deterministic conventions from Step 3 (kebab-case naming and singular→plural categories). It does NOT rewrite append→find_replace edit patterns or forward-reference wording; handle those by hand or route them to Step 6
- The transformer does NOT touch content contradictions; those remain the responsibility of Step 6

### 6. Resolve Content Contradictions

Handle the philosophical contradictions that transforms cannot fix.

**Constraints:**
- For each skill flagged by `content-contradictions`, You MUST present the specific conflicting text and the contradicting preference to the user
- You MUST offer explicit options: rewrite the passage to match preferences, or accept/skip the skill with the contradiction documented
- You MUST NOT silently transform a philosophical contradiction into aligned-looking text because doing so misrepresents the skill's actual guidance
- If the user chooses to rewrite, You MUST rewrite the passage to positively state the preference (e.g. controlled categories, relations to existing notes only)
- If the user chooses to skip, You MUST record the decision in `{output_dir}/skills-contradictions.md`

### 7. Write the Durability Lockfile

Record a checksum lockfile of the aligned skills so future runs can detect upstream overwrites.

**Constraints:**
- You MUST regenerate the lockfile with `python -m scripts.align_skills --write-lock --skills`
- The lockfile MUST be the git-tracked `src/basic_memory/_personalization/skills-alignment-lock.json`, mirroring the `skills-lock.json` schema (`version`, `skills`, per-skill `source`/`sourceType`/`skillPath`) with an `alignedHash` field recording our post-alignment SHA-256
- You MUST NOT write alignment hashes into the tool-managed `skills-lock.json` because that would corrupt the skills tool's own overwrite detection
- You MUST use a repo-relative `skillPath` (e.g. `skills/memory-notes/SKILL.md`) so the lockfile is portable across clones
- You SHOULD commit the lockfile so drift detection works after a fresh clone or on another machine

### 8. Verify Alignment

Re-run validation to confirm mechanical violations are resolved, and confirm the transform is idempotent and left no artifacts.

**Constraints:**
- You MUST run `python -m scripts.guide_validation --skills` again
- You MUST confirm mechanical error counts are zero for every skill, including the `kebab-punctuation` check that guards against transform artifacts such as stray commas in permalinks
- You MUST run `python -m scripts.align_skills --check --skills` and confirm it reports no changes (exit code 0), which proves the transform is idempotent and fully applied
- You MUST run `python -m scripts.align_skills --verify-lock --skills` and confirm it reports no drift, which proves the lockfile matches the aligned skills on disk
- You MUST confirm each aligned skill's frontmatter `name:` and `description:` are unchanged from upstream because altering them breaks skill discovery
- You MAY leave `content-contradictions` violations only where the user explicitly chose to skip a rewrite; You MUST report any such residual violations
- You MUST report the final validation summary to the user
- You MUST mark completed tasks in `{output_dir}/skills-resolution-tasks.md`

## Examples

### Example 1: Default Usage
**Input:**
- All parameters use defaults

**Expected Behavior:**
Agent loads `user-preferences.md`, globs `skills/memory-*/SKILL.md`, validates them for a baseline, fixes mechanical violations in-place, routes content contradictions (e.g. in `memory-notes`) to the user for a rewrite/skip decision, writes a checksum manifest, and re-validates to confirm zero mechanical errors.

### Example 2: Single Skill Re-Alignment After Upstream Update
**Input:**
- skills_glob: "skills/memory-notes/SKILL.md"

**Expected Behavior:**
Agent aligns only the `memory-notes` skill. Useful after an upstream skills sync overwrites a previously aligned skill and the manifest checksum no longer matches.

## Troubleshooting

### Skill Reverts After Update
If an aligned skill shows upstream content again, an upstream skills sync overwrote it. Run `python -m scripts.align_skills --verify-lock --skills` to detect which skills drifted from `src/basic_memory/_personalization/skills-alignment-lock.json`; for any that changed, re-run `--apply --skills` then `--write-lock --skills`.

### Content Contradiction Cannot Be Auto-Fixed
The `content-contradictions` check flags philosophical conflicts (arbitrary categories, forward-reference encouragement). These are not mechanical. Present the conflict to the user and rewrite or skip per their decision. Do not attempt a find/replace transform.

### Validation Still Reports Errors After Alignment
1. Re-read the preferences for recent changes
2. Run `python -m scripts.align_skills --check --skills` to confirm the transformer has nothing left to change (idempotent, fully applied)
3. If errors remain, they are outside the transformer's scope (append→find_replace, forward-reference wording, or a content contradiction) — resolve them by hand or via Step 6 rather than expecting the transformer to fix them

## Artifacts

- `{output_dir}/skills-baseline.json` - Pre-alignment validation snapshot
- `{output_dir}/skills-contradictions.md` - Per-skill violation analysis
- `{output_dir}/skills-resolution-tasks.md` - Task checklist grouped by skill
- `{lock_path}` - Git-tracked alignment lockfile (SHA-256 per skill) for overwrite detection; mirrors the `skills-lock.json` convention
- `skills/memory-*/SKILL.md` - The aligned skill files (edited in-place, git-tracked)
