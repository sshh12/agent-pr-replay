# Coding Agent Repo Report

- **Repository**: gin-gonic/gin
- **Sessions Analyzed**: 19

---

## Synthesized CLAUDE.md / AGENTS.md

```markdown
# Claude Agent Guidance for gin-gonic/gin

This document contains synthesized guidance from analyzing Claude's performance on actual PRs in this codebase. Follow these principles to align better with human development patterns.

## Code Style and Naming Conventions

- When adding new code, match the naming patterns used in the immediate context (same file/function), even if they differ from general best practices
- For single-use variables in small scopes (<10 lines), prefer the brevity level of surrounding code rather than maximally descriptive names
- Before implementing changes, check the file for similar patterns (e.g., other type assertions, variable naming in similar contexts) and mirror that style exactly
- When modifying files, scan for minor style improvements to bundle in (grouping related constants/vars, adding blank lines, consistent formatting)
- If the codebase has ungrouped constant declarations, check if similar PRs group them into `const ( ... )` blocks and apply the same transformation

## Constants and Magic String Refactoring

- When replacing magic strings/numbers with constants, first check for existing constant definitions in `utils.go`, constants files, or package-level declarations before creating new ones
- Never create duplicate constant definitions across multiple files; prefer defining shared constants once in a central location
- For test-only constants that appear in multiple test files, define them once in a shared test utility file or the main package's constants
- Preserve existing string formatting patterns: if the codebase uses `fmt.Sprintf` for string interpolation, continue using it rather than switching to concatenation
- After identifying replacement locations, search the codebase structure to determine the idiomatic location for constants

## Code Organization and Utility Placement

- Before adding new functions, check if similar utilities exist nearby (e.g., `cleanPath` in `path.go`, `bufApp` helper)
- Place path/string manipulation utilities in the file where related functions live, not just where they're first called
- When you see existing patterns (buffer allocation with `stackBufSize`, helper functions like `bufApp`), reuse them instead of reimplementing
- When adding methods, scan the file structure first to identify grouping patterns (e.g., all getters together, then setters, then other operations)
- Never place methods solely by logical similarity to one nearby method; prefer matching the established organizational flow of the entire file

## Struct Field Initialization in Constructors

- When adding new fields to structs with constructor functions, always check if the constructor explicitly initializes all fields, even zero values
- Go codebases often explicitly set zero values (false, 0, nil) in constructors for documentation clarity—never assume implicit zero initialization is sufficient
- After adding a field, search for patterns like `func New(` or `func Default` to find all initialization sites
- Update constructor documentation comments that list default values when adding new fields

## Test Coverage Calibration

- Match test depth to code complexity: simple utility functions (single if-statement, no loops/branches) need only 2-3 assertions covering normal operation and boundary/edge cases
- Never write exhaustive input permutations for straightforward logic; prefer focused tests that validate the key behavior and one edge case
- Match test complexity to the project's existing test patterns by reading 2-3 similar tests before writing new ones
- Never write comprehensive stress tests or extensive edge case coverage unless the existing test file shows this pattern
- For simple CRUD operations, prefer minimal happy-path tests that verify the core behavior in 10-20 lines
- Add concurrency tests only if: (1) the prompt explicitly requests thread-safety verification, or (2) existing tests in the file already include concurrent operation testing

## Test Implementation Patterns

- Prefer standard library testing utilities (`httptest.NewRequest`, `httptest.NewRecorder`) over internal test helpers unless the codebase consistently uses the internal approach
- Before writing tests, read existing tests in the same file to match the established patterns (test helper usage, assertion style, setup approach)
- Never create new test files for bug fixes; prefer adding tests to existing `*_test.go` files in the same package
- Add new test functions at the end of the existing test file, maintaining alphabetical or logical grouping
- For bug fix tests, include a comment referencing the issue/PR number

## Test Coverage for Refactored Functions

- When replacing a function with a new implementation, write comprehensive new tests rather than minimally adapting existing ones
- Create temporary files with `os.CreateTemp()` for testing file I/O functions to cover real-world scenarios
- Test edge cases explicitly: negative indices, out-of-bounds access, non-existent files, empty results
- For performance-critical changes, add benchmark tests using `testing.B` to quantify improvements

## Test Mocking Patterns in Go

- When making code testable by extracting dependencies, prefer the simplest extraction: extract computed values (e.g., `var runtimeVersion = runtime.Version()`) rather than function references (`var runtimeVersion = runtime.Version`) when the value is constant during a test
- In Go tests, directly reassigning package-level variables is simpler than save/restore patterns with defer when test isolation isn't needed
- When fixing existing tests to work with mocks, modify the test to be deterministic rather than adding conditional logic

## Code Modification Strategy: Extend Before Creating

- When requirements mention "the same way we handle X", investigate how X is currently handled and extend that exact mechanism rather than creating parallel logic
- Prefer setting existing flags/variables to trigger established code paths over adding early returns or new conditional branches
- Minimal diffs reduce maintenance burden: prefer reusing existing flags over creating new conditional blocks
- Never create divergent handling for similar error types; prefer unifying them under shared flags or abstraction points
- Modify existing conditionals rather than adding new defensive layers; refactor the logic that's already handling the case

## Bug Fixes: Minimal, Scoped Changes

- Never add "related" defensive fixes outside the reported problem scope; prefer addressing only the specific bug described
- When the prompt mentions specific failure modes, trace to the exact conditional causing it rather than adding guards elsewhere
- Consolidate checks into existing control flow instead of duplicating validation logic
- Test cases should cover exactly what the prompt describes
- Distinguish between "field not present" vs "field present but empty" when the bug involves form/request parsing

## Performance Optimization Refactoring

- When optimizing for performance, include benchmarks to validate the improvement (e.g., `BenchmarkStack` in `recovery_test.go`)
- Never return errors via sentinel values when the language supports explicit error returns; prefer `(T, error)` return signatures for distinguishable error conditions
- Look for opportunities to use standard library improvements like `cmp.Or()` (Go 1.22+) instead of inline ternary-style logic
- When introducing helper functions during optimization, consider whether related constants should move from local to package scope for reusability

## Generic vs Specialized Implementations

- When replacing regex with custom functions, consider if the operation is generic (works on any character) or truly specialized
- If a regex pattern uses a character class, the replacement function should probably accept a parameter for that character
- Prefer `strings.Map()` for simple character filtering when it's clearer than manual byte-slice iteration
- Don't hardcode values into function names and implementations if the logic naturally generalizes

## Code Cleanup After Refactoring

- When refactoring functions, always check for and remove dead code: unused imports, constants, helper variables, or utility functions that are no longer referenced
- After making changes, use `Grep` to search for references to removed patterns to verify nothing else depends on them
- When simplifying function logic, look for opportunities to collapse multi-step accumulations into single expressions
- After completing the primary refactor, review the changed functions for further simplification opportunities that align with language idioms

## Resource Cleanup in Go

- Always use `defer` for resource cleanup (file.Close(), mutex.Unlock(), etc.) immediately after resource acquisition
- Never call cleanup methods inline at arbitrary points in the function; prefer `defer` to guarantee cleanup on all exit paths
- Pattern: `resource := acquire(); defer resource.Close()` ensures cleanup happens regardless of early returns or errors
- Defer executes cleanup when the function exits, not immediately

## Pattern Recognition in Existing Code

- Before adding new functionality, examine the entire target file for established patterns (naming conventions, import re-exports, struct field ordering)
- When adding fields to structs alongside existing fields, match the exact naming convention—check capitalization patterns across all existing fields
- If similar constants exist in the file, check if they're re-exported from other packages and maintain that pattern
- Never assume external package constants are sufficient; prefer adding re-exports when the pattern exists (e.g., how `binding.MIMEJSON` is re-exported as `MIMEJSON` in `context.go`)

## Refactoring Scope and PR Boundaries

- When refactoring patterns across a codebase, match the scope implied by the PR context, not every possible instance
- Avoid expanding refactoring scope beyond what's explicitly requested; prefer surgical changes over comprehensive cleanup
- When asked to "fix flaky tests" or similar issues, read the prompt literally - if specific tests aren't named, ask which ones to fix rather than assuming all similar patterns need changes
- Never fix issues beyond what's described in the prompt without explicit user confirmation

## Linter-Driven Changes

- When fixing linter/security warnings, check if the PR also modifies linter configuration files (`.golangci.yml`, etc.) to exclude or adjust rules
- If adding helper functions to address linter warnings, prefer placing them inline in the same file where they're used unless they're genuinely reusable across 3+ files
- Look for `#nosec`, `#nolint`, or similar suppression comments in the target codebase—if the prompt mentions "addressing warnings" but not "fix vulnerabilities", expect suppression comments rather than architectural changes
- Never add comprehensive test files for simple helper functions unless the prompt explicitly requests tests

## Backward Compatibility with sync.Once Patterns

- When introducing `sync.Once` to replace explicit initialization calls, preserve existing explicit calls unless they cause conflicts
- The `sync.Once.Do()` pattern is idempotent - existing explicit calls become no-ops but maintain backward compatibility
- Example: If adding `engine.routeTreesUpdated.Do(func() { engine.updateRouteTrees() })` to `ServeHTTP()`, keep existing `engine.updateRouteTrees()` calls in methods like `Run()`
```

---

## Suggested Skills

### Skill 1: gin-refactoring-patterns

```markdown
---
name: gin-refactoring-patterns
description: Use when refactoring code in the gin-gonic/gin repository (constants, utility functions, helper methods). Applies gin-specific patterns for code organization, constant placement, and test coverage.
---

# Gin Refactoring Patterns

## Overview

This skill helps Claude apply gin-specific refactoring patterns when modifying code organization, extracting constants, or moving utility functions in the gin codebase.

## Instructions

When refactoring code in gin:

1. **Check for existing patterns first**: Before creating new constants or utilities, search `utils.go`, `path.go`, `context.go`, and test helper files
2. **Avoid duplication**: Never create duplicate constants across multiple files; use central locations
3. **Match local style**: Preserve existing string formatting patterns (e.g., `fmt.Sprintf` vs concatenation)
4. **Reuse existing helpers**: Look for patterns like `bufApp`, `stackBufSize` in `path.go` before reimplementing
5. **Test appropriately**: Match test depth to code complexity - simple functions need 2-3 assertions, not exhaustive coverage

## Patterns to Follow

- Place shared constants in `utils.go:22-25` (like `localhostIP`, `localhostIPv6`)
- Place path manipulation utilities in `path.go` alongside `cleanPath`
- For simple utility functions (single if-statement), write 2-3 test cases covering normal + edge case
- When extracting constants, use `Grep` to find similar existing constants and match their location
- Group constant declarations into `const()` blocks when modifying files that use this pattern
- Preserve `fmt.Sprintf` over string concatenation if that's the existing pattern

## Anti-patterns to Avoid

- Don't create file-local constants when the value could be reused across packages
- Don't write 9+ test assertions for simple utility functions with straightforward logic
- Don't place new utilities in the first file where they're called - find the architectural home
- Don't implement from scratch when helpers like `bufApp` exist in `path.go`
- Don't switch between `fmt.Sprintf` and concatenation inconsistently
```

### Skill 2: gin-test-coverage

```markdown
---
name: gin-test-coverage
description: Use when writing tests for gin-gonic/gin. Calibrates test depth to match gin's pragmatic testing patterns, avoiding over-engineering while ensuring adequate coverage.
---

# Gin Test Coverage Patterns

## Overview

This skill ensures test coverage matches gin's pragmatic approach: focused tests that validate key behaviors without exhaustive edge case permutations.

## Instructions

When writing tests for gin:

1. **Read existing tests first**: Check 2-3 similar test functions in the same file to understand depth and style
2. **Match test utilities**: Use `httptest.NewRequest`, `httptest.NewRecorder` if that's the pattern; use `testRequest()` if that's established
3. **Calibrate depth**: Simple functions need 2-3 assertions; don't write comprehensive suites for single-conditional logic
4. **Add tests to existing files**: Never create new test files for bug fixes - add to existing `*_test.go`
5. **Test what's requested**: If prompt says "add tests for X", focus on X's untested paths, not unrelated functions

## Patterns to Follow

- For simple utilities (single if-statement): 2-3 assertions (normal case + boundary/edge)
- For bug fixes: test the exact edge case mentioned in the prompt (e.g., "empty values")
- For performance optimizations: add benchmark using `testing.B` (see `BenchmarkStack` pattern)
- Use `os.CreateTemp()` for file I/O tests (see `recovery_test.go` patterns)
- Test edge cases: negative indices, out-of-bounds, non-existent files, empty results
- Never add concurrency tests unless: (1) prompt requests thread-safety verification, or (2) existing tests show this pattern

## Anti-patterns to Avoid

- Don't write 9+ test cases for functions with single conditionals (see `utils_test.go:152-160` for reference)
- Don't create comprehensive stress tests with goroutines unless the test file already shows this pattern
- Don't test every permutation (0, 1, -1, 128, 200, 1000, 999999) for straightforward capping logic
- Don't add tests to multiple test files when one file covering the modified function is sufficient
- Don't create standalone `test_*.go` verification files unless explicitly requested
```

### Skill 3: gin-minimal-changes

```markdown
---
name: gin-minimal-changes
description: Use when fixing bugs or making small changes in gin-gonic/gin. Enforces minimal, surgical changes that extend existing patterns rather than creating new code paths.
---

# Gin Minimal Changes Pattern

## Overview

This skill helps Claude make minimal, focused changes that extend existing code patterns rather than over-engineering solutions. Matches gin maintainers' preference for small diffs.

## Instructions

When fixing bugs or making small changes:

1. **Extend existing patterns**: When prompt says "same way we handle X", use `Grep` to find X's implementation and extend that mechanism
2. **Reuse flags/variables**: Set existing variables (like `brokenPipe`) to trigger established code paths instead of adding early returns
3. **Defer for cleanup**: Always use `defer resource.Close()` immediately after acquisition - never inline cleanup calls
4. **Match naming brevity**: Use short names (`f` not `flusher`) if surrounding code uses short variables
5. **Bundle style fixes**: Group constants, format imports, fix whitespace in files you're already modifying

## Patterns to Follow

- When fixing error suppression, reuse existing flags (e.g., set `brokenPipe = true` for `http.ErrAbortHandler`)
- Use `defer f.Close()` immediately after file/resource creation
- Modify existing conditionals rather than adding new defensive layers
- For linter fixes, check if PR includes `.golangci.yml` changes or `#nosec` comments
- Extract computed values (`var runtimeVersion = runtime.Version()`) not function references for test mocking
- Preserve existing explicit initialization calls when adding `sync.Once` patterns

## Anti-patterns to Avoid

- Don't create parallel logic paths when you can extend existing mechanisms (3-line change > 8-line early return)
- Don't add defensive checks across multiple call sites - validate once at entry point
- Don't call cleanup methods inline (use `defer` for guaranteed execution on all paths)
- Don't use verbose variable names in codebases that consistently use short names
- Don't expand refactoring scope beyond what's explicitly requested
- Don't remove `sync.Once`-protected explicit calls - they're idempotent and maintain compatibility
```

---

## Key Insights from Analysis

- **Constants placement**: Across multiple sessions, Claude created duplicate constants in individual test files instead of placing them centrally. The pattern emerged in "refactor(context): replace hardcoded localhost IPs with constants" where constants should live in `utils.go:22-25`, and again in the path optimization work. (From: "refactor(context): replace hardcoded localhost IPs with constants", "perf(path): replace regex with custom functions in redirectTrailingSlash")

- **Test over-engineering**: A consistent pattern shows Claude writing comprehensive test suites (9-12 assertions, concurrent stress tests) for simple utility functions, while humans prefer 2-3 focused assertions. This appeared when adding tests for `safeInt8`/`safeUint16`, implementing the `Delete` method, and improving debug.go coverage. (From: "refactor(utils): move util functions to utils.go", "feat(context): implemented Delete method", "test(debug): improve the test coverage of debug.go to 100%")

- **Extending vs creating patterns**: Multiple sessions showed Claude adding new conditional branches instead of extending existing mechanisms. Most notable in the recovery middleware where Claude created an 8-line early return instead of reusing the `brokenPipe` flag (3-line change), and in the binding empty value fix where Claude scattered checks instead of consolidating validation at entry point. (From: "fix(recover): suppress http.ErrAbortHandler", "binding:fix empty value error")

- **Scope creep in refactoring**: Claude consistently expanded refactoring scope beyond what was requested - fixing race conditions in tests not mentioned, adding comprehensive linter tests for simple helpers, and refactoring additional benchmark files. Humans made surgical changes to exactly what was specified. (From: "test(gin): resolve race conditions in integration tests", "ci(lint): prevent integer overflows and improve code safety", "refactor(benchmark): use b.Loop() to simplify the code")

- **Missing code cleanup**: When refactoring functions, Claude often left dead code (unused imports, orphaned constants, unused variables) while humans performed holistic cleanup. This pattern appeared in the path parsing optimization where `bytes` import and `strColon/strStar/strSlash` constants should have been removed. (From: "perf: optimize path parsing using strings.Count")

- **Resource management patterns**: Claude missed idiomatic Go patterns like using `defer` for resource cleanup, instead calling `f.Close()` inline at wrong points in the control flow. Humans consistently used `defer` immediately after acquisition. (From: "fix(gin): close os.File in RunFd to prevent resource leak")

- **Style consistency over best practices**: Multiple sessions showed Claude choosing "better" names or patterns (verbose variable names, function references vs values for mocking) instead of matching local conventions. Humans prioritized consistency with immediate context. (From: "chore(response): prevent Flush() panic when `http.Flusher`", "test(debug): improve the test coverage of debug.go to 100%")