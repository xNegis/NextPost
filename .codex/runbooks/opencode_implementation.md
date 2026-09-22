# Codex-Only OpenCode Implementation Runbook

> Audience boundary: this file is only for the Codex coordinator working with the product owner.
> External implementation agents must not use this runbook, launch other agents, or treat it as
> feature scope. Their authority comes from `AGENTS.md`, `harness/context`, and the assigned approved
> implementation plan.

## Purpose

Use this runbook only when the product owner explicitly asks Codex to launch or manage the external
implementation harness for an approved NextPost plan.

This starts a new OpenCode conversation. It is not a Codex subagent and is not a continuation unless
the product owner explicitly requests continuation.

## Verified setup

Verified on 2026-09-15:

- OpenCode CLI: `1.18.16`
- Provider: `OpenCode Go` (`opencode-go`), authenticated
- Model: `DeepSeek V4 Pro (New)` (`opencode-go/deepseek-v4-pro`), active
- Reasoning variant: `high`
- Available model variants: `high`, `max`

Do not silently select a different provider, model, or variant. If verification fails, stop and
report the problem to the product owner.

## Windows entry point

Use the CMD wrapper explicitly:

```powershell
& 'C:\Users\anton\AppData\Roaming\npm\opencode.cmd'
```

Do not change PowerShell execution policy as a workaround.

## Lightweight verification

When the installation or credentials may have changed, run:

```powershell
& 'C:\Users\anton\AppData\Roaming\npm\opencode.cmd' providers list
& 'C:\Users\anton\AppData\Roaming\npm\opencode.cmd' models opencode-go --verbose
```

## Preflight gate

Before launching:

1. Read `AGENTS.md` and all `harness/context` documents.
2. Resolve the exact `harness/features/RF-XX-Implementation-plan.md` requested by the owner.
3. Confirm its status is `Ready for implementation` and `Remaining questions` is `None`.
4. Confirm `harness/context/04_PROJECT_STATE.md` identifies the same ticket as ready.
5. Inspect and record current uncommitted changes so they can be preserved.
6. Do not launch if the plan is a draft, questions remain, or its contract conflicts with current code.

## Start a new conversation

Use `opencode run` without `--continue`, `--session`, or `--fork`:

```powershell
& 'C:\Users\anton\AppData\Roaming\npm\opencode.cmd' run `
  -m opencode-go/deepseek-v4-pro `
  --variant high `
  --title 'RF-XX Feature Title Implementation' `
  $implementationPrompt
```

Do not use `--auto` by default.

## Standard implementation prompt

Adapt only the ticket identifier, title, plan path, and known unrelated worktree changes:

```text
Start a new implementation task for the NextPost repository.

Implement <RF IDENTIFIER AND TITLE> completely, as specified in:
<APPROVED IMPLEMENTATION PLAN PATH>

Work autonomously through implementation and validation. Before making changes:
1. Read AGENTS.md completely.
2. Read every source-of-truth document under harness/context completely.
3. Read the complete assigned implementation plan and all plans it names as dependencies.
4. Inspect the current code, tests, configuration, and worktree.

Requirements:
- Implement only the approved plan scope.
- Follow all accepted decisions, architecture, security, privacy, and validation requirements.
- Preserve unrelated existing worktree changes; never overwrite or revert user changes.
- Add the meaningful tests required by the plan.
- Run every applicable validation command specified by the plan and any additional focused checks
  justified by the implementation risk.
- Do not merely produce another plan; continue until implementation and executable validation are
  complete or a concrete blocker requires product-owner input.
- Do not commit, push, deploy, or modify Trello.
- Keep code, documentation, test names, and the final report in English.
- Update harness/context/04_PROJECT_STATE.md only when the resulting state is supported by evidence.
- At the end, report changes, validation results, important decisions, and remaining limitations or
  manual checks concisely.

Use the repository as the source of truth. Do not rely on conversation history or direct Trello access.
```

Mention concrete unrelated dirty files in the prompt when useful.

## Long-running execution

- Launch the process with a retained execution handle and keep the Codex turn open until it exits.
- Tell the product owner when implementation is running.
- Poll at roughly 20-30 second intervals and provide a concise update at least once per minute.
- Do not start a second implementation conversation for the same ticket while one is active.
- Do not end the Codex turn merely to say the process is still running.

If continuity is explicitly required, inspect recent sessions first:

```powershell
& 'C:\Users\anton\AppData\Roaming\npm\opencode.cmd' session list --max-count 10 --format json
```

Pass continuation prompts as one physical command-line string on Windows.

## Completion review

OpenCode's final message is not proof of completion. Codex must:

1. Inspect the actual worktree diff and preserve unrelated changes.
2. Compare the implementation with every requirement and acceptance criterion.
3. Re-run or independently verify checks in proportion to risk.
4. Confirm project state does not claim completion prematurely.
5. Report evidence and remaining manual work to the product owner.

Do not commit, push, deploy, delete, revert, or mutate Trello unless separately authorized.
