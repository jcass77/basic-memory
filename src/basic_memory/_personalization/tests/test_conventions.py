"""Unit tests for the shared canonicalization conventions.

Each case documents the intended behavior and the review finding it guards.
"""

from scripts.conventions import (
    ERROR_SINGULAR_CATEGORIES,
    SINGULAR_TO_PLURAL,
    has_invalid_kebab_punctuation,
    is_category_context_line,
    kebabify,
    kebabify_path,
    pluralize_categories,
)


class TestKebabify:
    def test_lowercases_and_hyphenates_spaces(self):
        assert kebabify("API Design") == "api-design"

    def test_underscores_become_hyphens(self):
        assert kebabify("some_note_title") == "some-note-title"

    def test_strips_comma_and_other_punctuation(self):
        assert kebabify("some-note,") == "some-note"
        assert kebabify("Foo (Bar)") == "foo-bar"

    def test_collapses_and_trims_hyphens(self):
        assert kebabify("  Foo   Bar  ") == "foo-bar"
        assert kebabify("--Foo--Bar--") == "foo-bar"

    def test_preserves_version_periods(self):
        # BUG #1: periods are valid in version-derived permalinks and must not
        # be stripped (which would turn "2.0" into "20").
        assert kebabify("OAuth 2.0 Spec") == "oauth-2.0-spec"

    def test_trims_leading_trailing_periods(self):
        assert kebabify("spec.") == "spec"
        assert kebabify(".hidden") == "hidden"

    def test_idempotent(self):
        for s in ["API Design", "OAuth 2.0 Spec", "some-note,", "already-kebab"]:
            once = kebabify(s)
            assert kebabify(once) == once


class TestKebabifyPath:
    def test_preserves_slash_segments(self):
        assert kebabify_path("main/specs/API Design") == "main/specs/api-design"

    def test_drops_empty_segments(self):
        assert kebabify_path("a//b") == "a/b"

    def test_preserves_version_in_segment(self):
        assert kebabify_path("specs/OAuth 2.0") == "specs/oauth-2.0"


class TestPluralizeCategories:
    def test_maps_each_error_category_to_plural(self):
        for singular in ERROR_SINGULAR_CATEGORIES:
            plural = SINGULAR_TO_PLURAL[singular]
            line = f"- [{singular}] some observation"
            assert pluralize_categories(line) == f"- [{plural}] some observation"

    def test_plural_forms_unchanged(self):
        line = "- [decisions] already plural"
        assert pluralize_categories(line) == line

    def test_idempotent(self):
        line = "- [decision] a choice"
        once = pluralize_categories(line)
        assert pluralize_categories(once) == once

    def test_skips_grep_and_search_lines(self):
        # Search/grep examples reference categories as literals, not observations.
        for line in [
            'grep for "[decision]" in notes',
            'search_notes(query="[decision]")',
            'edit_note(query="[fact]")',
        ]:
            assert pluralize_categories(line) == line

    def test_transforms_observation_line_that_mentions_pattern(self):
        # BUG #4: a real observation must be checked/fixed even if the line
        # contains the word "pattern" (previously a blanket skip token).
        line = "- [decision] adopt the pattern"
        assert pluralize_categories(line) == "- [decisions] adopt the pattern"

    def test_transforms_observation_mentioning_grep_as_prose(self):
        # BUG B3: the bare word "grep" in prose must not suppress the transform;
        # only real grep *invocations* (quoted/flagged) are skipped.
        line = "- [decision] prefer grep over find"
        assert pluralize_categories(line) == "- [decisions] prefer grep over find"


class TestIsCategoryContextLine:
    def test_bare_pattern_word_is_not_skipped(self):
        # BUG #4: the plain word "pattern" must no longer suppress checks.
        assert is_category_context_line("- [decision] adopt the pattern") is False

    def test_bare_grep_word_is_not_skipped(self):
        # BUG B3: "grep" as an English word (no invocation) must not skip a line.
        assert is_category_context_line("- [decision] prefer grep over find") is False

    def test_search_invocations_are_skipped(self):
        assert is_category_context_line('search_notes(query="x")') is True
        assert is_category_context_line("grep '[fact]' notes") is True
        assert is_category_context_line('grep "[fact]" notes') is True
        assert is_category_context_line("grep -n '[fact]' notes") is True


class TestHasInvalidKebabPunctuation:
    def test_flags_hard_punctuation(self):
        for t in ["a,b", "a:b", "a;b", "a!b", "a?b", "a(b)", "a[b]"]:
            assert has_invalid_kebab_punctuation(t) is True

    def test_allows_periods_slashes_placeholders(self):
        for t in ["oauth-2.0-spec", "a/b/c", "<Related Character>", "{exact_title}", "..."]:
            assert has_invalid_kebab_punctuation(t) is False
