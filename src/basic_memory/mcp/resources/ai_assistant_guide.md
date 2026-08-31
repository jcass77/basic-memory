# AI Assistant Guide for Basic Memory

> **User Preference Note**: When presenting note content for review, use `view_note()` instead of `read_note()` because formatted artifacts improve readability.

Basic Memory is a persistent Markdown knowledge base shared by the user and their AI assistants. Use it for information that should survive this conversation: decisions, discoveries, plans, preferences, and connected reference material.

**For comprehensive coverage**: See the [Extended AI Assistant Guide](https://github.com/basicmachines-co/basic-memory/blob/main/docs/ai-assistant-guide-extended.md) with detailed examples, advanced patterns, and self-contained sections.

## Start usefully

1. Call `recent_activity` to orient in the user's existing notes.
2. If no project is resolved, call `list_memory_projects` and ask which project to use.
3. Preserve the selected route in later calls. Prefer a returned `project_id` over a project name because names can collide across cloud workspaces.
4. No recent activity does not prove the knowledge base is empty. If the user appears new, explain the shared-memory loop and offer a useful first note. Wait for agreement before creating it.

## Work with the user's knowledge

- Search before creating a note so related knowledge is reused instead of duplicated.
- Read a matching note before updating it, then use `edit_note` for focused changes. Prefer the `find_replace` operation to target specific sections precisely because it reduces unintended modifications.
- Use `write_note` for a new note. Use its `directory` parameter to choose the folder, and use lowercase kebab-case titles for filesystem compatibility and readable URLs.
- Keep notes useful and connected; add categorized observations (use plural categories such as `[decisions]`, `[facts]`, `[techniques]`), tags, or WikiLinks when they improve later retrieval, not to satisfy a quota.
- Create relations only to notes that already exist so the knowledge graph stays free of broken links.
- Confirm meaningful writes and preserve the project or `project_id` used for the read.

The tool descriptions and input schemas exposed by this MCP server are authoritative for the installed tool names and arguments.

## Fetch current documentation

If your client has a web, browser, or fetch tool:

1. Fetch `https://docs.basicmemory.com/llms.txt` for the documentation index.
2. Choose the page relevant to the user's task.
3. Fetch that page's linked `https://docs.basicmemory.com/raw/...md` URL for clean Markdown.

For tool details, the index links directly to the MCP Tools Reference. Fetch `https://docs.basicmemory.com/llms-full.txt` only when the task genuinely needs the complete documentation; progressive page-by-page discovery usually uses less context and stays focused. If no fetch capability is available, use this guide plus the MCP tool schemas.

For full documentation: https://docs.basicmemory.com

Built with ♥️ by Basic Machines
