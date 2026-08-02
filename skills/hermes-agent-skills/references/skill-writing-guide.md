# Skill Writing Guide

Expanded reference for writing great Hermes skills. Based on Matt Pocock's `writing-great-skills` philosophy.

## Skill Structure

```
skills/<skill-name>/
├── SKILL.md              # Main skill file (frontmatter + body)
├── references/           # Supporting reference docs
│   ├── api.md
│   ├── troubleshooting.md
│   └── ...
├── templates/            # Starter files to copy
│   └── config.yaml
└── scripts/              # Re-runnable scripts
    └── verify.py
```

## Frontmatter

```yaml
---
name: skill-name
description: "One-line trigger description for model invocation"
tags: [category, subcategory]
---
```

**`disable-model-invocation: true`** — makes skill user-invoked only (no context load, but user must remember to invoke it).

## Two Content Types

### Steps (ordered actions)
- Ordered list of what the agent does
- Each step ends on a **completion criterion** (checkable, exhaustive)
- Example: "Run `pytest` → completion: all tests pass"

### Reference (consulted on demand)
- Definitions, rules, facts
- Pushed to `references/` for progressive disclosure
- Flat peer-sets are fine (no hierarchy needed)

## Information Hierarchy

1. **In-skill step** — primary tier, in SKILL.md body
2. **In-skill reference** — secondary tier, in SKILL.md
3. **External reference** — tertiary tier, in `references/` file, loaded on context pointer

## Leading Words

Compact concepts already in the model's pretraining. Repeated throughout text to anchor behavior.

Examples:
- _lesson_ — for teaching skills
- _fog of war_ — for uncertainty
- _tracer bullets_ — for iterative development

**Test:** Does replacing a phrase with a leading word make the skill more deterministic?

## When to Split Skills

**By invocation:** Split into model-invoked when a distinct leading word should trigger it independently, or when another skill must reach it.

**By sequence:** Split a run of steps when steps ahead tempt the agent to rush the current one (premature completion).

## Failure Modes

| Mode | Symptom | Fix |
|------|---------|-----|
| Premature completion | Agent stops early | Sharpen completion criterion |
| Duplication | Same meaning in multiple places | Collapse to single source of truth |
| Sediment | Stale layers that never get removed | Prune regularly |
| Sprawl | Skill too long | Progressive disclosure, split by branch |
| No-op | Line model already obeys by default | Delete or use stronger leading word |
| Negation | "Don't do X" names the elephant | State positive target behavior |

## Progress

Use progressive disclosure: keep SKILL.md under 200 lines. Push detailed reference to `references/`.

## Examples

### Good Description
```yaml
description: "Use when the user wants to write documentation, proposals, technical specs, or similar structured content. Triggers on: documentation, spec, proposal, technical doc, write up."
```

### Bad Description
```yaml
description: "This skill helps you write good documentation."
```

The good description has rich trigger phrasing with specific use cases.