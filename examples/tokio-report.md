# Coding Agent Repo Report

**Repository**: tokio-rs/tokio
**Sessions Analyzed**: 19

---

## Synthesized CLAUDE.md / AGENTS.md

```markdown
# Tokio Development Guide for AI Coding Agents

This guide provides specific patterns and guardrails for working on the tokio codebase. It synthesizes common issues from PR analysis.

## Studying Existing Patterns Before Implementation

- When adding new functionality to existing subsystems (like io_uring operations), always read ALL similar implementations first (e.g., if adding `read_uring`, study `tokio/io/uring/write.rs` and `tokio/io/uring/open.rs`)
- Never assume APIs exist; verify types, traits, and methods by reading relevant files (check `tokio/runtime/driver/op.rs` for io_uring operation patterns)
- Look for constants and algorithmic patterns in related code before implementing your own approach
- When codebases have existing infrastructure (like `Op<T>` wrappers, `Completable` traits), match those patterns exactly rather than inventing new abstractions

## Trait Refactoring and Error Flow

- When refactoring trait signatures that change error handling, trace all error paths through the system, not just call sites. Use LSP "Find References" or Grep for the trait name to find all implementations and usage sites
- Trait method additions must be implemented for all existing implementors. After modifying a trait definition, always search for `impl TraitName` to find all implementations requiring updates
- Error handling refactors often introduce new error paths at different lifecycle stages. When changing from `io::Result<T>` to `T` where `T` contains a result, look for places that construct errors outside the normal completion path (e.g., initialization failures, registration errors)

## API Naming and Socket Options

- When adding socket options, match the exact underlying OS constant name (e.g., `IPV6_TCLASS` → `tclass_v6`, not `tos_v6`)
- Check socket2 documentation or source for platform support lists—use inclusion lists (`target_os = "x"`) for options with limited support, exclusion lists for widely supported options
- Before implementing wrapper methods, verify the underlying dependency already has the functionality

## Backward Compatibility for API Changes

- When renaming public methods, always add deprecated wrappers that delegate to the new names
- Use `#[deprecated(note = "reason")]` attributes on old methods
- Maintain the same platform conditionals on both old and new method variants

## Tokio Ecosystem Integration Patterns

- **Cooperative scheduling**: When implementing `AsyncRead`/`AsyncWrite`, always use `tokio::task::coop::poll_proceed()` at the start of poll methods before performing work
- **Vectored I/O**: `AsyncWrite` implementations should include `is_write_vectored()` returning true and `poll_write_vectored()` for performance
- Never clone wakers unconditionally; prefer checking `will_wake()` first to avoid unnecessary allocations
- Study how existing modules handle `cfg(feature = "rt")` - look for `cfg_rt!` macro patterns in `tokio-util/src/cfg.rs`

## API Stabilization Patterns

- When removing public constructors during stabilization, replace trait impls like `From` with private constructor methods (e.g., `pub(crate) fn new()`) to enforce API boundaries
- Never mark trait implementations as `pub(crate)` when the goal is preventing external construction; prefer removing the trait impl entirely and creating explicit private constructors
- Update all call sites consistently: if changing from `.into()` to explicit constructor, search codebase for all usages
- Remove `cfg_unstable!` blocks around internal helper methods when they're needed by now-stable APIs

## Test Coverage Principles

- Socket option additions require test coverage in corresponding test files (e.g., `tokio/tests/tcp_socket.rs`, `tokio/tests/udp.rs`)
- Follow existing test patterns in the file—look for similar option tests and replicate the structure
- Beyond happy path tests, include zero-capacity panics, empty buffer handling, precise boundary conditions, and cooperative scheduling yields

## Macro Hygiene Testing Patterns

- When fixing macro hygiene issues, look for existing compile-fail test infrastructure (e.g., `tests-build/tests/fail/` directories with `.stderr` expectation files)
- Never create standalone test files at repository root; prefer integrating tests into the existing test structure
- For hygiene fixes, compile-fail tests are more rigorous than runtime shadowing tests
- After adding compile-fail tests, search for test registration files (e.g., files that call `t.compile_fail()`) and register new tests there

## Rust Pinning and Method Resolution

- When working with `Pin<&mut T>` types in macro expansions, calling trait methods often requires explicit `.as_mut()` to reborrow the pinned reference
- Compare with nearby similar patterns in the same file before modifying Pin-related code

## Rust Deprecation Patterns

- When deprecating Rust APIs, prefer minimal deprecation attributes without `since` fields unless the codebase pattern clearly shows version tracking
- Use `#[expect(deprecated)]` with explanatory comments instead of `#[allow(deprecated)]` in tests for deprecated functionality
- When deprecating methods in doctest examples, add `# #![allow(deprecated)]` at the start of the example code block
- Check for existing deprecation patterns in the codebase (search for `#[deprecated` and `#[expect(deprecated)]`) and match the established style

## Error Handling Improvements

- When asked to "improve error handling" in specific files, audit all error paths in those files, not just the most obvious ones
- Match error log levels to severity: use `warn!` for expected error cases (client disconnections, network failures), `error!` for unexpected internal errors
- When improving error handling across "examples," check for related example files

## Lint Enablement Patterns

- When enabling strict lints like `unsafe_op_in_unsafe_fn`, assess whether low-level modules need module-level exemptions rather than wrapping every operation
- For modules with intrinsic unsafe operations (linked lists, raw pointer manipulation, task scheduling), consider `#![allow(lint)]` at module top with justification comment
- Add `// TODO: replace with #[expect(lint)] after MSRV X.Y.Z` when using allow attributes that should eventually become expectations
- Never create nested `unsafe { unsafe { ... } }` blocks

## Safety Documentation

- When wrapping unsafe operations due to lint requirements, add `// Safety:` comments explaining why the operation is safe
- For unsafe functions being modified, add or update `/// # Safety` doc sections describing caller obligations
- Document safety invariants for helper functions that perform pointer casts or transmutes

## Conditional Compilation and Feature Gating

- When adding conditional compilation for testing frameworks (loom, miri, wasi), audit ALL modules that transitively depend on excluded APIs
- For platform/test-specific exclusions: check sibling crates in the workspace for parallel changes (e.g., if modifying `tokio-util/src/wrappers.rs`, check `tokio-stream/src/wrappers.rs`)
- Never gate only the primary module; prefer gating at the `pub mod` declaration AND usage sites

## CI Configuration Completeness

- GitHub Actions workflow changes often require corresponding `.github/labeler.yml` updates to trigger the new workflow via PR labels
- CI job conditions like `contains(github.event.pull_request.labels.*.name, 'R-loom-util')` indicate a label-based trigger system
- When refactoring cfg flags to Cargo features, always check CI configuration files (`.github/workflows/`, `.cirrus.yml`) for hardcoded RUSTFLAGS and feature lists

## Match Expression Style in Rust

- When adding cases to existing match expressions, mirror the pattern style already used (single-line arms, guard clauses, block structure)
- For conditional returns in match arms, prefer guard clauses (`Pattern if condition => result`) over expanding arms into multi-line if-blocks
- Maintain visual consistency with surrounding match arms

## Rust Error Handling and Type Investigation

- When replacing deprecated error methods, investigate the actual error type before choosing an approach
- Never use `downcast_ref` for string comparison on custom error types; prefer implementing a zero-allocation comparison using `std::fmt::Write` trait
- For zero-allocation string comparisons: create a custom struct implementing `Write` that compares incrementally

## Documentation Style for Reference Material

- Keep examples minimal and focused: show the pattern once clearly rather than building elaborate scenarios with setup code
- Never add pedagogical commentary ("This would panic if...", "Note that...") in reference docs
- Rust stdlib/crate docs favor concise examples (10-15 lines) over complete programs

## Scope Discipline

- Never create standalone example files, demo scripts, or additional artifacts unless explicitly requested
- When asked to "add X", implement exactly X in the existing codebase structure
- Avoid over-documentation: don't add doc comments to code you're modifying unless explicitly requested
```

---

## Suggested Skills

Based on recurring patterns across multiple sessions, the following skills would help Claude perform better on the tokio codebase:

### Skill 1: Tokio Socket Option Implementation

```markdown
---
name: tokio-socket-option
description: Guides implementation of socket option wrappers in tokio's net module. Use when adding new socket options (SO_*, IPV6_*, TCP_*) to TcpStream, TcpSocket, UdpSocket, or UnixStream. Ensures proper naming conventions, platform conditionals, deprecation handling, and test coverage.
---

# Tokio Socket Option Implementation

## Overview

This skill guides you through adding socket option wrappers to tokio's networking types. Socket options require careful attention to naming conventions (matching OS constants), platform support (via cfg attributes), backward compatibility (deprecation wrappers), and test coverage.

## Instructions

### 1. Verify Underlying Support

Before implementing wrapper methods:
- Check `socket2` crate documentation or source for the method (e.g., `set_tclass_v6` for `IPV6_TCLASS`)
- Confirm the method exists and note its signature and platform conditionals
- Never implement methods that don't exist in the underlying socket type

### 2. Match OS Constant Names

Socket option method names must match the underlying OS constant:
- `IPV6_TCLASS` becomes `tclass_v6()` and `set_tclass_v6()`, NOT `tos_v6()`
- `SO_REUSEPORT` becomes `reuseport()` and `set_reuseport()`
- `TCP_NODELAY` becomes `nodelay()` and `set_nodelay()`

### 3. Apply Platform Conditionals Correctly

Use inclusion lists for limited-support options:
```rust
#[cfg(any(target_os = "linux", target_os = "android", target_os = "freebsd"))]
pub fn tclass_v6(&self) -> io::Result<u32> {
    self.inner.tclass_v6()
}
```

Use exclusion lists only for widely-supported options (see existing patterns in `tokio/src/net/tcp/socket.rs`).

### 4. Add Deprecation Wrappers for Renames

When renaming methods for clarity (e.g., `tos` → `tos_v4`):
```rust
#[deprecated(note = "Use `set_tos_v4` instead")]
#[cfg(not(any(target_os = "fuchsia", target_os = "redox")))]
pub fn set_tos(&self, tos: u32) -> io::Result<()> {
    self.set_tos_v4(tos)
}
```

Maintain identical platform conditionals on both old and new methods.

### 5. Add Test Coverage

Add tests to the appropriate test file (`tokio/tests/tcp_socket.rs`, `tokio/tests/udp.rs`):
- Follow existing socket option test patterns in the file
- Use simple set-then-get verification
- Apply platform conditionals to tests matching method conditionals

### 6. Update Documentation

- Add or update doc comments with links to related methods
- Note protocol compatibility ("may not have any effect on IPv4 sockets")
- Update cross-references when renaming (e.g., `[set_tos]` → `[set_tos_v4]`)

## Patterns to Follow

- Check `tokio/src/net/tcp/socket.rs` and `tokio/src/net/udp.rs` for existing socket option patterns
- Use Grep to find similar options: `pattern: "pub fn.*tos"` with `glob: "tokio/src/net/**/*.rs"`
- Delegate directly to socket2: `self.inner.method_name()` with no additional logic
- Group related options together in the file (IPv4 options near IPv4 options, etc.)

## Anti-patterns to Avoid

- Never invent method names; always match the OS constant
- Never copy platform conditionals from unrelated options (IPv4 ≠ IPv6 support)
- Never skip deprecation wrappers when renaming public methods
- Never add CHANGELOG entries unless you see them in recent commits
- Never implement the underlying method yourself; always use socket2's implementation
```

### Skill 2: Tokio Trait Refactoring

```markdown
---
name: tokio-trait-refactor
description: Guides refactoring trait definitions and implementations in tokio, especially for async traits and error handling changes. Use when modifying trait signatures, adding trait methods, or changing trait bounds. Ensures all implementations are updated and error paths are traced.
---

# Tokio Trait Refactoring

## Overview

This skill helps you safely refactor traits in the tokio codebase. Trait changes require tracing all implementations, updating error paths, and considering lifecycle implications for async operations.

## Instructions

### 1. Find All Implementations

After modifying a trait definition:
- Use Grep with `pattern: "impl.*TraitName"` to find all implementors
- Check both direct implementations and blanket implementations
- Use LSP findReferences on the trait name to discover usage sites

### 2. Trace Error Paths for Error-Handling Changes

When changing trait signatures that affect error handling:
- Identify all error construction sites, not just call sites
- Look for errors created at initialization, registration, completion, and cleanup stages
- When changing from `io::Result<T>` to `T` where `T` contains a result, search for early error paths

Example: If adding a `complete_with_error` method to handle registration failures:
- Update `Completable` trait definition
- Implement for all types: `Open`, `Write`, `Read`, etc. in `tokio/io/uring/`
- Update `Op::poll` in `tokio/runtime/driver/op.rs` to call the new method on registration failures

### 3. Update Method Signatures Consistently

When changing trait method signatures:
- Update trait definition first
- Update all implementations (use Grep results from step 1)
- Update all call sites (use Grep with the method name)
- Rebuild to catch any missed implementations

### 4. Consider Async Operation Lifecycle

For traits used in async operations (`Future`, `Completable`, async traits):
- Consider where in the lifecycle errors can occur: before submission, during execution, or during completion
- Add methods for each error stage if needed
- Document the responsibility split between lifecycle stages

### 5. Preserve Import Style

When updating implementations:
- Match the import style in each file (grouped vs separate lines)
- Avoid reformatting imports unless directly related to the functional change
- Keep style changes separate from functional changes

## Patterns to Follow

- Study `tokio/runtime/io/uring/` for patterns in async operation traits
- Check `Completable` trait in `tokio/runtime/io/uring/op.rs` for error-handling patterns
- Use `impl.*YourTrait` regex to find all implementations
- Test with `cargo check` after each implementation update

## Anti-patterns to Avoid

- Never assume you've found all implementations without systematic search
- Never modify trait signatures without updating ALL implementations in the same commit
- Never ignore "lifecycle stage" errors (initialization, registration) when refactoring completion-time error handling
- Never reformat imports or make stylistic changes in trait refactoring PRs unless explicitly requested
```

### Skill 3: Tokio Lint Enablement

```markdown
---
name: tokio-lint-enable
description: Guides enabling strict lints (unsafe_op_in_unsafe_fn, clippy lints) at crate level in tokio. Use when asked to enable lints or fix lint warnings project-wide. Handles module-level exemptions, safety documentation, and avoiding over-mechanical wrapping.
---

# Tokio Lint Enablement

## Overview

This skill helps you enable strict lints in tokio while maintaining code readability and adding appropriate safety documentation. Lint enablement requires assessing when module-level exemptions are appropriate and avoiding mechanical over-wrapping.

## Instructions

### 1. Enable Lint and Assess Violations

First, enable the lint in `tokio/src/lib.rs`:
```rust
#![deny(unsafe_op_in_unsafe_fn)]
```

Run `cargo check` to identify all violations. Count violations per module.

### 2. Identify Low-Level Modules for Exemption

For modules with >50 unsafe operations or intrinsic unsafe patterns:
- `tokio/src/runtime/task/core.rs` (task internals)
- `tokio/src/runtime/task/raw.rs` (raw pointer manipulation)
- `tokio/src/util/linked_list.rs` (intrusive data structures)

Add module-level exemptions:
```rust
#![allow(unsafe_op_in_unsafe_fn)]
// TODO: replace with #[expect(unsafe_op_in_unsafe_fn)] after MSRV 1.81.0
```

### 3. Wrap Remaining Violations with Safety Comments

For other modules, wrap unsafe operations in `unsafe {}` blocks with safety comments:
```rust
pub unsafe fn operation(&self) -> Value {
    // Safety: The caller guarantees X, and we maintain invariant Y
    unsafe {
        raw_pointer_operation()
    }
}
```

### 4. Add or Update Safety Documentation

For modified unsafe functions:
- Add `/// # Safety` sections describing caller obligations
- Document invariants that must be maintained
- Explain why operations are safe in `// Safety:` comments

Example from `tokio/src/io/read_buf.rs`:
```rust
/// # Safety
///
/// The caller must ensure the slice is initialized up to `n` bytes.
pub unsafe fn slice_from_raw_parts(data: *mut u8, len: usize) -> &mut [u8] {
    // Safety: Caller guarantees initialization
    unsafe { std::slice::from_raw_parts_mut(data, len) }
}
```

### 5. Remove Newly-Unused Imports

After wrapping, check for imports that are no longer needed:
- Remove unused `NonZeroU32`, raw pointer types if no longer referenced
- Use `cargo check` to identify unused imports

### 6. Avoid Nested Unsafe Blocks

Never create `unsafe { unsafe { ... } }`:
- If the outer function is unsafe, the inner block is sufficient
- Review nearby code to ensure consistency

## Patterns to Follow

- Check `tokio/src/runtime/task/core.rs` for module-level exemption patterns
- Study `tokio/src/io/read_buf.rs` for safety documentation examples
- Use `// Safety:` comments before each unsafe block
- Group related unsafe operations with shared safety justifications

## Anti-patterns to Avoid

- Never mechanically wrap every operation without considering module-level exemptions
- Never create nested `unsafe { unsafe { } }` blocks
- Never skip safety documentation when adding unsafe blocks
- Never use `allow` when `expect` is available (after MSRV allows)
- Never remove module structure or readability for lint compliance
```

---

## Key Insights from Analysis

- **Studying existing patterns**: Claude frequently failed to examine similar implementations before adding new functionality, leading to API hallucinations (non-existent `Op::read_at()` in io_uring) and missed optimizations (probe-read patterns). (From: "fs: support io_uring with `tokio::fs::read`")

- **Trait refactoring completeness**: When refactoring traits that change error handling, Claude focused on visible call sites but missed error paths at different lifecycle stages, particularly initialization/registration failures that occur before completion. (From: "io-uring: Change `Completable` to not return io::Result")

- **Socket option naming conventions**: Claude incorrectly copied IPv4 naming patterns (`tos_v6`) instead of matching the underlying OS constant name (`IPV6_TCLASS` → `tclass_v6`), and used wrong platform conditionals by copying from unrelated options. (From: "net: add support for `TCLASS` option on IPv6")

- **Tokio ecosystem integration**: Claude omitted critical tokio patterns like cooperative scheduling (`poll_proceed`), vectored I/O support, and proper waker management (`will_wake()` checks), focusing on basic functionality rather than production-grade integration. (From: "io: add `tokio_util::io::simplex`")

- **Test coverage philosophy**: Claude added comprehensive tests for basic scenarios but missed critical edge cases (zero-capacity panics, cooperative scheduling yields, boundary conditions) that the actual PRs tested thoroughly. (From: "io: add `tokio_util::io::simplex`" and "net: add support for `TCLASS` option on IPv6")

- **Macro hygiene testing**: Claude used runtime shadowing tests instead of the project's compile-fail test infrastructure, missing test registration in harness files, and created standalone test files at repo root rather than integrating with existing test structure. (From: "macros: fix the hygiene issue of `join!` and `try_join!`")

- **Documentation style mismatch**: Claude wrote verbose pedagogical documentation with extensive examples and explanatory notes, while tokio follows terse reference documentation style with minimal examples. (From: "runtime: clarify the behavior of `Handle::block_on`")

- **Build system completeness**: When refactoring cfg flags to Cargo features, Claude updated Rust source code but completely missed CI configuration files (`.github/workflows/`, `.cirrus.yml`) and labeler configuration required for the feature to work in CI. (From: "tokio: use cargo feature for taskdump support instead of cfg")

- **API stabilization patterns**: Claude marked trait implementations as `pub(crate)` instead of removing them entirely, failing to enforce the API boundary properly and not updating all call sites consistently. (From: "runtime: stabilize `runtime::id::Id`")

- **Rust deprecation conventions**: Claude added version fields and verbose notes to deprecation attributes when the codebase uses minimal attributes, and used `#[allow(deprecated)]` instead of the modern `#[expect(deprecated)]` pattern. (From: "net: deprecate `TcpStream::set_linger`")

- **Lint enablement strategy**: Claude mechanically wrapped every unsafe operation without considering module-level exemptions for low-level code (linked lists, task internals), and skipped adding safety documentation comments. (From: "tokio: enable the `unsafe_op_in_unsafe_fn` lint at the crate level")

- **Cross-crate consistency**: When modifying conditional compilation in one crate, Claude missed parallel changes needed in sibling workspace crates (`tokio-stream` when modifying `tokio-util`). (From: "util: enable loom tests")
