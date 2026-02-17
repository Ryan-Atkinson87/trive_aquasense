---
name: release-and-cleanup
description: Use after merging a release PR when the user needs to create the final release tag and clean up test/RC tags
---

# Post-Release Cleanup

After merging a release PR in GitHub, perform the following steps to finalize the release:

## Prerequisites Check
1. Verify you're on the main branch
2. Verify there are no uncommitted changes
3. Confirm the PR has been merged in GitHub

## Pull Latest Changes
1. Pull the latest changes from origin/main
2. Verify the merge commit is present locally

## Create Release Tag
1. Ask the user for the release version number (format: v2.4.0)
2. Create an annotated git tag: `git tag -a v2.4.0 -m "Release v2.4.0"`
3. Push the tag to origin: `git push origin v2.4.0`

## Cleanup Test Tags
1. List all test tags matching pattern `v*.*.*-pi_test*`
2. Delete each test tag from origin: `git push origin :refs/tags/TAG_NAME`
3. Delete each test tag locally: `git tag -d TAG_NAME`
4. Confirm all test tags have been removed

## Cleanup RC Tags
1. List all RC tags matching pattern `v*.*.*-rc*`
2. Delete each RC tag from origin: `git push origin :refs/tags/TAG_NAME`
3. Delete each RC tag locally: `git tag -d TAG_NAME`
4. Confirm all RC tags have been removed

## Feature Branch Cleanup
1. List all local branches: `git branch`
2. List all remote branches: `git branch -r`
3. Identify feature branches (exclude main and dev)
4. **IMPORTANT**: Ask the user to confirm which feature branch was just merged and should be deleted
5. Only after user confirmation, delete the specified branch:
   - Delete locally: `git branch -d BRANCH_NAME`
   - Delete from origin: `git push origin --delete BRANCH_NAME`
6. Do NOT automatically delete any branches without explicit user confirmation

## Final Verification
1. Run `git branch -a` to show all remaining branches
2. Verify only main and dev remain (plus any other active feature branches the user wants to keep)
3. Run `git tag` to show remaining tags
4. Verify only release tags (v*.*.* without suffixes) remain
5. Confirm the new release tag is present both locally and on origin

## GitHub Release Reminder
1. Remind the user to create or update the GitHub Release for this version
2. The release should be created at: https://github.com/Ryan-Atkinson87/trive_aquasense/releases
3. It should reference the tag just pushed and include highlights from the CHANGELOG

## Summary
Provide a summary of:
- ✅ Release tag created and pushed
- 🗑️ Number of test tags deleted
- 🗑️ Number of RC tags deleted
- 🗑️ Feature branch deleted (if confirmed by user)
- 📋 List of remaining branches and tags