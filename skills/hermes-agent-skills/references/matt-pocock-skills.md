# Matt Pocock Skills Reference

Source: https://github.com/mattpocock/skills

## Productivity Skills

### teach
Teach a user a new skill or concept across multiple sessions.

**How it works:**
- Creates a stateful teaching workspace in the current directory
- Builds `MISSION.md` (the real reason for learning)
- Produces beautiful HTML lessons in `./lessons/`
- Tracks progress via `./learning-records/`
- Maintains a glossary in `GLOSSARY.md`
- Curates high-trust resources in `RESOURCES.md`

**Key principles:**
1. **One mission per workspace** — if user wants two unrelated topics, that's two workspaces
2. **Push back on vagueness** — if user can't articulate why, interview before writing
3. **Difficulty is enemy** during knowledge acquisition (reduce cognitive load)
4. **Difficulty is tool** during skill acquisition (retrieval practice, spacing, interleaving)
5. **Every lesson links to a primary source** — never trust parametric knowledge
6. **Wisdom comes from community** — find forums, subreddits, local groups
7. **ZPD (Zone of Proximal Development)** — teach just-beyond-current-ability

**Workspace structure:**
```
./
├── MISSION.md           # Why the user is learning (grounding document)
├── RESOURCES.md         # High-trust external sources
├── GLOSSARY.md          # Canonical terminology
├── NOTES.md             # User preferences, working notes
├── lessons/             # HTML lesson files (0001-xxx.html)
├── reference/           # Cheat sheets, quick reference docs
├── learning-records/    # Key insights, prior knowledge, misconceptions
└── assets/              # Reusable components (stylesheets, quiz widgets)
```

### grill-me
User-invoked grilling. Gets interviewed relentlessly about a plan until every decision branch is resolved.

### grilling
Model-invoked grilling loop. The reusable discipline behind `grill-me`. Interview user one question at a time, waiting for feedback on each.

### handoff
Compact current conversation into a handoff document for another agent. Save to OS temp directory, not workspace. Include "suggested skills" section. Redact sensitive info.

## Core Philosophy

> "Skills are small, easy to adapt, and composable. They work with any model. Based on decades of engineering experience."

The skill system fixes common AI agent failure modes:
1. **Misalignment** → use `grill-me` before starting
2. **Verbosity** → build shared language (glossary, CONTEXT.md)
3. **Bad code** → feedback loops (tests, TDD, diagnosis)
4. **Architecture rot** → regular codebase audits