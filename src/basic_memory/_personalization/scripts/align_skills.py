"""Deterministically align Basic Memory skills/guides to preference conventions.

Replaces the previous ad-hoc `sed` transforms with a single reviewable,
version-controlled, idempotent transformer. It applies exactly two mechanical
conventions, using the shared definitions in `scripts.conventions` so
the output is precisely what `scripts.guide_validation` accepts:

  1. kebab-case for wiki-link targets, title=/identifier= params, memory:// URLs
  2. plural observation categories

Safety and determinism properties:
  - The YAML frontmatter block (opening `---` to closing `---`) is skipped
    entirely, so a skill's `name:`/`description:` (its discovery/trigger text)
    is never modified. This is enforced in code, not by convention.
  - Idempotent: running twice produces no further changes (kebabify and the
    singular->plural map are both fixed points on already-aligned text).
  - Does NOT touch philosophical "content contradictions" (arbitrary-categories
    doctrine, forward-reference encouragement). Those require a human decision
    and are handled outside this script.

Modes (mutually exclusive; the default with no flag is a dry run):
  (default)  print a unified diff of proposed changes; write nothing
  --apply    write changes in place
  --check    exit non-zero if any file would change (CI / idempotency gate)
  --write-lock   regenerate the alignment lockfile
  --verify-lock  detect drift vs the alignment lockfile

Targets:
  --skills   operate on ./skills/memory-*/SKILL.md (git-tracked in this repo)
  <paths...> operate on the given files
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

from scripts.conventions import (
    MEMORY_URL_TITLE_CASE,
    has_invalid_kebab_punctuation,
    kebabify,
    kebabify_path,
    pluralize_categories,
)

# The git-tracked skills now live in this repository under ./skills/. The
# --skills convenience flag globs them from the repo root so alignment operates
# on the canonical, version-controlled copies (not a per-machine install dir).
DEFAULT_SKILLS_ROOT = "skills"
DEFAULT_SKILLS_PATTERN = "memory-*/SKILL.md"

# Git-tracked lockfile mirroring the `skills-lock.json` convention. Records OUR
# post-alignment SHA-256 per skill (as `alignedHash`, distinct from the tool's
# own `computedHash`) so future runs can detect when an upstream update
# overwrote an aligned skill. Kept separate from the tool-managed
# `skills-lock.json` so we never corrupt its overwrite detection.
DEFAULT_LOCK_PATH = "src/basic_memory/_personalization/skills-alignment-lock.json"
SKILL_SOURCE = "basicmachines-co/basic-memory"

# Any wiki-link. The decision to transform is made in `_needs_wikilink_kebab`
# so we can also repair targets that contain invalid permalink punctuation even
# when they have no space (e.g. a stray trailing comma) — matching what the
# validator's kebab-punctuation check flags, so every flagged link is fixable.
_WIKILINK_ANY = re.compile(r"\[\[([^\]]+)\]\]")
# title=/identifier= params that are multi-word Title Case. The first word may
# be an acronym (e.g. "API Design"), hence [A-Z][A-Za-z0-9]* rather than
# requiring a trailing lowercase letter. Mirrors the validator's *_multi checks.
_TITLE_PARAM = re.compile(r'title="([A-Z][A-Za-z0-9]* [A-Z][^"]*)"')
_IDENT_PARAM = re.compile(r'identifier="([A-Z][A-Za-z0-9]* [A-Z][^"]*)"')
# memory:// URLs whose path is multi-word Title Case are matched by the shared
# pattern in `conventions` (single source of truth with the validator), which
# also handles version numbers like "2.0" and stops at lowercase prose.
_MEMORY_URL = MEMORY_URL_TITLE_CASE


def _needs_wikilink_kebab(target: str) -> bool:
    """Whether a wiki-link target should be rewritten.

    Transform when the target contains whitespace (definite Title Case) or
    invalid permalink punctuation (e.g. a trailing comma). Never touch template
    placeholders containing braces — those are illustrative, not real links.
    """
    if "{" in target or "}" in target:
        return False
    if re.search(r"\s", target):
        return True
    return has_invalid_kebab_punctuation(target)


def _kebab_wikilink(m: re.Match[str]) -> str:
    target = m.group(1)
    # Preserve angle-bracket placeholders like <Related Character> structure.
    if target.startswith("<") and target.endswith(">"):
        inner = target[1:-1]
        if not _needs_wikilink_kebab(inner):
            return m.group(0)
        return f"[[<{kebabify_path(inner)}>]]"
    if not _needs_wikilink_kebab(target):
        return m.group(0)
    return f"[[{kebabify_path(target)}]]"


def transform_line(line: str) -> str:
    """Apply all mechanical transforms to a single body line. Idempotent."""
    line = _WIKILINK_ANY.sub(_kebab_wikilink, line)
    line = _TITLE_PARAM.sub(lambda m: f'title="{kebabify(m.group(1))}"', line)
    line = _IDENT_PARAM.sub(lambda m: f'identifier="{kebabify(m.group(1))}"', line)
    line = _MEMORY_URL.sub(lambda m: f"memory://{kebabify_path(m.group(1))}", line)
    return pluralize_categories(line)


def transform_text(text: str) -> str:
    """Transform a whole file's body, skipping the YAML frontmatter block."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    in_frontmatter = False
    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        # Detect a leading frontmatter block delimited by --- ... ---
        if idx == 0 and stripped == "---":
            in_frontmatter = True
            out.append(raw)
            continue
        if in_frontmatter:
            out.append(raw)  # never transform frontmatter
            if stripped == "---":
                in_frontmatter = False
            continue
        # Body line
        newline = ""
        if raw.endswith("\r\n"):
            body, newline = raw[:-2], "\r\n"
        elif raw.endswith("\n"):
            body, newline = raw[:-1], "\n"
        else:
            body = raw
        out.append(transform_line(body) + newline)
    return "".join(out)


def process(paths: list[Path], mode: str) -> int:
    """Transform, diff, check, or apply alignment across the given paths.

    Returns a process exit code (non-zero only in ``check`` mode when files
    would change).
    """
    would_change: list[str] = []
    for path in paths:
        if not path.exists():
            print(f"skip (missing): {path}", file=sys.stderr)
            continue
        original = path.read_text(encoding="utf-8")
        transformed = transform_text(original)
        if transformed == original:
            continue
        would_change.append(str(path))
        if mode == "dry-run":
            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                transformed.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
            )
            sys.stdout.writelines(diff)
        elif mode == "apply":
            # newline="" preserves the per-line \n / \r\n handling done in
            # transform_text rather than letting the text layer re-translate it.
            path.write_text(transformed, encoding="utf-8", newline="")
            print(f"aligned: {path}")

    if mode == "check":
        if would_change:
            print("NOT ALIGNED (would change):")
            for p in would_change:
                print(f"  {p}")
            return 1
        print("OK: all files already aligned (idempotent)")
        return 0

    if mode == "dry-run" and not would_change:
        print("No changes needed — all files already aligned.")
    return 0


def resolve_paths(args: argparse.Namespace) -> list[Path]:
    """Resolve target files from the --skills glob and positional paths, deduped."""
    paths: list[Path] = []
    if args.skills:
        skills_root = Path(DEFAULT_SKILLS_ROOT).expanduser()
        paths += sorted(skills_root.glob(DEFAULT_SKILLS_PATTERN))
    paths += [Path(p) for p in args.paths]
    # Dedupe while preserving order: a file may be matched by --skills and also
    # passed positionally, or given via different spellings ("SKILL.md" vs
    # "./SKILL.md" vs a symlink), which would otherwise be processed/locked
    # twice. Dedupe on the resolved path so those all collapse to one entry.
    seen: set[str] = set()
    unique: list[Path] = []
    for p in paths:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_lock(paths: list[Path]) -> dict:
    """Build a skills-lock.json-shaped dict recording post-alignment hashes.

    Uses `alignedHash` (not the tool's `computedHash`) to make clear these are
    our aligned checksums, and a repo-relative `skillPath` so the lockfile is
    portable across clones (the skills are git-tracked in this repository).
    """
    skills: dict[str, dict] = {}
    repo_root = Path.cwd()
    for path in sorted(paths):
        if not path.exists():
            continue
        name = path.parent.name
        # Portable, repo-relative path. Use relative_to so a checkout at any
        # location produces the same lockfile; fall back to the given path for
        # files outside the repo root (e.g. an ad-hoc positional path).
        try:
            skill_path = str(path.resolve().relative_to(repo_root.resolve()))
        except ValueError:
            skill_path = str(path)
        skills[name] = {
            "source": SKILL_SOURCE,
            "sourceType": "github",
            "skillPath": skill_path,
            "alignedHash": _sha256(path),
        }
    return {"version": 1, "skills": skills}


def write_lock(paths: list[Path], lock_path: Path) -> int:
    """Regenerate the alignment lockfile from the current skill hashes."""
    lock = build_lock(paths)
    lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {lock_path} ({len(lock['skills'])} skills)")
    return 0


def verify_lock(paths: list[Path], lock_path: Path) -> int:
    """Compare current skill hashes against the lockfile and report drift.

    Exits non-zero if any skill is missing, added, or its hash changed —
    indicating an `npx skills` overwrite that needs re-alignment.
    """
    if not lock_path.exists():
        print(f"lockfile not found: {lock_path} — run --write-lock first", file=sys.stderr)
        return 1
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    locked = lock.get("skills", {})
    current = {p.parent.name: p for p in paths if p.exists()}

    drift = []
    for name, entry in locked.items():
        if name not in current:
            drift.append(f"  MISSING: {name} (in lock, not installed)")
            continue
        if _sha256(current[name]) != entry.get("alignedHash"):
            drift.append(f"  CHANGED: {name} (hash differs — likely overwritten by npx skills)")
    drift.extend(
        f"  NEW: {name} (installed, not in lock — align + --write-lock)"
        for name in current
        if name not in locked
    )

    if drift:
        print("DRIFT DETECTED:")
        print("\n".join(drift))
        print(
            "Re-run: python -m scripts.align_skills --apply --skills && "
            "python -m scripts.align_skills --write-lock --skills"
        )
        return 1
    print(f"OK: all {len(locked)} skills match {lock_path} (no drift)")
    return 0


def main() -> int:
    """Parse CLI arguments and dispatch to the requested alignment mode."""
    ap = argparse.ArgumentParser(description="Align BM skills/guides to preference conventions.")
    ap.add_argument("paths", nargs="*", help="Files to process")
    ap.add_argument("--skills", action="store_true", help="Process ./skills/memory-*/SKILL.md")
    ap.add_argument("--lock-path", default=DEFAULT_LOCK_PATH, help="Path to the alignment lockfile")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--apply", action="store_true", help="Write changes in place")
    grp.add_argument("--check", action="store_true", help="Exit non-zero if any file would change")
    grp.add_argument("--write-lock", action="store_true", help="Regenerate the alignment lockfile")
    grp.add_argument(
        "--verify-lock", action="store_true", help="Detect drift vs the alignment lockfile"
    )
    args = ap.parse_args()

    paths = resolve_paths(args)
    if not paths:
        print("No target files. Use --skills and/or pass file paths.", file=sys.stderr)
        return 2

    lock_path = Path(args.lock_path)
    if args.write_lock:
        return write_lock(paths, lock_path)
    if args.verify_lock:
        return verify_lock(paths, lock_path)

    mode = "apply" if args.apply else "check" if args.check else "dry-run"
    return process(paths, mode)


if __name__ == "__main__":
    sys.exit(main())
