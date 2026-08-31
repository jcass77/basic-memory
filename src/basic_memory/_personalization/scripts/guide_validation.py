"""Validate personalized Basic Memory AI assistant guides against preference conventions.

Output: JSON with errors (definite violations) and warnings (ambiguous, needs investigation).
Exit code: 1 if errors exist, 0 otherwise (warnings don't fail).
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict

from scripts.conventions import (
    ERROR_SINGULAR_CATEGORIES,
    MEMORY_URL_TITLE_CASE,
    has_invalid_kebab_punctuation,
    is_category_context_line,
)

DEFAULT_GUIDES = [
    "docs/ai-assistant-guide-extended.md",
    "src/basic_memory/mcp/resources/ai_assistant_guide.md",
]

# The git-tracked basic-memory skills live in this repo under ./skills/. The
# --skills flag globs these so the same convention checks that guard the guides
# also guard skills.
DEFAULT_SKILLS_ROOT = "skills"
DEFAULT_SKILLS_PATTERN = "memory-*/SKILL.md"

# Error-level detection uses the curated subset of unambiguous observation
# categories (avoids false positives on words like "status"). This subset is a
# subset of the transformer's full singular->plural map, so everything the
# checker flags as an error is something the fixer can rewrite — the checker
# never reports an error the fixer cannot resolve.
SINGULAR_CATEGORIES = ERROR_SINGULAR_CATEGORIES


@dataclass
class Violation:
    """A single convention violation found on one line of a guide."""

    line_num: int
    line: str
    match: str


@dataclass
class CheckResult:
    """The outcome of running one named check across a guide's lines."""

    name: str
    description: str
    severity: str  # "error" or "warning"
    violations: list[Violation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Return True if the check found no violations."""
        return len(self.violations) == 0

    def to_dict(self) -> dict[str, object]:
        """Serialise the result to a JSON-friendly dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "passed": self.passed,
            "violation_count": len(self.violations),
            "violations": [
                {"line": v.line_num, "match": v.match, "context": v.line} for v in self.violations
            ],
        }


# --- ERROR checks (definite violations) ---


def check_title_case_wikilinks_multi(lines: list[str]) -> CheckResult:
    """Wiki-links with spaces are definite Title Case violations."""
    result = CheckResult(
        "title-case-wikilinks-multi", "Wiki-links with spaces must use kebab-case", "error"
    )
    pattern = re.compile(r"\[\[[^\]]*\s[^\]]*\]\]")
    for i, line in enumerate(lines, 1):
        for m in pattern.finditer(line):
            result.violations.append(Violation(i, line.rstrip(), m.group()))
    return result


def check_title_case_identifiers_multi(lines: list[str]) -> CheckResult:
    """Flag identifier= params with uppercase-and-space as definite violations."""
    result = CheckResult(
        "title-case-identifiers-multi", "Multi-word identifier= params must use kebab-case", "error"
    )
    pattern = re.compile(r'identifier="([A-Z][A-Za-z0-9]* [A-Z][^"]*)"')
    for i, line in enumerate(lines, 1):
        for m in pattern.finditer(line):
            result.violations.append(Violation(i, line.rstrip(), m.group(1)))
    return result


def check_title_case_memory_urls(lines: list[str]) -> CheckResult:
    """memory:// URLs with uppercase + space are definite violations."""
    result = CheckResult(
        "title-case-memory-urls", "memory:// URLs with spaces must use kebab-case", "error"
    )
    for i, line in enumerate(lines, 1):
        for m in MEMORY_URL_TITLE_CASE.finditer(line):
            result.violations.append(Violation(i, line.rstrip(), m.group(1)))
    return result


def check_title_case_titles_multi(lines: list[str]) -> CheckResult:
    """title= params with uppercase + space are definite violations."""
    result = CheckResult(
        "title-case-title-params-multi", "Multi-word title= params must use kebab-case", "error"
    )
    pattern = re.compile(r'title="([A-Z][A-Za-z0-9]* [A-Z][^"]*)"')
    for i, line in enumerate(lines, 1):
        for m in pattern.finditer(line):
            result.violations.append(Violation(i, line.rstrip(), m.group(1)))
    return result


def check_singular_categories(lines: list[str]) -> CheckResult:
    """Singular observation categories are definite violations."""
    result = CheckResult("singular-categories", "Observation categories must be plural", "error")
    cat_pattern = re.compile(r"\[(" + "|".join(re.escape(c) for c in SINGULAR_CATEGORIES) + r")\]")
    for i, line in enumerate(lines, 1):
        if is_category_context_line(line):
            continue
        for m in cat_pattern.finditer(line):
            result.violations.append(Violation(i, line.rstrip(), m.group()))
    return result


def check_kebab_punctuation(lines: list[str]) -> CheckResult:
    """Flag wiki-link targets containing punctuation invalid in a kebab permalink.

    Invalid punctuation includes commas, periods, parens, etc. Catches transform
    artifacts like the trailing comma that previously slipped past the
    Title-Case checks.
    """
    result = CheckResult(
        "kebab-punctuation",
        "Wiki-link targets must not contain invalid permalink punctuation",
        "error",
    )
    link_pattern = re.compile(r"\[\[([^\]]+)\]\]")
    for i, line in enumerate(lines, 1):
        for m in link_pattern.finditer(line):
            if has_invalid_kebab_punctuation(m.group(1)):
                result.violations.append(Violation(i, line.rstrip(), m.group()))
    return result


def check_forward_references(lines: list[str]) -> CheckResult:
    """Flag forward-reference *encouragement*, not any mention of the phrase.

    The prior version skipped lines containing a small denylist of words, which
    incorrectly flagged correct explanatory prose (e.g. "linking to a note that
    was never created leaves a broken link"). This version only flags positive
    encouragement patterns, mirroring the content-contradictions check, so a
    preference-aligned explanation never trips it.
    """
    result = CheckResult("forward-references", "No forward reference encouragement", "error")
    encouragement = re.compile(
        r"(forward references? (?:are|is) (?:fine|ok|okay|valid|encouraged|supported)|"
        r"(?:feel free to|you can|it'?s fine to) (?:use |create )?forward references?|"
        r"reference (?:entities|notes) that don'?t exist yet)",
        re.IGNORECASE,
    )
    for i, line in enumerate(lines, 1):
        for m in encouragement.finditer(line):
            result.violations.append(Violation(i, line.rstrip(), m.group()))
    return result


def check_content_contradictions(lines: list[str]) -> CheckResult:
    """Detect philosophical contradictions that mechanical transforms CANNOT fix.

    These require a human/agent content-rewrite decision, not a find/replace.
    Two known classes, drawn from user-preferences.md:
      1. "categories are arbitrary / free-form / no fixed list" — contradicts the
         controlled-category preference (choose from a common list; extend only
         for domain needs).
      2. Positive forward-reference encouragement phrased as resolution-later
         (e.g. "valid - BM will resolve it when that note is created", "create
         target notes if they don't exist yet") — contradicts the relations-to-
         existing-notes-only preference.
    Reported as errors, but with a distinct check name so the SOP routes them to
    a content-rewrite gate rather than an automated transform.
    """
    result = CheckResult(
        "content-contradictions",
        "Philosophical contradictions requiring content rewrite (not mechanical fixes)",
        "error",
    )
    arbitrary_category = re.compile(
        r"(categor(?:y|ies)\s+(?:are|is)\s+arbitrary|"
        r"categor(?:y|ies)[^.]*\bfree-form|\bfree-form\b[^.]*categor|"
        r"no fixed list|invent categories)",
        re.IGNORECASE,
    )
    fwd_ref_encouragement = re.compile(
        r"(don'?t exist yet.*valid|valid.*resolve it when|resolve.*when that note is created|"
        r"create target notes if they don'?t exist)",
        re.IGNORECASE,
    )
    for i, line in enumerate(lines, 1):
        for pat in (arbitrary_category, fwd_ref_encouragement):
            for m in pat.finditer(line):
                result.violations.append(Violation(i, line.rstrip(), m.group()))
    return result


# --- WARNING checks (ambiguous, needs agent investigation) ---


def check_title_case_wikilinks_single(lines: list[str]) -> CheckResult:
    """Single-word Title Case wiki-links may be intentional (e.g., proper nouns)."""
    result = CheckResult(
        "title-case-wikilinks-single",
        "Single-word Title Case wiki-links (may be intentional)",
        "warning",
    )
    pattern = re.compile(r"\[\[([A-Z][a-z]{2,})\]\]")
    for i, line in enumerate(lines, 1):
        if "WikiLink" in line:
            continue
        for m in pattern.finditer(line):
            result.violations.append(Violation(i, line.rstrip(), m.group()))
    return result


def check_title_case_identifiers_single(lines: list[str]) -> CheckResult:
    """Single-word Title Case identifiers may be intentional."""
    result = CheckResult(
        "title-case-identifiers-single",
        "Single-word Title Case identifier= params (may be intentional)",
        "warning",
    )
    pattern = re.compile(r'identifier="([A-Z][a-z]{2,})"')
    for i, line in enumerate(lines, 1):
        for m in pattern.finditer(line):
            result.violations.append(Violation(i, line.rstrip(), m.group(1)))
    return result


def check_title_case_titles_single(lines: list[str]) -> CheckResult:
    """Single-word Title Case title= params may be intentional."""
    result = CheckResult(
        "title-case-title-params-single",
        "Single-word Title Case title= params (may be intentional)",
        "warning",
    )
    pattern = re.compile(r'title="([A-Z][a-z]{2,})"')
    for i, line in enumerate(lines, 1):
        for m in pattern.finditer(line):
            result.violations.append(Violation(i, line.rstrip(), m.group(1)))
    return result


def check_title_case_positional_single(lines: list[str]) -> CheckResult:
    """Single-word Title Case positional args may be intentional."""
    result = CheckResult(
        "title-case-positional-single",
        "Single-word Title Case function args (may be intentional)",
        "warning",
    )
    pattern = re.compile(r'(?:read_note|move_note|edit_note)\("([A-Z][a-z]{2,})"')
    for i, line in enumerate(lines, 1):
        for m in pattern.finditer(line):
            result.violations.append(Violation(i, line.rstrip(), m.group(1)))
    return result


def check_append_in_error_context(lines: list[str]) -> CheckResult:
    """operation="append" near error handling may indicate find_replace should be preferred."""
    result = CheckResult(
        "append-in-error-context",
        'operation="append" near error handling (find_replace preferred)',
        "warning",
    )
    pattern = re.compile(r'operation="append"')
    for i, line in enumerate(lines, 1):
        match = pattern.search(line)
        if not match:
            continue
        context_start = max(0, i - 5)
        context_window = "\n".join(lines[context_start:i]).lower()
        if any(
            p in context_window for p in ["already exists", "# preferred", "# solution", "# fix"]
        ):
            result.violations.append(Violation(i, line.rstrip(), match.group()))
    return result


ALL_CHECKS = [
    # Errors
    check_title_case_wikilinks_multi,
    check_title_case_identifiers_multi,
    check_title_case_memory_urls,
    check_title_case_titles_multi,
    check_singular_categories,
    check_kebab_punctuation,
    check_forward_references,
    check_content_contradictions,
    # Warnings
    check_title_case_wikilinks_single,
    check_title_case_identifiers_single,
    check_title_case_titles_single,
    check_title_case_positional_single,
    check_append_in_error_context,
]


class GuideReport(TypedDict):
    """The full validation report for a single guide file."""

    file: str
    exists: bool
    checks: list[dict[str, object]]
    error_count: int
    warning_count: int


def validate_guide(path: Path) -> GuideReport:
    """Run every check against one guide file and return a result summary."""
    if not path.exists():
        return {
            "file": str(path),
            "exists": False,
            "checks": [],
            "error_count": 0,
            "warning_count": 0,
        }

    lines = path.read_text(encoding="utf-8").splitlines()
    results = [check(lines) for check in ALL_CHECKS]

    return {
        "file": str(path),
        "exists": True,
        "checks": [r.to_dict() for r in results],
        "error_count": sum(len(r.violations) for r in results if r.severity == "error"),
        "warning_count": sum(len(r.violations) for r in results if r.severity == "warning"),
    }


def main() -> int:
    """Validate the requested guide/skill files and print a JSON report."""
    args = sys.argv[1:]

    if "--skills" in args:
        args = [a for a in args if a != "--skills"]
        skills_root = Path(DEFAULT_SKILLS_ROOT).expanduser()
        skill_paths = sorted(skills_root.glob(DEFAULT_SKILLS_PATTERN))
        paths = skill_paths + [Path(p) for p in args]
        if not paths:
            print(
                json.dumps(
                    {
                        "files": [],
                        "summary": {
                            "total_files": 0,
                            "total_errors": 0,
                            "total_warnings": 0,
                            "passed": True,
                        },
                        "note": f"No skills matched {DEFAULT_SKILLS_ROOT}/{DEFAULT_SKILLS_PATTERN}",
                    },
                    indent=2,
                )
            )
            return 0
    elif args:
        paths = [Path(p) for p in args]
    else:
        paths = [Path(p) for p in DEFAULT_GUIDES]

    files = [validate_guide(p) for p in paths]
    total_errors = sum(f["error_count"] for f in files)
    total_warnings = sum(f["warning_count"] for f in files)

    output = {
        "files": files,
        "summary": {
            "total_files": len(files),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "passed": total_errors == 0,
        },
    }

    print(json.dumps(output, indent=2))
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
