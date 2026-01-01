# Coding Agent Repo Report

- **Repository**: rust-lang/rust
- **Sessions Analyzed**: 10

---

## Synthesized CLAUDE.md / AGENTS.md

```markdown
# Coding Agent Guidance for rust-lang/rust

## Feature Removal vs Feature Migration

- When a feature is described as "superseded" or "replaced," treat it as complete removal, not find-and-replace migration
- Removing a superseded feature means: (1) delete from unstable features list, (2) add to removed features list with deprecation metadata, (3) delete specialized implementation code, (4) delete dedicated documentation files, (5) update tests to use the replacement feature
- Never keep old code paths with changed feature gates; prefer deleting superseded logic entirely since the new feature handles it differently
- For feature removals, check these locations: `rustc_feature/src/removed.rs` (add entry), `rustc_feature/src/unstable.rs` (remove entry), `rustc_span/src/symbol.rs` (remove symbols), implementation files (delete conditional blocks), `src/doc/unstable-book/` (delete feature docs), tests (migrate to new patterns)

## Comprehensive Impact Analysis for Compiler Changes

- When fixing compiler metadata or linking issues, use Grep to find ALL usages of affected data structures before implementing changes
- Never modify only the matching/resolution logic; prefer exploring the full data flow from source definitions through all access points to installation
- For issues involving "ambiguity" or "multiple versions", investigate both the detection/resolution layer AND the installation/sysroot layer
- When a fix involves removing an enum variant, this signals a data structure change requiring updates across all files that destructure or access that type

## Test Coverage for Correctness Fixes

- Always add a test case that would have caught the original bug, especially for "surprising" or "incorrect" behavior mentioned in prompts
- When fixing compiler errors/ICEs, check for existing test files in `tests/ui/` that exercise the buggy behavior and update their expectations
- Add comprehensive test coverage for the fixed issue, including edge cases mentioned in the issue description
- For ICE fixes, create a dedicated regression test file named after the issue (e.g., `ice-[description]-[issue-number].rs`)
- Test cases for compiler fixes should go in `tests/run-make/` or `tests/ui/` depending on whether they validate build behavior or compiler diagnostics

## Attribute Parser Migrations: File Organization

- When migrating attributes to the parser framework, create dedicated module files following the pattern in `compiler/rustc_attr_parsing/src/attributes/` (e.g., `instruction_set.rs`, `inline.rs`)
- Never inline new parsers into existing files like `codegen_attrs.rs`; prefer creating a new module file and importing it in `mod.rs`
- Check if the attribute requires new symbol definitions in `compiler/rustc_span/src/symbol.rs` for path segments
- Update `compiler/rustc_hir/src/attrs/encode_cross_crate.rs` to include the new `AttributeKind` variant in the match statement
- Remove any "need to be fixed" or "broken on stable" comments from `compiler/rustc_passes/src/check_attr.rs` when completing the migration

## Attribute Parser Error Messages: Specificity

- When validating path segments, use `expected_specific_argument` with the full list of valid symbols, not just the architecture prefix
- Provide separate validation and error messages for each segment of a multi-part path (architecture, then instruction set)
- Check for and remove obsolete error diagnostics from both `messages.ftl` and error module files when completing migrations

## Bootstrap and Build System Changes

- Before modifying bootstrap/build scripts, investigate how configuration flows through the entire build pipeline—check for downstream tools (rustc, rustdoc, cargo subcommands) that may need corresponding changes
- Never assume environment variables and CLI flags are interchangeable; prefer researching the specific tool's documentation for stability guarantees (stable vs unstable features)
- When changing warning/error handling in build systems, verify the change works for all build artifacts, not just the primary compilation target (see `src/bootstrap/src/bin/rustdoc.rs`)
- For rustc_* internal crates and sysroot issues, examine `src/bootstrap/src/core/build_steps/compile.rs` for installation logic and deduplication

## Enum-to-Struct Conversions for Single-Variant Removals

- When removing all but one variant from an enum, prefer converting to a struct rather than keeping a single-variant enum
- A single-variant enum requires pattern matching at every call site; a struct with direct field access is simpler and more idiomatic
- Search for all match statements on the enum type—these become direct field accesses after struct conversion

## Dead Code Removal After API Changes

- Search for comments like "FIXME: This hack should be removed once [condition]" where the condition now matches your change
- When making a variant the standard/default, look for temporary compatibility code that can be removed
- Use Grep with context (`-B 5 -C 5`) to find comments mentioning the old variant name or transition plans

## Function Signature Cleanup

- When removing conditional logic based on parameters (like `is_nightly_build`), check if those parameters become unused
- Trace parameter usage: if a parameter only controlled branching you removed, delete it from the signature and update all call sites
- Use LSP `findReferences` or Grep to locate all call sites when removing parameters

## CLI Option and Documentation Updates

- When removing code paths, search for CLI flags, help text, and error messages that reference them
- Use Grep for the variant name in string literals to find user-facing documentation
- Look for `--option-name` patterns in error messages, match statements on string inputs, and help text

## Test File Updates After Output Format Changes

- Run full test suite after emitter/formatter changes—`.stderr` files may need updates
- Test files in `tests/ui/*/*.stderr` capture exact error output and will fail if formatting changes
- Don't manually edit stderr files; use the test harness's update mode (`./x test --bless`)

## Standard Library: Refactoring Internals for New Features

- When implementing a feature similar to an existing one in a sibling module (e.g., `VecDeque::splice` mirroring `Vec::splice`), examine whether internal structures need refactoring to support both use cases efficiently
- Never add `pub(super)` to existing fields just to access them externally; prefer refactoring the internal structure's semantics and adding private helper methods
- If a struct field's meaning needs to change for a new feature, refactor the original struct rather than working around its current design
- When a prompt says "update X to use Y internally," treat this as a requirement to change X's implementation, not just add Y alongside X

## Standard Library: Feature Gates and Test Organization

- Search for existing related feature gates before inventing new ones (use Grep for `#[unstable(feature =`)
- Never use `issue = "none"` in unstable attributes; reuse an existing related issue number or file a tracking issue
- Match the feature gate used by the most closely related functionality
- Place tests for new public API features in `library/alloctests/tests/` rather than inline `#[cfg(test)] mod tests`
- Check where similar features put their tests and follow the same pattern

## Standard Library: Integration and Tooling

- Changes to core stdlib types (ManuallyDrop, Box, Option, etc.) require checking debugger integration files (`*.natvis`, `gdb_providers.py`)
- After structural changes to `repr(transparent)` types, search for test files containing the type name to find tests asserting on memory layout
- Never assume a stdlib change is complete without running tests—changes to type internals cascade to MIR dumps, size printing, and tooling

## Separating Code Paths vs. Parameterizing Behavior

- When asked to "split" or "separate" handling for special cases, prefer creating distinct execution paths (new methods that handle the full flow) over adding conditional branches at every call site
- If the prompt mentions that special cases have "different requirements" or need "special handling," this suggests architectural separation, not just parameterization
- Never add `if matches!(instance.def, ty::InstanceKind::Intrinsic(_))` checks at multiple call sites; prefer intercepting at a single high-level point before the call flow diverges

## Recognizing Out-of-Scope Tasks

- When a task requires deep domain expertise you don't possess (e.g., rustc type system internals, kernel subsystems), acknowledge the limitation early rather than producing empty or incorrect output
- Before starting implementation, assess: Do I understand the current architecture? Do I know where to make the first change? Can I trace data flow through the system? If no to any, use the Explore agent extensively to map the architecture
- Never silently produce an empty diff for a complex task; prefer explaining what architectural knowledge gaps prevent implementation
```

---

## Suggested Skills

### Skill 1: Rust Feature Removal

```markdown
---
name: rust-feature-removal
description: Guide for removing superseded language features from the Rust compiler. Use when the user asks to remove or deprecate a feature that has been superseded by a more general feature, or when migrating from an old feature gate to a new one.
---

# Rust Feature Removal Skill

## Overview

This skill provides guidance for properly removing superseded language features from the rust-lang/rust compiler. It ensures complete removal across all subsystems rather than simple find-and-replace migration.

## Instructions

When removing a superseded feature, execute these steps systematically:

### 1. Identify Full Feature Scope

Before making changes:
- Use Grep to find all references to the feature name across the codebase
- Check `compiler/rustc_feature/src/unstable.rs` for the feature declaration
- Check `compiler/rustc_span/src/symbol.rs` for any symbol definitions
- Locate implementation code that uses the feature gate
- Find documentation in `src/doc/unstable-book/src/language-features/`
- Locate tests in `tests/ui/` that exercise the feature

### 2. Remove from Feature Lists

- Delete the feature entry from `compiler/rustc_feature/src/unstable.rs`
- Add an entry to `compiler/rustc_feature/src/removed.rs` with:
  - Feature name
  - Removal version
  - Reason for removal
  - Reference to replacement feature
- Remove related symbol definitions from `compiler/rustc_span/src/symbol.rs`

### 3. Delete Implementation Code

- Remove entire conditional blocks that check for the feature gate
- Do not just change which feature is checked—delete the specialized code paths entirely
- The replacement feature should handle the use case through its general mechanism
- Remove feature-gated code from all compiler phases: parsing, AST lowering, HIR, type checking, MIR building

### 4. Update Documentation

- Delete the feature's documentation file from `src/doc/unstable-book/src/language-features/`
- Remove mentions of the old feature from the replacement feature's documentation
- Update any cross-references in other documentation files

### 5. Migrate and Reorganize Tests

- Update test files to use the replacement feature gate instead
- Tests may need to move to different directories (e.g., `tests/ui/feature-name/` → `tests/ui/replacement-feature/`)
- Update test expectations if error messages changed
- Ensure test file headers reference the correct feature gate

### 6. Verify Completeness

After making changes:
- Run the test suite to catch any missed references
- Use Grep to verify no references to the old feature name remain in active code
- Check that the feature appears in removed features list and not in unstable features list

## Patterns to Follow

- Feature removal is architectural cleanup, not code migration
- Superseded features should be completely deleted because the replacement handles the use case differently
- All feature-related artifacts must be removed: declarations, symbols, code, docs, and test organization
- Test files should demonstrate the replacement feature's capabilities, not preserve old patterns

## Anti-patterns to Avoid

- Never perform find-and-replace on feature gate names while keeping the same code structure
- Never keep specialized code paths that check for the replacement feature instead of the old one
- Never leave documentation files for removed features
- Never skip adding the feature to the removed features list with proper deprecation metadata
- Never assume tests can stay in their original location—feature removal may require reorganization
```

### Skill 2: Rust Compiler Enum-to-Struct Refactoring

```markdown
---
name: rust-enum-to-struct-refactor
description: Guide for converting single-variant enums to structs in the Rust compiler. Use when removing all but one variant from an enum, or when simplifying enum types that no longer need sum-type semantics. Common in compiler refactoring tasks involving error types, configuration enums, or API simplification.
---

# Enum-to-Struct Refactoring Skill

## Overview

This skill guides the conversion of single-variant enums to structs in the rust-lang/rust codebase. When all but one enum variant is removed, keeping a single-variant enum creates unnecessary complexity—conversion to a struct simplifies the API.

## Instructions

### 1. Identify the Scope of Changes

Before starting:
- Use LSP `findReferences` on the enum type to locate all usage sites
- Use Grep to find pattern matching: `match.*EnumName`, `let EnumName::`, `if let EnumName::`
- Locate where the enum is constructed
- Check for trait implementations on the enum (especially derived traits)
- Search for serialization/deserialization code

### 2. Convert the Type Definition

Transform the enum to a struct:
- Single-variant enum: `enum Foo { Bar { x: bool, y: u32 } }` becomes `struct Foo { x: bool, y: u32 }`
- Preserve field names and types exactly
- Preserve documentation comments
- Update visibility modifiers if needed

### 3. Update All Pattern Matching Sites

Replace pattern matching with direct field access:
- `match foo { Foo::Bar { x, y } => ... }` becomes direct usage of `foo.x` and `foo.y`
- `let Foo::Bar { x, y } = foo;` becomes `let x = foo.x; let y = foo.y;` or use `foo` directly
- `if let Foo::Bar { x } = foo` becomes direct field access
- Remove now-unnecessary match statements entirely where they only destructured the single variant

### 4. Update Construction Sites

Simplify construction:
- `Foo::Bar { x: true, y: 42 }` becomes `Foo { x: true, y: 42 }`
- Remove variant name qualifiers

### 5. Handle Trait Implementations

After struct conversion:
- Derived traits (`Copy`, `Clone`, `Debug`, etc.) remain compatible—keep `#[derive(...)]`
- Manual trait implementations may need adjustment if they matched on variants
- For traits that delegate through fields, ensure the struct's fields support those traits

### 6. Update Function Signatures and Return Types

- Function parameters: `fn process(foo: Foo)` remains the same, but internal usage changes
- Return types: `fn create() -> Foo` construction syntax changes
- Generic bounds referencing the type remain valid

### 7. Handle Cross-Module Impacts

Beyond compilation errors:
- Update imports if the type was re-exported
- Check debugger integration files (`*.natvis`, `gdb_providers.py`) that may reference variant names
- Update CLI parsing code that matches on string variants
- Check documentation that references the enum variant
- Update error messages that mention the variant name

### 8. Clean Up Dead Code

After conversion:
- Remove helper functions that only constructed the single variant
- Remove match-based accessor methods if direct field access is now simpler
- Remove comments explaining why variants were matched if that's no longer relevant

## Patterns to Follow

- Single-variant enums with named fields convert cleanly to structs with the same fields
- Direct field access (`.field`) is simpler than pattern matching (`match { Variant { field } => field }`)
- Struct conversions typically don't break derived traits—keep existing `#[derive(...)]`
- Test code often has the most pattern matching and benefits most from simplification

## Anti-patterns to Avoid

- Never keep a single-variant enum to "preserve the option to add variants later"—add them when needed
- Never wrap the struct in `match` statements out of habit—use fields directly
- Never convert tuple variants to tuple structs if named fields would be clearer
- Never forget to update documentation, error messages, and tooling that reference variant names
- Never assume the conversion is done when the code compiles—check for semantic simplifications (removing now-unnecessary match statements)
```

### Skill 3: Rust Standard Library Feature Implementation

```markdown
---
name: rust-stdlib-feature-impl
description: Guide for implementing new standard library features in Rust core/alloc/std. Use when adding new methods to existing types (Vec, VecDeque, Option, etc.), implementing iterator adapters, or extending standard library APIs. Covers feature gating, test organization, and internal refactoring patterns.
---

# Standard Library Feature Implementation Skill

## Overview

This skill provides guidance for implementing new features in Rust's standard library (`library/core`, `library/alloc`, `library/std`). It covers API design patterns, feature gating, test organization, and internal refactoring considerations specific to rust-lang/rust.

## Instructions

### 1. Research Existing Patterns

Before implementation:
- Find similar functionality in sibling types (e.g., if adding to `VecDeque`, check `Vec`)
- Use Grep to search for the method name in related modules to understand conventions
- Check how similar features are feature-gated: `grep -r '#\[unstable(feature ='`
- Review test organization for similar features
- Examine internal helper methods that similar features use

### 2. Design Internal Refactoring Needs

When adding features to complex types:
- Determine if existing internal structures need refactoring to support the new feature efficiently
- Never add `pub(super)` to fields just to access them externally—refactor internals instead
- If a field's semantic meaning needs to change, refactor the original struct and its consumers
- Add private helper methods to existing internal types rather than working around their APIs
- Consider if related types (like `Drain` for collection methods) need new capabilities

Example: Adding `VecDeque::splice` required refactoring `Drain` to expose helper methods (`fill`, `move_tail`) rather than accessing its internals externally.

### 3. Feature Gate Selection

Choose appropriate feature gates:
- Use Grep to find existing related features: `rg '#\[unstable\(feature = "(\w+)"' --replace '$1' library/`
- Reuse existing feature gates when adding related functionality (e.g., multiple `VecDeque` extensions under `deque_extend_front`)
- Never use `issue = "none"`—reuse a related tracking issue or file a new one
- Match the feature gate pattern: if extending an existing feature, use its gate
- Add the feature gate alphabetically to test file headers: `#![feature(feature_name)]`

### 4. Implementation Location

Place code appropriately:
- New methods go in the main implementation block for the type (`impl<T> VecDeque<T>`)
- Internal helpers go in private `impl` blocks or on internal types
- Generic implementations before specialized ones
- Follow the existing ordering in the file (construction, modification, access, iteration, etc.)

### 5. Trait Implementations

When adding functionality:
- Check if standard traits need implementation (Iterator, DoubleEndedIterator, ExactSizeIterator, FusedIterator)
- Use `#[unstable(feature = "...", issue = "...")]` on trait impls too
- Derive standard traits when possible (Debug, Clone)
- For complex types, verify trait bounds are minimal and correct

### 6. Test Organization

Standard library tests follow specific patterns:
- Place tests in `library/alloctests/tests/` for public API features (NOT inline `#[cfg(test)]` modules)
- Find the appropriate test file: `vec.rs`, `vec_deque.rs`, `string.rs`, etc.
- Enable feature gates in `library/alloctests/tests/lib.rs` alphabetically with others
- Test edge cases: empty collections, single elements, boundary conditions
- Test interaction with existing features
- Include tests that would catch common implementation mistakes

Example: `VecDeque::splice` tests go in `library/alloctests/tests/vec_deque.rs`, not inline in the source file.

### 7. Documentation Requirements

Comprehensive documentation:
- Document what the method does, not how it's implemented
- Include complexity guarantees (time/space)
- Provide at least one simple example in doctests
- Document panics, safety requirements, and special cases
- Reference related methods with backticks and links
- Use standard documentation patterns from similar methods

### 8. Integration Verification

After implementation:
- Run the test suite: `./x test library/alloc`, `./x test library/alloctests`
- Check that doctests pass: `./x test --doc library/alloc`
- Verify the feature gate is correctly applied (code shouldn't compile without it on stable)
- Check for internal trait implementations that should be preserved

## Patterns to Follow

- Refactor existing internals to support new features rather than working around them
- Reuse feature gates for related functionality to avoid gate proliferation
- Place tests in external test suites (`library/alloctests/tests/`), not inline
- Follow existing method organization and naming conventions in the module
- Provide helper methods on internal types (like `Drain`, `IntoIter`) when needed for clean implementation
- Check sibling types (`Vec` vs `VecDeque`) for parallel features and consistent APIs

## Anti-patterns to Avoid

- Never add `pub(super)` to existing struct fields to access them externally—refactor the internals
- Never invent new feature gates without checking for existing related ones first
- Never use `issue = "none"` in `#[unstable]` attributes
- Never skip external test files in favor of inline `#[cfg(test)]` modules for public APIs
- Never implement features without checking how similar features work in related types
- Never forget to enable feature gates in `library/alloctests/tests/lib.rs`
- Never assume code changes alone are sufficient—debugger integration (`gdb_providers.py`, `*.natvis`) may need updates for struct changes
```

---

## Key Insights from Analysis

- **Feature Removal Completeness**: Claude consistently performed find-and-replace migrations when prompts requested feature removal, missing that "superseded" features require deletion of specialized code paths, not just gate renaming. The pattern appears in both feature removals and attribute parser migrations where old code paths must be completely eliminated. (From: "Remove `feature(string_deref_patterns)`", "Port `#[instruction_set]` to attribute parser")

- **Scope Discovery Through Exploration**: Multiple sessions show Claude making localized changes without discovering full impact scope. When data structures change (removing enum variants, changing struct fields), Claude missed that compilation errors are insufficient—requires systematic search for all consumers, debugger integration files, test expectations, and cross-module references. (From: "Don't leak sysroot crates through dependencies", "Use annotate-snippet as default emitter on stable", "Add `MaybeDangling` to `core`")

- **Architectural Separation vs. Parameterization**: When asked to "split" or "separate" code paths, Claude added conditional branches at call sites rather than creating distinct execution flows. The Rust codebase prefers architectural separation (new trait methods, early interception) over parameterization (checking conditions everywhere). (From: "Split LLVM intrinsic abi handling from the rest of the abi handling")

- **Test Organization and Coverage**: Claude frequently missed test file updates, including: adding comprehensive edge case coverage, creating regression tests for fixed bugs, updating .stderr expectations after error message changes, and moving tests to appropriate directories when features are removed or reorganized. (From: "Fix ICE by rejecting const blocks in patterns during AST lowering", "Remove `feature(string_deref_patterns)`", "Use annotate-snippet as default emitter on stable")

- **Internal Refactoring for New Features**: When implementing features similar to existing ones, Claude added external access to internals (`pub(super)`) rather than refactoring internal structures to support both use cases. The Rust standard library pattern is to refactor field semantics and add helper methods on internal types. (From: "add VecDeque::splice", "Add `MaybeDangling` to `core`")

- **Dead Code and Cleanup Tasks**: Claude focused on making code compile but missed broader cleanup: removing FIXME comments whose conditions were met, deleting unused parameters after removing conditional logic, removing CLI options for deleted features, and updating feature gate metadata. (From: "Use annotate-snippet as default emitter on stable", "Port `#[instruction_set]` to attribute parser")

- **Build System Integration**: Changes to bootstrap, build configuration, and warning handling require verifying impact across the entire build pipeline including rustdoc, cargo invocations, and downstream tools—not just the primary compilation target. (From: "bootstrap: Use cargo's `build.warnings=deny` rather than -Dwarnings")

