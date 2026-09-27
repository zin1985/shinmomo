# Rolling Work / Checkpoint Protocol

Updated: 2026-09-28

## Purpose

This project is too large to rely on one ChatGPT conversation or one uninterrupted
tool session. The canonical continuation state therefore lives in GitHub, not
in chat history.

The rule is simple:

> meaningful work is not considered safely complete until the result and the
> next continuation point are committed to `zin1985/shinmomo`.

## Canonical continuation files

- `progress/current_task.json`
  - machine-readable current work item;
  - single canonical source for status, definition of done, completed steps,
    next actions and things that must not be repeated.
- `docs/handoff/CURRENT.md`
  - human-readable rolling handoff for the same current task.
- `progress/project_progress.json`
  - long-term project progress and top-level goals.
- topic-specific docs/data/tools
  - durable evidence and reproducible results.

`progress/current_task.json` has priority if the rolling Markdown handoff and
the machine-readable state ever disagree.

## Start-of-cycle procedure

Every work cycle must:

1. verify the current GitHub `main` HEAD;
2. read `progress/current_task.json`;
3. read the topic-specific evidence listed by that task;
4. preserve all newer parallel results on `main`;
5. define one concrete exit condition before doing substantial work.

Do not reset, force-push, or replace newer parallel findings with an older
handoff.

## Work-unit size

Prefer a work unit that can normally finish within a few minutes and that has
one externally verifiable result, for example:

- one decoder/table proof;
- one runtime experiment;
- one extracted catalog;
- one reproducible tool;
- one map capture promoted to derived evidence;
- one contradiction resolved.

A large goal can continue automatically across several work units without
asking the user to choose each step.

## Checkpoint rule

After every meaningful result:

1. commit the durable result;
2. update `progress/current_task.json`;
3. update `docs/handoff/CURRENT.md` when the next action or status changed.

Do not wait until a long multi-stage investigation is completely finished
before preserving useful evidence.

## Interruption rule

If a tool/session/chat is interrupted:

- preserve already verified results;
- mark the task `active` or `blocked`, never pretend it is complete;
- record the exact next action;
- record any local runtime artifact path needed to resume;
- record `do_not_redo` items for failed/rejected paths.

On the next request such as "continue":

1. read the current task;
2. verify latest `main`;
3. continue from `next_actions[0]`;
4. do not restart investigation already listed under `done` or
   `do_not_redo`.

## Chat-output rule

During long tool work, minimize conversational narration. Report only:

- a material new finding;
- a blocking condition;
- a checkpoint that materially changes the next action;
- the final consolidated result.

Do not return to chat merely because an intermediate discovery was interesting
if the current work-unit exit condition has not yet been reached.

## Completion rule

A task may be marked `done` only when its `definition_of_done` is satisfied
and the corresponding evidence is committed.

A chat statement such as "done" is not sufficient by itself.

## Runtime / copyright-sensitive artifacts

ROM, SRAM, savestate, raw VRAM/CGRAM/OAM and unrestricted raw copyrighted
payloads remain out of Git according to the existing project policy.

For runtime work:

- store raw captures locally;
- commit only derived evidence, metadata, hashes, schemas, tools and analysis
  necessary to reproduce or validate the finding;
- retain local capture paths in the current checkpoint when they are still
  needed.

## Git safety

- GitHub `main` is the source of truth.
- Always check HEAD at work start and before modifying an existing shared file.
- Prefer additive new files when parallel work might conflict.
- Never use force-push/reset to make an old handoff win.
- If local uncommitted work exists, inspect and preserve it before pulling.

## Handoff quality bar

A useful checkpoint must answer all of these without requiring chat history:

- What are we trying to finish right now?
- What has already been proven or implemented?
- What is in progress?
- What exactly should be done next?
- What should not be repeated?
- Which files contain the evidence?
- Which runtime-only artifacts are still needed?
- What is the exit condition for this work item?
