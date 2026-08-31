"""Shared canonicalization conventions for Basic Memory guide/skill alignment.

This module is the single source of truth for the two mechanical preference
conventions applied to both the personalized AI assistant guides and the
installed Basic Memory skills:

  1. kebab-case identifiers (wiki-link targets, title=/identifier= params,
     memory:// URLs)
  2. plural observation categories

Both the validator (`scripts.guide_validation`) and the transformer
(`scripts.align_skills`) import from here so that what the fixer produces
is exactly what the checker accepts. Keeping the definitions here prevents the
checker/fixer drift that previously allowed an invalid kebab permalink (a
trailing comma) to pass validation.
"""

from __future__ import annotations

import re

# --- Category conventions -------------------------------------------------

# Singular -> plural observation category map. This is the canonical mapping;
# the validator flags the keys, the transformer rewrites keys to values.
# Every value is already plural, so applying the map is idempotent: a second
# pass finds no singular keys to rewrite.
SINGULAR_TO_PLURAL: dict[str, str] = {
    "fact": "facts",
    "idea": "ideas",
    "decision": "decisions",
    "technique": "techniques",
    "requirement": "requirements",
    "insight": "insights",
    "problem": "problems",
    "solution": "solutions",
    "question": "questions",
    "feature": "features",
    "capability": "capabilities",
    "guideline": "guidelines",
    "implementation": "implementations",
    "integration": "integrations",
    "preference": "preferences",
    "reference": "references",
    "specification": "specifications",
    "example": "examples",
    "repository": "repositories",
    "risk": "risks",
    "action": "actions",
    "plan": "plans",
    "recommendation": "recommendations",
    "lesson": "lessons",
    "concern": "concerns",
    "stakeholder": "stakeholders",
    "pattern": "patterns",
    "tradeoff": "tradeoffs",
}

# Singular categories the validator treats as hard errors. This is a subset of
# the map keys: only categories that are unambiguously observation categories
# in the guides/skills (avoids false positives on words like "status" that are
# often schema field values rather than categories).
ERROR_SINGULAR_CATEGORIES: list[str] = [
    "fact",
    "idea",
    "decision",
    "technique",
    "requirement",
    "insight",
    "problem",
    "solution",
    "question",
    "feature",
    "capability",
    "guideline",
    "implementation",
    "integration",
    "preference",
    "reference",
    "specification",
    "example",
    "repository",
]

# A line is skipped for category checks/transforms only when it is clearly a
# search/grep example rather than a real observation. Tokens are deliberately
# specific (`search_notes(`, `query=`) rather than bare words like "pattern" or
# "query": a plain observation such as `- [decision] adopt the pattern` must
# still be checked and fixed, so broad substrings would cause false negatives.
_CATEGORY_SKIP_TOKENS = ("search_notes(", "query=")


def is_category_context_line(line: str) -> bool:
    """Return True if the line is a grep/search example that must not be transformed.

    A grep *invocation* (a line that starts with `grep ` or contains a quoted
    grep pattern like `grep '[fact]'`) is a search example and is skipped. The
    bare English word "grep" (e.g. `- [decision] prefer grep over find`) is not,
    so real observations that merely mention grep are still checked/fixed.
    """
    lower = line.lower()
    if any(tok in lower for tok in _CATEGORY_SKIP_TOKENS):
        return True
    if lower.lstrip().startswith("grep "):
        return True
    return "grep '" in lower or 'grep "' in lower


def pluralize_categories(line: str, categories: dict[str, str] | None = None) -> str:
    """Rewrite singular `[category]` labels to their plural form on one line.

    Only rewrites exact `[singular]` tokens present in the map, so the operation
    is idempotent (plural forms are never matched). Skips grep/pattern lines.
    """
    if is_category_context_line(line):
        return line
    cats = categories or SINGULAR_TO_PLURAL

    def _sub(m: re.Match[str]) -> str:
        singular = m.group(1)
        return f"[{cats[singular]}]"

    pattern = re.compile(r"\[(" + "|".join(re.escape(k) for k in cats) + r")\]")
    return pattern.sub(_sub, line)


# --- Kebab-case identifier conventions ------------------------------------

# A multi-word Title-Case `memory://` path that must be kebab-cased. Shared by
# the transformer and the validator so what the fixer produces is exactly what
# the checker accepts (no drift). Rules:
#   - The first word contains an uppercase letter (a real Title-Case/acronym
#     word), preceded by an optional scope/path prefix.
#   - Each subsequent space-separated word starts with an uppercase letter OR a
#     digit, so version numbers like "2.0" are captured (bug B1) while prose
#     stops the match at the first lowercase word (e.g. "My Note where ..." only
#     captures "My Note").
#   - Periods are allowed in the charset so versions survive; spaces are the
#     word separator. Wildcards (*) and comment hashes (#) are excluded so the
#     match never consumes them.
MEMORY_URL_TITLE_CASE = re.compile(
    r"memory://([A-Za-z0-9._/-]*[A-Z][A-Za-z0-9._/-]*(?: [A-Z0-9][A-Za-z0-9._/-]*)+)"
)

# Characters permitted in a canonical kebab permalink segment. Periods are kept
# because they are valid in version-derived permalinks (e.g. `oauth-2.0-spec`);
# stripping them would corrupt version numbers ("2.0" -> "20"). This matches
# `has_invalid_kebab_punctuation`, which also treats periods as valid, so the
# transformer produces exactly what the validator accepts. Everything else
# (commas, parens, colons, etc.) is stripped. Forward slashes are preserved by
# callers that handle path-scoped links separately.
_INVALID_KEBAB_CHARS = re.compile(r"[^a-z0-9.\-]")
_MULTI_HYPHEN = re.compile(r"-{2,}")


def kebabify(text: str) -> str:
    """Canonicalize a single identifier segment to kebab-case.

    - lowercases
    - converts whitespace and underscores to hyphens
    - strips all punctuation except periods (fixes the trailing-comma class of
      bug while preserving version numbers like "2.0")
    - collapses runs of hyphens and trims leading/trailing hyphens and periods
    """
    text = text.strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = _INVALID_KEBAB_CHARS.sub("", text)
    text = _MULTI_HYPHEN.sub("-", text)
    return text.strip("-.")


def kebabify_path(text: str) -> str:
    """Kebab-case an identifier that may contain path separators.

    Handles a project-scope prefix (e.g. "main/specs/API Design"). Each
    `/`-separated segment is kebab-cased independently; slashes are preserved.
    """
    return "/".join(kebabify(seg) for seg in text.split("/") if seg != "")


def has_invalid_kebab_punctuation(target: str) -> bool:
    """Return True if a wiki-link target contains artifact punctuation.

    Such punctuation indicates a transform artifact rather than a legitimate
    permalink.

    Deliberately conservative to avoid false positives on legitimate content:
      - Ignores path slashes (`/`) and angle-bracket placeholders (`<name>`).
      - Ignores template placeholders containing braces (e.g. `{exact_title}`).
      - Ignores pure syntax illustrations like `...`.
      - Ignores periods, which are valid in version-derived permalinks
        (e.g. `oauth-2.0-spec`).
    It flags the "hard" punctuation that no convention should leave in a link:
    commas, colons, semicolons, bang/question marks, parentheses, and brackets.
    The comma is the specific artifact class this check was added to catch.
    """
    # Skip obvious non-links: template placeholders and ellipsis illustrations.
    if "{" in target or "}" in target:
        return False
    if target.strip().strip(".") == "":  # e.g. "..."
        return False
    stripped = target.replace("/", "").replace("<", "").replace(">", "")
    return bool(re.search(r"[,:;!?()\[\]]", stripped))
