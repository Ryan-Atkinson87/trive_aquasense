---
name: prepare-release
description: Use after pi-testing i donwhen preparing for a release, deploying, or when the user asks to check if the project is ready for release
---

# Prepare for Release

When preparing this project for release, perform the following checks:

## Git Release Process
1. Verify you're on the `dev` branch. If not, stop and inform the user.
2. Verify at least one RC tag exists (rc1, rc2, etc.) for this release
3. Check there are no uncommitted changes (`git status` should be clean)

## Version
1. Check `monitoring_service/__version__.py` contains the correct release version
2. If the version needs updating, bump it to match the release tag

## Documentation
1. Verify CHANGELOG.md has been updated with changes for this release
2. Check README.md has any relevant changes documented
3. Review all documentation for accuracy

## Configuration Files
1. Ensure any changes in `.env` have been copied to `.env.example`
   - IMPORTANT: Anonymize any confidential information (API keys, passwords, tokens, etc.)
   - Replace sensitive values with placeholders like `your_api_key_here` or `example_value`

## Dependencies
1. Check requirements files are up to date (requirements.txt, package.json, etc.)
2. Remove any unused dependencies
3. Verify all dependencies have appropriate version pins

## Project Context
1. Review CLAUDE.md to ensure it reflects current project state
2. Update any outdated patterns or conventions
3. If `INSTRUCTIONS.md` exists in the project root, regenerate it from CLAUDE.md:
   - INSTRUCTIONS.md is the Claude.ai project instructions version — same content as CLAUDE.md but formatted for UI use (no CLI-specific commands, focuses on architecture and rules)
   - Compare the current INSTRUCTIONS.md against CLAUDE.md and update any sections that are out of date
   - INSTRUCTIONS.md is gitignored; no commit needed for this file
   - **If INSTRUCTIONS.md does not exist, skip this step silently — do not create it**

## Code Quality
1. Run linters and fix any issues
2. Ensure tests pass
3. Check for any TODO or FIXME comments that should be addressed before release

## Final Report
After completing all checks, provide a summary of:
- ✅ What was verified and is ready
- ⚠️ Any issues found that need addressing before release
- 🚀 Confirmation that the project is release-ready (or what's blocking it)