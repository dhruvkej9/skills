---
name: improve-codebase-architecture
description: "Survey a codebase for deepening opportunities (shallow→deep modules) and produce a visual HTML report of refactor candidates. Use when asked to improve/audit codebase architecture."
version: 1.0.0
author: Dhruv Kejriwal
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, refactor, codebase, survey, depth, seams, report, html]
    category: software-development
    related_skills: [codebase-design, grill-with-docs, codex-review]
---

# Improve Codebase Architecture

Survey a codebase for **deepening opportunities** — places where a shallow module (an interface nearly as complex as the thing it hides) could become a deep one — and write them up as a self-contained HTML report, then grill the user through whichever candidate they pick.

**It never changes the code.** The whole run produces one HTML file in the OS temp directory and a conversation. The refactor happens later, in a separate session, through the normal build flow. This is a *survey*, not a refactoring tool.

## When to reach for it

Invoke by typing `/improve-codebase-architecture`. The agent will NOT reach for it on its own.

Use it in four situations:
- **Routine upkeep** — every few days, or whenever a spare moment appears, to stop structure rotting between features.
- **Before a big build** — point it at the spec: "how can we make this change easy?" (most effective prompt)
- **Brownfield audit** — run on a large, unstructured or vibe-coded repo to find out what shape it is actually in.
- **Legacy test work** — find the missing seams first, before writing tests against untestable code.

Confusable siblings:
- Designing one module you already chose → `codebase-design` (that's the bench; this is the survey that finds what to put on it).
- A whole effort too big for one session → `wayfinder`.
- "This specific thing is broken" → `diagnosing-bugs`.

## Prerequisites

None to run it. It reads `CONTEXT.md` and any ADRs in `docs/adr/` if they exist, and speaks in the domain's own nouns when they do — a candidate reads as "deepen the Order intake module," not "refactor the FooBarHandler."

Writes in two places:
1. The report → `/architecture-review-<name>.html`, OUTSIDE the repo.
2. During the grilling loop → add/sharpen terms in `CONTEXT.md` (create it if missing), and offer to record a rejected candidate as an ADR so a future run does not re-suggest it.

## The core idea: depth

- **Deep module** — puts a lot of behaviour behind a small, stable interface.
- **Shallow module** — leaks its implementation through an interface nearly as wide as the code beneath it.

The report is a hunt for shallowness:
- Pure functions extracted only for testability while real bugs live in how they are called (no **locality**)
- Modules leaking across their **seams**
- A concept you cannot understand without opening five files

## The two filters

Every candidate must pass the **deletion test** — would removing this module concentrate complexity behind a smaller interface, or just spread it across callers? Only "concentrates" cases earn a card.

Unless pointed at a specific area, read recent commit history first and bias the scan toward paths that are **actively changing** — a deepening in code nobody touches is a refactor you will never cash in.

## Report format

Each candidate is a card: files involved, friction, plain-English solution, benefit stated as **locality** and **leverage**, a before/after diagram, and a strength badge:

| Badge | Meaning |
| --- | --- |
| `Strong` | Deletion test passes clearly, friction is real. Take seriously. |
| `Worth exploring` | Plausible deepening, payoff depends on where the code goes next. |
| `Speculative` | Surfaced for completeness. Most are safe to ignore. |

The report ends with a **Top recommendation** — the one to tackle first — then STOPS and asks which candidate to explore. Nothing has been decided; no code has moved.

## After picking a candidate

Start a **grilling** session over it: constraints, what sits behind the seam, which tests survive, what the deepened interface should look like. Output of that session is a **decision, not a diff**. Then the normal flow applies: take the decision into `to-spec` → `to-tickets` → `implement`.

## Procedure

1. Read `CONTEXT.md` and `docs/adr/` if present (for domain nouns).
2. If no specific area given, read recent commit history to find actively-changing paths.
3. Explore the codebase (parallel subagent exploration where the harness supports it) hunting for shallow modules.
4. Apply the deletion test to each candidate; drop the "spreads complexity" cases.
5. Build the HTML report (cards + badges + before/after diagrams + top recommendation).
6. Write report to temp dir (`/architecture-review-<name>.html`).
7. STOP. Ask which candidate to grill. Do not continue on your own.
8. On picking one: grill to a decision, update `CONTEXT.md`, offer ADR for rejected candidates.

## Pitfalls

- **No-grill mode**: user can say "don't grill me, just show the report" — this is the loudest complaint. Report comes first; grilling only starts on a candidate the user chose. Weaker models skip straight to interviewing about the first idea — don't.
- **CDN-styled report breaks offline**: the report loads Tailwind/Mermaid from CDNs and breaks silently when scripts are blocked (SRI hooks, offline, locked-down envs). Workaround: ask for inline CSS and hand-built SVG diagrams instead of the CDN scaffold.
- **One candidate per session** — working through several fills the context window. Carry the candidate, not the file: pick one, grill it, take the decision to `to-spec`, turn the rest into tickets.
- **It will rarely say the codebase is fine** — the skill is built to output findings. A report where everything is `Speculative` is the skill saying it found nothing.
- **Harness limits**: the exploration step names Claude Code's `Agent` tool with `subagent_type=Explore`; harnesses without it may skip parallel exploration (scan is less thorough but still runs).
- **No TYPESCRIPT.md exists** — translating a deepening into concrete package/directory structure is on the user.

## It's working if

- Candidates name the domain's concepts, not invented class names.
- Candidates cluster in files edited recently, not dormant corners.
- No code changed during the run — only the HTML report is new.
- It stops after the report and asks which candidate, rather than continuing on its own.
- Each card explains the payoff as locality/leverage and says which tests get simpler.
- Rejecting a candidate for a durable reason offers an ADR so the next run does not re-suggest it.

## Where it fits

`improve-codebase-architecture` is **periodic maintenance** — run it every few days, outside any chain, to queue up work rather than to do it. Neighbours: `codebase-design` (owns the depth-and-seam vocabulary), `grilling` (walks the decision tree after a candidate is chosen), `domain-modeling` (keeps `CONTEXT.md` and ADRs current). What it produces is an idea, which re-enters the main build flow at `grill-with-docs` or `to-spec`.
