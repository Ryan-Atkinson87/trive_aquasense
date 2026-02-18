---
name: pi-testing
description: Use when preparing a release candidate tag for Pi testing, after the feature branch has been merged into dev via GitHub
---

# Pi Testing - Create RC Tag

Prepare a release candidate tag on the dev branch for deployment and testing on the Raspberry Pi.

## Prerequisites Check
1. Verify you're on the `dev` branch. If not, check out `dev` and pull latest.
2. Verify there are no uncommitted changes (`git status` should be clean).
3. Confirm the feature branch has been merged into `dev` via a GitHub pull request:
   - Use `gh pr list --state merged --base dev --limit 5` to check recent merged PRs
   - If the merge cannot be confirmed, stop and inform the user

## Run Unit Tests
1. Run the full unit test suite: `source venv/bin/activate && pytest tests/unit/`
2. If any tests fail, stop and report the failures to the user
3. Do not proceed with tagging until all tests pass

## Determine Version and RC Tag Number
1. Extract the version from the merged feature branch name (format: `v2.x.x-feature-name` → `2.x.x`)
2. Check `monitoring_service/__version__.py` matches this version
   - If it doesn't match, ask the user to confirm the correct version before proceeding
   - If the user confirms it needs updating, update `__version__.py`, commit, and push to `dev`
3. List existing RC tags for this version: `git tag -l "v<VERSION>-rc*"`
4. If no RC tags exist, the new tag will be `v<VERSION>-rc1`
5. If RC tags exist, increment from the highest number (e.g. if `v2.4.2-rc3` exists, next is `v2.4.2-rc4`)

## Create and Push RC Tag
1. Create an annotated tag: `git tag -a v<VERSION>-rc<N> -m "Release candidate <N> for v<VERSION>"`
2. Push the tag to origin: `git push origin v<VERSION>-rc<N>`

## Summary
Provide a summary of:
- ✅ Feature branch merge confirmed (with PR reference)
- ✅ Unit tests passed (with count)
- 🏷️ RC tag created and pushed (with full tag name)