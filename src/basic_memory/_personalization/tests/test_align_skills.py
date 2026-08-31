"""Unit tests for the deterministic skill/guide transformer.

Each case documents the intended behavior and the review finding it guards.
"""

import argparse
from pathlib import Path

from scripts import align_skills as align
from scripts import guide_validation as validation

# --- Line-level transforms ------------------------------------------------


class TestTransformLine:
    def test_kebabs_spaced_wikilink(self):
        assert align.transform_line("see [[API Gateway]] here") == "see [[api-gateway]] here"

    def test_kebabs_title_param_including_acronym_first(self):
        # BUG #6: acronym-first Title Case (e.g. "API Design") must be caught.
        assert align.transform_line('title="API Design"') == 'title="api-design"'
        assert align.transform_line('identifier="OAuth Flow"') == 'identifier="oauth-flow"'

    def test_kebabs_plain_multiword_title_param(self):
        assert align.transform_line('title="My Note"') == 'title="my-note"'

    def test_memory_url_stops_at_lowercase_prose(self):
        # BUG #2: the fixer must not swallow trailing prose after a memory:// URL.
        line = "resume from memory://My Note where we left off"
        assert align.transform_line(line) == "resume from memory://my-note where we left off"

    def test_memory_url_kebabs_full_title_case_path(self):
        assert align.transform_line("memory://My Note Title") == "memory://my-note-title"

    def test_memory_url_preserves_version_number(self):
        # BUG B1: a versioned Title-Case memory URL must be matched AND kebabed
        # while preserving the version (e.g. "2.0"), matching the kebabify goal.
        assert align.transform_line("see memory://OAuth 2.0 Spec") == "see memory://oauth-2.0-spec"

    def test_memory_url_preserves_scope_prefix(self):
        assert align.transform_line("memory://api/My Note") == "memory://api/my-note"

    def test_fixes_wikilink_punctuation_without_space(self):
        # BUG #3: a comma (or other invalid punctuation) in a wiki-link with no
        # space must still be fixed, so the checker's kebab-punctuation error is
        # actually resolvable by the fixer.
        assert align.transform_line("[[some-note,]]") == "[[some-note]]"

    def test_leaves_template_placeholder_wikilink_untouched(self):
        assert align.transform_line("[[{exact_title}]]") == "[[{exact_title}]]"

    def test_leaves_clean_kebab_wikilink_untouched(self):
        assert align.transform_line("[[already-kebab]]") == "[[already-kebab]]"

    def test_kebabs_angle_placeholder_wikilink(self):
        assert align.transform_line("[[<Related Character>]]") == "[[<related-character>]]"

    def test_pluralizes_category(self):
        assert align.transform_line("- [decision] a choice") == "- [decisions] a choice"

    def test_idempotent(self):
        for line in [
            "see [[API Gateway]] here",
            'title="API Design"',
            "memory://My Note where we left off",
            "[[some-note,]]",
            "- [decision] a choice",
        ]:
            once = align.transform_line(line)
            assert align.transform_line(once) == once


# --- Whole-file transform -------------------------------------------------

FRONTMATTER_FIXTURE = """\
---
name: memory-notes
description: "Use [[Some Title]] and title=\\"Not Changed\\" in frontmatter."
---

# Body

See [[Some Title]] and title="My Note".
- [decision] pick one
"""


class TestTransformText:
    def test_frontmatter_is_never_modified(self):
        out = align.transform_text(FRONTMATTER_FIXTURE)
        # The description/name lines (discovery text) must be byte-identical.
        assert 'description: "Use [[Some Title]] and title=\\"Not Changed\\"' in out
        assert "name: memory-notes" in out

    def test_body_is_transformed(self):
        out = align.transform_text(FRONTMATTER_FIXTURE)
        assert "[[some-title]]" in out
        assert 'title="my-note"' in out
        assert "- [decisions] pick one" in out

    def test_idempotent(self):
        once = align.transform_text(FRONTMATTER_FIXTURE)
        assert align.transform_text(once) == once


# --- Checker/fixer round trip (the core design guarantee) -----------------

DIRTY_BODY = """\
# Notes

- see [[API Gateway]] and [[OAuth 2.0 Spec]]
- broken link [[some-note,]]
- resume memory://My Note where we left off
- spec at memory://OAuth 2.0 Spec
- build_context(url="memory://My Other Note")
- [decision] adopt the pattern
- edit_note(identifier="Some Title")
"""


def _error_violations(text: str) -> dict:
    """Run every ERROR-severity validator check on `text`; return name->count."""
    lines = text.splitlines()
    counts = {}
    for check in validation.ALL_CHECKS:
        result = check(lines)
        if result.severity == "error" and result.violations:
            counts[result.name] = len(result.violations)
    return counts


class TestRoundTrip:
    def test_dirty_body_has_errors_before(self):
        assert _error_violations(DIRTY_BODY), "fixture should start with violations"

    def test_transform_clears_all_mechanical_errors(self):
        # BUGS #1-#3: after transforming, every mechanical (auto-fixable) error
        # check must report zero. content-contradictions is excluded because it
        # is intentionally not auto-fixed.
        fixed = align.transform_text(DIRTY_BODY)
        remaining = _error_violations(fixed)
        remaining.pop("content-contradictions", None)
        assert remaining == {}, f"unfixed mechanical errors remain: {remaining}"


# --- Lockfile durability --------------------------------------------------


class TestLockfile:
    def _make_skill(self, tmp_path: Path, name: str, content: str) -> Path:
        d = tmp_path / ".agents" / "skills" / name
        d.mkdir(parents=True)
        p = d / "SKILL.md"
        p.write_text(content, encoding="utf-8")
        return p

    def test_write_then_verify_no_drift(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        skill = self._make_skill(tmp_path, "memory-x", "# X\n- [facts] a\n")
        lock = tmp_path / "skills-alignment-lock.json"
        assert align.write_lock([skill], lock) == 0
        assert align.verify_lock([skill], lock) == 0

    def test_skillpath_is_repo_relative(self, tmp_path, monkeypatch):
        # #9: lockfile paths must be portable (repo-relative), and must not be
        # produced by fragile string-prefix stripping. The skills are now
        # git-tracked in this repo, so paths are relative to the repo root
        # (cwd) rather than $HOME.
        monkeypatch.chdir(tmp_path)
        skill = self._make_skill(tmp_path, "memory-x", "# X\n")
        lock_data = align.build_lock([skill])
        skill_path = lock_data["skills"]["memory-x"]["skillPath"]
        assert skill_path == ".agents/skills/memory-x/SKILL.md"
        assert not skill_path.startswith("/")

    def test_verify_detects_drift_after_edit(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        skill = self._make_skill(tmp_path, "memory-x", "# X\n- [facts] a\n")
        lock = tmp_path / "skills-alignment-lock.json"
        align.write_lock([skill], lock)
        skill.write_text("# X\n- [facts] a\n- [ideas] b\n", encoding="utf-8")
        assert align.verify_lock([skill], lock) == 1


# --- resolve_paths dedup (#17) -------------------------------------------


class TestResolvePaths:
    def test_dedupes_overlapping_paths(self, tmp_path):
        p = tmp_path / "SKILL.md"
        p.write_text("# x\n", encoding="utf-8")
        args = argparse.Namespace(skills=False, paths=[str(p), str(p)])
        resolved = align.resolve_paths(args)
        assert len(resolved) == 1

    def test_dedupes_differing_representations(self, tmp_path):
        # S6: the same file expressed two ways ("SKILL.md" vs "./SKILL.md")
        # must dedupe to one, so it is never processed/locked twice.
        p = tmp_path / "SKILL.md"
        p.write_text("# x\n", encoding="utf-8")
        dotted = tmp_path / "." / "SKILL.md"
        args = argparse.Namespace(skills=False, paths=[str(p), str(dotted)])
        resolved = align.resolve_paths(args)
        assert len(resolved) == 1
