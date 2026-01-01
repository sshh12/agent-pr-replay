# Coding Agent Repo Report

**Repository**: fastapi/fastapi
**Sessions Analyzed**: 19

---

## Synthesized CLAUDE.md / AGENTS.md

```markdown
# FastAPI Development Guide for AI Agents

This guide provides specific patterns and guardrails for working with the FastAPI codebase based on common divergences between human and AI implementations.

## Removing Deprecated Features and Compatibility Layers

- Delete entire compatibility modules rather than stubbing them out when removing deprecated support—this prevents import confusion
- Remove all conditional branching (if/else checks) for deprecated versions completely, not just the code inside branches
- Delete documentation examples, test files, and coverage configurations that reference deprecated features (e.g., `docs_src/*_pv1_*.py`, `@needs_pydanticv1` decorators)
- Consolidate imports in `__init__.py` files to point directly to supported implementations after removing compatibility layers
- Add runtime error checks at API boundaries that raise exceptions when deprecated versions are detected, rather than returning boolean flags
- Remove temporary parameter modules entirely when their only purpose was compatibility with deprecated versions
- Update type encoders and serialization dictionaries (e.g., `fastapi/encoders.py:ENCODERS_BY_TYPE`) to remove deprecated type mappings

## Scope Control for Find-and-Replace Tasks

- Distinguish between project-owned patterns and external patterns when doing search-and-replace (e.g., FastAPI's own deprecation warnings vs warnings about external dependencies)
- Read surrounding context (5-10 lines) before replacing to verify the match is semantically related to the task
- Never blindly replace all grep results; filter by context to avoid changing unrelated test fixtures or external library references

## Public API Surface Area

- Check if similar internal classes are exported in `__init__.py` before adding new exports; if existing classes (like `DependencyScopeError`) are internal, follow that pattern
- Only export symbols that users need to import directly; internal utilities used only as `category=` arguments don't need public exports
- Prefer minimal public API exposure unless there's a clear use case for external access

## Code Placement and Minimal Diffs

- Append new classes to the end of files rather than inserting mid-file, unless there's a clear logical grouping requirement
- Maintain exact parameter naming patterns in function calls (e.g., if some calls use `message=` keyword, match that pattern)
- For docstrings, check if the project favors brief docstrings with external reference URLs over lengthy inline explanations

## Handling Breaking Changes and Version Migrations

- Use `Grep` with patterns like version checks (`PYDANTIC_V2`, `if.*PYDANTIC`) to find all compatibility layers before starting removal
- Version migrations affect dependencies, source code, tests, documentation, and CI configuration—never assume it's limited to a few files
- When prompts mention "keeping temporary support", verify what this means by examining existing patterns in the codebase
- Use the Task tool with `subagent_type=Explore` to map out all affected areas before implementing large-scale migrations

## Understanding PR Context from Diffs

- Read the entire actual PR diff before starting work; diffs show what was actually done, while prompts may only describe part of the changes
- Look for structural changes (renames, moves) before additive changes; directory renames cascade into documentation and test updates
- When Python package names conflict with standard library modules (like `dataclasses` or `graphql`), append underscores (e.g., `dataclasses_/`)
- After renaming directories, search for all references in markdown documentation and update paths consistently

## Writing Tests for Documentation Examples

- Use `importlib.import_module()` to dynamically load tutorial variants (e.g., `tutorial001_py39`, `tutorial001_py310`)
- Use `pytest.fixture` with `params` to test all variants in a single test file; avoid creating separate test files per variant
- Include tests for: successful cases, validation error cases (422 responses), invalid types, and OpenAPI schema validation
- Never create helper scripts (`.sh`, standalone `.py`) for repository changes; use proper tools directly

## Minimal Changes and Avoiding Over-Engineering

- Use the simplest implementation that satisfies requirements; frozen dataclasses are already hashable without custom `__post_init__` logic
- Test coverage should validate requirements, not exhaustively test framework guarantees (e.g., don't test that frozen dataclasses are immutable)
- Import simplicity: use `dataclasses.replace()` directly rather than aliased imports unless name conflicts exist

## Test File Patterns and Location

- Explore existing test directory structure with Glob/Grep before writing tests to identify conventions
- Never create standalone test scripts at repository root; add tests to `tests/` subdirectories following existing patterns
- Match testing style: if the codebase uses pytest fixtures, TestClient, snapshot testing (`inline_snapshot`), or version decorators (`@needs_pydanticv2`), replicate exactly
- Use assertions, not print statements or manual validation

## Bug Fix Scope and Discovery

- Fix only code paths that directly cause the reported bug; avoid adding defensive checks to related functions unless the bug manifests there
- When working on deepcopies, assignments like `new_schema[key] = schema[key]` are redundant if no transformation is needed
- Keep fixes concise; if code changes are self-documenting (e.g., adding `isinstance(value, str)`), omit explanatory comments

## CI/CD Integration Patterns

- Extend existing workflow files over creating new separate workflows; use matrix conditionals to run specialized steps
- For benchmark/performance tests, consolidate scenarios into fewer comprehensive test files rather than splitting by category
- Use module-level `pytest.skip` with CLI flag detection over custom markers when tests should only run with specific flags
- Match dependency version patterns in target files (exact pins `==` vs ranges)

## GitHub Actions Matrix Strategy

- Never expand test matrices into full Cartesian products; use sparse matrices with `include`/`exclude` to sample strategically
- Add marker fields (like `coverage: "coverage"`) to conditionally run expensive steps
- Multi-OS testing often requires config changes: check if coverage tools need path handling adjustments (e.g., `relative_files = true` in `pyproject.toml`)
- Add comments explaining matrix design decisions, especially when using conditionals to avoid resource limits

## Documentation and Scope Discipline

- Never create summary/documentation files (README.md, SETUP.md) unless explicitly requested
- Avoid generating "success" or "setup complete" documentation after implementation
- For bug fixes, write only integrated test files, not standalone demo scripts
- Match task scope: if asked to "fix the bug", don't add demos, migration guides, or extensive comments

## Fixing Failing Tests vs Adding New Tests

- When PR diffs show test modifications (removing `xfail` markers, changing assertions), fix existing tests rather than creating new test files
- If tests are marked with `pytest.mark.xfail` in diff removals, your changes must make those tests pass
- Look for patterns: if dozens of tests remove xfail markers, the implementation must handle all those cases

## Helper Functions vs Property Overloading

- When adding support for new field attributes (like `validation_alias`), add separate properties and helper functions rather than adding conditional logic to existing properties
- Pattern: Add simple extraction properties → Create helper functions for selection logic → Update call sites to use helpers
- For cross-cutting concerns like "get the right alias for validation", create utility functions (e.g., `get_validation_alias()`) rather than embedding logic in properties

## Documentation Code Example Variants

- When adding code variants for Python versions, update all three layers: source examples in `docs_src/`, documentation references in `docs/en/docs/`, and test files in `tests/test_tutorial/`
- Highlight line numbers (`hl[...]`) must be recalculated for each variant—removing imports changes line counts
- Tests for versioned examples should use `pytest.param()` with version markers (`needs_py39`, `needs_py310`), not separate test files
- Update `pyproject.toml` ruff configuration to include lint exceptions for new variant files

## Exception Context and Formatting

- Exception context for debugging should be added via `__str__` override on exception classes, not by modifying exception handlers
- Metadata will naturally appear in tracebacks via `__str__`—no need to explicitly log it in handlers
- Prefer TypedDict over `Dict[str, Any]` when defining structured data shapes (see `fastapi/exceptions.py`)
- For function metadata caching, prefer module-level dict caching (`_cache: Dict[int, T] = {}` with `id(func)` keys) over `functools.lru_cache`

## Import Cleanup During Refactoring

- After removing code, check if any imports are now unused and remove them
- When deleting functionality that was the sole consumer of an import, remove that import
- Never leave dead imports—they create confusion about dependencies

## Defensive Callable Detection with Multiple Decorator Layers

- When fixing callable detection for wrapped/partial functions, check BOTH `_impartial(call)` and `_unwrapped_call(call)` at every level
- Apply detection exhaustively: check impartial version, fully unwrapped version, impartial `__call__`, unwrapped `__call__`, then unwrapped's unwrapped `__call__`
- Return explicit `False` for `None` checks rather than relying on implicit returns

## Comprehensive Test Coverage for Decorator Combinations

- Test callable class instances with decorated `__call__` methods, not just decorated functions
- Test both composition directions: `partial(wrapped_func)` AND `wrapped(partial_func)`, including async variants
- Create separate test helper classes/instances at module level (e.g., `ClassInstanceWrappedDep`) to test instance behavior
- For async detection bugs, create async wrapper decorators that preserve generator/async generator behavior
```

---

## Suggested Skills

### Skill 1: FastAPI Deprecation Removal

```markdown
---
name: fastapi-deprecation-removal
description: Remove deprecated features and compatibility layers from FastAPI codebase. Use when removing support for old versions (e.g., Pydantic v1), cleaning up compatibility modules, or eliminating conditional version checks. Triggered by tasks mentioning "drop support", "remove deprecated", or "clean up compatibility".
---

# FastAPI Deprecation Removal Skill

## Overview

This skill provides specialized guidance for removing deprecated features and compatibility layers from the FastAPI codebase, particularly when dropping support for older library versions like Pydantic v1.

## Instructions

When removing deprecated features from FastAPI:

1. **Explore First**: Use Grep to identify all occurrences of the deprecated feature:
   - Version checks (e.g., `PYDANTIC_V2`, `if.*PYDANTIC`)
   - Compatibility imports (e.g., `pydantic.v1`, `fastapi._compat`)
   - Temporary modules (e.g., `temp_pydantic_v1_params.py`)
   - Test decorators (e.g., `@needs_pydanticv1`)

2. **Delete Completely**: Remove entire compatibility modules rather than stubbing out code:
   - Delete files like `fastapi/_compat/v1.py`, `fastapi/_compat/main.py`
   - Remove all conditional branching for deprecated versions
   - Consolidate imports in `__init__.py` to point directly to supported implementations

3. **Update All Layers**:
   - Source code: Remove compatibility classes, conditional logic, and temporary params
   - Documentation: Delete examples using deprecated features (e.g., `docs_src/*_pv1_*.py`)
   - Tests: Remove test files, xfail markers, and version-specific decorators
   - Configuration: Update `pyproject.toml`, CI workflows, coverage settings

4. **Add Error Boundaries**: At API boundaries (model validation, field creation), add runtime checks that raise clear error messages when deprecated versions are detected

5. **Clean Up Encoders**: Remove deprecated type mappings from serialization dictionaries like `fastapi/encoders.py:ENCODERS_BY_TYPE`

## Patterns to Follow

- Trace through all import statements in `__init__.py` and consolidate to import directly from remaining implementations
- Change helper functions that detect deprecated usage from returning booleans to raising exceptions (fail fast)
- Remove entire temporary parameter modules when their sole purpose was compatibility
- Update dependency injection utilities by removing isinstance checks for deprecated parameter classes

## Anti-patterns to Avoid

- Leaving empty stub classes in compatibility files
- Commenting out deprecated code instead of deleting it
- Keeping compatibility module structure intact while removing functionality
- Missing documentation, test, or configuration updates
- Preserving conditional imports "just in case"
```

### Skill 2: FastAPI Test Pattern Matcher

```markdown
---
name: fastapi-test-patterns
description: Write tests following FastAPI conventions for documentation examples, version variants, and API validation. Use when adding test coverage for docs_src examples, writing tests for new features, or fixing bugs that require test validation. Triggered by tasks mentioning "add tests", "test coverage", or "write tests for examples".
---

# FastAPI Test Pattern Matcher Skill

## Overview

This skill ensures tests follow FastAPI's established patterns for testing documentation examples, handling multiple Python/Pydantic versions, and validating API behavior with OpenAPI schema checks.

## Instructions

When writing tests for FastAPI:

1. **Explore Existing Patterns**: Before creating tests, use Glob to examine `tests/test_tutorial/` structure:
   - Look for naming conventions (e.g., `test_tutorial001_py39.py` vs parameterized fixtures)
   - Check for common imports (`TestClient`, `inline_snapshot`, decorators)
   - Note version-specific patterns (`@needs_pydanticv2`, `@needs_py310`)

2. **Test Documentation Examples**:
   - Use `importlib.import_module()` to dynamically load tutorial variants (e.g., `tutorial001_py39`, `tutorial001_py310`)
   - Use `pytest.fixture` with `params` to test all variants in a single test file
   - Test successful cases, validation errors (422 responses), invalid input types, and OpenAPI schema

3. **Place Tests Correctly**:
   - Add tests to `tests/` subdirectories following existing structure
   - Match file naming: `tests/test_tutorial/test_<topic>/test_tutorial<number>.py`
   - Never create standalone demo scripts at repository root

4. **Use Proper Assertions**:
   - Use `assert` statements, not print statements
   - For OpenAPI validation, use `inline_snapshot` library
   - Include `TestClient` for endpoint testing
   - For version-specific tests, use decorators like `@needs_pydanticv2`

5. **Handle Multiple Variants**:
   - Use `pytest.param()` with version markers for parameterized tests
   - Update `pyproject.toml` ruff configuration with lint exceptions for new variant files
   - Recalculate highlight line numbers in documentation when variant imports differ

## Patterns to Follow

- Consolidate related test scenarios in fewer comprehensive files rather than many small files
- Module-level `pytest.skip` with CLI flag detection for conditional test suites
- Fixture parameterization over duplicate test functions
- Reading existing test files in the same area to match patterns exactly

## Anti-patterns to Avoid

- Creating test files at repository root
- Writing demonstration scripts with print statements instead of proper tests
- Creating separate test files for each variant instead of using parameterization
- Adding tests without updating configuration files (pyproject.toml, coverage settings)
- Writing exhaustive tests for framework guarantees rather than testing actual requirements
```

### Skill 3: FastAPI Minimal Fix Discipline

```markdown
---
name: fastapi-minimal-fix
description: Apply minimal, surgical fixes to FastAPI bugs without over-engineering or adding unnecessary complexity. Use when fixing bugs, addressing specific issues, or making targeted improvements. Triggered by tasks mentioning "fix bug", "fix issue", or "address problem".
---

# FastAPI Minimal Fix Discipline Skill

## Overview

This skill enforces minimal, focused fixes for bugs and issues in FastAPI, avoiding over-engineering, unnecessary abstractions, and scope creep common in AI-generated code.

## Instructions

When fixing bugs in FastAPI:

1. **Understand the Bug First**: Read the actual PR diff if available to see what was changed:
   - Look for the minimal set of files modified
   - Identify structural changes (renames, refactors) vs simple fixes
   - Check if test files show xfail removals (meaning you need to make tests pass)

2. **Fix Only What's Broken**:
   - Target the specific code path causing the bug
   - Avoid adding defensive checks to related functions unless the bug manifests there
   - When working on copies, skip redundant assignments if no transformation is needed
   - Keep code self-documenting; only add comments for non-obvious logic

3. **Test Appropriately**:
   - If PR diff shows test modifications (removing xfail markers), modify those existing tests
   - Write minimal tests that validate the fix works
   - Avoid exhaustive test suites testing framework behavior
   - Match repository testing patterns (pytest fixtures, TestClient, inline_snapshot)

4. **Clean Up During Refactoring**:
   - Remove unused imports after deleting code
   - Delete entire unused files rather than leaving empty stubs
   - Consolidate imports to point directly to implementations after removing compatibility layers

5. **Avoid Over-Engineering**:
   - Use built-in Python features (frozen dataclasses are hashable without custom logic)
   - Prefer simple module-level dict caching over LRU cache decorators for static metadata
   - Add simple properties for new attributes rather than complex conditional logic in existing properties
   - Use direct imports (e.g., `dataclasses.replace`) rather than aliases unless necessary

## Patterns to Follow

- Append new classes to file ends to minimize merge conflicts
- Match existing parameter naming patterns in function calls
- Use TypedDict over `Dict[str, Any]` for structured data
- Extract helper functions for cross-cutting concerns rather than embedding logic in properties
- Exception context via `__str__` override, not handler modifications

## Anti-patterns to Avoid

- Creating separate utility modules for one-off operations
- Creating demo scripts, READMEs, or setup documentation alongside bug fixes
- Adding features, refactoring, or "improvements" beyond what was requested
- Creating new compatibility layers when task is to remove compatibility
- Leaving dead imports after removing functionality
- Modifying exception handlers to add logging instead of using `__str__` overrides
- Adding unnecessary defensive code for edge cases not demonstrated in the codebase
```

---

## Key Insights from Analysis

- **Scope Understanding**: Claude often misinterprets "remove support for X" as disabling rather than complete elimination, leading to stubbed files instead of deletion. The human understood this required removing entire modules, consolidating imports, and eliminating all conditional branching. (From: "Drop support for pydantic.v1" and "Drop support for Pydantic v1, keeping short temporary support")

- **Test Integration**: Claude creates standalone demonstration scripts with print statements at repository root instead of integrating tests into the existing pytest suite following patterns like `TestClient`, `inline_snapshot`, and version-specific decorators. (From: "Fix handling of JSON Schema attributes named $ref" and "Fix support for if TYPE_CHECKING, non-evaluated stringified annotations")

- **Over-Engineering Tendency**: Claude adds unnecessary complexity like custom `__post_init__` validation for frozen dataclasses, verbose test suites (184 lines vs 25), and separate utility modules when inline implementations suffice. (From: "Make the result of Depends() and Security() hashable")

- **Matrix Strategy**: Claude expands CI test matrices into full Cartesian products (42 jobs) instead of strategic sparse sampling with `include`/`exclude` (11 jobs), missing production concerns about runtime costs and resource limits. (From: "Expand test matrix to include Windows and MacOS")

- **Scope Control**: Claude performs broad search-and-replace operations without semantic filtering, updating test warnings about unrelated features when the task is scoped to specific deprecation categories. (From: "Add a custom FastAPIDeprecationWarning")

- **Documentation Discipline**: Claude creates README.md, SETUP.md, and SUMMARY.md files alongside implementations when none were requested, adding maintenance burden for educational artifacts that should be handled by inline documentation. (From: "Add performance tests with CodSpeed")

- **Comprehensive Refactoring**: For version migrations and structural changes, Claude misses the full scope by not exploring documentation, CI configuration, and test infrastructure updates that typically accompany breaking changes affecting thousands of lines. (From: "Add missing tests for code examples" and "Upgrade internal syntax to Python 3.9+")

