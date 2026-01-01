# Coding Agent Repo Report

- **Repository**: expressjs/express
- **Sessions Analyzed**: 21

---

## Synthesized CLAUDE.md / AGENTS.md

```markdown
# Express.js Development Guide for AI Agents

This document provides guidance for AI coding agents working on the Express.js repository, based on patterns observed across multiple pull request implementations.

## Release and Version Management

- When PR titles contain "Release: X.Y.Z" or similar versioning patterns, treat the task as a release preparation requiring coordinated updates across multiple files
- Always update version metadata files together: `package.json` version field and `History.md` changelog entries must be modified in the same changeset
- For version bumps: patch version (Z in X.Y.Z) for bug fixes/reverts, minor (Y) for features, major (X) for breaking changes
- Never update source code without corresponding version/changelog updates when the prompt mentions "release" or specific version numbers
- Preserve the exact date format from prompts or PR context; avoid using today's date unless explicitly creating a new unreleased version

## Changelog Conventions

- Before updating `History.md`, read the full file to understand: date formats, entry patterns, linking conventions, and verbosity style
- For security-related releases, this project links to both CVE.org records AND GitHub Security Advisories (GHSA); never link only to NVD or other sources
- Lead with security fixes before features or deprecations in changelog entries
- Never rewrite or paraphrase changelog content from prompts; use exact phrasing provided, especially for security advisories and deprecation warnings
- Match the verbosity level of existing entries; if prior security fixes use terse link-only format, don't add descriptive text
- When adding changelog entries to UNRELEASED sections, preserve existing order within the section; append new entries rather than prepending
- Check for `CHANGELOG.md`, `HISTORY.md`, or `History.md` files when making ANY code changes, especially dependency updates or bug fixes

## Dependency Version Updates

- When updating `package.json` dependencies, examine existing patterns carefully—if some dependencies use exact versions while others use ranges, this is intentional
- Never blanket-convert all exact versions to ranges; preserve exact versions for low-level utilities (e.g., `array-flatten`, `merge-descriptors`, `utils-merge`, `safe-buffer`, `setprototypeof`, `depd`)
- Limit scope to runtime `dependencies` unless the prompt explicitly mentions `devDependencies`—dev tooling versions are often intentionally pinned
- For simple version string format changes (adding ~, ^, etc.), verify the pattern by examining surrounding dependencies before making changes
- Always add corresponding `History.md` entries for dependency updates, following the format: `deps: package-name@^X.Y.Z`

## Reverting Changes

- When asked to revert a security fix because a CVE was rejected or invalidated, treat this as a legitimate request to undo unnecessary breaking changes
- For revert tasks, first read the most recent `History.md` entries to understand what was changed, then systematically reverse those changes across all affected files
- When reverting test cases, remove entire test blocks that were added for the reverted feature, not just assertions
- Revert tasks require synchronized changes across: version files, changelogs, source code, and tests—create a todo list covering all file types

## GitHub Actions Version Pinning

- Always preserve existing action reference patterns: if actions use commit SHA hashes (e.g., `uses: actions/checkout@1af3b93b6815bc44a9784bd300feb67ff0d1eeb3 # v6.0.0`), maintain that format when updating versions
- Never simplify pinned SHA references to version tags; this pattern exists for supply chain security and prevents tag-hijacking attacks
- When updating action versions with SHA pins: find the commit SHA for the new version tag using `gh api repos/OWNER/REPO/git/ref/tags/vX.Y.Z`, update both the SHA and the version comment
- Before editing workflow files in `.github/workflows/`, read at least one to identify the established versioning convention (SHA-pinned vs tag-based)
- Search for ALL occurrences across `.github/workflows/**/*.yml` and `.github/workflows/**/*.yaml` files—never assume an action appears in only one workflow
- The SHA hash in the `uses:` line is the actual reference that needs changing, not just the comment

## Documentation File Discovery

- When asked to modify "the README" or similar documentation, check for case-sensitive variations using: `Glob` with pattern `**/[Rr][Ee][Aa][Dd][Mm][Ee]*`
- Never assume standard naming conventions; this repository uses `Readme.md` (capital R), not `README.md`
- For repository root files, check common variations in parallel: `README.md`, `Readme.md`, `README.rst`, `readme.txt`

## List Modifications and Contextual Cleanup

- When adding entries to lists (team members, contributors, changelogs), preserve the existing ordering pattern rather than imposing alphabetical sort
- Before editing a list, read enough context (5-10 lines above/below the insertion point) to verify the ordering convention
- If you notice formatting errors (missing punctuation, inconsistent spacing) within 2-3 lines of your change location, fix them in the same edit
- Never assume lists should be alphabetized; prefer appending to the end unless evidence shows strict alphabetical maintenance

## External API and URL Migrations

- When migrating between service providers (badges, CDNs, APIs), verify correct endpoint mappings using current documentation rather than inferring from URL pattern similarity
- For badge services: badgen.net and shields.io have different URL structures; use shields.io documentation to find correct endpoints rather than translating path segments literally
- When encountering workflow-specific badges (CI/CD status), look for explicit workflow file references (e.g., `ci.yml`) and preserve them in the migration

## Handling Ambiguous Task Scope

- When a prompt references external criteria ("according to our governance policy") without specifics, use `AskUserQuestion` to clarify which items need action
- Never produce an empty diff when given an explicit modification task; make a reasonable attempt based on context clues or ask for clarification
- If you cannot determine which list items to move/modify, read the target file first to understand current structure, then ask the user to specify
```

---

## Suggested Skills

### Skill 1: Express Release Preparation

```markdown
---
name: express-release-prep
description: Prepares Express.js releases by coordinating version bumps, changelog updates, and managing reverts of security fixes. Use when the user asks to "release version X.Y.Z", "prepare release", "bump version and update changelog", or "revert security fix" in the Express.js repository.
---

## Overview

This skill helps prepare releases for the Express.js repository by ensuring all required files are updated together: `package.json` version, `History.md` changelog entries, source code changes, and test modifications. It handles both forward releases and reverts of security fixes.

## Instructions

When preparing a release:

1. Create a todo list covering all file types that need updates:
   - `package.json` version field
   - `History.md` changelog entry
   - Source code changes (if applicable)
   - Test additions or removals (if applicable)

2. For version bumps:
   - Use patch version (Z in X.Y.Z) for bug fixes/reverts
   - Use minor version (Y) for new features
   - Use major version (X) for breaking changes

3. For changelog entries:
   - Read `History.md` first to understand date format, entry style, and linking conventions
   - Use exact phrasing from the prompt; never paraphrase security advisories
   - For security releases: link to both CVE.org records AND GitHub Security Advisories (GHSA)
   - Lead with security fixes before features or deprecations
   - Match the verbosity of existing entries (terse vs. descriptive)

4. For reverting security fixes when CVEs are rejected:
   - Treat this as a legitimate request to undo breaking changes
   - Read recent `History.md` entries to identify what was changed
   - Systematically reverse changes across all affected files
   - Remove entire test blocks added for the reverted feature

## Patterns to Follow

- Always update `package.json` and `History.md` together in the same changeset
- Preserve exact date format from prompts; avoid using today's date unless explicitly creating UNRELEASED entries
- For dependency updates, use changelog format: `deps: package-name@^X.Y.Z`
- Check if the previous release involved test additions—reverts must remove those tests

## Anti-patterns to Avoid

- Never update just source code without version/changelog updates when the prompt mentions "release"
- Never refuse to revert security fixes when the CVE was rejected or invalidated
- Never paraphrase or simplify changelog entries; use exact wording provided
- Never link only to NVD or generic CVE sources; this project uses CVE.org + GHSA
```

### Skill 2: GitHub Actions SHA Pinning

```markdown
---
name: github-actions-sha-pinning
description: Updates GitHub Actions with commit SHA pinning for supply chain security. Use when the user asks to "update actions/[action-name] to version X.Y.Z", "bump GitHub Action", or "upgrade workflow action" in repositories that pin actions to commit SHAs.
---

## Overview

This skill handles updates to GitHub Actions that use commit SHA pinning instead of version tags. It ensures both the SHA hash and version comment are updated correctly across all workflow files while preserving the security benefits of SHA pinning.

## Instructions

When updating GitHub Actions with SHA pins:

1. Identify the pinning pattern:
   - Read at least one workflow file in `.github/workflows/` to check the format
   - SHA-pinned format: `uses: owner/action@<sha> # vX.Y.Z`
   - Tag-based format: `uses: owner/action@vX.Y.Z`

2. If SHA-pinned, find the correct commit SHA:
   - Use: `gh api repos/OWNER/REPO/git/ref/tags/vX.Y.Z` to get the canonical SHA
   - Or check: `https://github.com/OWNER/REPO/releases/tag/vX.Y.Z`
   - Never guess or generate SHA hashes

3. Search for ALL occurrences:
   - Use `Grep` with pattern: `actions/ACTION-NAME@` across `.github/workflows/`
   - Update all instances to the same SHA and version comment
   - Check both `.yml` and `.yaml` file extensions

4. Update both components:
   - Replace the commit SHA (the actual reference Git uses)
   - Update the version comment (e.g., `# v6.0.0`)

## Patterns to Follow

- Preserve SHA pinning if it exists; never simplify to version tags
- Update all workflow files consistently—the same action version must use the same SHA across files
- For actions used multiple times in one workflow (e.g., codeql-action init/analyze), update all instances
- Verify the SHA exists using: `gh api repos/OWNER/REPO/git/commits/<sha>`

## Anti-patterns to Avoid

- Never convert SHA-pinned actions to tag-based versions; SHA pinning prevents tag-hijacking attacks
- Never use different SHAs for the same version across workflow files
- Never assume an action appears in only one workflow file
- Never update only the version comment without changing the SHA hash
```

---

## Key Insights from Analysis

- **Release Workflow Understanding**: Claude frequently failed to recognize that "Release: X.Y.Z" PR titles signal coordinated updates across `package.json`, `History.md`, source code, and tests—not just version bumps. (From: "Release: 5.2.1", "Release: 4.22.1", "Release: 5.2.0", "Release: 4.22.0")

- **Changelog Linking Conventions**: Claude used incorrect CVE reference patterns (linking to NVD instead of CVE.org + GitHub Security Advisories) and failed to match the project's terse, link-focused style for security fixes. (From: "Release: 5.2.0", "Release: 4.22.0")

- **Dependency Update Documentation**: Multiple sessions showed Claude successfully updating `package.json` but completely missing required `History.md` changelog entries for dependency changes. (From: "fix: upgrade body-parser to 2.2.1 to address CVE-2025-13466", "deps: qs@6.14.0")

- **Security Revert Hesitation**: Claude produced empty diffs when asked to revert security fixes even after being explicitly told the CVE was rejected, suggesting overly cautious safety guardrails around security-related code modifications. (From: "Release: 5.2.1", "Release: 4.22.1")

- **GitHub Actions SHA Pinning**: Claude consistently failed to preserve SHA-pinned action references, either simplifying them to version tags or using incorrect SHAs, breaking the repository's supply chain security pattern. (From: "build(deps): bump actions/checkout from 5.0.0 to 6.0.0", "build(deps): bump actions/download-artifact from 4.3.0 to 5.0.0", "build(deps): bump actions/download-artifact from 5.0.0 to 6.0.0")

- **Case-Sensitive File Discovery**: Claude failed to find `Readme.md` (capital R) when asked to modify "the README", resulting in empty diffs due to insufficient glob pattern flexibility. (From: "docs: update emeritus triagers")

- **Selective Judgment in Bulk Updates**: When asked to add tilde notation to dependencies "using exact versions", Claude converted ALL dependencies including intentionally-pinned ones, lacking the domain judgment to preserve exact pins for stability-critical packages. (From: "use tilde notation for certain dependencies")
