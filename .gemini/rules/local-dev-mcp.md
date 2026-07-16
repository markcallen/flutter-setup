# Local Development: MCP Configuration

Task system MCP configuration is now handled by the `tasks` agent rule. Add the `tasks` agent and re-run `ballast install`.

---
# Local Development: MCP Configuration

Task system MCP configuration (GitHub Issues, Jira, Linear) is now handled by the `tasks` agent rule.

To set up MCP for your task system, add the `tasks` agent to your `.rulesrc.json` and re-run `ballast install`.

Once the `tasks` agent is installed, ask your AI assistant: "set up my task system MCP" and it will walk you through configuration for your platform (Claude Code, Cursor, Codex, or OpenCode).

## Gemini Mandates

### Narrative Flow
Always use the `update_topic` tool at the beginning of a task and when transitioning between major strategic phases. Provide a concise `title` and a detailed `summary` (5-10 sentences) that recaps completed work and outlines the immediate strategic intent.

### Context Efficiency
- **Surgical Reads:** Use `start_line` and `end_line` in `read_file` to minimize context usage.
- **Parallelism:** Execute independent searches and reads in parallel whenever possible.
- **Topic Search:** Use `grep_search` to identify points of interest before reading entire files.

### Strategic Orchestration
Delegate complex, repetitive, or high-volume tasks to specialized sub-agents (`codebase_investigator`, `generalist`) to keep the main session history lean and efficient.

# Local Development: MCP Configuration

Task system MCP configuration (GitHub Issues, Jira, Linear) is now handled by the `tasks` agent rule.

To set up MCP for your task system, add the `tasks` agent to your `.rulesrc.json` and re-run `ballast install`.

Once the `tasks` agent is installed, ask your AI assistant: "set up my task system MCP" and it will walk you through configuration for your platform (Claude Code, Cursor, Codex, or OpenCode).
