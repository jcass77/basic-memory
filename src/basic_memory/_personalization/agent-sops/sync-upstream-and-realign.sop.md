# Sync Fork on Upstream and Re-align Personalizations

## Overview

This SOP keeps a personal fork (`origin`, e.g. `jcass77/basic-memory`) current
with the project upstream (`upstream`, `basicmachines-co/basic-memory`) while
preserving the local personalizations that live in this repository (the
`_personalization/` tooling, the applied `skills/memory-*/SKILL.md` edits, and
the personalized guides).

It exists because a naive `git pull` / `git rebase upstream/main` repeatedly
produced spurious merge conflicts and, in one case, silently unwound a good
rebase. The procedure below encodes the specific failure modes observed and the
verification that proves the re-align was faithful.

The end state after a successful run:

- `git rev-list --left-right --count upstream/main...HEAD` → `0  N`
  (0 behind upstream, N = the personalization commits ahead).
- `git rev-list --left-right --count origin/main...HEAD` → `0  0`
  (fork remote in sync).
- `--check`, both validators, and `--verify-lock` all exit 0.

## Parameters

- **upstream_remote** (optional, default: `upstream`): remote tracking the
  canonical `basicmachines-co/basic-memory`.
- **origin_remote** (optional, default: `origin`): remote tracking the personal
  fork.
- **branch** (optional, default: `main`): the branch carrying the
  personalization commits.

**Constraints for parameter acquisition:**
- If all required parameters are already provided, You MUST proceed to the Steps.
- If any are missing, You MUST ask for all of them in a single prompt using the
  exact parameter names, then confirm acquisition before proceeding.
- You MUST run `git remote -v` and confirm both remotes resolve to the expected
  repositories before any history-rewriting step.

## Background: failure modes this SOP prevents

These are not hypothetical — each was hit in practice and is the reason a step
below is written the way it is.

- **`git pull` rebases onto the stale fork, not upstream.** `main` tracks
  `origin/main`. If `origin/main` is behind (the usual case before a sync),
  `git pull` rebases your commits back onto that old tip and tries to replay
  every upstream commit you already have — undoing a completed rebase. **Never
  `git pull` on this fork.** Always fetch and rebase explicitly against
  `upstream/main`.
- **`git rebase upstream/main` uses `--fork-point` by default.** Fork-point
  consults the *reflog* of `upstream/main` to guess where your branch diverged.
  After several fetches, that reflog holds old positions, so git computes a
  merge base far back in history and replays ~150 already-applied commits
  (printing many `skipped previously applied commit` warnings) before hitting a
  spurious conflict — typically on `skills/memory-literary-analysis/SKILL.md`.
  **Always pass `--no-fork-point`** (or use the explicit `--onto` form in
  Step 3).
- **A conflicting commit may already be upstream under a different SHA.** A PR
  that was rebase-merged upstream appears in your history with one SHA and in
  `upstream/main` with another. During rebase it conflicts even though it is
  redundant. When the conflicting commit's change is already an ancestor of
  `upstream/main`, `git rebase --skip` it rather than hand-merging.
- **`align_skills --apply` is NOT a faithful reproduction of manual
  personalization.** For `memory-literary-analysis` the committed personalization
  goes beyond the deterministic transformer:
  - it pluralizes categories the `SINGULAR_TO_PLURAL` map in
    `scripts/conventions.py` does not contain (`convention`, `role`,
    `structure`, `summary`, `event`, `tone`, `quote`, `arc`, `trait`,
    `manifestation`, `evolution`, `appearance`, `interpretation`, `atmosphere`);
  - it preserves template placeholders like `[[chapter-<n-1>-<previous-title>]]`,
    whereas `kebabify` mangles `<N-1>`/`<N+1>` into `n-1`/`n1`;
  - it adds a manual "Required Conventions" section the transformer never emits.
  Running `--apply` on that file therefore *regresses* the personalization. Treat
  the committed content as the source of truth and re-apply manual parts by hand.

## Steps

### 1. Establish a clean, known-good starting point

**Constraints:**
- You MUST run `git status` and confirm a clean working tree. If a rebase or
  merge is already in progress and tangled, You MUST `git rebase --abort` (or
  `git merge --abort`) first — abort returns to the pre-operation commit via the
  reflog and is non-destructive.
- You MUST record the current tip: `git rev-parse HEAD` and
  `git log --oneline upstream/main..HEAD` (the personalization commits). These
  are the commits that must survive the rebase.
- You MUST confirm the `_personalization/` tree is present on disk
  (`git ls-files src/basic_memory/_personalization/ | head`).

### 2. Fetch upstream and decide whether a rebase is even needed

**Constraints:**
- You MUST run `git fetch {upstream_remote}` (and `git fetch {origin_remote}`).
- You MUST check `git rev-list --left-right --count {upstream_remote}/{branch}...HEAD`.
  - If the left count is `0`, `{upstream_remote}/{branch}` is already an ancestor
    of `HEAD`: **there is nothing to rebase**. Skip to Step 6 (lockfile) and
    Step 7 (push) only if other changes are pending; otherwise stop.
  - If the left count is non-zero, upstream has new commits; proceed to Step 3.
- You MUST NOT interpret an `origin/main` "diverged" message from `git status`
  as an upstream problem. `git status` compares against `origin/{branch}` (the
  fork). Divergence there is expected until Step 7.

### 3. Rebase the personalization commits onto the new upstream tip

**Constraints:**
- You MUST rebase without fork-point. Use either form:
  - `git rebase --no-fork-point {upstream_remote}/{branch}`, or
  - the explicit, reflog-independent form that replays only your commits:
    `git rebase --onto {upstream_remote}/{branch} <base>`
    where `<base>` is the parent of the *oldest* commit reported by
    `git log --oneline {upstream_remote}/{branch}..HEAD` in Step 1.
- You MUST NOT run `git pull` at any point.
- If a rebase pauses on a conflict, You MUST classify it before resolving:
  - **Redundant upstream commit** (the conflicting commit's change is already an
    ancestor of `{upstream_remote}/{branch}`, e.g. a PR merged upstream under a
    different SHA): confirm with
    `git merge-base --is-ancestor <sha> {upstream_remote}/{branch}` and then
    `git rebase --skip`.
  - **Real overlap** (upstream edited the same lines your personalization did):
    resolve favoring the personalization *intent* — keep upstream's new prose,
    re-apply the mechanical transform (plural categories, kebab identifiers) and
    any manual additions on top — then `git add <file>` and
    `git rebase --continue`.
- You MUST NOT hand-write `sed`/ad-hoc replacements to resolve category or
  identifier conventions; use the shared canonicalization (see Step 5).

### 4. Confirm the personalization commits survived

**Constraints:**
- You MUST verify `git log --oneline {upstream_remote}/{branch}..HEAD` lists
  exactly the personalization commits recorded in Step 1 (allowing for a new
  lockfile commit added later).
- You MUST verify `git log HEAD..{upstream_remote}/{branch}` is empty (HEAD now
  contains every upstream commit).
- You MUST confirm the `_personalization/` tree is still present.

### 5. Verify re-alignment non-destructively (no missing upstream content)

This is the load-bearing check. It proves each personalized skill equals
"current upstream content + your personalization" with nothing dropped, WITHOUT
overwriting the manual personalization.

**Constraints:**
- For each personalized skill that drifted (see Step 6) You MUST compare the
  transform of the *pristine upstream* file against your committed local file:
  ```bash
  tmp=$(mktemp -d)
  git show {upstream_remote}/{branch}:skills/<name>/SKILL.md > "$tmp/SKILL.md"
  PYTHONPATH=src/basic_memory/_personalization \
    uv run python -m scripts.align_skills --apply "$tmp/SKILL.md"
  diff "$tmp/SKILL.md" skills/<name>/SKILL.md
  ```
- You MUST classify every line the `diff` reports as exactly one of:
  - a **personalization variance** — a category the transformer's map does not
    cover but your commit pluralized, a preserved `<placeholder>`, or the manual
    "Required Conventions" block. These are expected and benign.
  - a **missing upstream line** — upstream prose present in `transform(upstream)`
    but absent from your local file. This is the only real finding.
- If the diff shows **only personalization variances**, the file is fully
  aligned; no content change is required. (`memory-metadata-search` typically
  diffs to nothing; `memory-literary-analysis` diffs only in the categories the
  map omits, the `<n-1>` placeholders, and the Required Conventions block.)
- If the diff shows a **missing upstream line**, You MUST bring that line across
  by hand, preserving surrounding personalization, then re-run the diff.
- You MUST NOT resolve a discrepancy by running `align_skills --apply` on the
  real `skills/<name>/SKILL.md`, because for manually-personalized files that
  regresses the personalization (see Background). `--apply` is safe only on a
  throwaway copy for comparison.
- You MUST then confirm global invariants:
  - `python -m scripts.align_skills --check --skills` exits 0 (transformer has
    nothing to add — mechanical conventions fully applied).
  - `python -m scripts.guide_validation --skills` and
    `python -m scripts.guide_validation` both exit 0 (no violations, no
    `content-contradictions`).

### 6. Regenerate the alignment lockfile

**Constraints:**
- You MUST first run `python -m scripts.align_skills --verify-lock --skills` and
  read the drift report.
  - **Benign post-rebase drift**: `--verify-lock` reports `CHANGED` for skills
    upstream edited, but Step 5's `--check` and validators are clean. The content
    is correct; only the recorded `alignedHash` is stale (it predates the
    integrated upstream edits). The fix is to refresh the lock — nothing else.
  - **True overwrite** (e.g. an `npx skills` sync clobbered a file): `--check`
    would want changes and/or validators would error. In that case re-align
    first (Step 5 by hand for manual files) *before* refreshing the lock.
- You MUST refresh the lock only after Step 5 passes:
  `python -m scripts.align_skills --write-lock --skills`.
- You MUST confirm `python -m scripts.align_skills --verify-lock --skills` now
  exits 0.
- You MUST confirm the lockfile diff is scoped to the drifted skills only
  (`git diff --numstat .../skills-alignment-lock.json` — expect two changed hash
  lines per drifted skill).
- You MUST commit the lockfile with a signed commit and an allowed semantic
  title/scope, e.g.
  `git commit -s -m "chore(skills): refresh alignment lock after upstream rebase"`.

### 7. Publish to the fork

**Constraints:**
- You MUST push with lease protection because the rebase rewrote history:
  `git push --force-with-lease {origin_remote} {branch}`.
  Never plain `--force`; `--force-with-lease` refuses if the remote moved since
  your last fetch.
- You MUST NOT push to `{upstream_remote}`.
- You MUST verify the final state:
  - `git rev-list --left-right --count {origin_remote}/{branch}...HEAD` → `0  0`.
  - `git rev-list --left-right --count {upstream_remote}/{branch}...HEAD` →
    `0  N`.
  - `git status` reports a clean tree and no divergence message.

## Examples

### Example 1: Upstream advanced; a skill drifted benignly

**Input:** defaults; `upstream/main` has new commits, two skills were edited
upstream.

**Expected behavior:** Agent fetches upstream, rebases with `--no-fork-point`,
skips any redundant already-upstream commit, confirms the personalization
commits survived, runs the `transform(upstream)` vs local diff for the two
drifted skills and finds only personalization variances, confirms `--check` and
validators are clean, refreshes the lockfile, commits it signed, and
force-with-lease pushes to the fork. Final counts: `0 0` vs origin, `0 N` vs
upstream.

### Example 2: Already up to date

**Input:** defaults; `git rev-list --left-right --count upstream/main...HEAD`
shows `0` on the left.

**Expected behavior:** Agent reports HEAD already contains all upstream commits,
does not rebase, and stops (or proceeds only to a pending lockfile/push task).

## Troubleshooting

### Rebase prints dozens of "skipped previously applied commit" then conflicts
Fork-point picked an old merge base from `upstream/main`'s reflog. Abort
(`git rebase --abort`) and re-run with `--no-fork-point` or the `--onto` form.

### `git status` says the branch "diverged" from origin/main
Expected before Step 7 — `origin/main` (the fork) is stale. It is not an upstream
problem. Do not `git pull`; complete the rebase and force-with-lease push.

### A drifted skill's diff shows a mangled placeholder or a lost category
That is the transformer's limitation, not a real regression, *only if* it appears
on the `transform(upstream)` side of the Step 5 diff (the `<` side). Your local
(`>` side) is the correct, richer form. Do not "fix" it by running `--apply` on
the real file.

### `--verify-lock` still reports drift after `--write-lock`
Re-check you ran `--write-lock --skills` (the glob) from the repo root, and that
Step 5's `--check` was clean first. If `--check` wanted changes, the file was a
true overwrite; re-align before locking.

## Artifacts

- `skills-alignment-lock.json` — refreshed alignment lockfile (committed).
- The rebased `{branch}` with personalization commits on top of
  `{upstream_remote}/{branch}`, pushed to `{origin_remote}`.

## Known tooling limitations (candidate follow-ups)

These make the process less automatic and are worth fixing in `scripts/`
(each needs a regression test proving idempotency, per this directory's
`AGENTS.md`):

- `SINGULAR_TO_PLURAL` in `conventions.py` omits several categories used in the
  skills (`convention`, `role`, `structure`, `summary`, `event`, `tone`,
  `quote`, `arc`, `trait`, `manifestation`, `evolution`, `appearance`,
  `interpretation`, `atmosphere`, …). Until they are added, those pluralizations
  must be maintained by hand and are invisible to `--check`.
- `kebabify` strips angle brackets and `+`/`-` signs, turning template
  placeholders like `[[Chapter <N-1> - <Previous Title>]]` into
  `[[chapter-n-1-previous-title]]`. Placeholder-preserving kebab handling would
  let the transformer reproduce the `memory-literary-analysis` links faithfully.
- The transformer cannot emit manual content blocks (e.g. the "Required
  Conventions" section). If such blocks become common, consider a templated
  insertion step so re-alignment is fully reproducible.
