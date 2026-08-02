# Optional Skills Reference

Optional skills ship with Hermes under `optional-skills/` but are **not active by default**. Install explicitly with `hermes skills install <name>`.

## How to Install

```bash
# Install a single optional skill
hermes skills install memento-flashcards

# Install from a GitHub repo
hermes skills tap add mattpocock/skills
hermes skills install teach
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

## Full Catalog

Browse all optional skills: https://hermes-agent.nousresearch.com/docs/reference/optional-skills-catalog