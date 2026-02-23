---
name: check-github-issues
description: Use when the user asks to check, review, or triage new GitHub issues on the project board — including suggesting descriptions and advising on release placement
---

# Check GitHub Issues

Review the project board for new or undescribed issues, draft descriptions based on codebase analysis, and advise on which release milestone each issue belongs in.

## Step 1 — Fetch the Project Board

Fetch all items from the GitHub project board:

```
gh project item-list 1 --owner Ryan-Atkinson87 --format json --limit 100
```

Parse the JSON response and extract all issues. For each issue, note:
- Issue number and title
- `status` field (e.g. Backlog, Next Release, In Progress, Done, On Hold)
- `milestone` field (title or null)
- `content.body` (the issue body text)
- `content.url`

## Step 2 — Identify New or Undescribed Issues

An issue is considered **new/undescribed** if it meets one or more of these criteria:
- `content.body` is empty (`""`) or contains only whitespace
- `milestone` is null/missing
- `status` is `"Backlog"` and the body is empty

If no such issues exist, report that to the user and stop.

If multiple new issues are found, list them all for the user and ask which ones they want descriptions drafted for — or proceed with all if the user has already asked for that.

## Step 3 — Analyse Each Issue Against the Codebase

For each issue to be described, read the issue title carefully and identify which part of the codebase it relates to. Use Glob, Grep, and Read tools to:

- Locate the relevant source files (sensors, telemetry, outputs, config, tests, etc.)
- Read the current implementation to understand what the issue is pointing at
- Identify the specific gap, bug, or improvement implied by the title
- Note any architecture constraints from CLAUDE.md that affect how the issue should be solved

**Key source directories to explore as relevant:**
- `monitoring_service/inputs/sensors/` — sensor drivers, base classes, factory
- `monitoring_service/outputs/display/` — display drivers and base class
- `monitoring_service/telemetry.py` — telemetry pipeline (key mapping, calibration, smoothing, ranges)
- `monitoring_service/exceptions/` — exception hierarchy
- `monitoring_service/config_loader.py` — configuration loading
- `monitoring_service/agent.py`, `main.py` — orchestration
- `tests/unit/` — existing test coverage

## Step 4 — Draft Issue Descriptions

For each analysed issue, draft a GitHub issue description using the following structure:

```markdown
### Description
[1–2 paragraphs explaining the problem or gap, grounded in what you found in the code. Reference specific files and line numbers where helpful.]

### Tasks
- [ ] [Concrete step 1]
- [ ] [Concrete step 2]
- [ ] ...

### Acceptance Criteria
- [Measurable outcome 1]
- [Measurable outcome 2]
- ...
```

Keep descriptions factual and grounded in the codebase. Do not invent requirements that aren't implied by the title or the code.

## Step 5 — Advise on Release Fit

Read `_local_notes/RELEASES.md` to understand the planned release roadmap and each milestone's scope/description.

For each issue, determine the most appropriate milestone:
- Does the issue fit the scope of an existing planned release?
- Is it a non-functional cleanup that fits alongside code quality work (e.g. v2.5.0)?
- Is it a functional change that should go in its own milestone or a later one?
- Is it too large or hardware-dependent to schedule yet (On Hold)?

Note any cases where a milestone's stated description would need to be loosened to include the issue.

## Step 6 — Write Draft to File

Write all draft descriptions and release recommendations to:

```
_local_notes/issue_descriptions_draft.md
```

Structure the file as:
1. A header noting the date and which issues were reviewed
2. One section per issue with the draft description
3. A **Release Fit** table at the end summarising milestone recommendations for all issues

If `_local_notes/issue_descriptions_draft.md` already exists, overwrite it (it is a working scratch file, not a permanent record).

## Step 7 — Present Summary to User

After writing the file, present a concise summary to the user:
- Which issues were found and reviewed
- A brief (1–2 sentence) synopsis of each draft description
- The release milestone recommendation for each issue
- Confirm the draft file has been written and where to find it

Do **not** push any descriptions to GitHub or update any issues automatically — drafting only. The user will review and decide what to push.