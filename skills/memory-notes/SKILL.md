---
name: memory-notes
description: "How to write well-structured Basic Memory notes: frontmatter, observations with semantic categories, relations with wiki-links, and best practices for building a rich knowledge graph. Use when creating or improving notes."
---

# Memory Notes

Write well-structured notes that Basic Memory can parse into a searchable knowledge graph. Every note is a markdown file with three key sections: frontmatter, observations, and relations.

## Note Anatomy

```markdown
---
title: API Design Decisions
tags: [api, architecture, decisions]
---

# API Design Decisions

The API team evaluated multiple approaches for the public API during Q1. After
prototyping both REST and GraphQL, the team chose REST due to broader ecosystem
support and simpler caching semantics. This note captures the key decisions and
their rationale, along with open questions still to resolve.

## Observations
- [decisions] Use REST over GraphQL for simplicity #api
- [requirements] Must support versioning from day one
- [risks] Rate limiting needed for public endpoints

## Relations
- implements [[api-specification]]
- depends_on [[authentication-system]]
- relates_to [[performance-requirements]]
```

### Frontmatter

Every note starts with YAML frontmatter:

```yaml
---
title: Note Title          # required — becomes the entity name in the knowledge graph
tags: [tag1, tag2]         # optional — for organization and filtering
type: note                 # optional — defaults to "note", use custom types with schemas
permalink: custom-path     # optional — auto-generated from title if omitted
---
```

- The `title` must match the `# Heading` in the body
- Tags are searchable and help with discovery
- Custom `type` values (Task, Meeting, Person, etc.) work with the schema system. See the **memory-schema** skill for defining schemas, validating notes against them, and detecting drift.
- The `permalink` is auto-generated from the `title` and `directory`. For example, title "API Design Decisions" in directory "specs" produces permalink `specs/api-design-decisions` and memory URL `memory://specs/api-design-decisions`. If no directory is specified, the permalink is just the kebab-cased title. By default permalinks stay stable across file moves (unless the project enables `update_permalinks_on_move`). You rarely need to set one manually.

> **Note:** When using `write_note`, you don't write frontmatter yourself. The `title`, `tags`, `note_type`, and `metadata` are separate parameters — Basic Memory generates the frontmatter automatically. Your `content` parameter is just the markdown body starting with `# Heading`.

### Body / Context

Free-form markdown between the heading and the Observations section. This is the heart of the note — write generously here:
- Background, motivation, and history
- Detailed explanation of what happened and why it matters
- Analysis, reasoning, and trade-offs considered
- Context that someone (or an AI) needs to understand this note later

Write complete, substantive prose. Basic Memory's search retrieves relevant chunks from note bodies, so longer, richer context makes notes more discoverable and more useful when found. Don't reduce everything to bullet points — tell the story.

## Observations

Observations are categorized facts — the atomic units of knowledge. Each one becomes a searchable entity in the knowledge graph.

### Syntax

```
- [category] Content of the observation #optional-tag
```

- **Square brackets** define the semantic category
- **Content** is the fact, decision, insight, or note
- **Hash tags** (optional) add extra metadata for filtering

### Categories Are Free-Form but Conventional

The category in brackets is free-form — there is no fixed list, so use whatever label makes sense for the observation. The only hard rule is the `[category] content` syntax. By convention, always write category names as **plural, lowercase** words (e.g. `[decisions]`, `[risks]`, `[techniques]`) because that consistency keeps observations searchable and the knowledge graph coherent. Invent new categories freely when a domain-specific type is genuinely needed, keeping the same plural-lowercase form.

A few examples to illustrate the range:

```
- [decisions] Use PostgreSQL for primary data store
- [risks] Third-party API has no SLA guarantee
- [techniques] Exponential backoff for retry logic #resilience
- [questions] Should we support multi-tenancy at the DB level?
- [preferences] Use Bun over Node for new projects
- [lessons] Always validate webhook signatures server-side
- [status] active
- [flavor] Ethiopian beans work best with lighter roasts
```

### Observation Tips

- **One fact per observation.** Don't pack multiple ideas into one line.
- **Be specific.** `[decisions] Use JWT` is less useful than `[decisions] Use JWT with 15-minute expiry for API auth`.
- **Use tags for cross-cutting concerns.** `[risks] Rate limiting needed #api #security` makes this findable under both topics.
- **Categories are queryable.** `search_notes(entity_types=["observation"], categories=["decision"])` returns every decision observation across your knowledge base.

## Relations

Relations create edges in the knowledge graph, linking notes to each other. They're how you build structure beyond individual notes.

### Syntax

```
- relation_type [[target-note-title]]
```

- **relation_type** is a descriptive verb or phrase (snake_case by convention)
- **Double brackets** `[[...]]` identify the target note by title or permalink
- Relations are directional: this note → target note

### Relation Types

| Type | Purpose | Example |
|------|---------|---------|
| `implements` | One thing implements another | `- implements [[auth-spec]]` |
| `requires` | Dependencies | `- requires [[database-setup]]` |
| `relates_to` | General connection | `- relates_to [[performance-notes]]` |
| `part_of` | Hierarchy/composition | `- part_of [[backend-architecture]]` |
| `extends` | Enhancement or elaboration | `- extends [[base-config]]` |
| `pairs_with` | Things that work together | `- pairs_with [[frontend-client]]` |
| `inspired_by` | Source material | `- inspired_by [[crdt-research-paper]]` |
| `replaces` | Supersedes another note | `- replaces [[old-auth-design]]` |
| `depends_on` | Runtime/build dependency | `- depends_on [[mcp-sdk]]` |
| `contrasts_with` | Alternative approaches | `- contrasts_with [[graphql-approach]]` |

### Inline Relations

Wiki-links anywhere in the note body — not just the Relations section — also create graph edges:

```markdown
We evaluated [[graphql-approach]] but decided against it because
the team has more experience with REST. See [[api-specification]]
for the full contract.
```

These create `references` relations automatically. Use the Relations section for explicit, typed relationships; use inline links for natural prose references.

### Relation Tips

- **Link liberally.** Relations are what turn isolated notes into a knowledge graph. When in doubt, add the link.
- **Link only to notes that already exist.** Confirm the target note's exact title before adding `[[target]]` — forward references to not-yet-created notes create broken links and degrade the graph.
- **Use `build_context` to traverse.** `build_context(url="memory://note-title")` follows relations to gather connected knowledge.
- **Custom relation types are fine.** `taught_by`, `blocks`, `tested_in` — use whatever is descriptive.

## Memory URLs

Every note is addressable via a `memory://` URL, built from its permalink. These URLs are how you navigate the knowledge graph programmatically.

### URL Patterns

```
memory://api-design-decisions          # by permalink (title → kebab-case)
memory://docs/authentication           # by file path
memory://docs/authentication.md        # with extension (also works)
memory://auth*                         # wildcard prefix
memory://docs/*                        # wildcard suffix
memory://project/*/requirements        # path wildcards
```

### Project-Scoped URLs

In multi-project setups, prefix with the project name:

```
memory://main/specs/api-design         # "main" project, "specs/api-design" path
memory://research/papers/crdt          # "research" project
```

The first path segment is matched against known project names. If it matches, it's used as the project scope. Otherwise the URL resolves in the default project.

### Using Memory URLs

Memory URLs work with `build_context` to assemble related knowledge by traversing relations:

```python
# Get a note and its connected context
build_context(url="memory://api-design-decisions")

# Wildcard — gather all docs
build_context(url="memory://docs/*")

# Direct read by permalink
read_note(identifier="memory://api-design-decisions")
```

## Before Creating a Note

Always search Basic Memory before creating a new note. Duplicates fragment your knowledge graph — updating an existing note is almost always better than creating a second one.

### Search with Multiple Variations

A single search often misses. Try the full name, abbreviations, acronyms, and keywords:

```python
# Searching for an entity that might already exist
search_notes(query="Kubernetes Migration")
search_notes(query="k8s migration")
search_notes(query="container migration")
```

For people, try full name and last name. For organizations, try the full name and common abbreviations.

### Decision Tree

- **Entity exists** → Update it with `edit_note` (append observations, add relations, find-and-replace outdated info)
- **Entity doesn't exist** → Create it with `write_note`
- **Unsure if it's the same entity** → Read the existing note first, then decide

### Granular Updates with `edit_note`

When a note already exists, make targeted edits instead of rewriting the whole file:

```python
# Add a new observation under the existing Observations heading
edit_note(
  identifier="api-design-decisions",
  operation="insert_after_section",
  section="Observations",
  content="- [decisions] Switched to OpenAPI 3.1 for spec generation #api"
)

# Fix outdated information
edit_note(
  identifier="api-design-decisions",
  operation="find_replace",
  find_text="- [status] draft",
  content="- [status] approved"
)

# Add a new relation
edit_note(
  identifier="api-design-decisions",
  operation="insert_after_section",
  section="Relations",
  content="- depends_on [[rate-limiter]]"
)
```

This preserves existing content and keeps the edit history clean.

## Writing Notes with Tools

### Creating a Note

```python
write_note(
  title="api-design-decisions",
  directory="architecture",
  tags=["api", "architecture"],
  content="""# API Design Decisions

The API team evaluated REST and GraphQL during Q1 planning. After prototyping
both approaches, we chose REST for the public API — broader ecosystem support,
simpler caching with HTTP semantics, and a lower learning curve for external
consumers. GraphQL remains an option for internal services where query
flexibility matters more.

## Observations
- [decisions] Use REST for public API #api
- [requirements] Support API versioning from v1

## Relations
- implements [[api-specification]]
- relates_to [[backend-architecture]]"""
)
```

Basic Memory auto-generates frontmatter (including the permalink and memory URL) from the parameters. This note would get permalink `architecture/api-design-decisions` and be addressable at `memory://architecture/api-design-decisions`.

### Editing an Existing Note

Use `edit_note` to update a note in place — six operations: `append`, `prepend`,
`find_replace`, `replace_section`, `insert_before_section`, `insert_after_section`.

```python
# insert_after_section / insert_before_section — add lines at an existing heading
edit_note(
  identifier="api-design-decisions",
  operation="insert_after_section",
  section="Observations",
  content="- [decisions] Use OpenAPI 3.1 for spec generation #api"
)

# append / prepend — add to the end of the note or the start of the body
# (use for time-ordered logs; neither one targets a section)
edit_note(
  identifier="api-design-decisions",
  operation="prepend",
  content="> Updated 2026-05-28: auth approach finalized.\n"
)

# replace_section — rewrite a named section (use for living content that stays current)
edit_note(
  identifier="api-design-decisions",
  operation="replace_section",
  section="Summary",
  content="Concise, current summary of the decision and its rationale."
)

# find_replace — swap specific text
edit_note(
  identifier="api-design-decisions",
  operation="find_replace",
  find_text="OpenAPI 3.0",
  content="OpenAPI 3.1"
)
```

When an edit is destructive (`replace_section`, `find_replace`), it's good practice to
read the note first and confirm the change before applying it.

### Moving a Note

Use `move_note` to reorganize notes into different directories:

```python
move_note(
  identifier="api-design-decisions",
  destination_path="archive/api-design-decisions.md"
)
```

By default the permalink stays the same after a move, so links keep resolving. Projects with `update_permalinks_on_move` enabled rewrite it from the new path.

## Best Practices

1. **Start with context.** Before listing observations, explain *why* this note exists. Future-you (or your AI collaborator) will thank you.

2. **Favor completeness.** Write rich, substantive notes. Basic Memory's search pulls relevant chunks from note bodies, so longer notes with more context are *more* discoverable, not less. Use prose in the body to tell the full story — the background, the reasoning, the nuance. Then distill key facts into `[category] content` observations for structured queries. Both matter: prose gives meaning, observations give precision.

3. **Build incrementally.** Add to existing notes rather than creating duplicates. Use `edit_note` to append new observations or relations as you learn more.

4. **Use consistent titles.** Note titles are identifiers in the knowledge graph. `API Design Decisions` and `Api Design decisions` are different entities. Pick a convention and stick with it.

5. **Link related concepts.** The value of a knowledge graph compounds with connections. A note with zero relations is an island — useful, but not as powerful as a connected one.

6. **Let the graph grow naturally.** Don't try to design a perfect taxonomy upfront. Write notes as you work, add relations as connections emerge, and periodically use the **memory-reflect** or **memory-defrag** skills to consolidate.
