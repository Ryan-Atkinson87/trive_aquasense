---
name: organise-releases
description: Use when the user asks to organise, triage, or update the release plan — groups all open GitHub issues into releases and keeps _local_notes/RELEASES.md in sync
---

# Organise Releases

Review all open issues on the project board, group them into planned releases, and update `_local_notes/RELEASES.md` to reflect the current state.

**Important workflow note:** `_local_notes/RELEASES.md` is the source of truth for release planning. GitHub milestone assignments are set manually by the user *after* RELEASES.md is updated. New issues on the board will not have milestones yet — do not rely on milestone fields to determine placement. Instead, analyse the issue content and suggest placement based on scope and fit.

---

## Semantic Versioning Reference

This project uses **MAJOR.MINOR.PATCH** versioning:

| Segment | When to increment | Examples |
|---------|-------------------|---------|
| **MAJOR** | Breaking changes — incompatible with previous deployments or requiring migration steps | Restructured import paths, changed config schema, new storage dependencies |
| **MINOR** | New features or significant non-breaking improvements | New sensor driver, new transport layer, new telemetry field |
| **PATCH** | Bug fixes, internal cleanup, test improvements, small quality-of-life changes | Rounded output values, fixed test failures, improved docstrings |

Use this table when suggesting which release version an unplaced issue belongs in.

---

## Step 1 — Fetch All Project Board Issues

```
gh project item-list 1 --owner Ryan-Atkinson87 --format json --limit 100
```

For each item, record: issue number, title, body, status, milestone, labels, URL.

**Classify each issue:**

| Bucket | Status values | Treatment |
|--------|---------------|-----------|
| **Active** | Backlog, Next Release, In Progress, Review / Testing | Must appear in RELEASES.md |
| **On Hold** | On Hold | Goes in the On Hold section only |
| **Done** | Done | Excluded from RELEASES.md entirely |

---

## Step 2 — Read the Current Version

Read `monitoring_service/__version__.py` to get the current shipped version string (e.g. `"2.4.2"`). This goes in the `Current version:` line at the top of RELEASES.md.

---

## Step 3 — Check Whether RELEASES.md Exists

Check for `_local_notes/RELEASES.md`.

- **If it exists:** read its full contents — this is the baseline to update.
- **If it does not exist:** build it from scratch and note this to the user.

---

## Step 4 — Cross-Reference Issues Against RELEASES.md

Compare every **Active** issue from the board against the existing RELEASES.md:

- **Already listed** — issue number appears in an existing release section. No action needed unless it has moved or been marked Done.
- **New / unlisted** — issue is Active but not mentioned anywhere in the file. These need to be placed (see Step 5).
- **Should be removed** — issue was in the file but its status is now Done. Remove it from the release section.
- **Moved milestone** — if the user has updated a GitHub milestone since the last RELEASES.md update, flag this and adjust the section accordingly.

---

## Step 5 — Place New / Unlisted Issues

For each Active issue not yet in RELEASES.md:

1. Read the issue title and body carefully.
2. Determine the correct release using the semver table above and the existing release scope descriptions:
   - Is it a bug fix or cleanup? → PATCH release (or the nearest upcoming PATCH)
   - Is it a new feature or meaningful improvement? → MINOR release
   - Does it break compatibility or require migration? → MAJOR release
3. Check whether an appropriate existing release section already exists. If so, add it there.
4. If no appropriate release exists, propose a new release version and a short name/description.
5. For each placement, include a one-line rationale in the change summary (Step 6).

Do **not** skip or defer unplaced issues. Every Active issue must be assigned a position before the file is written.

---

## Step 6 — Determine Suggested Order Within Each Release

For each release section, determine the recommended implementation order:

- **Unblocking work first** — issues that are prerequisites for others go at the top
- **Lower risk before higher risk** — self-contained changes before those that touch many files
- **Analysis before refactoring** — audit/coverage work before structural changes
- **Infrastructure before features** — foundational plumbing before things that depend on it
- Note any inter-issue constraints inline (e.g. `(unblocks #X)`, `(blocked by #Y)`, `(prerequisite for #Z)`)

---

## Step 7 — Present the Change Summary and Confirm

Before writing anything, present a clear summary of every change that will be made:

```
Proposed changes to _local_notes/RELEASES.md:

Added to v2.5.0:
  + #127 — Audit abstracted methods and make improvements
  + #128 — Round water flow telemetry to 2 decimal places

Removed (now Done):
  - #125 — Fix pkg_resources test failure

No changes:
  v3.0.0, v3.1.0, v4.0.0, v4.1.0, On Hold
```

Ask the user to confirm, or whether they want any placements adjusted, before writing the file.

---

## Step 8 — Write the Updated RELEASES.md

Write the full updated file to `_local_notes/RELEASES.md` using this structure consistently:

```markdown
# Release Planning

Current version: vX.Y.Z

---

## vA.B.C — Release Name

**Milestone description:** [1–2 sentences describing scope and intent of this release]

[Optional Note: any cross-issue constraints, e.g. "Note: #X must be completed before #Y"]

**Suggested order:**
1. #N — Short title (reason for position, e.g. "unblocks test suite")
2. #N — Short title (reason for position)
...

---

## On Hold (no milestone assigned)

- #N — Title (reason, e.g. "hardware not yet available")
```

**Rules:**
- Releases ordered by version number ascending
- Only Active issues appear in release sections — no Done issues
- On Hold section lists all On Hold issues
- Preserve existing `Note:` lines unless no longer relevant
- Preserve existing milestone descriptions unless scope has materially changed
- Update the `Current version:` line to match `__version__.py`

---

## Step 9 — Remind User to Update GitHub Milestones

After writing the file, remind the user to update GitHub milestone assignments to match any changes:

- Issues newly added to a release → assign the corresponding GitHub milestone
- Issues that moved between releases → update their GitHub milestone
- Issues with no GitHub milestone yet → assign one now

Provide the board URL for convenience: `https://github.com/users/Ryan-Atkinson87/projects/1`

---

## Step 10 — Final Summary

Report:
- ✅ RELEASES.md updated (or created)
- Total Active issues tracked across all releases
- Count of issues added, removed, or moved
- Any issues that were placed by suggestion (so the user can double-check)