---
name: agent-tool-evaluation
description: Research and compare external AI agent skill libraries.
---

# Agent Tool Evaluation

Use when the user wants to:
- Research and compare AI agent skill libraries or tools
- Install external agent packages (The Agency, PPT skills, coding helpers)
- Understand compatibility between agent tools and Hermes/other platforms
- Evaluate whether a tool supports selective vs full installation

## Core Workflow

### 1. Research Phase

Always fetch the README first:
```bash
curl -sL "https://raw.githubusercontent.com/<repo>/main/README.md" | head -300
```
Also check GitHub metadata for stars, language, license:
```bash
curl -sL "https://api.github.com/repos/<repo>" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('desc:', d.get('description'))
print('stars:', d.get('stargazers_count'))
print('lang:', d.get('language'))
print('topics:', d.get('topics'))
"
```

### 2. Understand Installation Model

Key questions to answer:
- Does it use selective install (`--agent`, `--division`) or full install + lazy-loading?
- Does it require a conversion step before install?
- Which platforms are supported?
- What are the platform-specific quirks?

### 3. Platform-Specific Patterns

**Hermes**: Many tools install as plugins/skills. Check if the tool supports Hermes natively or via a custom integration script.

**Claude Code / Codex / Cursor**: Commonly supported. Install paths vary by tool.

**Selective vs Lazy Loading**:
- Some tools (e.g., agency-agents with Hermes) install ALL agents but load lazily
- Others support `--agent slug` or `--division name` for selective install
- **Never assume selective install works on Hermes** — check the install script

### 4. Report Findings

When comparing tools, structure the report around:
- Core positioning (what problem does it solve?)
- Input methods (files? URLs? plain text?)
- Output format (editable PPTX? image-based? HTML?)
- Editing capabilities (post-generation customization)
- Platform support
- GitHub popularity (stars as signal of community health)

## Pitfalls

- **Hermes lazy-loading**: Some tools silently ignore `--agent`/`--division` flags on Hermes. Always verify by checking the install script, not just the README.
- **Pre-install steps**: Some tools require running a conversion/generation script before the install script works (e.g., `convert.sh` before `install.sh` in agency-agents).
- **Agent limit**: Some platforms (e.g., OpenCode) have a hard agent limit (~119) and silently drop excess agents.
- **One-off research**: PPT tool comparisons, tool evaluations, and similar research sessions produce reference material worth saving — don't let it disappear between sessions.

## When to Save Findings

Save a reference file when:
- You compared multiple tools and the comparison is useful for future decisions
- You discovered a platform-specific quirk (e.g., Hermes lazy-loading behavior)
- The user expressed interest in a tool category that may recur

Use `skill_manage` with `action=create` to create the skill, then `action=write_file` to add reference files.