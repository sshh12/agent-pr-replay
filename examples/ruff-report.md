# Coding Agent Repo Report

- **Repository**: astral-sh/ruff
- **Sessions Analyzed**: 20

---

## Synthesized CLAUDE.md / AGENTS.md

```markdown
# Coding Agent Guide for astral-sh/ruff

This document provides guidance for AI coding agents working on the Ruff codebase, a Rust-based Python linter and type checker.

## Rust Linter Rule Implementation

- Before implementing new linting rules, search for similar rules using Glob/Grep to understand diagnostic patterns (e.g., `DiagnosticGuard` pattern in `crates/ruff_linter/src/rules/`)
- Never invent methods like `create_diagnostic()` or `with_secondary_label()`; use existing checker API patterns discovered through codebase exploration
- For secondary annotations during AST visitation, use `Option<DiagnosticGuard>` with `get_or_insert_with()` to lazily create diagnostics
- Use `guard.secondary_annotation("", range)` for secondary highlights; empty messages let visual underlines convey meaning
- When narrowing diagnostic ranges for loop constructs, use `token::parenthesized_range()` to handle parenthesized targets correctly
- Prefer borrowed lifetimes (`&'a str`) over owned `String` in violation structs when data comes from the source code locator

### Rule File Organization

- Use generic, extensible file names for rules that may expand in scope (e.g., `function_signature_change_in_3.rs` not `keyword_only_args.rs`)
- Violation naming should match patterns in `crates/ruff_linter/src/codes.rs` and use descriptive names indicating broad categories
- For new rules, use `preview_since` with the current/next version, never `stable_since`; check existing rules in codes.rs for version patterns
- Define extensible enums for violation types when a rule may handle multiple similar cases in the future
- Integrate rule checks in `checkers/ast/analyze/statement.rs` for statement-level analysis, not in `module.rs`

### Qualified Name Resolution

- Use `typing::resolve_assignment()` first to handle variable assignments, then fall back to direct calls (see `crates/ruff_linter/src/rules/airflow/rules/function_signature_change_in_3.rs:86-90`)
- Never implement custom qualified name resolution; use `checker.semantic().resolve_qualified_name()`
- For rules checking special Python patterns (TYPE_CHECKING, dunder methods), grep for existing handling like `is_type_checking_block`

### Testing and Snapshots

- Add test fixtures in `resources/test/fixtures/` using descriptive paths (e.g., `fixtures/ruff/RUF067/modules/__init__.py`)
- Never manually create snapshot files; let `cargo test` generate them via the test harness in `snapshots/` directory
- Study snapshot test patterns in existing `mod.rs` files to match testing style (e.g., `assert_diagnostics_diff!` for configuration variations)
- After creating test fixtures, run tests to generate snapshot files that must be committed

## Type Checker Implementation

### Diagnostic and Narrowing Patterns

- Extract reusable narrowing logic into dedicated helper methods that mirror existing patterns (e.g., `narrow_typeddict_subscript`, `narrow_tuple_subscript` in `narrow.rs`)
- If logic needs to be called from multiple locations (comparison operators AND match statements), extraction is essential
- When existing helper functions become applicable to multiple contexts, rename them to reflect broader usage (e.g., `is_supported_typeddict_tag_literal` → `is_supported_tag_literal`)
- Place new helper functions near related helpers at the file's end, maintaining logical grouping

### Type System Feature Implementation

- Never add constraint tracking as a parallel system; prefer integrating into existing inference flow (see `types/generics.rs:infer_reverse_map`)
- Type inference changes typically require new `TypeMapping` enum variants, not just new fields in builders
- For type narrowing features, search for existing narrowing infrastructure (e.g., `narrow.rs`, constraint types) before adding simple boolean checks
- When implementing features similar to existing ones (TypeIs/TypeGuard), look for semantic differences; the prompt description indicates whether fundamentally different constraint merging logic is needed
- Before implementing, read ALL test files mentioned in diffs; test expectations reveal semantic requirements better than prose descriptions
- Trace how similar existing features handle: display, variance, visitor patterns, subtyping relations, constraint merging, and materialization policies

### Property and Descriptor Handling

- For property-related bugs, examine both descriptor protocol handling AND scope classification of property getter/setter methods
- Before modifying core type resolution logic (types.rs), check if the issue is in method/scope resolution (class.rs, scope.rs)
- For inheritance/override-specific issues, prefer fixes in class member resolution over general descriptor protocol changes

### Type Materialization

- Apply materialization per-signature in signature lists, not at the callable level
- For gradual parameters (`...`): top materialization preserves return type and creates unmatchable parameters, bottom materialization creates `(*object, **object)` parameters
- Never simplify `Bottom[Callable[..., R]]` to `(*object, **object) -> Never`; preserve the return type as `-> R`
- When asked to "move X from level A to level B", eliminate X entirely from level A, don't keep it as a computed method

### Code Integration and Refactoring

- When adding features similar to existing ones, look for opportunities to extract shared abstractions rather than duplicating logic
- Never add parallel handler functions for similar contexts; prefer refactoring into a unified handler with context detection via AST ancestor traversal
- When detecting type-based behavior (like TypedDict subclasses), prefer using existing semantic model type inference over manual AST pattern matching
- Make minimal, targeted visibility changes to internal APIs; if type system methods are needed, expose them properly

## Test Organization

### Test File Management

- Before creating new test files, check if existing test files already cover related scenarios (use Glob/Grep to find relevant test files)
- Add new test cases to existing files that cover the same feature category (e.g., narrowing tests go in `narrow/*.md` files)
- For linter tests: augment existing test files in `resources/test/fixtures/` rather than creating parallel test structures
- For type checker tests: add test cases to existing `.md` files in `resources/mdtest/` (e.g., narrowing in `complex_target.md`, match patterns in `match.md`)
- Match test file to the feature area: descriptor protocol bugs → descriptor_protocol.md, not properties.md
- Never create standalone .py test files when mdtest markdown files exist

### Test Coverage Strategy

- When fixing bugs, add minimal targeted tests that directly validate the fix, not exhaustive edge case coverage
- Prefer 2-3 simple test cases showing before/after behavior over comprehensive scenario exploration
- Never test tangential scenarios; focus tests on the exact reported issue
- For autocomplete/suggestion features, include tests for: basic cases, already-set arguments, inheritance scenarios, aliased imports, and edge cases specific to language features

### Test Documentation

- Variable renaming in tests (a→x1, b→x2) often accompanies feature work to improve clarity
- In test files, prefer concise comments describing expected behavior over before/after comparisons
- Use `reveal_type` comments matching the expected behavior after the fix
- Never create IMPLEMENTATION.md, EXAMPLES.md, or CHANGES_SUMMARY.md files for type checker changes

## Simplicity and Engineering Tradeoffs

### Avoid Over-Engineering

- Prefer hard-coded limits for initial performance fixes over threading configuration parameters through multiple layers
- Never add configuration infrastructure when the PR shows a direct, hard-coded fix; match the complexity level of the actual change
- For single-use validation logic, inline the check rather than extracting a helper function
- Never create helper functions called only once in a tight scope; prefer direct pattern matching or conditionals

### Performance and Observability

- When addressing performance issues, look for accompanying observability changes in the PR diff (tracing, logging, metrics)
- Performance fixes often come with instrumentation; if the PR adds tracing spans or changes log levels, include similar changes
- Check if the PR modifies multiple files for non-functional changes (logging, tracing); these are often equally important to the functional fix
- Look for patterns like `trace!` → `debug!` log level changes or new tracing spans being added across multiple files

## Documentation Tasks

### Systematic Documentation

- When a prompt describes discovering multiple instances (\"I went through the rules and found several...\"), conduct a comprehensive codebase search rather than limiting work to mentioned examples
- For documentation tasks mentioning "various" or "several" items, use Grep/Glob to find all matching patterns
- Never assume examples in a prompt are exhaustive; treat them as representative samples requiring broader application
- Pattern: Grep for settings access to identify undocumented rules before making changes

### Python Stub Files

- In `.pyi` stub files, preserve existing declaration patterns; special forms are typically declared as `Name: _SpecialForm` followed by docstrings, not as decorated functions
- Never restructure type declarations from assignment syntax to function syntax
- When modifying stub files that provide hover documentation, search for existing tests to understand how documentation changes should be validated
- Docstrings for type system features should reference authoritative sources (e.g., typing specification URLs) with links to `https://typing.python.org/en/latest/spec/`

### Config Option Changes

- When renaming configuration options, always search for test snapshots that serialize config output (files in `tests/.../snapshots/`)
- Use Grep with the old config name to find all references including test fixtures, not just source code
- Ruff configuration changes require updates to: `options.rs`, `settings.rs`, `ruff.schema.json`, AND snapshot files in `crates/ruff/tests/cli/snapshots/`

## Architectural Patterns

### Code Organization

- Extract all repeated validation logic into small, focused helper functions rather than duplicating checks
- When restructuring control flow, minimize nesting depth and intermediate boolean variables; use early returns where appropriate
- Import statement-specific AST types directly rather than using fully qualified paths throughout code

### Refactoring for Performance

- When asked to reduce monomorphization, move substantial logic blocks (50+ lines) into helper structs to achieve meaningful compile-time improvements
- Never extract only the final operation; identify what causes code generation explosion (generic parameters, closures)
- Builder pattern refactorings: return a builder struct that captures context, letting callers invoke closures themselves
- When refactoring methods to return slices instead of iterators, investigate whether this implies internal data structure optimization
- For methods returning iterators over internal collections, consider whether returning slices enables simplifying underlying storage

### Understanding Prompt Context

- The PR title and prompt may emphasize one aspect while the diff shows the change is part of a larger effort
- When analyzing diffs, identify the ratio of functional vs observability changes
- For refactoring-style tasks ("add support for X in context Y"), search for where X already works in a different context and extract common logic
- Never produce empty outputs when given a clear feature request; if blocked by unfamiliar architecture, explicitly read core files and ask clarifying questions

## Rust-Specific Patterns

### Memory and Optimization

- For small collections with variable length, consider `SmallVec` to eliminate heap allocations
- When a struct has multiple related `Box<[T]>` fields, evaluate consolidating them into a single vector with index markers
- Returning slices (`&[T]`) from accessor methods is preferable to returning iterators when data is contiguously stored
- Provide separate `iter_*` convenience methods for common iteration patterns rather than forcing callers to add `.iter()` everywhere

### Lifetime and Type Handling

- When extracting logic that references AST nodes, add explicit lifetime parameters (e.g., `'ast`) to struct definitions
- For Rust-based projects with lifetime annotations and database patterns (e.g., `Type<'db>`, `self.db`), prioritize reading method signatures and return types
```

---

## Suggested Skills

### Skill 1: Ruff Linter Rule Implementation

```markdown
---
name: ruff-linter-rule
description: Specialized guidance for implementing new linting rules in the Ruff codebase. Use when the user asks to add a new lint rule (e.g., "add rule RUF123", "implement check for X pattern"), extend existing rule categories (AIR3xx, PLC, etc.), or modify rule diagnostic behavior.
---

# Ruff Linter Rule Implementation

## Overview

This skill provides specialized patterns for implementing linting rules in the Ruff codebase, ensuring correct diagnostic API usage, proper rule organization, and comprehensive testing.

## Instructions

When implementing a new linting rule:

1. Search for similar rules using Grep in `crates/ruff_linter/src/rules/` to understand existing patterns
2. Identify the rule category and check version patterns in `crates/ruff_linter/src/codes.rs`
3. Use generic, extensible file names when the rule category may expand
4. Integrate checks in the appropriate analyzer file (statement.rs for statement-level, expression.rs for expressions)
5. Create test fixtures in `resources/test/fixtures/` with descriptive paths
6. Run `cargo test` to generate snapshot files that must be committed

## Patterns to Follow

### Diagnostic Construction

- Use `Option<DiagnosticGuard>` with `get_or_insert_with()` to lazily create diagnostics during AST visitation
- Call `guard.secondary_annotation("", range)` for secondary highlights; empty messages let visual underlines convey meaning
- Use `token::parenthesized_range()` for narrowing diagnostic ranges in loop constructs
- Prefer borrowed lifetimes (`&'a str`) over owned `String` in violation structs when data comes from source code

### Rule Organization

- Violation names should match patterns in `codes.rs` and indicate broad categories (e.g., `Airflow3IncompatibleFunctionSignature` not `Airflow3KeywordOnlyArgs`)
- Define extensible enums for violation types when a rule may handle multiple cases (see `FunctionSignatureChangeType` pattern)
- For new rules, use `preview_since` with current/next version, never `stable_since`

### Qualified Name Resolution

- Use `typing::resolve_assignment()` first to handle variable assignments, then fall back to direct calls
- Never implement custom qualified name resolution; use `checker.semantic().resolve_qualified_name()`
- See `crates/ruff_linter/src/rules/airflow/rules/function_signature_change_in_3.rs:86-90` for proper resolution pattern

### Testing

- Create test fixtures in descriptive paths like `fixtures/ruff/RUF067/modules/__init__.py` for file-specific behavior
- Study snapshot test patterns in existing `mod.rs` files to match testing style (e.g., `assert_diagnostics_diff!`)
- Never manually create snapshot files; let the test harness generate them in `snapshots/` directory
- Configuration schema changes require updating `options.rs`, `settings.rs`, `ruff.schema.json`, and snapshot files in `crates/ruff/tests/cli/snapshots/`

## Anti-patterns to Avoid

- Never invent diagnostic methods like `create_diagnostic()` or `with_secondary_label()` without searching the codebase first
- Never use `stable_since` for new rules; check existing rules in the same category for version patterns
- Never create specific file names like `keyword_only_args.rs` when a generic name like `function_signature_change_in_3.rs` would accommodate future related checks
- Never integrate checks in `checkers/ast/analyze/module.rs` for statement-level analysis; use `statement.rs` instead
- Never manually create or edit snapshot files; always generate via test execution
```

### Skill 2: Ruff Type Checker Implementation

```markdown
---
name: ruff-type-checker
description: Specialized guidance for implementing type system features in Ruff's type checker. Use when the user asks to implement type narrowing (e.g., "add narrowing for X"), add type system features (TypeGuard, TypeIs, protocols), fix type inference bugs, or modify callable/generic type handling.
---

# Ruff Type Checker Implementation

## Overview

This skill provides patterns for implementing type system features in Ruff's Rust-based Python type checker, focusing on narrowing semantics, type inference, and constraint handling.

## Instructions

When implementing type checker features:

1. Read existing test files in `resources/mdtest/` first; test expectations reveal semantic requirements
2. Search for similar existing features to understand display, variance, visitor patterns, constraint merging, and materialization
3. Check if changes require new `TypeMapping` enum variants, not just new fields in builders
4. Modify existing test files rather than creating new ones; add sections to relevant `.md` files
5. Update display logic in `types/display.rs` when changing type representations
6. Run tests to update `revealed:` type expectations

## Patterns to Follow

### Narrowing Logic

- Extract reusable narrowing logic into dedicated helper methods mirroring existing patterns (e.g., `narrow_typeddict_subscript` in `narrow.rs`)
- If logic is called from multiple locations (comparison operators AND match statements), extraction is essential
- Place new helper functions near related helpers, maintaining logical grouping
- When helpers become applicable to multiple contexts, rename them generically (e.g., `is_supported_typeddict_tag_literal` → `is_supported_tag_literal`)

### Type Inference and Constraints

- Never add constraint tracking as a parallel system; integrate into existing inference flow (see `types/generics.rs:infer_reverse_map`)
- Type inference changes typically require new `TypeMapping` enum variants
- For complex narrowing semantics (TypeGuard "overriding" vs TypeIs "intersecting"), search for constraint merging logic and DNF/CNF representations
- The phrase "overrides previous type information" indicates non-commutative constraint operations requiring explicit ordering
- Search for `NarrowingConstraint`, `merge_constraints`, and `infer_narrowing_constraint` to understand constraint infrastructure

### Property and Descriptor Handling

- For property-related bugs, check both descriptor protocol handling AND scope classification of property methods
- Before modifying core type resolution in `types.rs`, check if the issue is in method/scope resolution (`class.rs`, `scope.rs`)
- For inheritance/override issues, prefer fixes in class member resolution over general descriptor protocol changes

### Type Materialization

- Apply materialization per-signature in signature lists, not at the callable level
- For gradual parameters (`...`): top materialization preserves return type and creates unmatchable parameters, bottom creates `(*object, **object)` parameters
- Never simplify `Bottom[Callable[..., R]]` to `(*object, **object) -> Never`; preserve return type
- When moving a concept from one level to another (e.g., callable to parameters), eliminate it from the original level entirely

### Integration and Refactoring

- When adding features similar to existing ones, extract shared abstractions; look for trait opportunities (e.g., `TypeGuardLike`)
- Never add parallel handler functions; refactor into unified handlers with AST ancestor traversal for context detection
- When detecting type-based behavior (TypedDict subclasses), use semantic model type inference over manual AST pattern matching
- Make minimal, targeted visibility changes; if type system methods are needed, expose them properly with trait imports

### Variance Implementation

- Check if documentation files like `generics/pep695/variance.md` contain formal reasoning
- Variance is often counterintuitive and requires mathematical proof, not intuition
- Never assume similar types have identical variance (TypeIs vs TypeGuard require different reasoning)

## Anti-patterns to Avoid

- Never assume two similar types (TypeIs/TypeGuard) have identical implementations without checking semantic differences in the prompt
- Never add simple boolean checks for complex narrowing features; they usually require constraint algebra
- Never create new test files when existing mdtest files exist; augment existing `.md` files in `resources/mdtest/`
- Never create IMPLEMENTATION.md, EXAMPLES.md, or CHANGES_SUMMARY.md documentation files for type checker changes
- Never skip changes to completion.rs, type_properties tests, bound_super.rs, or class_base.rs when adding new Type variants
- Never modify only core type resolution (types.rs) for property bugs; check scope classification in class.rs first
- Never add top materialization as a callable-level flag; represent through parameter kinds
```

### Skill 3: Codebase Exploration for Context

```markdown
---
name: ruff-codebase-patterns
description: Guidance for understanding Ruff codebase context before implementation. Use when the user asks to "add support for X", "fix Y behavior", or provides vague requirements requiring architectural understanding. Use this to discover existing patterns before writing code.
---

# Ruff Codebase Exploration

## Overview

This skill helps agents discover existing patterns, conventions, and architectural decisions in the Ruff codebase before implementing features, preventing API hallucination and ensuring consistency.

## Instructions

Before implementing any feature:

1. Use Grep to find similar existing functionality (e.g., search for related rule names, type narrowing patterns, or feature keywords)
2. Read method signatures and return types in the same file to understand API contracts
3. Check test files in `resources/test/fixtures/` (linter) or `resources/mdtest/` (type checker) to understand expected behavior
4. For refactoring tasks, search where the feature already works in a different context
5. Identify whether the task requires statement-level, expression-level, or module-level integration

## Patterns to Follow

### Understanding PR Context

- The PR title and prompt may emphasize one aspect while the diff shows a larger effort (e.g., prompt says "limit completions" but 80% of diff is tracing/logging)
- Identify the ratio of functional vs observability changes; if most of the diff is tracing spans or log level changes, that's the primary focus
- Look for patterns like `trace!` → `debug!` changes or new tracing spans across multiple files as indicators of debugging work

### Discovering Existing Patterns

- Search for where existing similar functionality lives before implementing (e.g., if-statement narrowing when adding match-statement narrowing)
- For type system work, grep for existing constraint types, TypeMapping variants, and inference methods
- Check how existing rules handle special patterns (TYPE_CHECKING blocks, dunder methods) by grepping for `is_type_checking_block` or specific dunders
- For diagnostic features, search for `DiagnosticGuard`, `secondary_annotation`, and similar rules' implementation files

### Test Organization Discovery

- Use Glob to find existing test files before creating new ones (e.g., `**/*narrow*.md` or `**/RUF0*.py`)
- Check if test files use mdtest format (`.md` files) or Python fixtures (`.py` files)
- Identify test file organization: narrowing tests in `narrow/*.md`, match patterns in `match.md`, fixtures in `resources/test/fixtures/`

### Configuration Pattern Discovery

- Before adding configuration options, grep for similar settings in `options.rs` and `settings.rs`
- Check if boolean flags are preferred over enums by examining existing similar options
- Search for how existing rules expose configuration (e.g., grep for rule-specific settings in rule files)

### Refactoring Scope Recognition

- For "add support for X in context Y" tasks, search for X in existing contexts to find extraction opportunities
- When asked to "move X from A to B", check what removing X from A entirely would require (don't keep it as computed method)
- Search for TODOs mentioning the feature area but recognize humans may solve differently than TODOs suggest

## Anti-patterns to Avoid

- Never jump directly to implementation without searching for existing similar functionality
- Never invent API methods without grepping the codebase for actual patterns (e.g., searching for `DiagnosticGuard` usage)
- Never create standalone test files without checking if mdtest or fixture patterns are used
- Never assume prompt examples are exhaustive; use Grep to find all instances when prompt says "several" or "various"
- Never produce empty outputs when blocked; explicitly read core files and ask clarifying questions
- Never skip observability changes (tracing, logging) that appear in the broader PR context
- Never treat configuration as always needing enums; check if boolean flags match codebase patterns
```

---

## Key Insights from Analysis

- **Diagnostic API Discovery**: Claude frequently invents non-existent diagnostic methods instead of discovering actual patterns. The human implementation always uses `DiagnosticGuard` with `get_or_insert_with()` for lazy diagnostic construction, while Claude created imaginary APIs like `create_diagnostic()` and `with_secondary_label()`. (From: "[`pylint`] Improve diagnostic range for `PLC0206`")

- **Over-Engineering vs. Simplicity**: When addressing performance issues, Claude tends to add configuration infrastructure and thread parameters through multiple layers, while humans prefer hard-coded fixes for initial solutions. The human used `truncate(1000)` directly; Claude created `CompletionSettings`, `max_completions` fields, and configuration serialization. (From: "[ty] Limit the returned completions to reduce lag")

- **Test File Organization**: Claude consistently creates new test files instead of augmenting existing ones. Across multiple PRs (tuple narrowing, TypedDict narrowing), the human added test cases to existing `.md` files in appropriate categories, while Claude created standalone test files with duplicate coverage. (From: "[ty] Support narrowing for tuple matches with literal elements", "[ty] Narrow `TypedDict` literal access in `match` statements")

- **Constraint System Misunderstanding**: For complex type system features requiring constraint algebra, Claude adds simple boolean checks or parallel systems instead of integrating into existing constraint infrastructure. The human's TypeGuard implementation added ~200 lines of DNF constraint merging logic, while Claude only added a boolean check to skip narrowing. (From: "[ty] implement `typing.TypeGuard`")

- **Observability Changes Missed**: Claude focuses on the functional change mentioned in prompts while missing accompanying tracing/instrumentation changes that dominate the actual diff. When fixing completion lag, Claude missed that 80% of the human's changes were logging and tracing additions across multiple files. (From: "[ty] Limit the returned completions to reduce lag")

- **Refactoring Scope**: Claude interprets refactoring tasks too narrowly, extracting only minimal operations instead of moving substantial logic. For monomorphization reduction, the human moved 100+ lines into a builder struct with API changes across callsites, while Claude extracted only the final map insertion. (From: "[ty] Reduce monomorphization in `add_binding`")

- **Documentation Task Completeness**: When prompts mention "several" or "various" instances, Claude limits work to mentioned examples rather than conducting comprehensive searches. The human systematically added Options documentation to multiple rule modules, while Claude only addressed the mentioned flake8_gettext examples. (From: "Document options for more rules")

