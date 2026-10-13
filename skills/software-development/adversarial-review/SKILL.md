---
name: adversarial-review
description: >-
  Use when changes are complete (code or plan docs) and the agent is
  considering committing, proceeding with implementation, or marking work as
  done. Also use when an implementation plan has been drafted or modified
  before executing it.
---

<!--
Source: verbatim SKILL.md from Appendix A.3.4 of

  Eric S. Qiu and Joyce Gill, "Adversarial Review: Structured Disagreement
  for Grounded Agentic Code Review", arXiv:2608.18167v1, ICML 2026.

  https://arxiv.org/abs/2608.18167

The prompt templates are released by the authors alongside the
implementation; this file reproduces their SWE-bench Verified SKILL.md
without modification apart from rewrapping PDF-extracted line breaks and
this comment. Do not edit the protocol text without checking the paper.
-->

# Adversarial Review

## Overview

Every change -- code or plan document -- must pass an adversarial
review loop before committing or proceeding. Three agent types must
agree: the main agent, a reviewer, and a critic of the reviewer. No
exceptions.

Core principle: Self-review is not review. A single reviewer is not
enough. Adversarial validation catches what consensus misses.

Context rule: Every sub-agent (reviewer AND critic) receives the same
full context -- diff, project docs (CLAUDE.md, architecture docs), and
related code. The critic is not a second-class citizen; it needs the
same information the reviewer had to properly evaluate the review.

## When to Use

Trigger on ANY of these:

- You finished implementing code changes and are about to commit
- You drafted or modified an implementation plan and are about to execute it
- You are about to mark a task or milestone as complete
- The user says "commit", "looks good", "ship it", or similar

This includes small or trivial changes, single-line fixes,
documentation-only changes, and plan documents before execution. No
size exemption.

Do NOT use for mid-implementation exploration (reading files, running
tests to understand behavior) or when the user explicitly says to skip
review for a specific change.

## The Adversarial Review Loop

CRITICAL STRUCTURE: The loop has two nested levels. The artifact
(code or plan) is ONLY edited by the main agent between outer
iterations -- never during the inner loop. Reviewer and critic
exchange text-only reviews; they never touch the artifact.

### Inner loop: converge on a consistent review

Given artifact version N (DO NOT edit the artifact during this loop):

1. Reviewer sub-agent evaluates version N with full context.
   Produces Review_1.
2. Critic sub-agent (fresh) evaluates Review_1 with the same full
   context the reviewer had.
   - If critic agrees with Review_k -> converged. Review_k is the
     consistent review.
   - If critic disagrees -> reviewer responds to the critique,
     producing Review_(k+1). Go to step 2 with the new review.
3. Continue bouncing until reviewer and critic agree on ONE review.

One inner round = reviewer response + critic response. Max 7 inner
rounds before escalating to the user.

The reviews exchanged here are text only. No edits to the code or
plan doc happen yet.

### Outer loop: iterate the artifact

After the inner loop converges on a consistent review:

Termination condition (strict): Terminate and commit/proceed if and
only if BOTH are true:

- The reviewer approved on their first pass -- Review_1 identified
  zero flaws
- The critic agreed on their first pass -- no back-and-forth in the
  inner loop

If terminated:
- If programmatic tests exist: run them, confirm they pass, then commit.
- If changes are UI-only / manually testable: ask the user to test on
  device, then commit.

Otherwise (the consistent review lists flaws, OR the inner loop
needed any back-and-forth to converge): the main agent edits the
artifact to address the flaws in the consistent review, producing
artifact version N+1. Start a fresh inner loop on version N+1.

### Why this structure

- Separation of review and editing prevents the main agent from
  prematurely editing based on one reviewer’s opinion, before
  adversarial validation.
- First-pass termination guarantees quality: if the reviewer had to
  think twice, or the critic had to push back at all, the artifact
  isn’t yet at a "both obviously approve it without discussion"
  state -- so it’s not ready.
- Text-only inner loop keeps the artifact stable while reviewers
  figure out what (if anything) is actually wrong.

### Context for every sub-agent

Every sub-agent invocation (reviewer AND critic, every round, every
outer iteration) receives:

- The current artifact version (diff or plan document)
- Project docs (CLAUDE.md, architecture docs, related code)
- Any prior reviews in the current inner loop

Sub-agents are fresh -- they have no memory. Full context must be
passed every time.

## What the Reviewer Assesses

The reviewer is a senior software engineer evaluating: clarity,
consistency, feasibility, architecture, best practices, correctness,
security, testability.

## Two-Phase Workflow (Plans + Code)

When work involves a plan followed by implementation, the adversarial
review runs twice -- once on the plan, once on the code. You MUST NOT
collapse these into one review.

Phase 1 -- Plan review:
1. Write the plan document (or modify an existing one).
2. Run the full adversarial review loop on the plan.
3. Do NOT write any implementation code until reviewer + critic +
   main agent all agree on the plan.
4. If the review surfaces issues, revise the plan and re-run from
   step 2.

Phase 2 -- Code review:
1. Implement the agreed-upon plan.
2. Run the full adversarial review loop on the code changes.
3. Do NOT commit until reviewer + critic + main agent all agree on
   the implementation.
4. If the review surfaces issues, fix the code and re-run from step 2.

The sequence is: plan -> review plan -> agree -> implement -> review
code -> agree -> commit.

## Implementation Notes

- Use the Agent tool (not TaskCreate) to launch reviewer and critic
  sub-agents. Use subagent_type "general-purpose" or a code-reviewer
  agent type.
- Each sub-agent is fresh -- it has no memory of prior sub-agents.
  Always include full context in the prompt.
- If the original sub-agent can be continued via SendMessage, prefer
  that for the reviewer’s follow-up responses to preserve
  conversation history.
- Launch reviewer and critic sequentially -- each depends on the
  previous output.

## Red Flags -- STOP and Review

You are about to violate this workflow if you think:

- "This change is too small to review"
- "I just wrote this, I know it’s correct"
- "The user already approved it"
- "It’s just a plan doc, not code"
- "Self-review of the diff is sufficient"
- "Running tests is enough without adversarial review"
- "The user is in a hurry"
- "This is a follow-up fix to reviewed code"
- "I’ll implement first, then review the code"
- "The plan is straightforward, I can just implement it"
- "The reviewer already found the flaw, let me fix it while the
  critic reviews"
- "Small flaw, I’ll just fix it now and the critic can catch up"
- "I agree with the reviewer, no need to wait for the critic’s
  opinion"
- "The critic is going to agree, let me start editing"
- "Reviewer approved -- we’re done" (without first-pass verification)
- "The critic disagreed but I agree with the reviewer, let me
  proceed"

All of these mean: start/continue the adversarial review loop. Do
NOT edit the artifact until the inner loop has converged on a
consistent review.

## Common Mistakes

- Editing the artifact during the inner loop. Reviewer and critic
  exchange reviews only. The artifact stays frozen until the inner
  loop converges. Premature edits defeat the whole point of
  adversarial validation.
- Terminating without first-pass verification. The only valid
  termination is "reviewer approved on Review_1 AND critic agreed
  immediately." Any back-and-forth means another outer iteration is
  required.
- Skipping the outer loop after edits. Once you edit the artifact,
  you MUST run a fresh inner loop. Prior approval of version N does
  not carry forward to version N+1.
- Skipping the critic. Sending only to one reviewer and committing

  on approval. The critic catches reviewer blind spots.
- Counting inner rounds wrong. One round is reviewer response +
  critic response. Reviewer alone is half a round.
- Shallow context. Sending just the diff without project docs.
  Reviewers and critics both need CLAUDE.md, architecture docs, and
  surrounding code -- every round.
- Committing before manual test confirmation. For UI-only changes,
  you MUST get explicit user confirmation from device testing.
