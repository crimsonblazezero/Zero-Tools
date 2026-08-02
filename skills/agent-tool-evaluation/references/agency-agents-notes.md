# agency-agents (The Agency) — Session Notes

**Date**: 2026-08-01
**Source**: https://github.com/msitarzewski/agency-agents

## Repository Stats

- **Stars**: 13,796+
- **Language**: Shell
- **License**: MIT
- **Author**: Maciej Sitarzewski
- **App**: [Agency Agents](https://agencyagents.app) (macOS/Linux/Windows native)

## What It Is

A collection of ~150+ AI agent personas organized by division. Each persona is a `.md` file with identity, personality, workflow, deliverables, and success metrics. Install into Claude Code, Codex, Cursor, Gemini CLI, Hermes, and 10+ other platforms.

## Divisions & Agent Counts

| Division | Approx Count | Examples |
|----------|-------------|----------|
| Engineering | 55+ | frontend-developer, backend-architect, code-reviewer, devops-automator, ai-engineer |
| Design | 10 | ui-designer, ux-researcher, brand-guardian, whimsy-injector |
| Marketing | 35+ | seo-specialist, tiktok-strategist, xiaohongshu-specialist, douyin-strategist |
| Sales | 10+ | outbound-strategist, discovery-coach, deal-strategist |
| Paid Media | 7 | ppc-strategist, search-query-analyst, tracking-specialist |
| Product | 5 | product-manager, sprint-prioritizer |
| Project Management | 7 | studio-producer, project-shepherd |
| Academic | 6 | anthropologist, historian, psychologist, statistician |

## Hermes Installation Quirk (Critical)

The `--agent` and `--division` flags are **silently ignored** for Hermes:

```
warn "Hermes: selection flags ignored; router keeps the full roster on disk and loads agents lazily."
```

**What this means**:
1. `convert.sh` MUST run first to generate `integrations/hermes/agency-agents-router/`
2. `install.sh` installs the full lazy-router plugin to `~/.hermes/plugins/agency-agents-router/`
3. All ~150 agents are on disk but only loaded when activated in conversation
4. To install selectively, use `--tool claude-code` or other platforms instead

## Correct Install Sequence for Hermes

```bash
git clone https://github.com/msitarzewski/agency-agents.git
cd agency-agents

# Step 1: Convert for Hermes
./scripts/convert.sh --tool hermes

# Step 2: Install
./scripts/install.sh --tool hermes

# Restart Hermes session for plugin to be discovered
```

## Selective Install (Non-Hermes Platforms)

```bash
# Install only specific agents to Claude Code
./scripts/install.sh --tool claude-code --agent frontend-developer,backend-architect

# Install entire division
./scripts/install.sh --tool codex --division engineering

# Dry run to see what would install
./scripts/install.sh --tool hermes --division marketing --dry-run
```

## Platform Support Matrix

| Platform | Selective Install | Lazy Load | Notes |
|----------|------------------|-----------|-------|
| Hermes | ❌ (ignored) | ✅ | Full roster on disk, loaded on demand |
| Claude Code | ✅ | ❌ | Only selected agents installed |
| Codex | ✅ | ❌ | Only selected agents installed |
| Cursor | ✅ | ❌ | Only selected agents installed |
| OpenCode | ✅ | ❌ | **Warning**: ~119 agent soft limit, excess silently dropped |
| Gemini CLI | ✅ | ❌ | Only selected agents installed |
| Antigravity | ✅ | ❌ | Only selected agents installed |

## Key Insight for Future Sessions

When the user asks about installing from a skill library:
1. Check the install script for platform-specific behavior
2. Look for `warn` messages about flags being ignored
3. Distinguish between "lazy load" (all on disk, load on demand) vs "selective install" (only requested agents)
4. Verify if a conversion step is required before install