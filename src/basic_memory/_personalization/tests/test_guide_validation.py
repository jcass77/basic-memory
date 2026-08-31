"""Unit tests for the guide/skill validation checks.

Previously these checks were exercised only indirectly via the transformer
round-trip; these cases test them directly (review S2), including the versioned
memory-url case from bug B1.
"""

from scripts import guide_validation as gv


class TestMemoryUrlCheck:
    def test_flags_plain_title_case(self):
        result = gv.check_title_case_memory_urls(["see memory://My Note Title here"])
        assert [v.match for v in result.violations] == ["My Note Title"]

    def test_flags_versioned_title_case(self):
        # B1: a version number inside a Title-Case memory URL must be flagged.
        result = gv.check_title_case_memory_urls(["spec at memory://OAuth 2.0 Spec"])
        assert [v.match for v in result.violations] == ["OAuth 2.0 Spec"]

    def test_stops_at_lowercase_prose(self):
        result = gv.check_title_case_memory_urls(["memory://My Note where we left off"])
        assert [v.match for v in result.violations] == ["My Note"]

    def test_ignores_kebab_url(self):
        assert not gv.check_title_case_memory_urls(["memory://oauth-2.0-spec"]).violations

    def test_ignores_single_word_url(self):
        assert not gv.check_title_case_memory_urls(["memory://Notes"]).violations


class TestTitleAndIdentifierChecks:
    def test_flags_acronym_first_title(self):
        result = gv.check_title_case_titles_multi(['title="API Design"'])
        assert [v.match for v in result.violations] == ["API Design"]

    def test_flags_acronym_first_identifier(self):
        result = gv.check_title_case_identifiers_multi(['identifier="API Design"'])
        assert [v.match for v in result.violations] == ["API Design"]

    def test_ignores_kebab_title(self):
        assert not gv.check_title_case_titles_multi(['title="api-design"']).violations


class TestSingularCategories:
    def test_flags_singular(self):
        assert gv.check_singular_categories(["- [decision] a choice"]).violations

    def test_ignores_plural(self):
        assert not gv.check_singular_categories(["- [decisions] a choice"]).violations

    def test_skips_grep_invocation(self):
        assert not gv.check_singular_categories(["grep '[decision]' notes"]).violations

    def test_regex_metachar_category_does_not_crash(self, monkeypatch):
        # S2: categories are escaped with re.escape, so a metacharacter-bearing
        # category is matched literally rather than compiled as a regex.
        monkeypatch.setattr(gv, "SINGULAR_CATEGORIES", ["a.b(c"])
        result = gv.check_singular_categories(["- [a.b(c] weird category"])
        assert [v.match for v in result.violations] == ["[a.b(c]"]
