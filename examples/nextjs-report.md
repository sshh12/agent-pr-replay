# Coding Agent Repo Report

- **Repository**: vercel/next.js
- **Sessions Analyzed**: 10

---

## Synthesized CLAUDE.md / AGENTS.md

```markdown
## Test Fixes and Scope Management

- When fixing "flaky test errors", prioritize minimal, targeted changes over comprehensive refactoring across the codebase
- If a prompt mentions specific test failures, search for recent test failure logs, CI outputs, or error traces to identify exactly which files are affected; never apply fixes globally to all similar patterns
- For async/timing-related test flakiness, consider adding synchronization primitives (e.g., `waitForIdleNetwork()`, `waitForSelector()`) alongside the core fix
- When parameterizing tests with new configurations, update ALL test assertions consistently throughout the entire file; never stop partway through

## Test Coverage for Hydration and Client-Server Boundaries

- When fixing hydration mismatches, instanceof checks, or other client-server boundary issues, create both integration tests AND example pages in the test app directory
- For Next.js repos with `test/e2e/app-dir/` structure, follow the pattern: create `test/e2e/app-dir/[feature]/app/[feature]/[scenario]/page.js` alongside the test spec
- Example pages serve as living documentation and allow visual verification of fixes; use patterns like `useSyncExternalStore` and `suppressHydrationWarning` for hydration testing
- If adding a test case to a spec file that tests routes (e.g., `next.browser('/hooks/...')`), ensure the corresponding page component exists or create it

## Algorithm and Tiebreaking Logic

- When changing tiebreaking logic, prefer simple counter closures over HashMap-based tracking; a local counter (`let mut counter = 0; || { let c = counter; counter += 1; c }`) is clearer and more efficient than per-node state tracking
- If the requirement is to replace existing tiebreaking logic (not augment it), fully replace rather than adding layers; never keep old tiebreakers as tertiary fallbacks
- For graph traversal ordering changes, add targeted tests with simple graph structures (triangle or tree) that demonstrate the expected visit order under tied priorities

## Refactoring During Feature Removal or Simplification

- When removing broken features, look for opportunities to simplify related code structure beyond just the removal itself
- If a constant becomes redundant or is only used to compute a single value, inline it at point of use rather than preserving it as a variable
- Reorganize code flow to group related operations together (e.g., all file operations adjacent rather than interleaved with logging)
- When path resolution logic becomes trivial (no conditionals), rename variables to reflect their specific purpose (e.g., `analyzeDir` not `resolvedOutputPath`)
- When removing test cases that validated removed functionality, check if remaining tests need enhanced assertions to maintain coverage

## UI Component Refactoring

- When replacing UI patterns across multiple controls in a single area, extract to a dedicated component rather than inline refactoring (prefer extraction when >50 lines or >3 related controls)
- For select/multi-select components, prefer count summaries ("2 items") over inline badges in the trigger for compactness
- Study existing component patterns before creating new ones; check for `data-slot` attributes, size variants, scroll buttons, and display name exports
- Choose semantic icons that represent the actual value (e.g., `File`/`FileArchive` for compression, not generic `Minimize2`); place icons inside `SelectItem` children, not as custom trigger props
- When modernizing a UI section, review all components in the modified area for related enhancements (e.g., adding search icons to existing search inputs)

## Accessibility in Form Controls

- Wrap checkbox/radio groups in `<fieldset>` with `<legend className="sr-only">` for screen reader context
- Implement keyboard navigation (ArrowUp/ArrowDown, Escape) in custom dropdown components
- Add `aria-label` props to interactive components and pass them through to underlying elements
- Use `sr-only` class for checkbox inputs in visual-only selection UIs

## Stream Error Handling and Async Patterns

- When fixing Node.js stream error handling, prefer `stream/promises` pipeline over callback-based `pipeline()` from `stream`—it returns a Promise that properly propagates errors
- Use `AbortController` with `Promise.all([pipeline(..., {signal}), consumer()])` to run stream processing and consumption concurrently with proper cleanup
- Never manually wrap callback-based `pipeline()` in Promises or use `Promise.race()` with never-resolving promises; prefer built-in promise-based APIs
- For stream teardown on errors, use `abortController.abort()` with promise-based pipelines rather than calling `.destroy()` on individual streams
- Replace manual ReadableStream construction from Node streams with `Readable.toWeb()` (available in modern Node.js)
- When encountering callback-based async patterns causing error propagation issues, check if a promise-based API already exists before adding manual Promise wrappers

## Tracing and Observability Patterns

- When fixing span lifecycle issues with async/streaming operations, prefer replacing `wrap()` with manual `startSpan()` + `withSpan()` rather than adding complexity to preserve wrappers
- Use `.allReady.finally()` callbacks to end spans after React streaming completes; never end spans synchronously when rendering continues asynchronously
- When error handlers need span access, pass the span directly through function parameters rather than relying on `getActiveScopeSpan()` during async callbacks
- For streaming/async boundaries, end spans in `finally()` blocks attached to completion promises, not in `catch` blocks or at function return

## Minimal Changes During Bug Fixes

- When fixing bugs, preserve the existing code structure unless the structure itself is the problem
- Never invert conditional logic or extract helper functions during a bug fix; prefer keeping the same branching structure with minimal moves
- Focus on the minimal change that fixes the issue: if the bug is about bypassing normalization, ensure normalization runs rather than restructuring the entire flow
- When a property causes incorrect behavior, determine if it should be removed entirely or just modified; removing a flag that causes bypass is different from removing data that should be processed

## Refactoring Boolean Flags to Enums

- When replacing boolean parameters with enums, examine all call sites AND all places where the boolean is used in conditional logic—the enum likely needs to map to multiple derived boolean values
- Never create a helper function that reduces an enum back to a single boolean; prefer inline switch statements that compute all derived flags needed for that context
- If the refactoring prompt mentions "unifying" logic, search for duplicate/parallel implementations that handle the same concept differently—these likely need to be consolidated into the new enum-based approach
- Large refactorings that introduce new type systems often eliminate old specialized functions—actively search for functions that became redundant (grep for names like "onPopstate", "onRestore", "special case")
- For enum-driven behavior with complex state management, keep switch statements inline where state transitions happen rather than scattering helper functions across multiple files

## Refactoring Philosophy

- When the root cause is architectural (e.g., callback-based APIs not propagating errors, wrapper patterns not supporting async), prefer refactoring to modern patterns over adding workarounds
- If you find yourself adding manual error tracking variables or complex promise wrappers, consider whether a better built-in API exists
- Before implementing manual lifecycle management, check for built-in patterns like `AbortController` that handle cleanup automatically
```

---

## Suggested Skills

### Skill 1: Next.js Test Coverage Enhancement

```markdown
---
name: nextjs-test-coverage
description: Enhances test coverage for Next.js hydration, routing, and client-server boundary fixes by creating both integration tests and example app pages. Use when fixing hydration mismatches, instanceof checks, interception routes, or other features that require visual verification across server and client rendering.
---

## Overview

This skill ensures comprehensive test coverage for Next.js features by creating example pages alongside integration tests, following the repository's established patterns in `test/e2e/app-dir/`.

## Instructions

When the user asks you to fix issues related to hydration, client-server boundaries, routing, or instanceof checks:

1. Check if the fix involves behavior that spans server and client rendering
2. Create integration tests in the appropriate `test/e2e/app-dir/[feature]/[feature].test.ts` file
3. Create companion page components in `test/e2e/app-dir/[feature]/app/[feature]/[scenario]/page.js` that demonstrate the fix
4. Use `useSyncExternalStore` and `suppressHydrationWarning` patterns for hydration testing
5. Ensure test routes referenced in `next.browser('/path/...')` have corresponding page components

## Patterns to Follow

- Example pages serve as living documentation and enable visual verification
- For hydration testing, include both server-side and client-side instanceof checks or behavior verification
- Follow the existing test structure: if `hooks.test.ts` exists with companion `app/hooks/**/page.js` files, maintain that pattern
- When parameterizing tests (e.g., `trailingSlash: true/false`), update ALL assertions and URLs consistently throughout the file
- Move configuration into parameterized test blocks when tests need to run with different Next.js config options

## Anti-patterns to Avoid

- Never add only test assertions for hydration or routing issues without creating a test page to demonstrate the fix in a real app context
- Never stop partway through updating a test file when parameterizing—use global search to find all assertions that need updating
- Never create tests with routes that don't have corresponding page components in the app directory
- Never skip adding synchronization primitives (like `waitForIdleNetwork()`) when fixing timing-related flakiness
```

### Skill 2: Next.js Stream and Async Error Handling

```markdown
---
name: nextjs-stream-error-handling
description: Fixes error handling and lifecycle management in Next.js streaming, Server Actions, and OpenTelemetry tracing. Use when fixing issues with stream error propagation, request body consumption, span lifecycle with streaming SSR, or async boundary error handling.
---

## Overview

This skill applies modern Node.js async patterns and proper lifecycle management to fix error handling issues in streaming contexts, particularly for Server Actions and OpenTelemetry spans.

## Instructions

When the user asks you to fix error handling or lifecycle issues in streaming contexts:

1. Identify if the issue involves callback-based APIs that don't propagate errors properly
2. Replace callback-based `pipeline()` from `stream` with `stream/promises` pipeline that returns Promises
3. Use `AbortController` with `Promise.all([pipeline(..., {signal}), consumer()])` for concurrent operations with proper cleanup
4. For OpenTelemetry spans, replace `wrap()` with manual `startSpan()` + `withSpan()` when dealing with async/streaming operations
5. Use `.allReady.finally()` or equivalent completion promises to end spans after async operations complete
6. Replace manual ReadableStream construction with `Readable.toWeb()`

## Patterns to Follow

- Use `abortController.abort()` for cleanup instead of calling `.destroy()` on individual streams
- Pass spans directly through function parameters when error handlers need access, rather than relying on `getActiveScopeSpan()` in async callbacks
- End spans in `finally()` blocks attached to completion promises, not in `catch` blocks or at function return
- Check for built-in promise-based APIs before manually wrapping callbacks
- In `crates/next-api/src/server_actions.rs` and similar files, prefer `PassThrough` streams with `Readable.toWeb()` over manual stream construction

## Anti-patterns to Avoid

- Never manually wrap callback-based `pipeline()` in Promises or use `Promise.race()` with never-resolving promises
- Never end spans synchronously when rendering continues asynchronously
- Never add manual error tracking variables (like `let pipelineError: Error | null`) when a better API exists
- Never check for implementation-specific properties (like `accumulatedChunksPromise`) on return types; prefer explicit lifecycle hooks
- Never preserve wrapper patterns when the architecture mismatch is the root cause—refactor to the right pattern
```

### Skill 3: Minimal Scoped Bug Fixes

```markdown
---
name: nextjs-minimal-bug-fixes
description: Applies surgical, minimal-change bug fixes for Next.js issues, avoiding scope creep and unnecessary refactoring. Use when fixing specific test failures, flaky tests, route matching bugs, or targeted issues where the prompt describes a specific problem to fix.
---

## Overview

This skill ensures bug fixes remain focused on the specific issue without expanding into broader refactoring, applying changes only where necessary while preserving existing code structure.

## Instructions

When the user asks you to fix a specific bug, test failure, or flaky test:

1. Search for error logs, CI outputs, or stack traces to identify exactly which files are affected
2. Apply the fix only to the files exhibiting the problem—do not search for similar patterns elsewhere
3. Preserve the existing code structure, conditional logic, and branching patterns unless they are the direct cause of the bug
4. If the fix involves removing a problematic flag or property, determine whether to remove it entirely or modify it—removing `internal: true` is different from removing `regex: source.namedRegex`
5. Add only the synchronization primitives or timing guards (like `waitForIdleNetwork()`) that are necessary for the specific failure mode

## Patterns to Follow

- For flaky test errors, prioritize minimal targeted changes over comprehensive pattern replacement
- If a prompt mentions specific test files or routes, limit changes to those specific files
- When fixing routing or normalization bypass issues, ensure the problematic code path now goes through normalization rather than restructuring the entire flow
- Keep related operations together when making minimal moves (e.g., compilation + modification should stay adjacent)
- For tiebreaking logic changes, use simple counter closures (`let mut counter = 0`) instead of HashMap-based tracking

## Anti-patterns to Avoid

- Never apply fixes globally across all similar code patterns when only specific tests are failing
- Never invert conditional logic or extract helper functions during a bug fix
- Never keep old tiebreakers as fallback when the requirement is to replace the logic entirely
- Never introduce HashMap lookups for ordering if a sequential counter suffices
- Never remove properties that should be processed (like regex data) when the issue is a flag that causes bypass (like `internal: true`)
```

---

## Key Insights from Analysis

- **Test Scope and Minimal Changes**: Claude tends to apply fixes globally across all similar patterns, while targeted fixes to specific failing tests are often sufficient. (From: "[test] Don't use `request.allHeaders()` in sync `page.on()` callbacks")

- **Test Page Creation for Hydration Issues**: Claude successfully implements code fixes but misses creating example page components that demonstrate the fix works in real application scenarios, which is critical for hydration and client-server boundary issues. (From: "Ensure constructor for `useSearchParams` can be imported for `instanceof` checks")

- **Refactoring Opportunities During Feature Removal**: When removing broken features, Claude focuses narrowly on the removal itself, missing opportunities to simplify related code structure, inline redundant constants, and enhance test assertions. (From: "bundle analyzer: remove custom output option")

- **Modern Async API Adoption**: Claude attempts to patch callback-based patterns with manual Promise wrappers and error tracking variables, while switching to built-in promise-based APIs (`stream/promises`, `AbortController`) provides cleaner solutions. (From: "Fix error propagation and teardown in Server Action request decoding")

- **Component Extraction vs Inline Refactoring**: Claude keeps UI changes inline when replacing multiple controls, while extracting to dedicated components with proper accessibility, keyboard navigation, and icon placement improves maintainability. (From: "bundle-analyzer: use <Select> and multiselect for top bar")

- **Span Lifecycle Management**: Claude tries to preserve existing wrapper patterns when fixing OpenTelemetry issues, while replacing `wrap()` with manual `startSpan()` + `.allReady.finally()` properly handles async streaming lifecycles. (From: "fix: otel error spans from streamed responses")

- **Enum Refactoring Depth**: When replacing booleans with enums, Claude creates simple helper functions that reduce enums back to single booleans, while comprehensive inline switch statements that compute multiple derived flags per enum value capture the full semantic complexity. (From: "Refactor: Unify history traversal with other nav types")

- **Algorithm Simplicity**: Claude introduces HashMap-based tracking and keeps old tiebreakers as fallbacks, while simple counter closures with full replacement of existing logic are more efficient and clearer. (From: "[turbopack] Break ties using a counter instead of node index")

- **Test Parameterization Completeness**: Claude partially updates test files when parameterizing configurations, while comprehensive updates to all assertions, URLs, and configuration blocks throughout the entire file are necessary. (From: "Fix interception routes with trailing slash configuration")
