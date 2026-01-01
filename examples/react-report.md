# Coding Agent Repo Report

- **Repository**: facebook/react
- **Sessions Analyzed**: 18

---

## Synthesized CLAUDE.md / AGENTS.md

```markdown
## Cross-Package Synchronization

- When prompts mention "syncing" or "porting" changes between packages, use Glob to find all parallel implementations before modifying files (e.g., `packages/*/src/**/ReactFlight*.js`)
- React Server DOM changes typically require identical updates across bundler variants: webpack, esm, parcel, turbopack
- Search for sister implementations using patterns like `*References.js`, `*Server.js`, `*Client.js` to ensure consistency
- Never modify only one variant when the codebase has multiple parallel implementations

## Test Coverage During Refactoring

- When removing deprecated patterns or polyfills, always grep for usage in test files: `**/*test*.js`, `__tests__/**/*.js`
- Test utilities often duplicate production polyfills; removing production code requires updating test helpers
- After removing functions or changing validation behavior, search for the pattern across the entire codebase including test fixtures
- For compiler validation changes, always create test fixtures for each new mode (both `.js` input and `.expect.md` output)
- When modifying error message text, use Grep to find and update ALL `.expect.md` files containing the old error format

## Feature Implementation Completeness

- New settings/config options require updates across: test files, documentation (README.md), UI panels, backend initialization, and tests for both true/false states
- When adding modes or validation rules to compiler code, create corresponding test fixtures demonstrating each mode
- Never consider tests optional; they are required deliverables for validation/configuration changes
- Update existing test files that use changed configuration to use explicit new values

## Validation Over Filtering

- When fixing hydration or diffing issues in framework code, prefer validating expected runtime behavior over blanket filtering
- Look for data attributes (like `vt-name`) associated with runtime behavior; they indicate the framework should validate expected state, not ignore it
- For "allow X in context Y" compiler problems, implement context detection in type inference, not just validation relaxation
- Use type system information (`identifier.type.shapeId`) for validation decisions, not just AST structure

## Minimal Code Changes

- When adding conditions to existing if-statements, prefer extending the boolean expression inline (`if (existing && newCondition)`) over wrapping in outer blocks
- Avoid restructuring code indentation when a simple boolean operator achieves the same result
- Preserve existing code structure unless explicitly asked to refactor
- For bug fixes, prefer relocating or reordering existing logic over adding new defensive code

## Refactoring Opportunities

- When adding functionality that duplicates existing logic, extract shared patterns into custom hooks or utility functions
- Look for existing implementations of similar behavior and refactor to share logic
- Before adding new state or computed values, check if other components compute the same values and centralize the logic
- When extending validation systems for similar constructs (effects vs memos), refactor existing validators to be generic with callbacks rather than duplicating logic

## Boolean Naming Conventions

- Prefer positive boolean names (`enableX`, `showX`, `allowX`) over negative ones (`disableX`, `hideX`)
- Default values should make the name read naturally: `dimLogs: true` is clearer than `disableDimming: false`
- When the existing codebase uses negative booleans, match that pattern for consistency

## Schema Design Simplicity

- Prefer `z.enum([...])` over `z.union([z.literal(...), ...])` for simple string enums
- When replacing boolean configs with enums, use the new enum exclusively; don't add `.transform()` for backward compatibility unless requested
- Use the exact mode names mentioned in the prompt, don't substitute synonyms

## Error Messages

- Keep error messages concise with external documentation links; never inline multi-line code examples in error descriptions
- For compiler diagnostics, use imperative error reasons ('Cannot X') rather than descriptive ones ('X may cause Y')
- When implementing "verbose" error modes for agents, keep messages focused and scannable (~20-30 lines max)
- Use markdown formatting (**bold**) for pattern names to aid agent parsing

## Security Vulnerability Patterns

- When a prompt mentions "security vulnerability," use Grep to search for dynamic property access patterns like `obj[key]` without `hasOwnProperty` checks
- Prototype pollution fixes require `hasOwnProperty.call(obj, key)` checks before accessing dynamic properties, not just try-catch blocks
- In React codebases, import `hasOwnProperty` from `shared/hasOwnProperty` rather than using `Object.prototype.hasOwnProperty`

## Stream and Event Handler Error Handling

- For event handlers on streams (busboy, ReadableStream), wrap operations in try-catch and call `stream.destroy(error)` rather than throwing
- After calling `stream.destroy()`, always `return` immediately to prevent further processing
- For idempotent stream close/error handlers, use the flag pattern: `let closed = false; if (closed) return; closed = true;`

## Protocol and Serialization Format

- When fixing protocol parsing bugs, check if both client and server sides need changes; search for corresponding encode/decode functions
- If fixes involve binary data, look for existing type tags; new data types may need new protocol tags
- For "prevent infinite loops" in reference resolution, look for existing cycle detection utilities before implementing Set-based tracking
- When changing serialization formats (like `$F` to `$h`), apply consistently across all files handling that protocol

## Package Refactoring

- When moving code to a new package, create the complete package structure first: package.json, README, entry points, source files
- Treat as two phases: (1) create new package with all files, (2) update references from old to new
- Never update import paths to non-existent packages; verify the target exists or create it first
- Files should be moved (not deleted), preserving content but updating internal imports

## Test File Naming Conventions

- For compiler validation tests, use `invalid-[validation-name]-[variant].js` pattern
- Include `.expect.md` files for compiler tests demonstrating validation behavior
- Check existing test fixtures to match naming conventions
- Test files should match component boundaries: DOM-specific tests belong in `react-dom/src/__tests__/`, not reconciler tests

## Type System Extensions

- When fixing compiler validation errors for new safe patterns, define new shape IDs in `ObjectShape.ts` and check during validation
- Infer and attach type information during type inference pass, then check during validation
- For function context detection (e.g., "is this an event handler?"), use type inference not AST heuristics
- New behavioral changes to compilers should be gated behind config flags in `Environment.ts`

## Minimal Change Scope

- When fixing a reported issue, limit changes to the exact problem unless explicitly asked to find related issues
- If you discover related issues, mention them but don't modify without user approval
- Prefer surgical one-line fixes over comprehensive pattern-based changes for specific bug reports

## Settings UI Interaction Patterns

- When settings have logical dependencies (A makes B irrelevant), add UI state: disable dependent inputs with onChange logic
- Setting interactions need CSS (disabled states), checked state logic, and onChange handlers
- Search for `__REACT_DEVTOOLS_.*__` globals to find all propagation points for DevTools settings

## Architecture Patterns

- In systems with distinct phases (like React's complete/commit phases), fixes often need changes in multiple phases
- Before implementing, trace the full lifecycle: flags set in one phase and consumed in another require updates to both
- For React reconciler: flag introduction needs updates to `ReactFiberFlags.js`, `ReactFiberCompleteWork.js` (bubbling), and `ReactFiberCommitWork.js` (consumption)

## Handling Complex Features

- When a prompt describes a feature without implementation details, use EnterPlanMode to explore the codebase first
- For features requiring changes across 10+ files, break into phases: (1) define core types/constants, (2) implement core logic, (3) propagate to dependent systems, (4) add tests
- If exploration reveals 15+ files need changes, use AskUserQuestion to clarify scope before proceeding
```

---

## Suggested Skills

### Skill 1: React Cross-Package Synchronization

```markdown
---
name: react-cross-package-sync
description: Use when syncing changes across React's parallel package implementations (react-server-dom-webpack, react-server-dom-esm, react-server-dom-parcel, react-server-dom-turbopack). Automatically identifies and applies consistent changes across bundler variants.
---

## Overview

React Server Components code is duplicated across multiple bundler-specific packages. When modifying functionality in one variant, all parallel implementations must be updated identically to maintain consistency.

## Instructions

When the user's request involves:
- Syncing or porting changes between React packages
- Modifying Flight protocol (ReactFlightClient, ReactFlightServer, ReactFlightReply)
- Updating server references, client references, or bundler configs
- Fixing bugs in react-server-dom-* packages

Follow this process:

1. **Identify Parallel Implementations**
   - Use Glob to find all variants: `packages/react-server-dom-*/src/**/*.js`
   - Common parallel files: `ReactFlightServer.js`, `ReactFlightClient.js`, `*References.js`
   - Bundler variants: webpack, esm, parcel, turbopack, unbundled

2. **Apply Changes Consistently**
   - Never modify only one bundler variant
   - Apply identical changes to all parallel files
   - For bundler-specific files (like `*References.js`), ensure same property overrides and registration patterns

3. **Update Build Configurations**
   - Check `scripts/rollup/bundles.js` for bundle definitions
   - Update `scripts/rollup/inlinedHostConfigs.js` if host configs changed
   - Search for package references in test mocks and fixtures

4. **Test Coverage**
   - Update test mocks for all variants
   - Check fixture imports in `fixtures/` directories
   - Ensure integration tests cover the changed behavior

## Patterns to Follow

- Use Glob patterns like `packages/*/src/**/ReactFlight*.js` to find all variants
- Search for specific symbols across packages to ensure completeness
- For protocol changes (serialization tags like `$F`, `$Q`), update both client and server sides
- Import shared utilities from `shared/` directory (e.g., `shared/hasOwnProperty`) rather than duplicating

## Anti-patterns to Avoid

- Modifying only `react-server-dom-webpack` when other bundler packages exist
- Adding features to one bundler variant without checking for parallel implementations
- Changing serialization format in client code without updating server code
- Missing bundler-specific reference registration functions
```

### Skill 2: React Compiler Test Fixture Management

```markdown
---
name: react-compiler-test-fixtures
description: Use when modifying React Compiler validation rules, error messages, or adding new compilation modes. Ensures comprehensive test fixture coverage including both valid and error cases with proper .expect.md snapshot files.
---

## Overview

React Compiler changes require synchronized updates to test fixtures. Each validation rule, mode, or error message change must have corresponding test cases with expected output snapshots.

## Instructions

When modifying React Compiler code in `compiler/packages/babel-plugin-react-compiler/src/`:

1. **Identify Affected Test Fixtures**
   - Search for test files using the affected annotations (e.g., `@validateExhaustiveEffectDependencies`)
   - Check `compiler/packages/babel-plugin-react-compiler/src/__tests__/fixtures/compiler/` directory
   - Use Grep to find all `.js` and `.expect.md` files referencing changed validation functions

2. **Update Existing Fixtures**
   - When changing error message format, update ALL `.expect.md` files containing old messages
   - When adding modes to existing flags, update annotations from `@flag` to `@flag:"value"`
   - For validation logic changes, regenerate `.expect.md` by running test suite

3. **Create New Test Fixtures**
   - For new validation rules: create both valid and error cases
   - Naming: `invalid-[validation-name]-[variant].js` for main tests
   - Error cases: `error.invalid-[name].js` for expected failures
   - Each `.js` file needs corresponding `.expect.md` with expected compiler output

4. **Test Coverage Requirements**
   - New modes require fixtures demonstrating each mode
   - Validation rule changes need edge cases: valid patterns, invalid patterns, boundary conditions
   - For exhaustive dependency validation: test missing deps, extra deps, and effect event functions

## Patterns to Follow

- Place test fixtures adjacent to related tests in `__tests__/fixtures/compiler/`
- Use pragma comments for configuration: `@enableFeatureName`, `@outputMode:"lint"`
- Include both cases that should pass and cases that should fail
- For verbose error modes, test both standard and verbose output

## Anti-patterns to Avoid

- Changing validation logic without updating affected `.expect.md` files
- Creating only positive test cases without error cases
- Using inconsistent naming patterns (check existing fixtures first)
- Forgetting to run tests to regenerate `.expect.md` after changes
```

### Skill 3: React Protocol and Streaming Fixes

```markdown
---
name: react-protocol-streaming
description: Use when fixing bugs in React Flight protocol, streaming, serialization, or reference resolution. Ensures both client and server sides are updated consistently and protocol changes maintain backward compatibility.
---

## Overview

React Flight uses a custom protocol for serializing and streaming React trees between server and client. Changes to protocol handling require coordinated updates across client parsing, server serialization, and error handling.

## Instructions

When fixing bugs related to:
- React Flight protocol (ReactFlightClient.js, ReactFlightServer.js, ReactFlightReply.js)
- Streaming bugs (ReadableStream, chunks, buffers)
- Reference resolution and cycles
- Serialization format issues

Follow this process:

1. **Identify Protocol Layer**
   - Check if bug affects serialization tags (`$F`, `$Q`, `$@`, etc.)
   - Determine if issue is client-side (parsing), server-side (encoding), or both
   - Look for chunk state management (`PENDING`, `BLOCKED`, `RESOLVED`, `ERRORED`)

2. **Cross-Boundary Analysis**
   - Always check both client and server implementations
   - Search for corresponding functions: `resolveModel`/`parseModel`, `processChunk`/`emitChunk`
   - Verify tag handling is consistent: if client parses tag 'b', server must emit 'b'

3. **State Management Patterns**
   - For chunk types, ensure all state fields are initialized (`status`, `value`, `reason`)
   - Use existing cycle detection utilities (`resolveBlockedCycle`) rather than implementing Set-based tracking
   - For stream lifecycle, use idempotent flag pattern: `let closed = false; if (closed) return; closed = true;`

4. **Error Handling**
   - For stream event handlers, wrap in try-catch and call `stream.destroy(error)`
   - Always `return` immediately after calling `stream.destroy()`
   - Add context to error messages: include chunk type, position, and expected format

5. **Test Coverage**
   - Test edge cases: partial chunks, buffer boundaries, multi-chunk streams
   - For byte streams, test both small single-chunk and large multi-chunk scenarios
   - Include tests for error conditions and malformed data

## Patterns to Follow

- Search for protocol tag definitions to understand format before modifying
- When adding new data type support, define new protocol tag (don't reuse existing)
- Check if changes need updates to both inline and unbundled variants
- For buffer handling, consider zero-copy optimization when safe (end of processing batch)

## Anti-patterns to Avoid

- Modifying client parsing without checking server serialization
- Adding defensive `.slice()` copies in hot paths without investigating zero-copy alternatives
- Implementing cycle detection from scratch when utilities exist
- Throwing errors in async event handlers instead of calling `stream.destroy()`
- Changing chunk state without initializing all required fields
```

---

## Key Insights from Analysis

- **Cross-Package Consistency**: React Server DOM changes require identical updates across 4+ bundler variants (webpack, esm, parcel, turbopack). Claude frequently modified only one variant, missing parallel implementations. (From: "Patch FlightReplyServer with fixes from ReactFlightClient", "Move react-server-dom-webpack/*.unbundled to private package")

- **Test Coverage Integration**: Test fixtures are not optional additions but integral to feature implementation. Claude consistently omitted test updates when removing polyfills, adding validation modes, or changing error messages. (From: "Use FormData submitter parameter", "Add reporting modes for exhaustive-effect-dependencies", "Add enableVerboseNoSetStateInEffect flag")

- **Minimal vs. Comprehensive Changes**: Humans prefer surgical edits that extend existing conditionals inline, while Claude tends to refactor with new functions and indentation changes. This pattern appears in compiler changes where minimal diffs are critical. (From: "Only run validations with env.logErrors on outputMode: 'lint'", "Fix VariableDeclarator source location")

- **Architecture Over Patches**: Complex bugs often require architectural changes (moving logic to different lifecycle phases, extracting custom hooks) rather than defensive coding. Claude adds validation checks where humans restructure control flow. (From: "Fix form status reset when component state is updated", "Navigating commits performance panel hotkey")

- **Protocol Synchronization**: React Flight protocol bugs require coordinated client/server updates. Claude focuses on one side, missing that serialization tag changes, cycle detection, and stream handling need bilateral consistency. (From: "[Flight] Patch Promise cycles and toString on Server Functions", "[Flight] Fix broken byte stream parsing")

- **Type System for Validation**: Compiler validation should use type inference and shape IDs, not just AST patterns. Claude relaxes validation with blanket filtering where humans add typed inference paths distinguishing safe vs unsafe contexts. (From: "Allow ref access in callbacks passed to event handler props", "Skip hydration errors when a view transition has been applied")

- **Feature Completeness**: New features need synchronized updates across multiple layers: core logic, UI, backend, tests, and docs. Claude implements core logic but misses UI interactions, settings propagation, and documentation. (From: "Devtools disable log dimming strict mode setting", "Add keyboard shortcuts to navigate commits")
