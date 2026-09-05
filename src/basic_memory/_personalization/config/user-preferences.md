
These are my personal preferences and settings that should be applied in all AI assistant interactions that make use of Basic Memory. These preferences are designed to optimize AI assistant performance by providing explicit instructions with context and rationale.

## Communication Style

You MUST tailor your responses to meet my communication style preferences.

### Response Format Requirements
- Provide direct and concise responses without excessive pleasantries because efficiency and clarity are prioritized over social niceties
- Structure all lists and information using bullet points because this format enhances readability and allows for quick scanning of key points
- Get straight to the point without lengthy introductions because time efficiency is valued and verbose responses reduce productivity

### Technical Communication Standards
- Include complete code examples when explaining technical concepts because concrete implementations are more valuable than abstract descriptions for learning and application
- Prioritize practical, actionable advice over theoretical explanations because immediate applicability is more valuable than conceptual understanding alone
- Provide step-by-step instructions with clear numbered sequences because this format reduces errors and ensures reproducible results

### Structure and Readability
- Use clear hierarchical headings and logical sections because well-organized content reduces cognitive load and improves information retention
- Highlight critical warnings, errors, and important notes using callout formatting because safety-critical information must be immediately visible to prevent mistakes
- Include relevant links, references, and documentation sources because external validation and additional context enhance credibility and enable deeper learning

### Quality Assurance Standards
- Request explicit clarification when requirements are ambiguous rather than making assumptions because incorrect assumptions lead to wasted effort and suboptimal outcomes
- Proactively suggest industry best practices and alternative approaches because comprehensive guidance prevents common pitfalls and improves long-term maintainability
- Focus recommendations on ease of maintenance, reliability, and security because these factors determine long-term success more than initial implementation speed 

## Basic Memory Usage Standards

You MUST follow these guidelines when creating or editing notes using the basic-memory MCP tools.

### Notes
- Use lowercase kebab-case naming convention (dashes instead of spaces) for all note titles because this format ensures consistent file system compatibility and improves URL readability
- Use `view_note()` instead of `read_note()` when presenting note content for review because formatted artifacts improve readability
- Update permalinks immediately when moving or renaming notes because maintaining link integrity is critical for knowledge graph navigation
- Use the `find_replace` operation to target specific sections for edits because precise targeting reduces unintended modifications and maintains content integrity
- When editing an existing note, you MUST first show me the diffs in markdown format with ANSI color codes (red for deletions, green for additions) in the terminal preview before executing the `find_replace` tool because it is hard to read the tool's `content` parameter to confirm the edits are correct

**❌ Bad Example - Direct execution without preview:**
```
AI: I'll update the session summary now.
[Immediately calls edit_note tool without showing changes]
```

**✅ Good Example - Show diff first, then request permission:**
```
AI: I'll show you the proposed changes as a diff, then apply them.

**Proposed changes to session summary:**

	```diff
	 ### **Key Learnings**
	 - Original content here
	+
	+### **New Section**
	+- New content added here
	```

[After user confirms with "proceed" or similar]
[Then calls edit_note tool]
```
- Always update the 'last updated at' frontmatter field when a note has been created or edited with format `last updated at: {{YYYY-MM-DD}} {{HH:mm}}` because tracking modification timestamps enables chronological navigation and helps identify stale content
- After editing a note, ALWAYS perform these two mandatory verification steps: (1) read the note again to confirm changes were applied correctly including the 'last updated at' frontmatter field, and (2) ensure the 'Relations' section appears at the bottom of the note because edit verification prevents content corruption and proper section placement maintains knowledge graph navigation standards

#### Classifications
- Notes typically fall into one of the following categories. We store different types of notes in different folders, and use different templates for each, because this increases standardisation and gives context on what a note contains and how it should be used.
	- **Context Sources:** a 'context source' is a note that describes or references external sources that we can add to your context to increase its knowledge on a particular subject. We add context sources because this lets you know where it can find more information on particular topics. Save context sources in the 'context-sources' folder
	- **References:** Short notes that reference facts and figures that we want to remember. These typically do not change very often. The difference between a context source and a reference is that references are self-contained, stand-alone sources of information. We create reference notes because they allow us to retrieve useful facts about a topic we are working on. Store reference notes in the 'references' folder
	- **Session Summaries**: A session summary note contains a summary of the interaction with an agent. We typically refer to a 'session' as all of the interactions that occurred on that date. We create session summaries because they let you know what we were working on recently and ensure continuity for long-running projects or research. Store session summaries in the session-summaries folder (i.e. `write_note` with `"folder": "session-summaries"`)
	- **Todo**: A list of todo items that we need to keep track off. We will usually have only one todo note in our vault. We create todos because this allows us to keep track of things we want to accomplish or try next. Ensure that we always have a single todo note with permalink /todo
	- **Issues**: An issue note documents a problem encountered, its root cause, and resolution. We create issue notes because they serve as a searchable troubleshooting knowledge base for recurring problems. Store issue notes in the 'issues' folder
	- **General:** A general note does not fall into any of the other classifications. It typically uses the templates/core.md template and MUST be stored in the project root folder (i.e. `write_note` with `"directory": "."`)
- You MUST ask me what type of note to create if you are unsure.
- Use snake_case for all `note_type` values (e.g. `session_summary`, `context_source`) because Basic Memory's code normalizes `note_type` to snake_case internally via `to_snake_case()` — using kebab-case or other formats creates inconsistency between what you pass and what gets stored in frontmatter

### Observations
- Apply semantic markup with categorised observations and typed relations in every note because this structure enables powerful knowledge graph connections and semantic search capabilities

### Categories
- Use categories to classify the semantic type of observations because categories define what kind of information it is rather than what topic it covers
- Apply one category per observation using an option from the below list of common categories because consistency enables better search and knowledge graph structure
- Extend beyond the standard categories only when domain-specific types are needed (e.g., issues, solutions, concerns, stakeholders) because maintaining a focused category set prevents proliferation while allowing necessary specialization
- Choose the most specific category that fits the observation because precise classification improves semantic search and filtering capabilities
- Use plurals for category names because standardising on this convention makes it easier to find related categories later on. Suggest alternative category names if just changing the current name to its plural form will produce a word that is not considered proper English
- Use lowercase for all category names because standardising on this convention ensures consistency across the knowledge base 
 
### Common Categories
- `[capabilities]`: System or tool capabilities
- `[decisions]`: Choices made
- `[examples]`: Example implementations or use cases
- `[facts]`: Objective information
- `[features]`: Product or system features
- `[guidelines]`: Best practices and standards
- `[ideas]`: Thoughts and concepts
- `[implementations]`: Technical implementations
- `[insights]`: Key realizations and understanding gained
- `[integrations]`: System integrations
- `[knowledge]`: General knowledge and learnings
- `[patterns]`: Reusable approaches identified
- `[preferences]`: User preferences and settings
- `[problems]`: Issues identified
- `[questions]`: Open questions
- `[references]`: Reference materials
- `[repositories]`: Code repositories
- `[requirements]`: Needs and constraints
- `[solutions]`: Resolutions and fixes applied
- `[specifications]`: Technical specifications
- `[techniques]`: Methods and approaches
- `[tradeoffs]`: Options weighed and rationale for choices

### Tags
- Create nested tags by using forward slashes (`/`) in the tag name, for example  `#preferences/notes`and `#preferences/responses` because nested tags define tag hierarchies that make it easier to find and filter related tags
- Use plurals for tag names because standardising on this convention makes it easier to find related tags later on. Suggest alternative tag names if just changing the current name to its plural form will produce a word that is not considered proper English
- Try to re-use tags with similar semantic meaning, or that are synonyms of each other, rather than creating new tags because tag proliferation make it more difficult to find related topics
- Use tags to describe subject matter, domain, and content topics because tags indicate what the observation is about rather than what type of information it is
- Apply multiple tags per observation when relevant for cross-cutting concerns (e.g., #performance #api #security) because tags enable flexible filtering and discovery across different dimensions
- Use tags for domain/topic (#brewing, #security), technology (#python, #aws), project context (#work/clients), and status (#completed, #urgent) because this creates rich metadata for search and organization

### Relations
- Add entries in the 'Relations' section only when they point to existing notes because forward references create broken links and reduce knowledge graph integrity
- Reference notes using their exact titles in the 'Relations' section because precise naming ensures accurate link resolution and prevents orphaned connections
- Automatically remove all references to deleted notes from other notes during cleanup operations because broken references degrade knowledge graph quality and user experience

### Templates
- Templates are not stored as notes but as files in the 'templates' folder. Templates need to be read with the 'fs_read' tool and created / updated with the 'fs_write' tool because we do not want the front-matter section of the template to be update when it is edited.

### Context Sources Management
- Use the 'context-sources' template from the 'templates/' folder when adding new context sources because standardized templates ensure consistent metadata capture and improve search accuracy across documentation sources
- Prefix tags for notes that are context sources with 'context-sources' (e.g. `#context-sources/{{context-source-name}}/tag)` because nesting tags makes it easier to search for related topics

### Session Summary Requirements
- Use the 'session-summary' template from the 'templates/' folder for all session summaries because consistent structure enables pattern recognition and improves session continuity across time
- Save all session summaries in the 'session-summaries/' folder because centralized organization enables chronological browsing and prevents summary files from cluttering other content areas
- Apply {{date}}-{{keyword}}.md naming convention for session summaries where date has format 'YYYYMMDD' and keyword describes the primary focus because date-prefixed naming enables chronological sorting while descriptive keywords enable topic-based discovery
- Try to limit session summaries to less than 100 lines because concise summaries maintain focus on key insights while remaining readable and preventing information overload during review
- When creating new session summary notes:
	- Analyse today's `git` commit history, staged changes (`git diff --cached`), and unstaged changes (`git diff`) and include relevant observations of changes that were made to the repository.
	- Focus on functional content changes rather than chores like renaming or moving files.

## MCP Server Tools
Preferences related to the discovery and use of MCP server tools.

### context7
- Always use context7 when I need code generation, setup or configuration steps, or library/API documentation. This means you SHOULD automatically use the Context7 MCP tools to resolve library id and get library docs without me having to explicitly ask

### git-mcp
- You MUST NOT use the `web_fetch` tool against `github.com` or `api.github.com` URLs because GitHub's `robots.txt` blocks agent access and the request will fail
- When fetching content from github.com (repositories, files, issues, PRs, releases), use tools in this order: (1) the `github` MCP server tools (e.g. `@github/get_file_contents`, `@github/search_code`, `@github/issue_read`) if available, (2) the `gh` CLI as a fallback (e.g. `gh api repos/{owner}/{repo}/contents/{path}`, `gh repo view`, `gh pr view`), (3) `web_fetch` only as a last resort
- Example: to read `CHANGELOG.md` from `basicmachines-co/basic-memory`, use `@github/get_file_contents` or `gh api repos/basicmachines-co/basic-memory/contents/CHANGELOG.md` — do NOT use `web_fetch` with the `https://github.com/...` or `https://api.github.com/...` URL
## README
Preferences related to creating and updating project `README.md` files.

- You MUST NOT list basic-memory notes when creating or updating sections in `README.md` that show the project structure because individual notes are not relevant to the overall project layout and function
- You MUST only generate the project structure to folder depth 2 because deeply nested structure diagrams are difficult to read and to not add meaningful additional context
- This entry **IS NOT** aligned with my preferences because it shows individual `.md` entries (i.e. notes) in the `basic-memory` folder structure **and** shows `nested-folder`, which is an example of a deeply nested folder beyond our folder depth preferences
```markdown
## Project Structure

{{project-root-folder}}/
├── basic-memory/              # Basic Memory knowledge base
    ├── config/                # User preferences and session templates
    │   ├── user-preferences.md # User preference configuration
    │   └── session-initialization.md # Session setup templates
    ├── notes/                 # Knowledge base content. THIS IS THE ROOT OF THE BASIC-MEMORY PROJECT
    │   ├── context-sources/   # Documentation source references
    │   ├── session-summaries/ # GenAI session summary notes
    │   ├── references/        # Reference materials and links
    │   └── todo.md            # Task management
    │   └── nested-folder/     # Deeply nested folder example
    ├── templates/             # Templates for creating Basic Memory notes
    │   ├── core.md            # Core note template
    │   ├── context-sources.md # Context source template
    │   ├── session-summary.md # Session summary template
    │   └── todo.md            # Todo template
    └── .project-name          # Project identifier
```

- This entry **IS** aligned with my preferences because it only shows the basic-memory folder structure, but not individual `.md` files (i.e. notes)
```markdown
## Project Structure 

{{project-root-folder}}/
├── basic-memory/              # Basic Memory knowledge base
│   ├── config/                # User preferences and session templates
│   ├── notes/                 # Knowledge base content
│   ├── templates/             # Templates for creating Basic Memory notes
│   └── .project-name          # Project identifier
```

