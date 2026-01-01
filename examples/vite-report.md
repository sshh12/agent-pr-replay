# Coding Agent Repo Report

- **Repository**: vitejs/vite
- **Sessions Analyzed**: 18

---

## Synthesized CLAUDE.md / AGENTS.md

```markdown
# Vite Development Guide for AI Agents

This document provides guidance for AI agents working on the Vite codebase, synthesized from analysis of common patterns and corrections needed across multiple PRs.

## Dependency Management

- After updating dependency versions in `package.json` files, ALWAYS run `pnpm install` to regenerate `pnpm-lock.yaml`
- Never edit lockfiles manually; the package manager must update integrity hashes, transitive dependencies, and resolution entries
- For monorepo dependency updates: (1) update all relevant `package.json` files, (2) run `pnpm install` at root, (3) verify lockfile includes all expected version updates
- When dependency upgrades are requested, run the test suite after installation to catch breaking changes
- If tests fail after dependency upgrades, investigate whether failures are due to changed behavior requiring test assertion updates (e.g., esbuild changing IIFE formatting)

## Experimental Features and Deep Integration

- Experimental modes that fundamentally change system behavior require deep integration across subsystems, not isolated additive changes
- Look for existing boolean flags that gate build vs dev behavior (e.g., `command === 'build'`, `isBuild`) and consider if a new combined flag is needed throughout the codebase
- Never add new top-level config options for experimental features; prefer `experimental.featureName` namespace
- For features marked "experimental" in PR titles, examine how they affect plugin hooks, middleware ordering, and core transformation pipelines
- Check which plugins are conditionally applied based on mode flags in `packages/vite/src/node/plugins/index.ts`

## Plugin System Patterns

- Plugin hooks like `renderChunk`, `generateBundle`, `augmentChunkHash` may need conditional application based on build mode
- Wrap entire hook objects in conditional spreads rather than adding early returns: `...(condition && { hookName: () => {} })`
- When experimental features require different environment behavior, extend `DevEnvironment` via subclassing rather than adding parallel systems
- Features that change when bundling occurs must update plugin conditionals throughout `packages/vite/src/node/plugins/` and `packages/vite/src/node/build.ts`

## Conditional Logic and Mode Checking

- When restricting code execution to specific modes, prefer positive checks (`command === 'serve'`) over negative checks (`command !== 'build'`)
- Negative conditionals are fragile to future changes—new modes may unintentionally match the negated condition
- For dev-only features in Vite specifically: use `config.command === 'serve'`, not `config.command !== 'build'`
- If a bug description says "shouldn't run during X", consider whether the code should "only run during Y" instead

## Test Coverage Principles

- When modifying conditional logic in middleware or filters, add new test cases that verify the newly-allowed behavior
- For bug fixes, prefer extending existing test cases over creating new test files when a fixture can demonstrate the issue with 1-3 line additions
- For security-sensitive changes (CORS, auth, validation), both positive and negative test cases are required
- When fixing formatter-related bugs (Prettier, etc.), write test cases that replicate the actual formatted output with realistic indentation and line breaks
- Test names should reference the root cause tool/behavior, not just symptoms

## Scope Discipline and Minimal Changes

- Match the scope of the request exactly—don't automatically add test cases, documentation, or refactoring unless explicitly requested
- Before adding tests proactively, check `git log -p` on the modified file to see if similar historical changes included tests in the same commit
- Never make changes to source files outside the explicit scope of the task
- When tasks say "similar to how X was added previously", use `git log -p -- <file>` to examine the exact commit and match its scope
- Prioritize functional changes (code + tests) over documentation updates unless explicitly requested

## Test Assertion Patterns

- When validating error messages, prefer `toContain()` over `toBe()` for partial string matching—more resilient to message wording changes
- Use exact string matching (`toBe()`) only when the complete message format is part of the API contract
- Replace generic success indicators (like boolean `true`) with descriptive values that make test failures more diagnosable

## Regex and Pattern Matching

- When multiple regex patterns solve the same problem, prefer patterns that group related optional elements: `(?:,\s*)?` over `,?\s*`
- Non-capturing groups `(?:...)` with `?` quantifier make it clearer that elements are treated as a unit
- When replacing inline checks with regex patterns, extract to a named constant if the pattern is non-trivial or referenced multiple times
- Follow existing variable naming conventions in the function (e.g., if other patterns use `__vite_injected_*` names, define related constants nearby)

## Bug Fix Philosophy

- Before adding conditional logic around existing code, consider if the code should be removed entirely
- If a function call is causing issues, ask: "Should this be called at all at this point?"
- Never add guards to work around problematic behavior; prefer removing the problematic code if it's at the wrong stage of the pipeline
- For import/module resolution bugs, understand the pipeline order: resolution happens before transformation
- Prefer removing problematic code over adding branching logic—simpler code with fewer conditionals is more maintainable

## Browser Targets and Language Version Alignment

- When updating browser compatibility targets, search for JavaScript language version references (`ES20\d{2}`, `es20\d{2}`) across tooling configs
- Check TypeScript `target`/`lib` settings in `packages/create-vite/template-*/tsconfig*.json` patterns
- Check ESLint `globals` configuration in `eslint.config.js`
- Browser baseline years map to ECMAScript versions: 2026 baseline implies ES2023, 2025 baseline implies ES2022
- Configuration updates span multiple domains: runtime (source code), compile-time (tsconfig), and lint-time (eslint)

## Documentation Consistency

- When fixing documentation errors, always search the entire codebase recursively using `Grep` tool without path restrictions
- Never assume you've found all instances after 1-2 matches
- For monorepos, explicitly search `packages/*/README.md` and `*/docs/**` patterns
- After making documentation changes, re-search for the old pattern to confirm zero remaining matches
- State verification explicitly: "Searched entire codebase, found and updated all N occurrences"

## TypeScript Interface Changes

- When adding internal state to objects (properties starting with `_`), always define them in the corresponding TypeScript interface with `@internal` JSDoc comments
- Never use type assertions like `(server as any)._property` when adding new functionality; prefer updating the interface definition
- For multi-file changes involving type definitions, identify all interface/type definition files that need updates before modifying implementation files
- Pattern: If adding `server._property` in implementation, search for the server's interface definition and add the property there first

## File Creation Conventions

- When creating new files, follow POSIX text file conventions: end with a single newline character
- Check existing files in the same directory to match trailing newline conventions
- Most linters and formatters expect files to end with a newline; omitting it can trigger CI/CD warnings

## Dependency Patch Files

- Examine existing patch files in `patches/` directory to match naming conventions before creating new ones
- Check `pnpm-workspace.yaml` `patchedDependencies` section to determine if project uses version-suffixed names
- When patching third-party dependencies, look for and fix obvious formatting issues (trailing spaces, inconsistent indentation) in the vicinity of functional changes
- Examine 2-3 existing patch files to extract patterns for header formats and style choices
```

---

## Suggested Skills

### Skill 1: Vite Dependency Updater

```markdown
---
name: vite-dependency-updater
description: Updates dependencies in Vite monorepo with proper lockfile regeneration. Use when the user asks to update, upgrade, or bump package versions in package.json files.
---

## Overview

This skill handles dependency version updates in the Vite monorepo, ensuring both package.json files and the pnpm-lock.yaml lockfile are correctly updated. It addresses the common pattern where Claude updates package.json but forgets to regenerate the lockfile.

## Instructions

When updating dependency versions in the Vite repository:

1. **Identify all package.json files** that need updates
   - Search for the dependency name across all `package.json` files
   - Check both `dependencies` and `devDependencies` sections
   - Common locations: root `package.json`, `packages/vite/package.json`, `packages/create-vite/package.json`, `playground/*/package.json`

2. **Update version specifications**
   - Change version strings in all identified files
   - Pay attention to version prefixes: `^`, `~`, or exact versions
   - Note if the prompt specifies exact version format (e.g., "0.20.0" vs "^0.20.0")

3. **Regenerate the lockfile** (CRITICAL STEP)
   - After updating all package.json files, run `pnpm install` from the repository root
   - This updates `pnpm-lock.yaml` with transitive dependencies, integrity hashes, and resolution entries
   - Wait for the command to complete successfully

4. **Run tests to verify compatibility**
   - Execute `pnpm test` or relevant test commands
   - If tests fail, investigate whether failures are due to breaking changes in the updated dependency
   - Common issues: changed output formats, API changes, removed features

5. **Update test assertions if needed**
   - For build tools (esbuild, rolldown, etc.), check if output format changed
   - Update test expectations to match new behavior (e.g., IIFE formatting, code generation differences)
   - Use Grep to find test files that reference the updated dependency

## Patterns to Follow

- Always run `pnpm install` after editing package.json files—never commit package.json changes without lockfile updates
- Check for platform-specific bindings that may need updating (e.g., `@rolldown/binding-*` packages)
- Verify lockfile diff is significantly larger than package.json diff due to transitive updates
- For monorepo updates, make all package.json changes before running install (not one at a time)

## Anti-patterns to Avoid

- Never edit pnpm-lock.yaml manually
- Never skip running the package manager after version updates
- Never assume dependency updates are complete without test verification
- Never update only the direct dependency without checking for related packages (e.g., updating `rolldown` should prompt checking for `@rolldown/*` packages)
```

### Skill 2: Vite Test Case Designer

```markdown
---
name: vite-test-case-designer
description: Designs appropriate test coverage for Vite changes following project conventions. Use when implementing bug fixes, adding features, or when user asks to add or update tests.
---

## Overview

This skill ensures test coverage follows Vite project conventions, particularly around scope discipline (not over-testing), test location decisions (extend vs create new), and formatter-aware test cases.

## Instructions

When adding or updating tests in the Vite repository:

1. **Determine if tests are needed**
   - Check `git log -p` on modified files to see if similar historical changes included tests
   - If the prompt doesn't mention tests AND historical precedent shows minimal changes without tests, don't add them proactively
   - Ask the user if uncertain: "Should I add test coverage for this change, or keep it minimal?"

2. **Choose test location strategy**
   - For bug fixes in existing features: extend existing test cases rather than creating new files
   - Check if adding 1-3 lines to an existing test fixture can demonstrate the bug
   - Create new test files only for genuinely new features or when existing tests can't accommodate the case
   - Pattern: bugs in `packages/vite/src/node/plugins/css.ts` should extend tests in `packages/vite/src/node/__tests__/plugins/css.spec.ts`

3. **Design formatter-aware test cases**
   - If fixing bugs caused by code formatters (Prettier), replicate the actual formatted output in tests
   - For multi-line formatting bugs, include realistic indentation and line breaks
   - Test names should reference the root cause: "multi-line formatting" not just "trailing comma"
   - Run Prettier on sample code to see exact output before writing test expectations

4. **Create playground tests for integration issues**
   - For path resolution, import analysis, or build output issues, create minimal playground in `playground/[issue-name]/`
   - Include minimal reproduction: `package.json`, test file, and necessary fixtures
   - Use `file:` protocol for external package resolution tests; use `link:` for workspace references
   - Keep fixtures minimal—only include code paths that exercise the specific bug

5. **Write appropriate assertions**
   - Use `toContain()` for error messages (resilient to wording changes)
   - Use `toBe()` only for API contracts or exact values
   - Replace boolean success indicators with descriptive strings that aid debugging
   - For behavior changes (e.g., allowing new request types), add both positive and negative test cases

6. **Verify test specificity**
   - Tests should fail if the bug is reintroduced
   - Avoid generic "does it work" tests—target the specific condition that was broken
   - For conditional logic changes, ensure test exercises both branches

## Patterns to Follow

- Extend existing test fixtures when possible: add lines to existing files rather than creating new directories
- For security-sensitive changes (CORS, auth), always include both allowed and blocked scenario tests
- Test file organization: `packages/vite/src/node/__tests__/` for unit tests, `playground/*/\_\_tests__/` for integration tests
- Match test assertion style to existing tests in the same file

## Anti-patterns to Avoid

- Never create new test fixtures when existing ones can demonstrate the bug with minor additions
- Never only update assertion strings in existing tests when fixing conditional logic—add complementary test cases
- Never write simplified test cases for formatter bugs—replicate actual formatter output
- Never add tests speculatively for low-risk pattern-following changes unless explicitly requested
```

---

## Key Insights from Analysis

- **Dependency Management**: Multiple sessions show Claude updating `package.json` but forgetting to run `pnpm install` to regenerate the lockfile, causing incomplete dependency updates. This pattern appeared in both "update rolldown to 1.0.0-beta.57" and "update rolldown to 1.0.0-beta.54", as well as "feat(deps): update esbuild from ^0.25.0 to ^0.27.0". (From: "feat: update rolldown to 1.0.0-beta.57", "feat: update rolldown to 1.0.0-beta.54", "feat(deps): update esbuild from ^0.25.0 to ^0.27.0")

- **Scope Discipline**: Claude tends to add "best practice" additions like test cases and documentation even when historical precedent shows minimal changes. The human made surgical changes following established patterns, while Claude expanded scope. (From: "feat(css): support es2024 build target for lightningcss", "fix: detect `import.meta.resolve` when formatted across multiple lines")

- **Test Design Philosophy**: When fixing bugs, Claude creates new test files/fixtures while humans prefer extending existing tests. Claude added a new test directory for multi-line `import.meta.resolve`, while the human added 3 lines to an existing fixture. (From: "fix: detect `import.meta.resolve` when formatted across multiple lines")

- **Conditional Logic Patterns**: Claude uses negative checks (`command !== 'build'`) when prompted about avoiding a mode, while humans use positive checks (`command === 'serve'`) that explicitly whitelist intended behavior. This makes human code more robust to future mode additions. (From: "fix: unreachable error when building with `experimental.bundledDev` is enabled")

- **Root Cause Analysis**: Claude tends to add conditional guards around problematic code, while humans remove the problematic code entirely. In the base path stripping bug, Claude added an `if` statement while the human removed the `stripBase()` call completely. (From: "fix: don't strip base from imports")

- **Architectural Understanding**: For experimental features requiring deep integration, Claude creates isolated modules with minimal core changes, while humans make invasive changes across many subsystems. Claude's bundle mode was additive; human's modified plugin loading, build flags, and HMR throughout the codebase. (From: "feat: highly experimental full bundle mode")

- **Cross-Cutting Updates**: When updating browser targets, Claude focuses on explicit version numbers mentioned in the prompt but misses related language version settings in TypeScript configs and ESLint. Humans understand browser targets and JavaScript language versions must stay synchronized. (From: "feat!: update default browser target")
