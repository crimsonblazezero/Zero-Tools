---
name: hermes-agent-skills
description: "Hermes skills management & Matt Pocock skills reference."
tags: [hermes, skills, configuration]
---

# Hermes Agent — Skills & Configuration

Hub skill for Hermes Agent skill management and configuration.

## Skills Overview

Hermes has two skill tiers:

### Bundled Skills (active by default)
Ship in `~/.hermes/skills/` on install.

### Optional Skills (install explicitly)
Ship under `optional-skills/` but NOT active by default. Install with:
```bash
hermes skills install <name>
```

## Key Optional Skills

### Productivity & Learning
| Skill | Description |
|-------|-------------|
| `memento-flashcards` | Spaced-repetition flashcards. Create cards, chat with flashcards, grade free-text, generate quizzes from YouTube. |
| `teach` | Cross-session teaching workspace: MISSION.md, HTML lessons, learning-records, glossary. From Matt Pocock. |
| `grill-me` | User-invoked grilling: interviewed relentlessly about a plan until every decision branch resolved. From Matt Pocock. |
| `grilling` | Model-invoked grilling loop (underlying `grill-me`). From Matt Pocock. |
| `handoff` | Compact conversation into handoff doc for another agent. From Matt Pocock. |

### AI Agent Gateways
| Skill | Description |
|-------|-------------|
| `antigravity-cli` | Operate Antigravity CLI (agy): plugins, auth, sandbox. |
| `blackbox` | Delegate coding to Blackbox AI multi-model CLI. |
| `grok` | Delegate coding to xAI Grok Build CLI. |
| `openhands` | Delegate coding to OpenHands CLI (model-agnostic). |
| `honcho` | Configure Honcho memory for Hermes. |

### Creative
| Skill | Description |
|-------|-------------|
| `heartmula` | Suno-like song generation from lyrics + tags. |
| `hyperframes` | Render MP4/WebM from HTML compositions. |
| `creative-ideation` | Generate ideas via named creative methods. |
| `concept-diagrams` | Flat educational SVG visuals as HTML. |

### Research
| Skill | Description |
|-------|-------------|
| `duckduckgo-search` | Free keyless web/news/image search. |
| `parallel-cli` | Agent-native web search and deep research. |
| `searxng-search` | Meta-search aggregating 70+ engines. |

### Blockchain
| Skill | Description |
|-------|-------------|
| `solana` | Query Solana wallets, tokens, txs, NFTs. |
| `evm` | Read-only EVM client across 8 chains. |

### Security
| Skill | Description |
|-------|-------------|
| `web-pentest` | Authorized web app pen testing. |
| `oss-forensics` | GitHub repo supply chain forensics. |

## Matt Pocock Skills

Install from GitHub:
```bash
hermes skills tap add mattpocock/skills
hermes skills install teach
hermes skills install grill-me
```

See `references/matt-pocock-skills.md` for full details.

## Skill Management Commands

```bash
hermes skills list                  # List all available skills
hermes skills browse                # Interactive browser
hermes skills search QUERY          # Search by keyword
hermes skills inspect ID            # View skill details
hermes skills install ID            # Install optional skill
hermes skills tap add REPO          # Add GitHub repo as skill source
hermes bundles                      # List skill bundles
```

## Writing Great Skills

See `references/skill-writing-guide.md` for expanded guidance. Key principles:
- **Predictability over output** — same process every run
- **Leading words** — recruit model priors with compact concepts
- **Information hierarchy** — steps in SKILL.md, reference in `references/`
- **Progressive disclosure** — push detailed content behind context pointers

## Related Skills

- `writing-great-skills` — skill writing reference (bundled)

## Full Catalogs

- [Bundled Skills Catalog](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog)
- [Optional Skills Catalog](https://hermes-agent.nousresearch.com/docs/reference/optional-skills-catalog)