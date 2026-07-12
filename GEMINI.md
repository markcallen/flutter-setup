# GEMINI.md

This file provides guidance to Gemini CLI for working in this repository.

@./AGENTS.md

## Installed agent rules

Created by [Ballast](https://github.com/everydaydevopsio/ballast) v5.9.3. Do not edit this section.

Read and follow these rule files in `.gemini/rules/` when they apply:

- `.gemini/rules/local-dev-badges.md` — Add standard badges (CI, Release, License, GitHub Release, npm) to the top of README.md
- `.gemini/rules/local-dev-env.md` — Local development environment specialist - reproducible dev setup, DX, and documentation
- `.gemini/rules/local-dev-license.md` — License setup - ensure LICENSE file, package.json license field, and README reference (default MIT; overridable in AGENTS.md/CLAUDE.md)
- `.gemini/rules/local-dev-mcp.md` — Optional: use GitHub MCP and issues MCP (Jira/Linear/GitHub) for local-dev context
- `.gemini/rules/docs.md` — Documentation specialist - GitHub Markdown docs by default, or maintain existing Docusaurus sites with publish-docs automation
- `.gemini/rules/cicd.md` — CI/CD specialist - pipeline design, quality gates, and deployment
- `.gemini/rules/observability.md` — Observability specialist - logging, tracing, metrics, and SLOs
- `.gemini/rules/publishing-api.md` — REST API publishing specialist - Docker CD with Kubernetes health probes and Helm chart update
- `.gemini/rules/publishing-apps.md` — App publishing specialist - npmjs for Node apps, PyPI for Python apps, GitHub Releases for Go apps
- `.gemini/rules/publishing-apt.md` — APT/deb package publishing specialist - GoReleaser nfpms and GitHub Releases
- `.gemini/rules/publishing-brew.md` — Homebrew tap publishing specialist - GoReleaser brews block and tap repo setup
- `.gemini/rules/publishing-cli.md` — CLI publishing specialist - GoReleaser for Go, npmjs for Node, PyPI for Python
- `.gemini/rules/publishing-libraries.md` — Library publishing specialist - npmjs for TypeScript, PyPI for Python, GitHub tags/releases for Go
- `.gemini/rules/publishing-sdks.md` — SDK publishing specialist - npmjs for TypeScript SDKs, PyPI for Python SDKs, GitHub tags/releases for Go SDKs
- `.gemini/rules/publishing-web.md` — Web app publishing specialist - Docker to GHCR/Docker Hub with Helm chart CD on push to main
- `.gemini/rules/git-hooks.md` — Git hook specialist - configure pre-commit, pre-push, and Husky workflows that match the repository layout
- `.gemini/rules/typescript-linting.md` — TypeScript linting specialist - implements comprehensive linting and code formatting for TypeScript/JavaScript projects
- `.gemini/rules/typescript-logging.md` — Centralized logging specialist - configures Pino with Fluentd for Node/Next.js, and pino-browser to /api/logs
- `.gemini/rules/typescript-testing.md` — Testing specialist - sets up Jest (default) or Vitest for Vite projects, 50% coverage, and test step in build GitHub Action
- `.gemini/rules/tasks-task-system.md` — Task system integration - use {{taskSystem}} for work items and configure the MCP server
- `.gemini/rules/tasks-todo.md` — Branch-local TODO tracking - manage tasks/TODO.md and triage before PR
