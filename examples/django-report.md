# Coding Agent Repo Report

- **Repository**: django/django
- **Sessions Analyzed**: 18

---

## Synthesized CLAUDE.md / AGENTS.md

```markdown
# Django Development Guidelines for Claude

## Test Coverage for Bug Fixes

- When fixing bugs in Django, always add test coverage unless explicitly told not to - bug fixes without tests are incomplete
- Test files are typically in parallel directory structures (e.g., `django/db/models/lookups.py` → `tests/lookup/tests.py`)
- Add tests to existing test files that match the component being tested, never create new standalone test files or root-level scripts
- For crash fixes and regressions, write tests that reproduce the original failure condition using minimal reproduction cases
- Test assertions should verify root cause: compare operations against independent equivalent computations (e.g., `qs.count()` vs `len(list(qs))`), not hardcoded values
- For concurrency/async bugs, test all execution paths: combinations of sync/async handlers, different method variants (send/asend/robust variants)
- When fixing ORM lookups, test: plain values, F() expressions, Value() wrapped expressions, mixed lists, and edge cases like JSONNull()

## Minimal Code Changes and Scope Discipline

- Prefer minimal, surgical changes: modify only the lines necessary to fix the issue, don't restructure surrounding code
- Fix only what's broken - resist adding "defensive" logic for edge cases not mentioned in the issue
- When a bug can be fixed by adjusting an existing conditional vs adding new code blocks, prefer the conditional adjustment
- Never add explanatory comments for simple conditional logic; prefer clean, self-documenting code
- Avoid reformatting or "fixing" unrelated code (whitespace, quote styles, trailing commas) - these create noise in diffs
- Don't add defensive checks without evidence from existing code patterns; trust the framework's conventions

## Database-Dependent Patterns

- When making checks database-dependent by iterating over multiple databases, preserve the original control flow patterns (early returns, error accumulation)
- Maintain original error check ordering to preserve consistent error priority
- When replacing `connection` with `connections[db]` in loops, wrap only the code that originally referenced `connection.features`

## Null Checks and Falsy Values

- Use explicit `is None` checks rather than truthy evaluation (`if x is None` not `x or fallback`)
- Truthy checks treat empty strings, 0, False, and None identically - in database/query contexts, empty strings may be valid results
- For fallback logic, prefer: `return fallback if value is None else value`

## Code Efficiency and DRY Principle

- When a value needs to be computed and reused multiple times, use assignment expressions (walrus operator `:=`) to avoid redundant computations
- Never call the same conversion function (`str()`, `int()`, etc.) multiple times on the same value within a single method

## Django ORM Lookup Implementation Patterns

- When fixing lookup behavior to match another lookup, prefer delegation over reimplementation: use `get_lookup()` to retrieve and delegate to the existing lookup
- Never duplicate database-specific SQL generation (`as_sqlite`, `as_oracle`, `as_postgresql`) that already exists in another lookup class
- For ORM features, explore both the field-specific module AND `django/db/models/lookups.py` - features often require coordination
- When comparing query components (ORDER BY vs GROUP BY), resolve expressions on a cloned query to avoid polluting the original
- Handle raw SQL edge cases (e.g., `extra(order_by=...)`) explicitly by checking for them first

## CSS Architecture and Browser Compatibility

- When fixing browser-specific rendering bugs, prefer removing problematic patterns at the source (HTML/templates) over adding defensive CSS overrides
- Never pile specificity-based workarounds on top of incompatible patterns
- Safari's poor flexbox support on `<fieldset>` is a known issue - remove flex classes from fieldset elements rather than overriding with `display: block`
- After fixing root cause, look for adjacent cleanup opportunities: related CSS rules, outdated hacks, non-internationalized properties (e.g., `float: left` → `float: inline-start`)

## Django System Checks and Warnings

- Warning messages should be extremely brief and direct (10 words or less) - see `docs/ref/checks.txt` for examples
- Never create verbose multi-sentence warning messages with hints
- Check methods should follow the pattern `_check_<aspect>(self, databases)` and always accept the `databases` parameter
- When adding a new system check, ALWAYS update `docs/ref/checks.txt` to register the new check ID

## Template Tag Validation

- When moving validation logic from one location to another, search for ALL call sites using `Grep` before starting implementation
- Check `contrib/` subdirectories for framework extensions that may instantiate core classes
- When a parameter becomes unused after refactoring, delete it from all call sites and the function definition

## Property-Based Refactoring

- When fixing logic bugs in query builders or compilers, prefer extracting decision logic into computed properties/methods rather than adding inline guards
- Complex conditional logic belongs in dedicated properties/methods with explicit edge case handling, not embedded in the operation itself
- For query optimization bugs, examine existing patterns - if the codebase uses properties for query state, follow that pattern

## Documentation Updates

- Bug fixes in Django require release notes entries in `docs/releases/<version>.txt`
- When fixing regressions or bugs with ticket references, search for release note files before completing the task
- New system checks MUST update both `docs/ref/checks.txt` (check ID registry) and relevant topic docs
- When adding/fixing features in utility functions (especially `django/utils/*`), check for corresponding docs in `docs/ref/`
- Release note format: "* Fixed a regression in Django X.Y where [description] (:ticket:`NUMBER`)."
- Security and bug fixes often need backporting - check if multiple version release notes should be updated

## Defensive Attribute Access

- When accessing attributes that may not exist on all expression types (like `param.value`), use `hasattr()` checks before access
- Never assume param type uniformity in `resolve_expression_parameter`; prefer explicit `isinstance()` and `hasattr()` guards
- For expression parameter handling, check both `hasattr(param, 'as_sql')` AND `isinstance(param, expressions.Value)`
```

---

## Suggested Skills

### Skill 1: Django Bug Fix

```markdown
---
name: django-bug-fix
description: Specialized workflow for fixing bugs in Django codebase. Use when the user asks to fix a bug, regression, or crash in Django code. Ensures test coverage, release notes, and proper validation are included.
---

# Django Bug Fix Workflow

## Overview

This skill guides you through fixing bugs in the Django codebase with proper test coverage and documentation.

## Instructions

### Step 1: Understand and Implement the Fix

- Read the relevant source files to understand the current implementation
- Make minimal, surgical changes to fix the issue - avoid refactoring unrelated code
- Use explicit `is None` checks rather than truthy evaluation for null handling
- Preserve existing control flow patterns (early returns, error accumulation)

### Step 2: Add Test Coverage

- Locate the existing test file that corresponds to the module being fixed
- Use `Grep` to find existing test files: pattern like `tests/**/*test*.py` searching for the module name
- Add test methods to the existing test file - never create new standalone test files or root-level scripts
- Write tests that reproduce the original failure condition
- Test assertions should compare against independent computations, not hardcoded expected values
- For ORM bugs: test plain values, F() expressions, Value() expressions, and mixed lists
- For async bugs: test combinations of sync/async handlers and method variants

### Step 3: Update Documentation

- Search for release notes files using `Glob` pattern: `docs/releases/*.txt`
- Add an entry to the current version's release notes following the format: "* Fixed [description] (:ticket:`NUMBER`)."
- Check if the bug is a regression that needs backporting to multiple versions
- For new system checks, update `docs/ref/checks.txt` to register the check ID
- For utility function changes in `django/utils/*`, check for corresponding docs in `docs/ref/`

### Step 4: Validate Completeness

- Verify you have made changes to at least three types of files: source code, tests, and documentation
- Check that all call sites are updated if you modified function signatures
- Ensure test names clearly describe what they're testing

## Patterns to Follow

- Place tests in parallel directory structures: `django/db/models/lookups.py` → `tests/lookup/tests.py`
- Match existing test patterns in the file: assertion styles, fixture usage, class organization
- Keep test methods concise and focused on the specific bug being fixed
- For database features, ensure tests implicitly exercise all backend code paths

## Anti-patterns to Avoid

- Never create standalone test scripts like `test_fix.py` in the repository root
- Don't add verbose docstrings to tests if existing tests in the file lack them
- Avoid over-engineering: don't add features, extra validation, or refactor beyond the fix
- Don't skip documentation updates - bug fixes without release notes are incomplete
- Never make cosmetic changes (whitespace, quotes, comments) unrelated to the fix
```

### Skill 2: Django ORM Lookup Implementation

```markdown
---
name: django-orm-lookup
description: Specialized guidance for implementing or fixing Django ORM lookups and field transforms. Use when implementing __in, __exact, or other lookups for fields like JSONField, or when fixing query generation bugs.
---

# Django ORM Lookup Implementation

## Overview

This skill helps implement or fix Django ORM lookups with proper cross-module integration and backend-specific handling.

## Instructions

### Step 1: Explore Both Field and Core Lookup Modules

- Read the field-specific module (e.g., `django/db/models/fields/json.py`)
- ALWAYS also check `django/db/models/lookups.py` for base lookup classes that may need updates
- Search for similar existing lookups using `Grep`: `class.*LookupName.*lookups.` pattern
- Understand how `FieldGetDbPrepValueIterableMixin` handles expressions vs literals

### Step 2: Prefer Delegation Over Duplication

- When making a lookup behave like another lookup (e.g., "__iexact=None behave like __exact=None"), use delegation
- Create an instance of the target lookup class and call its methods instead of reimplementing
- Never duplicate database-specific SQL generation (`as_sqlite`, `as_oracle`, `as_postgresql`)
- Use `get_lookup()` to retrieve and delegate to existing lookup classes
- Use vendor-specific method delegation: `getattr(lookup, f"as_{vendor}", lookup.as_sql)`

### Step 3: Handle Backend-Specific Behavior

- For MySQL/Oracle/PostgreSQL/SQLite differences, check existing backend-specific methods in the lookup class
- When adding mixins like `ProcessJSONLHSMixin`, ensure they properly serialize values for backends without native JSON support
- In `resolve_expression_parameter`, use defensive attribute access: check `hasattr(param, 'value')` before accessing
- Handle both `isinstance(param, expressions.Value)` AND `hasattr(param, 'as_sql')` cases

### Step 4: Comprehensive Test Coverage

- Test all variations: plain values, F() expressions, Value() wrapped expressions, mixed lists
- For JSON fields, test edge cases: JSONNull(), empty collections, nested key transforms
- Write tests that exercise all backend code paths (MySQL, Oracle, SQLite, PostgreSQL)
- Add tests to existing test files in `tests/lookup/tests.py` or similar

### Step 5: Query Component Comparisons

- When comparing ORDER BY vs GROUP BY or other query clauses, resolve expressions on a cloned query
- Never compare unresolved field name strings with resolved expression objects
- Use `F().resolve_expression()` or similar to normalize both sides before set operations
- Handle raw SQL cases (e.g., `extra(order_by=...)`) explicitly with early checks

## Patterns to Follow

- Place lookup classes in the same module as the field they support
- Register lookups using `@Field.register_lookup` decorator
- Follow existing patterns for `as_sql()` methods: return (sql, params) tuples
- For complex lookups, extract decision logic into properties/methods rather than inline conditionals

## Anti-patterns to Avoid

- Never implement database-specific SQL generation from scratch when delegation is possible
- Don't assume param type uniformity - use explicit `isinstance()` and `hasattr()` guards
- Avoid modifying only the field module - ORM features require coordination with base lookup system
- Don't write minimal "happy path" tests - ORM features need comprehensive edge case coverage
```

### Skill 3: Django Test Integration

```markdown
---
name: django-test-integration
description: Guidance for adding tests to Django's existing test suite with proper file placement, pattern matching, and integration conventions. Use when adding test coverage for bug fixes or new features.
---

# Django Test Integration

## Overview

This skill ensures tests are properly integrated into Django's existing test structure with correct patterns and organization.

## Instructions

### Step 1: Locate the Correct Test File

- Use `Grep` to find existing test files for the module: search for test files mentioning the module name
- Place tests in parallel directory structures: `django/contrib/admin/options.py` → `tests/admin_scripts/tests.py`
- For database backends: `django/db/backends/sqlite3/features.py` → `tests/backends/sqlite/test_features.py`
- NEVER create new test files when existing files cover the component
- NEVER create standalone test scripts in repository root (like `test_fix.py`)

### Step 2: Match Existing Test Patterns

- Read the existing test file before writing new tests
- Match assertion styles: if existing tests use `assertEqual`, don't use `assertIs` without reason
- Match fixture patterns: if tests use `self.create_test_model()`, don't use direct ORM calls
- Match test method naming: follow the `test_<specific_behavior>` convention used in the file
- Check for test registration patterns (e.g., `register_tests()` functions) and follow them

### Step 3: Create Focused Test Cases

- Test the specific bug or feature being fixed - avoid testing general functionality already covered
- Write minimal reproduction cases that isolate the issue
- For bug fixes, the test should fail before the fix and pass after
- One focused test is better than multiple tests covering tangential scenarios

### Step 4: Test Coverage Strategy

- Match the coverage level of existing tests in the same file
- For crash fixes: test the exact code path that previously failed
- For ORM features: test plain values, expressions, and combinations
- For async features: test all combinations of sync/async handlers and method variants
- For validation: test both valid and invalid inputs with appropriate error checking

### Step 5: Test Data and Assertions

- Use `bulk_create()` for test setup when creating multiple objects
- Compare operations against independent computations, not hardcoded values
- Example: `qs.count() == len(list(qs))` not `qs.count() == 5`
- This makes tests resilient to test data changes

## Patterns to Follow

- Use existing test models from `tests/*/models.py` when possible
- For new test models, add them to existing model files, not new files
- Use `@skipUnless`, `@skipIf` decorators for database-specific or version-specific tests
- Place test utilities in the same file or import from established test utility modules

## Anti-patterns to Avoid

- Never create `test_*.py` files in the repository root for permanent test coverage
- Don't create new test files when `tests/<component>/tests.py` exists
- Avoid verbose test docstrings when test names and assertions are self-explanatory
- Don't add comprehensive test suites for one-line bug fixes - match the scope
- Never use hardcoded expected values that assume specific database state
- Don't create standalone demonstration scripts alongside test suite additions
```

---

## Key Insights from Analysis

- **Test Coverage is Non-Negotiable**: Claude consistently omitted test coverage across 10+ sessions. Tests were missing for async signal context sharing, DecimalField system checks, last_executed_query fallback, In lookup crashes, and more. (From: "Fixed #36714 -- Fixed context sharing for signals", "Fixed #36112 -- Added fallback in last_executed_query() on Oracle and PostgreSQL", "Fixed #36787 -- Fixed crash in In lookups with mixed expressions and strings")

- **Documentation Updates Are Required**: Release notes in `docs/releases/*.txt` were omitted in 8+ sessions despite bug fixes with ticket numbers. Django requires these for every user-facing change. (From: "Fixed #36796 -- Handled lazy routes correctly in RoutePattern.match()", "Fixed #36810 -- Avoided __repr__ recursion in SimpleLazyObject", "Fixed #36800 -- Restored ManyToManyField renaming in BaseDatabaseSchemaEditor.alter_field()")

- **Prefer Delegation Over Duplication**: Claude reimplemented 54 lines of database-specific SQL generation for KeyTransformIExact instead of delegating to KeyTransformExact. The human solution used just 12 lines by creating and calling the existing lookup. (From: "Fixed #36508 -- Interpreted __iexact=None on KeyTransforms as __exact=None")

- **Root Cause Over Symptoms**: Claude added defensive guards in SimpleLazyObject.__repr__ but didn't refactor LazyNonce to eliminate the bound method self-reference causing the bug. The human fixed both the library code and the architectural issue. (From: "Fixed #36810 -- Avoided __repr__ recursion in SimpleLazyObject")

- **Minimal Changes Beat Over-Engineering**: Claude added 20+ line detection blocks and complex resolution logic for M2M migration autodetection. The human made a 3-line conditional adjustment to existing logic that achieved the same result. (From: "Fixed #36791 -- Made MigrationAutodetector recreate through table when m2m target model changes")

- **Test File Organization Matters**: Claude created standalone test scripts in repository root across 6+ sessions. Django tests belong in `tests/` directories with existing test files. (From: "Fixed #36818 -- Ensured SQLite connection before accessing max_query_params", "Fixed #36786 -- Fixed XML serialization of None values in natural keys", "Fixed #36376 -- Fixed color suppression in argparse help on Python 3.14+")

- **Cross-Module Integration for ORM**: Claude missed that fixing JSONField __in lookup required changes to both `django/db/models/fields/json.py` AND `django/db/models/lookups.py`. ORM features require coordination between field definitions and base lookup system. (From: "Fixed #36689 -- Fixed top-level JSONField __in lookup failures on MySQL and Oracle")
