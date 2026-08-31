# AI Assistant Guide for Basic Memory - Extended Edition

**This is the comprehensive guide for AI assistants using Basic Memory through MCP.**

> **User Preference Note**: When presenting note content for review, use `view_note()` instead of `read_note()` because formatted artifacts improve readability.

> **Note for Developers**: This guide is organized into self-contained sections. You can copy/paste individual sections to create customized guides for specific use cases or AI assistants. Each section is designed to stand alone while also working as part of the complete guide.

## Table of Contents

1. [Understanding Basic Memory](#understanding-basic-memory)
2. [Project Management](#project-management)
3. [Knowledge Graph Fundamentals](#knowledge-graph-fundamentals)
4. [Writing Knowledge](#writing-knowledge)
5. [Reading and Navigation](#reading-and-navigation)
6. [Search and Discovery](#search-and-discovery)
7. [Building Context](#building-context)
8. [Recording Conversations](#recording-conversations)
9. [Editing Notes](#editing-notes)
10. [Moving and Organizing](#moving-and-organizing)
11. [Error Handling](#error-handling)
12. [Advanced Patterns](#advanced-patterns)
13. [Tool Reference](#tool-reference)
14. [Best Practices](#best-practices)

---

## Understanding Basic Memory

**Core Concept**: Basic Memory is a local-first knowledge management system that creates a semantic knowledge graph from markdown files. It enables persistent, structured knowledge that survives across AI sessions.

### Key Principles

**Local-First Architecture**
- All knowledge stored as plain text markdown files on user's computer
- SQLite database indexes files for fast search and navigation
- Files are the source of truth, database is derived state
- User maintains complete control over their data

**Semantic Knowledge Graph**
- Entities: Individual markdown files representing concepts
- Observations: Categorized facts with optional tags
- Relations: Directional links between entities
- Graph traversal enables context building and exploration

**Persistent Context**
- Knowledge persists across conversations
- AI can reference previous discussions
- Context builds over time through accumulated knowledge
- Enables long-term collaborative development

### AI as Knowledge Collaborator

Basic Memory's semantic knowledge graph - observations, relations, context building - is designed to help you (the AI assistant) provide better help to humans. You use the graph structure to:
- Build relevant context from past conversations
- Navigate connections between ideas
- Understand relationships and dependencies
- Provide continuity across sessions

**The distinction**: You're helping humans build enduring knowledge they'll own forever, not creating disposable agent memory. The better you use these tools, the more valuable their knowledge becomes over time. Think of markdown files as artifacts that will outlast any particular AI model - your job is to help create knowledge worth keeping.

### Architecture Overview

```
User's Markdown Files (Source of Truth)
         ↓
    File Sync
         ↓
SQLite Database (Index)
         ↓
    MCP Server
         ↓
   AI Assistant
```

**Data Flow**:
1. User creates/edits markdown files
2. Sync process detects changes
3. Files are parsed and indexed in SQLite
4. MCP server exposes indexed data to AI
5. AI can query, traverse, and update knowledge graph
---

## Project Management

**Project Concept**: A project is a directory of markdown files with its own knowledge graph. Users can have multiple independent projects.

### Discovering Projects

**Always start by discovering available projects:**

```python
# List all projects
projects = await list_memory_projects()

# Response structure (each entry includes external_id you can pass as project_id):
# [
#   {
#     "name": "main",
#     "external_id": "550e8400-e29b-41d4-a716-446655440000",
#     "path": "/Users/name/notes",
#     "is_default": True,
#     "note_count": 156,
#     "last_synced": "2025-01-15T10:30:00Z"
#   },
#   {
#     "name": "work",
#     "external_id": "9f86d081-884c-42a3-b5e3-1c0c5b4c8e52",
#     "path": "/Users/name/work-notes",
#     "is_default": False,
#     "note_count": 89,
#     "last_synced": "2025-01-14T16:45:00Z"
#   }
# ]
```

**When to discover projects**:
- Start of conversation when project unknown
- User asks about available projects
- Before any operation requiring project selection
- After errors related to project not found

### Project Selection Patterns

**Resolution priority:**
1. CLI constraint: `BASIC_MEMORY_MCP_PROJECT` env var (highest priority)
2. Explicit parameter: `project_id="<uuid>"` (preferred when known) or `project="name"` in tool calls
3. Default project: `default_project` in config (fallback)

**`project` vs `project_id`:** Every project has a stable `external_id` (UUID) returned by `list_memory_projects()`. Pass it as `project_id=...` to address a project unambiguously — required when the same project name exists in multiple cloud workspaces. For local single-project setups, the `project` name is fine.

**When to prefer `project_id`:**
1. **Cloud multi-workspace setups.** If the user belongs to more than one workspace (personal + organization, or several organizations) and the same project name might exist in more than one of them, pass `project_id` to route to the exact project. Without it, name resolution falls back to the default workspace, which may not be the one the user means.
2. **After `list_memory_projects()`.** Once you have the `external_id`, prefer using it — it's the same number of characters in JSON and saves a name-resolution round-trip.
3. **When persisting a project choice across a long session.** UUIDs are stable; names can be renamed.

**When `project` (name) is fine:**
- Local single-workspace setups (no collision risk).
- One-off operations where the name is clearly visible to the user (e.g., quick `search_notes(project="main", ...)`).
- The user explicitly references a project by name in their message.

**Example — cloud multi-workspace pattern:**

```python
# Discover and pick the right project for this user
projects = await list_memory_projects()
target = next(p for p in projects if p["name"] == "research" and p["workspace"]["slug"] == "acme")

# Use the UUID for all subsequent operations — no ambiguity
await write_note(
    title="meeting-notes",
    content="...",
    folder="meetings",
    project_id=target["external_id"],
)

results = await search_notes(query="kickoff", project_id=target["external_id"])
```

**Precedence rule:** When both are passed, `project_id` wins. This lets you safely supply `project="main"` for backward compatibility while still routing precisely with `project_id`.

**Single-Project Users**:

```python
# Enable default_project_mode in config
# ~/.basic-memory/config.json
{"default_project": "main", "default_project_mode": true}

# Then tools work without project parameter
await write_note("Note", "Content", "folder")
await search_notes(query="test")
```

**Multi-Project Users**:

```python
# Keep default_project_mode disabled (default)
# Always specify project explicitly

# All tool calls require project
await write_note("Note", "Content", "folder", project="main")
await search_notes(query="test", project="work")

# Can target different projects in same conversation
results_main = await search_notes(query="auth", project="main")
results_work = await search_notes(query="auth", project="work")
```

**Recommended Workflow**:

```python
# 1. Discover projects
projects = await list_memory_projects()

# 2. Ask user which to use (if ambiguous)
# "I found 2 projects: 'main' and 'work'. Which should I use?"

# 3. Store choice for session
active_project = "main"

# 4. Use in all subsequent calls
results = await search_notes(query="topic", project=active_project)
```

### Cross-Project Operations

**Some tools work across all projects when project parameter omitted:**

```python
# Recent activity across all projects
activity = await recent_activity(timeframe="7d")
# Returns activity from all projects

# Recent activity for specific project
activity = await recent_activity(timeframe="7d", project="main")
# Returns activity only from "main" project
```

**Tools supporting cross-project mode**:
- `recent_activity()` - aggregate activity across projects
- `list_memory_projects()` - always returns all projects
- `sync_status()` - can show all projects or specific

### Creating Projects

**Create new projects programmatically:**

```python
# Create new project
await create_memory_project(
    project_name="research", project_path="/Users/name/Documents/research", set_default=False
)

# Create and set as default
await create_memory_project(
    project_name="primary", project_path="/Users/name/notes", set_default=True
)
```

**Use cases**:
- User requests new knowledge base
- Separating work/personal notes
- Project-specific documentation
- Client-specific knowledge

### Project Status

**Check sync status before operations:**

```python
# Check if sync complete
status = await sync_status(project="main")

# Response indicates:
# - sync_in_progress: bool
# - files_processed: int
# - files_remaining: int
# - last_sync: datetime
# - errors: list

# Wait for sync if needed
if status["sync_in_progress"]:
    # Inform user: "Sync in progress, please wait..."
    # Or proceed with available data
```

---

## Knowledge Graph Fundamentals

**The knowledge graph is built from three core elements: entities, observations, and relations.**

### Entities

**What is an Entity?**
- Any concept, document, or idea represented as a markdown file
- Has a unique title and permalink
- Contains frontmatter metadata
- Includes observations and relations

**Entity Structure**:

```markdown
---
title: Authentication System
permalink: authentication-system
tags:
- security
- auth
- api
type: note
last updated at: 2025-01-15 09:15
---

# Authentication System

## Context
Brief description of the entity

## Observations
- [category] Facts about this entity

## Relations
- relation_type [[other-entity]]
```

**Entity Types**:
- `note`: General knowledge (default)
- `person`: People and contacts
- `project`: Projects and initiatives
- `meeting`: Meeting notes
- `decision`: Documented decisions
- `spec`: Technical specifications

### Observations

**Observations are categorized facts with optional tags.**

**Syntax**: `- [category] content #tag1 #tag2`

**Common Categories**:
- `[facts]`: Objective information
- `[features]`: Product or system features
- `[guidelines]`: Best practices and standards
- `[ideas]`: Thoughts and concepts
- `[decisions]`: Choices made
- `[examples]`: Example implementations or use cases
- `[techniques]`: Methods and approaches
- `[requirements]`: Needs and constraints
- `[questions]`: Open questions
- `[insights]`: Key realizations
- `[problems]`: Issues identified
- `[solutions]`: Resolutions
- `[implementations]`: Technical implementations
- `[integrations]`: System integrations
- `[knowledge]`: General knowledge and learnings
- `[preferences]`: User preferences and settings
- `[references]`: Reference materials
- `[repositories]`: Code repositories
- `[specifications]`: Technical specifications

**Examples**:

```markdown
## Observations
- [decisions] Use JWT tokens for authentication #security
- [techniques] Hash passwords with bcrypt before storage #best-practice
- [requirements] Support OAuth 2.0 providers (Google, GitHub) #auth
- [facts] Session timeout set to 24 hours #configuration
- [problems] Password reset emails sometimes delayed #bug
- [solutions] Implemented retry queue for email delivery #fix
- [insights] 2FA adoption increased security by 40% #metrics
```

**Why Categorize?**:
- Enables semantic search by observation type
- Helps AI understand context and intent
- Makes knowledge more queryable
- Provides structure for analysis

### Relations

**Relations are directional links between entities.**

**Syntax**: `- relation_type [[target-entity]]`

**Common Relation Types**:
- `relates_to`: General connection
- `implements`: Implementation of spec/design
- `requires`: Dependency relationship
- `extends`: Extension or enhancement
- `part_of`: Hierarchical membership
- `contrasts_with`: Opposite or alternative
- `caused_by`: Causal relationship
- `leads_to`: Sequential relationship
- `similar_to`: Similarity relationship

**Examples**:

```markdown
## Relations
- implements [[authentication-spec-v2]]
- requires [[user-database-schema]]
- extends [[base-security-model]]
- part_of [[api-backend-services]]
- contrasts_with [[api-key-authentication]]
- leads_to [[session-management]]
```

**Bidirectional Links**:

```markdown
# In "login-flow" note
## Relations
- part_of [[authentication-system]]

# In "authentication-system" note
## Relations
- includes [[login-flow]]
```

**Why explicit relation types matter**:
- Enables semantic graph traversal
- AI can understand relationship meaning
- Supports sophisticated context building
- Makes knowledge more navigable

### Relation Integrity

**Create relations only to existing notes:**

Relations should point to notes that already exist in the knowledge graph. Before adding a relation, verify the target note exists by searching for it. This ensures knowledge graph integrity and prevents broken links.

```python
# Verify target exists before creating relation
results = await search_notes(query="api-specification", project="main")

if results["total"] > 0:
    # Target exists, safe to reference
    content = "## Relations\n- implements [[api-specification]]"
else:
    # Create target note first, then add relation
    await write_note(
        title="api-specification",
        content="# api-specification\n...",
        folder="specs",
        project="main",
    )
```

**Best practices**:
- Search for target notes before adding relations
- Create target notes first when building connected knowledge
- Use exact note titles (lowercase kebab-case) in relation references
- Regularly validate knowledge graph for broken links

---

## Writing Knowledge

**Creating rich, well-structured notes is fundamental to building a useful knowledge graph.**

### Basic Note Creation

**Minimal note**:

```python
await write_note(
    title="quick-note",
    content="# Quick Note\n\nSome basic content.",
    folder="notes",
    project="main",
)
```

> **Important**: `write_note` errors if the note already exists. Use `edit_note` for incremental changes, or pass `overwrite=True` to replace.

**Well-structured note**:

```python
await write_note(
    title="database-design-decisions",
    content="""# Database Design Decisions

## Context
Documenting our database architecture choices for the authentication system.

## Observations
- [decisions] PostgreSQL chosen over MySQL for better JSON support #database
- [techniques] Using UUID primary keys instead of auto-increment #design
- [requirements] Must support multi-tenant data isolation #security
- [facts] Expected load is 10K requests/minute #performance
- [insights] UUID keys enable easier horizontal scaling #scalability

## Relations
- implements [[authentication-system-spec]]
- requires [[database-infrastructure]]
- relates_to [[api-design]]
- contrasts_with [[previous-mysql-design]]
""",
    folder="architecture",
    tags=["database", "design", "authentication"],
    project="main",
)
```

### Effective Observation Writing

**Good observations are**:
- **Specific**: Use precise, detailed statements
- **Categorized**: Use appropriate category
- **Tagged**: Add relevant tags
- **Atomic**: One fact per observation
- **Contextual**: Include enough detail

**Examples**:

**❌ Poor observations**:
```markdown
- [facts] We use a database
- [ideas] Security is important
- [decisions] Made some changes
```

**✓ Good observations**:
```markdown
- [facts] PostgreSQL 14 database runs on AWS RDS with 16GB RAM #infrastructure
- [decisions] Implemented rate limiting at 100 requests/minute per user #security
- [techniques] Using bcrypt with cost factor 12 for password hashing #cryptography
```

### Writing Effective Relations

**Relations should be**:
- **Directional**: Clear source and target
- **Typed**: Use meaningful relation type
- **Accurate**: Use exact entity titles
- **Purposeful**: Add value to graph

**Choosing relation types**:

```markdown
# Implementation relationship
- implements [[feature-specification]]

# Dependency relationship
- requires [[user-authentication]]
- depends_on [[database-connection]]

# Hierarchical relationship
- part_of [[payment-system]]
- includes [[payment-validation]]

# Contrast relationship
- contrasts_with [[alternative-approach]]
- alternative_to [[previous-design]]

# Temporal relationship
- leads_to [[next-phase]]
- follows [[initial-setup]]

# Causal relationship
- caused_by [[performance-issue]]
- results_in [[optimization]]
```

### Note Templates

**Decision Record**:

```python
await write_note(
    title="decision-use-graphql-for-api",
    content="""# Decision: Use GraphQL for API

## Context
Evaluating API architecture for new product features.

## Decision
Adopt GraphQL instead of REST for our API layer.

## Observations
- [decisions] GraphQL chosen for flexible client queries #api
- [requirements] Frontend needs to minimize round trips #performance
- [techniques] Apollo Server for GraphQL implementation #technology
- [facts] REST API still maintained for legacy clients #compatibility
- [insights] GraphQL reduced API calls by 60% in prototype #metrics

## Rationale
- Type safety reduces runtime errors
- Single endpoint simplifies deployment
- Built-in schema documentation
- Better mobile performance

## Consequences
- Team needs GraphQL training
- More complex caching strategy
- Additional monitoring required

## Relations
- implements [[api-architecture-plan]]
- requires [[graphql-schema-design]]
- affects [[frontend-development]]
- replaces [[rest-api-v1]]
""",
    folder="decisions",
    tags=["decision", "api", "graphql"],
    note_type="decision",
    project="main",
)
```

**Meeting Notes**:

```python
await write_note(
    title="api-review-meeting-2025-01-15",
    content="""# API Review Meeting 2025-01-15

## Attendees
- Alice (Backend Lead)
- Bob (Frontend Lead)
- Carol (Product)

## Observations
- [decisions] Finalized GraphQL schema for user endpoints #api
- [actions] Bob to implement Apollo client integration by Friday #task
- [problems] Rate limiting causing issues in staging #bug
- [insights] GraphQL subscriptions reduce polling load significantly #performance
- [requirements] Need better error handling for network failures #frontend

## Action Items
- [ ] Implement rate limiting improvements (Alice)
- [ ] Apollo client setup (Bob)
- [ ] Document error handling patterns (Alice)
- [ ] Update API documentation (Carol)

## Relations
- relates_to [[api-architecture-plan]]
- references [[graphql-implementation]]
- follows_up [[api-planning-meeting-2025-01-08]]
""",
    folder="meetings",
    tags=["meeting", "api", "team"],
    note_type="meeting",
    project="main",
)
```

**Technical Specification**:

```python
await write_note(
    title="user-authentication-spec",
    content="""# User Authentication Spec

## Overview
Specification for user authentication system using JWT tokens.

## Observations
- [requirements] Support email/password and OAuth authentication #auth
- [requirements] JWT tokens expire after 24 hours #security
- [requirements] Refresh tokens valid for 30 days #security
- [techniques] Use RS256 algorithm for token signing #cryptography
- [facts] Tokens include user_id, email, and roles claims #implementation
- [decisions] Store refresh tokens in HTTP-only cookies #security
- [techniques] Implement rate limiting on login endpoints #protection

## Technical Details

### Authentication Flow
1. User submits credentials
2. Server validates against database
3. Generate JWT access token
4. Generate refresh token
5. Return tokens to client

### Token Structure
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "roles": ["user"],
  "exp": 1234567890,
  "iat": 1234567890
}
```

## Relations
- implemented_by [[authentication-service]]
- requires [[user-database-schema]]
- part_of [[security-architecture]]
- extends [[oauth-2.0-spec]]
""",
    folder="specs",
    tags=["spec", "auth", "security"],
    note_type="spec",
    project="main"
)
```

### Tags Strategy

**Effective tagging**:

```python
# Technology tags
#python #fastapi #graphql #postgresql

# Domain tags
#auth #security #api #frontend #backend

# Status tags
#wip #completed #deprecated #planned

# Priority tags
#urgent #important #nice-to-have

# Category tags
#bug #feature #refactor #docs #test
```

**Example with strategic tags**:

```python
await write_note(
    title="oauth-integration",
    content="""# OAuth Integration

## Observations
- [features] Google OAuth integration completed #oauth #google #completed
- [features] GitHub OAuth in progress #oauth #github #wip
- [requirements] Add Microsoft OAuth support #oauth #microsoft #planned
- [techniques] Using authlib for OAuth flow #python #authlib
- [insights] OAuth reduces password reset requests by 80% #metrics #security
""",
    folder="features",
    tags=["oauth", "authentication", "integration"],
    project="main",
)
```

---

## Reading and Navigation

**Reading notes and navigating the knowledge graph is fundamental to building context.**

### Reading by Identifier

**Read by title**:

```python
# Simple title
note = await read_note(identifier="authentication-system", project="main")

# Title in specific folder
note = await read_note(identifier="specs/authentication-system", project="main")
```

**Read by permalink**:

```python
# Permalink is auto-generated from title
note = await read_note(identifier="authentication-system", project="main")

# Permalink with folder
note = await read_note(identifier="specs/authentication-system", project="main")
```

### Reading by memory:// URL

**URL formats**:

```python
# By title
note = await read_note(identifier="memory://authentication-system", project="main")

# By folder and title
note = await read_note(identifier="memory://specs/authentication-system", project="main")

# By permalink
note = await read_note(identifier="memory://authentication-system", project="main")

# Wildcards for folder contents
notes = await read_note(identifier="memory://specs/*", project="main")
```

```python
# Cross-project URL (auto-routes to the correct project)
note = await read_note(identifier="memory://research/specs/api-design")
```

```python
# Underscores automatically converted to hyphens
note = await read_note(identifier="memory://my_note_title", project="main")
# Finds entity with permalink "my-note-title"

# Both forms work
note1 = await read_note("memory://api_design", project="main")
note2 = await read_note("memory://api-design", project="main")
# Both find same entity
```

### Response Structure

**read_note response includes**:

```python
{
    "title": "Authentication System",
    "permalink": "authentication-system",
    "content": "# Authentication System\n\n...",
    "folder": "specs",
    "tags": ["auth", "security"],
    "type": "spec",
    "created": "2025-01-10T14:30:00Z",
    "updated": "2025-01-15T09:15:00Z",
    "observations": [
        {"category": "decision", "content": "Use JWT for authentication", "tags": ["security"]}
    ],
    "relations": [
        {
            "type": "implemented_by",
            "target": "Authentication Service",
            "target_permalink": "authentication-service",
        }
    ],
}
```

### Pagination

**For long notes, use pagination**:

```python
# First page (default: 10 items)
page1 = await read_note(identifier="long-document", page=1, page_size=10, project="main")

# Second page
page2 = await read_note(identifier="long-document", page=2, page_size=10, project="main")

# Large page size for complete content
full = await read_note(identifier="long-document", page=1, page_size=1000, project="main")
```

### Reading Raw Content

**For non-markdown files or raw access**:

```python
# Read text file
content = await read_content(path="config/settings.json", project="main")

# Read image (returned as base64)
image = await read_content(path="diagrams/architecture.png", project="main")

# Read any file type
data = await read_content(path="data/export.csv", project="main")
```

**Difference from read_note**:
- `read_note`: Parses markdown, extracts knowledge graph
- `read_content`: Returns raw file content
- Use `read_note` for knowledge graph navigation
- Use `read_content` for non-markdown files

### Viewing as Artifact

**Use view_note as the preferred method when presenting note content for review:**

```python
# Display as formatted artifact
artifact = await view_note(identifier="authentication-system", project="main")

# Returns formatted markdown suitable for display
# - Syntax highlighting
# - Rendered markdown
# - Better visual presentation
```

**When to use view_note**:
- Presenting note content for user review (preferred over read_note)
- Showing documentation
- Displaying specifications
- Better than raw markdown for reading

### Directory Browsing

**List directory contents**:

```python
# List top-level folders
root = await list_directory(dir_name="/", project="main")

# List specific folder
specs = await list_directory(dir_name="specs", project="main")

# Recursive listing
all_files = await list_directory(dir_name="/", depth=3, project="main")

# Filter by pattern
markdown_files = await list_directory(dir_name="docs", file_name_glob="*.md", project="main")
```

**Response structure**:

```python
{
    "path": "specs",
    "files": [
        {
            "name": "authentication-system.md",
            "path": "specs/authentication-system.md",
            "type": "file",
            "size": 2048,
            "modified": "2025-01-15T09:15:00Z",
        }
    ],
    "directories": [{"name": "api", "path": "specs/api", "type": "directory", "file_count": 5}],
}
```

---

## Search and Discovery

**Search is the primary way to discover relevant knowledge.**

### Basic Search

**Simple text search**:

```python
# Search across all content
results = await search_notes(query="authentication", project="main")

# Search with pagination
results = await search_notes(query="authentication", page=1, page_size=10, project="main")

# Get more results
results = await search_notes(query="authentication", page=1, page_size=50, project="main")
```

### Advanced Search

**Filter by entity type**:

```python
# Search only specifications
specs = await search_notes(query="authentication", types=["spec"], project="main")

# Search decisions and meetings
decisions = await search_notes(query="api design", types=["decision", "meeting"], project="main")
```

**Filter by observation category**:

```python
# Find all decisions
decisions = await search_notes(query="", entity_types=["decision"], project="main")

# Find problems and solutions
issues = await search_notes(
    query="performance", entity_types=["problem", "solution"], project="main"
)
```

**Date filtering**:

```python
# Find recent changes
recent = await search_notes(query="api", after_date="2025-01-01", project="main")

# Combine with other filters
recent_decisions = await search_notes(
    query="authentication", types=["decision"], after_date="2025-01-01", project="main"
)
```

**Structured frontmatter filters**:

```python
# Filter by tags and status
results = await search_notes(
    query="authentication", tags=["security"], status="in-progress", project="main"
)

# Complex metadata filters (supports $in, $gt, $gte, $lt, $lte, $between)
results = await search_notes(
    query="api design",
    metadata_filters={
        "type": "spec",
        "priority": {"$in": ["high", "critical"]},
        "tags": ["architecture"],
    },
    project="main",
)

# Metadata-only search
results = await search_notes(
    metadata_filters={"type": "spec", "status": "in-progress"}, project="main"
)
```

### Search Types

Available types: `"text"`, `"title"`, `"permalink"`, `"vector"`/`"semantic"`, `"hybrid"`. Default is `"hybrid"` when semantic search is enabled, `"text"` otherwise.

**Text search**:

```python
# Full-text search across all content
results = await search_notes(query="JWT authentication", search_type="text", project="main")
```

**Title and permalink search**:

```python
# Search by title only
results = await search_notes(query="api-design", search_type="title", project="main")

# Search by permalink
results = await search_notes(query="specs/api-design", search_type="permalink", project="main")
```

**Semantic search**:

```python
# Semantic/vector search (if enabled)
results = await search_notes(query="user login security", search_type="semantic", project="main")

# Override similarity threshold
results = await search_notes(
    query="user login security", search_type="semantic", min_similarity=0.5, project="main"
)
```

**Hybrid search** (combines text + semantic):

```python
results = await search_notes(
    query="authentication best practices", search_type="hybrid", project="main"
)
```

**Tag shorthand in query**:

```python
# Use tag: prefix as shorthand
results = await search_notes(query="tag:security", project="main")

# Multiple tags with boolean operators
results = await search_notes(query="tag:security AND tag:auth", project="main")
results = await search_notes(query="tag:security tag:auth", project="main")
```

### Search Response

**Result structure**:

```python
{
    "results": [
        {
            "title": "Authentication System",
            "permalink": "authentication-system",
            "folder": "specs",
            "snippet": "...JWT authentication for user login...",
            "score": 0.95,
            "tags": ["auth", "security"],
            "type": "spec",
            "updated": "2025-01-15T09:15:00Z",
        }
    ],
    "total": 15,
    "page": 1,
    "page_size": 10,
    "has_more": true,
}
```

### Search Strategies

**Broad to narrow**:

```python
# Start broad
all_auth = await search_notes(query="authentication", project="main")

# Narrow down
jwt_auth = await search_notes(
    query="JWT authentication", types=["spec", "decision"], project="main"
)

# Very specific
recent_jwt = await search_notes(
    query="JWT token implementation", types=["spec"], after_date="2025-01-01", project="main"
)
```

**Find related content**:

```python
# 1. Search for main topic
auth_notes = await search_notes(query="authentication", project="main")

# 2. Read top result
main_note = await read_note(identifier=auth_notes["results"][0]["permalink"], project="main")

# 3. Build context from relations
context = await build_context(url=f"memory://{main_note['permalink']}", depth=2, project="main")

# 4. Search for related terms from relations
for relation in main_note["relations"]:
    related = await search_notes(query=relation["target"], project="main")
```

**Multi-faceted search**:

```python
# Search by different aspects
by_topic = await search_notes(query="api design", project="main")
by_author = await search_notes(query="Alice", project="main")
by_date = await search_notes(query="", after_date="2025-01-15", project="main")
by_tag = await search_notes(query="#security", project="main")
by_type = await search_notes(query="", types=["decision"], project="main")

# Combine for precision
precise = await search_notes(
    query="api security", types=["decision"], after_date="2025-01-01", project="main"
)
```

---

## Building Context

**Context building enables conversation continuity by traversing the knowledge graph.**

### Basic Context Building

**Simple context**:

```python
# Build context from entity
context = await build_context(url="memory://authentication-system", project="main")

# Returns:
# - The root entity
# - Directly related entities
# - Recent observations
# - Connection paths
```

### Depth Control

**Shallow context (depth=1)**:

```python
# Only immediate connections
shallow = await build_context(url="memory://authentication-system", depth=1, project="main")

# Returns:
# - Root entity
# - Entities with direct relations
# - First-degree connections only
```

**Deep context (depth=2)**:

```python
# Two levels of connections
deep = await build_context(url="memory://authentication-system", depth=2, project="main")

# Returns:
# - Root entity
# - Direct relations (depth 1)
# - Relations of relations (depth 2)
# - More comprehensive context
```

**Very deep context (depth=3+)**:

```python
# Three or more levels
very_deep = await build_context(url="memory://authentication-system", depth=3, project="main")

# Warning: Can return a lot of data
# Use for comprehensive understanding
# May be slow for large graphs
```

### Timeframe Filtering

**Recent context**:

```python
# Last 7 days
recent = await build_context(url="memory://authentication-system", timeframe="7d", project="main")

# Natural language timeframes
last_week = await build_context(url="memory://api-design", timeframe="1 week", project="main")

last_month = await build_context(
    url="memory://project-planning", timeframe="30 days", project="main"
)

# Minimum: 1 day (enforced since v0.15.0)
```

**All-time context**:

```python
# No timeframe = all history
complete = await build_context(url="memory://authentication-system", depth=2, project="main")
```

### Context Response Structure

**Response includes**:

```python
{
    "root_entity": {
        "title": "Authentication System",
        "permalink": "authentication-system",
        "content": "...",
        "observations": [...],
        "relations": [...],
    },
    "related_entities": [
        {
            "title": "User Database",
            "permalink": "user-database",
            "relation_type": "requires",
            "distance": 1,
            "content": "...",
            "observations": [...],
            "relations": [...],
        },
        {
            "title": "Login API",
            "permalink": "login-api",
            "relation_type": "implemented_by",
            "distance": 1,
            "content": "...",
            "observations": [...],
            "relations": [...],
        },
    ],
    "paths": [
        {
            "from": "authentication-system",
            "to": "login-api",
            "path": [
                {"entity": "authentication-system", "relation": "implemented_by"},
                {"entity": "login-api"},
            ],
        }
    ],
    "summary": {"total_entities": 5, "total_relations": 8, "max_depth": 2, "timeframe": "7d"},
}
```

### Context Building Patterns

**Continuing conversations**:

```python
# User: "Let's discuss authentication"

# 1. Search for topic
results = await search_notes(query="authentication", project="main")

# 2. Build context from most relevant
context = await build_context(
    url=f"memory://{results['results'][0]['permalink']}", depth=2, timeframe="30d", project="main"
)

# 3. Use context to inform response
# "Based on our previous work on authentication, including
#  the JWT implementation and OAuth integration..."
```

**Exploring knowledge areas**:

```python
# Start with broad topic
initial = await build_context(url="memory://api-design", depth=1, project="main")

# Explore interesting branches
for entity in initial["related_entities"]:
    if "GraphQL" in entity["title"]:
        graphql_context = await build_context(
            url=f"memory://{entity['permalink']}", depth=2, project="main"
        )
```

**Finding connection paths**:

```python
# Build context from both endpoints
start_context = await build_context(url="memory://frontend-app", depth=2, project="main")

end_context = await build_context(url="memory://database-schema", depth=2, project="main")

# Analyze paths in response
# Shows how frontend connects to database through API layer
```

---

## Recording Conversations

**Capturing conversations in Basic Memory enables long-term context and knowledge accumulation.**

### Permission and Transparency

**Always ask before recording**:

```
AI: "Would you like me to save our discussion about API authentication
     to Basic Memory? This will help us continue this conversation later
     and build on what we've learned."

User: "Yes, please"

AI: [Saves to Basic Memory]
    "I've saved our discussion to Basic Memory as 'API Authentication Discussion'."
```

**Be transparent**:
- Ask permission before saving
- Confirm after saving
- Explain what was saved
- Mention how it helps future conversations

**Your role**: As an AI collaborator, you're helping build knowledge that will outlast any particular AI model or session. Write observations and relations that will be valuable to the human (and future AI assistants) years from now. Think: enduring insights, not ephemeral chat logs. These plain-text markdown files are artifacts worth keeping - make them count.

### What to Record

**Good candidates for recording**:

1. **Decisions and Rationales**
```python
await write_note(
    title="decision-graphql-vs-rest",
    content="""# Decision: GraphQL vs REST

## Context
User asked about API architecture choice.

## Decision
Chose GraphQL for new features, maintain REST for legacy.

## Observations
- [decisions] GraphQL for flexibility and performance #api
- [requirements] Mobile app needs efficient data loading #mobile
- [facts] REST API has 50K existing clients #legacy
- [insights] Hybrid approach minimizes migration risk #strategy

## Relations
- implements [[api-modernization-plan]]
- affects [[mobile-development]]
""",
    folder="decisions",
    project="main",
)
```

2. **Important Discoveries**
```python
await write_note(
    title="discovery-database-performance-issue",
    content="""# Discovery: Database Performance Issue

## Context
User reported slow login times.

## Observations
- [problems] Login queries taking 2-3 seconds #performance
- [insights] Missing index on users.email column #database
- [solutions] Added index, login now <100ms #fix
- [techniques] Used EXPLAIN ANALYZE to identify bottleneck #debugging
- [facts] 80% of queries were sequential scans #metrics

## Resolution
Created index on email column, query time improved 20x.

## Relations
- relates_to [[user-authentication]]
- caused_by [[database-schema-migration]]
""",
    folder="troubleshooting",
    project="main",
)
```

3. **Action Items and Plans**
```python
await write_note(
    title="plan-api-v2-migration",
    content="""# Plan: API v2 Migration

## Overview
Discussed migration strategy from REST v1 to GraphQL v2.

## Observations
- [plans] Phased migration over 3 months #roadmap
- [actions] Create GraphQL schema this week #task
- [actions] Implement parallel APIs next month #task
- [decisions] Deprecate v1 after 6-month notice #timeline
- [requirements] Must maintain backward compatibility #constraint

## Timeline
- Week 1-2: Schema design
- Week 3-4: Core API implementation
- Month 2: Client migration support
- Month 3: Documentation and training

## Relations
- implements [[api-modernization-strategy]]
- requires [[graphql-schema-design]]
- affects [[all-api-clients]]
""",
    folder="planning",
    project="main",
)
```

4. **Connected Topics**
```python
await write_note(
    title="conversation-security-best-practices",
    content="""# Conversation: Security Best Practices

## Discussion Summary
User asked about security measures for new API.

## Observations
- [recommendations] Implement rate limiting on all endpoints #security
- [techniques] Use JWT with short expiry + refresh tokens #auth
- [requirements] HTTPS only in production #infrastructure
- [techniques] Input validation with Pydantic schemas #validation
- [recommendations] Regular security audits quarterly #process

## Key Insights
- Defense in depth approach is essential
- Rate limiting prevents most automated attacks
- Token rotation improves security posture

## Related Topics
- Authentication mechanisms
- Authorization patterns
- Data encryption
- Audit logging

## Relations
- relates_to [[api-security-architecture]]
- implements [[security-policy]]
- requires [[rate-limiting-service]]
""",
    folder="conversations",
    project="main",
)
```

### Recording Patterns

**Conversation summary**:

```python
# After substantial discussion
await write_note(
    title=f"Conversation: {topic} - {date}",
    content=f"""# Conversation: {topic}

## Summary
{brief_summary}

## Key Points Discussed
{key_points}

## Observations
{categorized_observations}

## Decisions Made
{decisions}

## Action Items
{action_items}

## Relations
{relevant_relations}
""",
    folder="conversations",
    tags=["conversation", topic_tags],
    project="main",
)
```

**Decision record**:

```python
# For important decisions
await write_note(
    title=f"Decision: {decision_title}",
    content=f"""# Decision: {decision_title}

## Context
{why_decision_needed}

## Decision
{what_was_decided}

## Observations
{categorized_observations}

## Rationale
{reasoning}

## Consequences
{implications}

## Relations
{related_entities}
""",
    folder="decisions",
    note_type="decision",
    project="main",
)
```

**Learning capture**:

```python
# For new knowledge or insights
await write_note(
    title=f"Learning: {topic}",
    content=f"""# Learning: {topic}

## What We Learned
{insights}

## Observations
{categorized_facts}

## How This Helps
{practical_applications}

## Relations
{connected_knowledge}
""",
    folder="learnings",
    project="main",
)
```

### Building on Past Conversations

**Reference previous discussions**:

```python
# 1. Search for related past conversations
past = await search_notes(
    query="api authentication", types=["conversation", "decision"], project="main"
)

# 2. Build context
context = await build_context(
    url=f"memory://{past['results'][0]['permalink']}", depth=2, timeframe="30d", project="main"
)

# 3. Reference in new conversation
# "Building on our previous discussion about JWT authentication,
#  let's now address the refresh token implementation..."

# 4. Link new note to previous
await write_note(
    title="refresh-token-implementation",
    content="""# Refresh Token Implementation

## Relations
- builds_on [[conversation-api-authentication]]
- implements [[jwt-authentication-decision]]
""",
    folder="implementation",
    project="main",
)
```

---

## Editing Notes

**Edit existing notes incrementally without rewriting entire content.**

### Edit Operations

**Available operations**:
- `find_replace`: Replace specific text (preferred for targeted edits)
- `replace_section`: Replace markdown section by heading
- `insert_before_section`: Insert content before a section heading without consuming it
- `insert_after_section`: Insert content after a section heading without consuming it
- `append`: Add to end of note
- `prepend`: Add to beginning

**Preferred approach**: Use `find_replace` to target specific sections for edits because precise targeting reduces unintended modifications and maintains content integrity.

**Edit preview requirement**: Always show proposed changes as a diff preview before executing edits. This ensures the user can verify changes are correct before they are applied.

### Append Content

**Add to end of note**:

```python
await edit_note(
    identifier="authentication-system",
    operation="append",
    content="""

## New Section

Additional information discovered.

## Observations
- [facts] New security requirement identified #security
""",
    project="main",
)
```

**Use cases**:
- Adding new observations
- Appending related topics
- Adding follow-up information
- Extending discussions

### Prepend Content

**Add to beginning of note**:

```python
await edit_note(
    identifier="meeting-notes",
    operation="prepend",
    content="""## Update

Important development since meeting.

---

""",
    project="main",
)
```

**Use cases**:
- Adding urgent updates
- Inserting warnings
- Adding important context
- Prepending summaries

### Find and Replace

**Replace specific text**:

```python
await edit_note(
    identifier="api-documentation",
    operation="find_replace",
    find_text="http://api.example.com",
    content="https://api.example.com",
    expected_replacements=3,
    project="main",
)
```

**With expected replacements count**:

```python
# Expects exactly 1 replacement
await edit_note(
    identifier="config-file",
    operation="find_replace",
    find_text="DEBUG = True",
    content="DEBUG = False",
    expected_replacements=1,
    project="main",
)

# Error if count doesn't match
# Prevents unintended changes
```

**Use cases**:
- Updating URLs
- Correcting terminology
- Fixing typos
- Updating version numbers

### Replace Section

**Replace markdown section by heading**:

```python
await edit_note(
    identifier="project-status",
    operation="replace_section",
    section="## Current Status",
    content="""## Current Status

Project completed successfully.

All milestones achieved ahead of schedule.
""",
    project="main",
)
```

**Replace nested section**:

```python
await edit_note(
    identifier="technical-docs",
    operation="replace_section",
    section="### Authentication",  # Finds h3 heading
    content="""### Authentication

Updated authentication flow using OAuth 2.0.

See [[oauth-implementation]] for details.
""",
    project="main",
)
```

**Use cases**:
- Updating status sections
- Replacing outdated information
- Modifying specific topics
- Restructuring content

### Adding Observations

**Append new observations**:

```python
# Read current note
note = await read_note("api-design", project="main")

# Add new observations
await edit_note(
    identifier="api-design",
    operation="append",
    content="""
- [insights] GraphQL reduces API calls by 60% #performance
- [decisions] Implement query complexity limiting #security
- [actions] Document schema changes weekly #documentation
""",
    project="main",
)
```

### Adding Relations

**Add new relations**:

```python
await edit_note(
    identifier="authentication-system",
    operation="find_replace",
    find_text="## Relations",
    content="""## Relations
- integrates_with [[oauth-provider]]
- requires [[rate-limiting-service]]""",
    project="main",
)
```

**Update relations section**:

```python
await edit_note(
    identifier="api-backend",
    operation="replace_section",
    section="## Relations",
    content="""## Relations
- implements [[api-specification-v2]]
- requires [[database-layer]]
- integrates_with [[authentication-service]]
- monitored_by [[logging-system]]
- deployed_to [[production-infrastructure]]
""",
    project="main",
)
```

### Bulk Updates

**Update multiple notes**:

```python
# Search for notes to update
notes = await search_notes(query="deprecated", project="main")

# Update each note
for note in notes["results"]:
    await edit_note(
        identifier=note["permalink"],
        operation="prepend",
        content="⚠️ **DEPRECATED** - See [[new-implementation]]\n\n---\n\n",
        project="main",
    )
```

### Collaborative Editing

**Track changes and updates**:

```python
# Add update log
await edit_note(
    identifier="living-document",
    operation="find_replace",
    find_text="## Relations",
    content=f"""## Update Log

### {current_date}
- Updated authentication section
- Added OAuth examples
- Fixed broken links

## Relations""",
    project="main",
)
```

---

## Moving and Organizing

**Organize notes by moving them between folders while maintaining knowledge graph integrity.**

### Basic Move

**Move to new folder**:

```python
await move_note(
    identifier="api-documentation", destination_path="docs/api/api-documentation.md", project="main"
)
```

**Move with auto-extension**:

```python
# Both work (v0.15.0+)
await move_note(identifier="note", destination_path="new-folder/note.md", project="main")

await move_note(
    identifier="note",
    destination_path="new-folder/note",  # .md added automatically
    project="main",
)
```

### Organizing Knowledge

**Create folder structure**:

```python
# Move related notes to dedicated folders

# Move specs
await move_note("authentication-spec", "specs/auth/authentication.md", project="main")
await move_note("api-spec", "specs/api/api-spec.md", project="main")

# Move implementations
await move_note("auth-service", "services/auth/auth-service.md", project="main")
await move_note("api-server", "services/api/api-server.md", project="main")

# Move decisions
await move_note("decision-oauth", "decisions/oauth-decision.md", project="main")

# Move meetings
await move_note("api-review-meeting-2025-01-15", "meetings/2025/01/api-review.md", project="main")
```

**Folder hierarchy**:

```
project/
├── specs/
│   ├── auth/
│   └── api/
├── services/
│   ├── auth/
│   └── api/
├── decisions/
├── meetings/
│   └── 2025/
│       └── 01/
├── conversations/
└── learnings/
```

### Batch Organization

**Organize multiple notes**:

```python
# Get all auth-related notes
auth_notes = await search_notes(query="authentication", project="main")

# Move to auth folder
for note in auth_notes["results"]:
    if note["type"] == "spec":
        await move_note(
            identifier=note["permalink"],
            destination_path=f"specs/auth/{note['permalink']}.md",
            project="main",
        )
    elif note["type"] == "decision":
        await move_note(
            identifier=note["permalink"],
            destination_path=f"decisions/auth/{note['permalink']}.md",
            project="main",
        )
```

### Preserving Relations

**Relations are automatically updated**:

```python
# Before move:
# Note A (folder: root) -> relates_to [[note-b]]
# Note B (folder: root)

# Move Note B
await move_note(identifier="note-b", destination_path="subfolder/note-b.md", project="main")

# After move:
# Note A (folder: root) -> relates_to [[note-b]]
# Note B (folder: subfolder) <- relation still works!
# Database updated automatically
```

### Renaming

**Move to rename**:

```python
# Rename by moving to same folder with new name
await move_note(identifier="old-name", destination_path="same-folder/new-name.md", project="main")

# Title and permalink updated
# Relations preserved
```

### Archiving

**Move to archive folder**:

```python
# Archive old notes
await move_note(
    identifier="deprecated-feature",
    destination_path="archive/deprecated/deprecated-feature.md",
    project="main",
)

# Batch archive by date
old_notes = await search_notes(query="", after_date="2024-01-01", project="main")

for note in old_notes["results"]:
    if note["updated"] < "2024-06-01":
        await move_note(
            identifier=note["permalink"],
            destination_path=f"archive/2024/{note['permalink']}.md",
            project="main",
        )
```

---

## Error Handling

**Robust error handling ensures reliable AI-human interaction.**

### Missing Project Parameter

**Error**: Tool called without project parameter

**Solution**:

```python
try:
    results = await search_notes(query="test")
except:
    # Show available projects
    projects = await list_memory_projects()

    # Ask user which to use
    # "I need to know which project to search. Available projects: ..."

    # Retry with project
    results = await search_notes(query="test", project="main")
```

**Prevention**:

```python
# Always discover projects first
projects = await list_memory_projects()

# Store active project for session
active_project = projects[0]["name"]

# Use in all calls
results = await search_notes(query="test", project=active_project)
```

### Entity Not Found

**Error**: Note doesn't exist

**Solution**:

```python
try:
    note = await read_note("nonexistent-note", project="main")
except:
    # Search for similar
    results = await search_notes(query="Note", project="main")

    # Suggest alternatives
    # "I couldn't find 'Nonexistent Note'. Did you mean:"
    # - Similar Note 1
    # - Similar Note 2
```

### Note Already Exists

**Error**: `write_note` called for a note that already exists

**Solution**:

```python
# Preferred: use edit_note for incremental updates
await edit_note(
    identifier="existing-topic",
    operation="find_replace",
    find_text="## Relations",
    content="- [facts] New information\n\n## Relations",
    project="main",
)

# Alternative: replace the entire note
await write_note(
    title="existing-topic",
    content="# existing-topic\n...",
    folder="notes",
    overwrite=True,
    project="main",
)
```

### Sync Status Issues

**Error**: Data not found, sync in progress

**Solution**:

```python
# Check sync status
status = await sync_status(project="main")

if status["sync_in_progress"]:
    # Inform user
    # "The knowledge base is still syncing. Please wait..."

    # Wait or proceed with available data
    # Can still search/read synced content
else:
    # Sync complete, proceed normally
    results = await search_notes(query="topic", project="main")
```

### Ambiguous References

**Error**: Multiple entities match

**Solution**:

```python
# Ambiguous title
try:
    note = await read_note("api", project="main")
except:
    # Search to disambiguate
    results = await search_notes(query="API", project="main")

    # Show options to user
    # "Multiple notes found with 'API':"
    # - API Specification (specs/)
    # - API Implementation (services/)
    # - API Documentation (docs/)

    # Use specific identifier
    note = await read_note("specs/api-specification", project="main")
```

### Empty Search Results

**Not an error**: No matches found

**Solution**:

```python
results = await search_notes(query="rare topic", project="main")

if results["total"] == 0:
    # Broaden search
    broader = await search_notes(query="topic", project="main")

    # Or suggest creating note
    # "No notes found about 'rare topic'. Would you like me to create one?"
```

### Project Not Found

**Error**: Specified project doesn't exist

**Solution**:

```python
try:
    results = await search_notes(query="test", project="nonexistent")
except:
    # List available projects
    projects = await list_memory_projects()

    # Show to user
    # "Project 'nonexistent' not found. Available projects:"
    # - main
    # - work

    # Offer to create
    # "Would you like to create a new project called 'nonexistent'?"
```

### Edit Conflicts

**Error**: find_replace didn't match expected count

**Solution**:

```python
try:
    await edit_note(
        identifier="config",
        operation="find_replace",
        find_text="old_value",
        content="new_value",
        expected_replacements=1,
        project="main",
    )
except:
    # Read note to check
    note = await read_note("config", project="main")

    # Verify text exists
    if "old_value" in note["content"]:
        count = note["content"].count("old_value")
        # Inform user: "Found {count} occurrences, expected 1"

        # Adjust or use replace_all
        await edit_note(
            identifier="config",
            operation="find_replace",
            find_text="old_value",
            content="new_value",
            replace_all=True,
            project="main",
        )
```

### Permission Errors

**Error**: Can't write to destination

**Solution**:

```python
try:
    await move_note(identifier="note", destination_path="/restricted/note.md", project="main")
except:
    # Inform user about permission issue
    # "Cannot move note to /restricted/ - permission denied"

    # Suggest alternative
    # "Try moving to a folder within the project directory"

    # Use valid path
    await move_note(identifier="note", destination_path="archive/note.md", project="main")
```

---

## Advanced Patterns

**Sophisticated techniques for knowledge management and AI collaboration.**

### Progressive Knowledge Building

**Build knowledge incrementally over time**:

```python
# Session 1: Create foundation
await write_note(
    title="api-design",
    content="""# API Design

## Observations
- [requirements] Need REST API for mobile app

## Relations
- relates_to [[mobile-development]]
""",
    folder="planning",
    project="main",
)

# Session 2: Add details
await edit_note(
    identifier="api-design",
    operation="find_replace",
    find_text="## Relations",
    content="""
- [decisions] Using FastAPI framework #python
- [techniques] Auto-generate OpenAPI docs

## Relations""",
    project="main",
)

# Session 3: Add related entities
await write_note(
    title="api-authentication",
    content="""# API Authentication

## Relations
- part_of [[api-design]]
""",
    folder="specs",
    project="main",
)

# Update original with relation
await edit_note(
    identifier="api-design",
    operation="find_replace",
    find_text="## Relations",
    content="""## Relations
- includes [[api-authentication]]""",
    project="main",
)

# Session 4: Add implementation
await write_note(
    title="api-implementation",
    content="""# API Implementation

## Relations
- implements [[api-design]]
""",
    folder="code",
    project="main",
)
```

### Cross-Project Knowledge Transfer

**Transfer knowledge between projects**:

```python
# Read from source project
template = await read_note(identifier="api-architecture-template", project="templates")

# Adapt for target project
adapted_content = template["content"].replace("{{PROJECT_NAME}}", "New Project")

# Write to target project
await write_note(
    title="api-architecture", content=adapted_content, folder="architecture", project="new-project"
)
```

### Knowledge Graph Traversal

**Traverse graph to discover insights**:

```python
# Start with entry point
start = await read_note("product-roadmap", project="main")

# Traverse relations
visited = set()
to_visit = [start["permalink"]]
all_related = []

while to_visit:
    current = to_visit.pop(0)
    if current in visited:
        continue

    visited.add(current)
    note = await read_note(current, project="main")
    all_related.append(note)

    # Add related entities to queue
    for relation in note["relations"]:
        if relation["target_permalink"] not in visited:
            to_visit.append(relation["target_permalink"])

# Analyze collected knowledge
# - All connected entities
# - Relation patterns
# - Knowledge clusters
```

### Temporal Analysis

**Track knowledge evolution over time**:

```python
# Get recent activity
week1 = await recent_activity(timeframe="7d", project="main")
week2 = await recent_activity(timeframe="14d", project="main")

# Compare what's new
new_this_week = [item for item in week1 if item not in week2]

# Identify trends
# - What topics are active
# - What areas growing
# - What needs attention
```

### Knowledge Validation

**Ensure knowledge graph integrity**:

```python
# Find all broken references
all_notes = await search_notes(query="", page_size=1000, project="main")

unresolved = []
for note in all_notes["results"]:
    full_note = await read_note(note["permalink"], project="main")

    for relation in full_note["relations"]:
        if not relation.get("target_exists"):
            unresolved.append({"source": note["title"], "target": relation["target"]})

# Report broken references
# "Found {len(unresolved)} broken references:"
# - Note A -> Missing Target 1
# - Note B -> Missing Target 2
```

### Automated Documentation

**Generate documentation from knowledge graph**:

```python
# Gather all specs
specs = await search_notes(query="", types=["spec"], project="main")

# Build comprehensive documentation
doc_content = "# System Documentation\n\n"

for spec in specs["results"]:
    full_spec = await read_note(spec["permalink"], project="main")

    doc_content += f"\n## {full_spec['title']}\n"
    doc_content += f"{full_spec['content']}\n"

    # Add related implementations
    context = await build_context(url=f"memory://{spec['permalink']}", depth=1, project="main")

    implementations = [
        e for e in context["related_entities"] if e.get("relation_type") == "implemented_by"
    ]

    if implementations:
        doc_content += "\n### Implementations\n"
        for impl in implementations:
            doc_content += f"- {impl['title']}\n"

# Save generated documentation
await write_note(
    title="generated-system-documentation", content=doc_content, folder="docs", project="main"
)
```

### Knowledge Consolidation

**Merge related notes**:

```python
# Find related notes
related = await search_notes(query="authentication", project="main")

# Read all related
notes_to_merge = []
for note in related["results"]:
    full = await read_note(note["permalink"], project="main")
    notes_to_merge.append(full)

# Consolidate
merged_content = "# Consolidated: Authentication\n\n"

merged_observations = []
merged_relations = []

for note in notes_to_merge:
    merged_observations.extend(note.get("observations", []))
    merged_relations.extend(note.get("relations", []))

# Deduplicate
unique_observations = list({obs["content"]: obs for obs in merged_observations}.values())

unique_relations = list({rel["target"]: rel for rel in merged_relations}.values())

# Build consolidated note
merged_content += "## Observations\n"
for obs in unique_observations:
    merged_content += f"- [{obs['category']}] {obs['content']}"
    if obs.get("tags"):
        merged_content += " " + " ".join(f"#{tag}" for tag in obs["tags"])
    merged_content += "\n"

merged_content += "\n## Relations\n"
for rel in unique_relations:
    merged_content += f"- {rel['type']} [[{rel['target']}]]\n"

# Save consolidated note
await write_note(
    title="consolidated-authentication",
    content=merged_content,
    folder="consolidated",
    project="main",
)
```

---

## Tool Reference

**Complete reference for all MCP tools.**

### Content Management

**write_note(title, content, folder, tags, note_type, overwrite, project)**
- Create new markdown notes (errors if note already exists unless overwrite=True)
- Parameters:
  - `title` (required): Note title
  - `content` (required): Markdown content
  - `folder` (required): Destination folder
  - `tags` (optional): List of tags
  - `note_type` (optional): Type of note (stored in frontmatter). Can be "note", "person", "meeting", "guide", etc.
  - `overwrite` (optional): Set to True to replace an existing note (default: error if exists)
  - `project` (required unless default_project_mode): Target project
- Returns: Created/updated entity with permalink
- Example:
```python
await write_note(
    title="api-design",
    content="# API Design\n...",
    folder="specs",
    tags=["api", "design"],
    note_type="spec",
    project="main",
)
```

**read_note(identifier, page, page_size, project)**
- Read notes with knowledge graph context
- Parameters:
  - `identifier` (required): Title, permalink, or memory:// URL
  - `page` (optional): Page number (default: 1)
  - `page_size` (optional): Results per page (default: 10)
  - `project` (required unless default_project_mode): Target project
- Returns: Entity with content, observations, relations
- Example:
```python
note = await read_note(identifier="memory://specs/api-design", project="main")
```

**edit_note(identifier, operation, content, find_text, section, expected_replacements, project)**
- Edit notes incrementally
- Parameters:
  - `identifier` (required): Note identifier
  - `operation` (required): append, prepend, find_replace, replace_section, insert_before_section, insert_after_section
  - `content` (required): Content to add/replace
  - `find_text` (optional): Text to find (for find_replace)
  - `section` (optional): Section heading (for replace_section)
  - `expected_replacements` (optional): Expected replacement count
  - `project` (required unless default_project_mode): Target project
- Returns: Updated entity
- Example:
```python
await edit_note(
    identifier="api-design",
    operation="find_replace",
    find_text="## Relations",
    content="- [facts] New requirement\n\n## Relations",
    project="main",
)
```

**move_note(identifier, destination_path, project)**
- Move notes to new locations
- Parameters:
  - `identifier` (required): Note identifier
  - `destination_path` (required): New path (with or without .md)
  - `project` (required unless default_project_mode): Target project
- Returns: Updated entity with new path
- Example:
```python
await move_note(identifier="api-design", destination_path="archive/api-design.md", project="main")
```

**delete_note(identifier, project)**
- Delete notes from knowledge base
- Parameters:
  - `identifier` (required): Note identifier
  - `project` (required unless default_project_mode): Target project
- Returns: Deletion confirmation
- Example:
```python
await delete_note(identifier="outdated-note", project="main")
```

**read_content(path, project)**
- Read raw file content
- Parameters:
  - `path` (required): File path
  - `project` (required unless default_project_mode): Target project
- Returns: Raw file content (text or base64 for binary)
- Example:
```python
content = await read_content(path="config/settings.json", project="main")
```

**view_note(identifier, page, page_size, project)**
- View notes as formatted artifacts
- Parameters: Same as read_note
- Returns: Formatted markdown for display
- Example:
```python
artifact = await view_note(identifier="api-design", project="main")
```

### Knowledge Graph Navigation

**build_context(url, depth, timeframe, max_related, page, page_size, project)**
- Navigate knowledge graph
- Parameters:
  - `url` (required): memory:// URL
  - `depth` (optional): Traversal depth (default: 1)
  - `timeframe` (optional): Time window (e.g., "7d", "1 week")
  - `max_related` (optional): Max related entities (default: 10)
  - `page` (optional): Page number
  - `page_size` (optional): Results per page
  - `project` (required unless default_project_mode): Target project
- Returns: Root entity, related entities, paths
- Example:
```python
context = await build_context(url="memory://api-design", depth=2, timeframe="30d", project="main")
```

**recent_activity(type, depth, timeframe, project)**
- Get recent changes
- Parameters:
  - `type` (optional): Activity type filter
  - `depth` (optional): Include related entities
  - `timeframe` (optional): Time window (default: "7d")
  - `project` (optional): Target project (omit for all projects)
- Returns: List of recently updated entities
- Example:
```python
activity = await recent_activity(timeframe="7d", project="main")
```

**list_directory(dir_name, depth, file_name_glob, project)**
- Browse directory contents
- Parameters:
  - `dir_name` (optional): Directory path (default: "/")
  - `depth` (optional): Recursion depth (default: 1)
  - `file_name_glob` (optional): File pattern (e.g., "*.md")
  - `project` (required unless default_project_mode): Target project
- Returns: Files and subdirectories
- Example:
```python
contents = await list_directory(dir_name="specs", depth=2, file_name_glob="*.md", project="main")
```

### Search & Discovery

**search_notes(query, page, page_size, search_type, types, entity_types, after_date, metadata_filters, tags, status, min_similarity, project, project_id)**
- Search across knowledge base
- Parameters:
  - `query` (optional): Search query (not required for filter-only searches)
  - `page` (optional): Page number (default: 1)
  - `page_size` (optional): Results per page (default: 10)
  - `search_type` (optional): "text", "title", "permalink", "vector"/"semantic", "hybrid" (default: "hybrid" when semantic enabled, "text" otherwise)
  - `types` (optional): Entity type filter
  - `entity_types` (optional): Observation category filter
  - `after_date` (optional): Date filter (ISO format)
  - `metadata_filters` (optional): Structured frontmatter filters (dict, supports `$in`, `$gt`, `$gte`, `$lt`, `$lte`, `$between` operators)
  - `tags` (optional): Frontmatter tags filter (list); also available via `tag:` query shorthand
  - `status` (optional): Frontmatter status filter (string)
  - `min_similarity` (optional): Override similarity threshold for vector/hybrid search
  - `project` (required unless default_project_mode): Target project
- Returns: Matching entities with scores
- Example:
```python
results = await search_notes(
    query="authentication", types=["spec", "decision"], after_date="2025-01-01", project="main"
)
```

**Metadata-only search (via search_notes)**
- Use `search_notes` with `metadata_filters` and no `query` for metadata-only searches:
```python
results = await search_notes(
    metadata_filters={"type": "spec", "status": "in-progress"}, project="main"
)
```

### Project Management

**list_memory_projects()**
- List all available projects
- Parameters: None
- Returns: List of projects with metadata
- Example:
```python
projects = await list_memory_projects()
```

**create_memory_project(project_name, project_path, set_default)**
- Create new project
- Parameters:
  - `project_name` (required): Project name
  - `project_path` (required): Directory path
  - `set_default` (optional): Set as default (default: False)
- Returns: Created project details
- Example:
```python
await create_memory_project(
    project_name="research", project_path="/Users/name/research", set_default=False
)
```

**delete_project(project_name)**
- Delete project from configuration
- Parameters:
  - `project_name` (required): Project to delete
- Returns: Deletion confirmation
- Example:
```python
await delete_project(project_name="old-project")
```

**sync_status(project)**
- Check synchronization status
- Parameters:
  - `project` (optional): Target project
- Returns: Sync progress and status
- Example:
```python
status = await sync_status(project="main")
```

**list_workspaces()**
- List available workspaces (cloud)
- Parameters: None
- Returns: List of workspaces with metadata
- Example:
```python
workspaces = await list_workspaces()
```

---

## Best Practices

**Guidelines for effective knowledge management and AI collaboration.**

### 1. Project Setup

**Single-project users**:
- Enable `default_project_mode=true` in config
- Simplifies tool calls
- Less explicit project parameters

**Multi-project users**:
- Keep `default_project_mode=false`
- Always specify project explicitly
- Prevents cross-project errors

**Always start with discovery**:
```python
# First action in conversation
projects = await list_memory_projects()

# Ask user which to use
# Store for session
# Use consistently
```

### 2. Knowledge Structure

**Every note should have**:
- Clear, descriptive title
- 3-5 observations minimum
- 2-3 relations minimum
- Appropriate categories and tags
- Proper frontmatter

**Good structure example**:
```markdown
---
title: clear-descriptive-title
tags: 
- relevant
- tags
- here
type: note
last updated at: 2025-01-15 09:15
---

# clear-descriptive-title

## Context
Brief background

## Observations
- [category] Specific fact #tag1 #tag2
- [category] Another fact #tag3
- [category] Third fact #tag4

## Relations
- relation_type [[related-entity-1]]
- relation_type [[related-entity-2]]
```

### 3. Search Before Creating

**Always search first**:
```python
# Before writing new note
existing = await search_notes(query="topic name", project="main")

if existing["total"] > 0:
    # Update existing instead of creating duplicate
    await edit_note(
        identifier=existing["results"][0]["permalink"],
        operation="find_replace",
        find_text="## Relations",
        content=f"{new_information}\n\n## Relations",
        project="main",
    )
else:
    # Create new
    await write_note(...)
```

### 4. Use Exact Entity Titles in Relations

**Wrong**:
```markdown
## Relations
- relates_to [[auth-system]]  # Won't match "authentication-system"
- implements [[api-spec]]      # Won't match "api-specification"
```

**Right**:
```python
# Search for exact title
results = await search_notes(query="authentication-system", project="main")
exact_title = results["results"][0]["title"]

# Use in relation
content = f"## Relations\n- relates_to [[{exact_title}]]"
```

### 5. Meaningful Categories

**Use semantic categories**:
- `[decisions]` for choices made
- `[facts]` for objective information
- `[techniques]` for methods
- `[requirements]` for needs
- `[insights]` for realizations
- `[problems]` for issues
- `[solutions]` for resolutions
- `[actions]` for tasks

**Use specific, semantic categories**:
- Choose from the standard category list (decisions, facts, techniques, etc.)
- Be specific and intentional with category selection

### 6. Descriptive Relation Types

**Use meaningful relation types**:
- `implements` for implementation
- `requires` for dependencies
- `part_of` for hierarchy
- `extends` for enhancement
- `contrasts_with` for alternatives

**Use specific relation types**:
- Use the most descriptive relation type available
- Be specific about the relationship

### 7. Progressive Elaboration

**Build knowledge over time**:
```python
# Session 1: Create foundation
await write_note(
    title="topic",
    content="Basic structure with initial observations",
    folder="notes",
    project="main",
)

# Session 2: Add details
await edit_note(
    identifier="topic",
    operation="find_replace",
    find_text="## Relations",
    content="Additional observations and insights\n\n## Relations",
    project="main",
)

# Session 3: Add relations
await edit_note(
    identifier="topic",
    operation="find_replace",
    find_text="## Relations",
    content="## Relations\nRelations to related topics",
    project="main",
)
```

### 8. Consistent Naming

**Folder structure**:
- specs/ - Specifications
- decisions/ - Decision records
- meetings/ - Meeting notes
- conversations/ - AI conversations
- implementations/ - Code/implementations
- docs/ - Documentation

**File naming**:
- Use descriptive titles
- Consistent format
- Use alphanumeric characters and hyphens

### 9. Regular Validation

**Check knowledge graph health**:
```python
# Find unresolved references
# Check for orphaned notes
# Verify relation consistency
# Update outdated information
```

### 10. Permission and Transparency

**With users**:
- Always ask before recording
- Confirm after saving
- Explain what was saved
- Describe how it helps

**Recording pattern**:
```
AI: "Would you like me to save our discussion about {topic}?"
User: "Yes"
AI: [Saves to Basic Memory]
    "Saved as '{title}' in {folder}/"
```

### 11. Context Building Strategy

**For new conversations**:
```python
# 1. Search for topic
results = await search_notes(query="topic", project="main")

# 2. Build context from top result
context = await build_context(
    url=f"memory://{results['results'][0]['permalink']}", depth=2, timeframe="30d", project="main"
)

# 3. Use context to inform response
# Reference previous knowledge
# Build on existing understanding
```

### 12. Error Recovery

**Graceful degradation**:
```python
try:
    # Attempt operation
    result = await tool_call(...)
except:
    # Fall back to alternative
    # Inform user of issue
    # Suggest workaround
```

### 13. Incremental Updates

**Prefer editing over rewriting**:
```python
# Good: Incremental update
await edit_note(
    identifier="note",
    operation="find_replace",
    find_text="## Relations",
    content="New information\n\n## Relations",
    project="main",
)

# Avoid: Complete rewrite
# (unless necessary for major restructuring)
```

### 14. Tagging Strategy

**Use tags strategically**:
- Technology: #python #fastapi
- Domain: #auth #security
- Status: #wip #completed
- Priority: #urgent #important
- Category: #bug #feature

**Keep tags focused**:
- 3-5 tags per observation
- Focus on most relevant
- Reuse existing tags with similar semantic meaning

### 15. Documentation as Code

**Treat knowledge like code**:
- Version control friendly (markdown)
- Review and refine regularly
- Keep it DRY (Don't Repeat Yourself)
- Link instead of duplicating
- Maintain consistency

---

## Conclusion

This extended guide provides comprehensive coverage of Basic Memory's capabilities for AI assistants. Each section is designed to be self-contained so you can reference or copy specific sections as needed.

For the condensed quick-reference version, see the [AI Assistant Guide](https://github.com/basicmachines-co/basic-memory/blob/main/src/basic_memory/mcp/resources/ai_assistant_guide.md).

For complete documentation including setup, integrations, and advanced features, visit [docs.basicmemory.com](https://docs.basicmemory.com).

**Remember**: Basic Memory is about building persistent, structured knowledge that grows over time. Focus on creating rich observations, meaningful relations, and building a connected knowledge graph that provides lasting value across conversations and sessions.

Built with ♥️ by Basic Machines
