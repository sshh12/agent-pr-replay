# Coding Agent Repo Report

- **Repository**: pytorch/pytorch
- **Sessions Analyzed**: 10

---

## Synthesized CLAUDE.md / AGENTS.md

```markdown
# Claude Agent Guidelines for pytorch/pytorch

This document provides guidance for AI coding agents working on the PyTorch codebase. Focus on patterns that have caused issues across multiple pull requests.

## Prefer Deletion Over Defensive Programming

- When fixing bugs in cleanup/teardown code, consider whether the cleanup is necessary at all before adding defensive logic
- If a method only contains error-prone resource cleanup, check if callers would work correctly without it
- Empty or stub cleanup methods (especially with only `pass` or docstrings) are often candidates for removal rather than preservation
- Avoid expanding fixes into unrelated files—if the bug is in one module, question whether changes to other modules are actually needed

## Minimal Changes to Conditionals

- When fixing boolean conditions: prefer extending the existing condition with OR/AND clauses over restructuring the entire conditional block
- Preserve existing code structure: if the body of a conditional doesn't need changes, don't nest it further or move it
- Never introduce intermediate variables for conditions when a direct boolean expression suffices; this increases diff size unnecessarily
- For guard clauses or multi-part conditions: add new predicates directly to the condition line rather than creating early-return or nested if-else patterns

## Refactoring vs. Minimal Fixes

- When fixing bugs caused by conceptual misunderstandings (not just typos), trace the incorrect concept through all related code—variable names, helper functions, downstream usage—and refactor comprehensively
- If a fix requires changing what a data structure represents (e.g., "ordered_tensor_names" should actually be "ordered_arg_names"), rename variables and update all callsites to reflect the corrected domain model
- Look for helper functions that encode the old incorrect logic—consider removing them if they're no longer semantically meaningful
- Never patch just the immediate symptom; prefer identifying where the wrong mental model leaked into the codebase and correcting it systematically

## Bug Fixes: Root Cause vs Symptom Patching

- When fixing KeyError or missing key bugs, investigate whether the data structure design is flawed rather than adding defensive lookups or fallback values
- If the same key can represent multiple distinct scenarios (e.g., same resume offset from different entry points), the key structure needs to change to distinguish them; prefer changing dict keys to tuples over adding fallback logic
- Never add try-except or defensive "use offset as-is" fallback logic when the real issue is key collision; prefer redesigning the key to capture all relevant context
- When a fix requires passing additional context through a call chain, trace the full path from call site to usage and update all intermediate functions

## PyTorch Dynamo Integration Patterns

- When adding new runtime state functions (like `_is_in_optimized_module()`), register them in dynamo's tracing infrastructure: add to `torch/_dynamo/trace_rules.py` MANUAL_FUNCTIONS dict as `TorchInGraphFunctionVariable`, and to `torch/_dynamo/variables/torch.py` in both `tracing_state_functions()` and `handle_tracing_state_functions()`
- Never add state-checking functions without trace registration; prefer checking all three integration points (trace_rules, tracing_state_functions, handle_tracing_state_functions)
- Test validation: When fixing graph breaks or compilation issues, always add a test case using `torch.compile(..., fullgraph=True)` to verify no graph breaks occur

## Reference Cycle Cleanup and Error Handling

- When the PR title or prompt mentions "failed" operations (e.g., "failed tracer outputs"), the fix belongs at exception handling sites, not in normal cleanup paths
- Never add cleanup to existing `cleanup()` methods when the problem is specific to error cases; prefer creating targeted cleanup methods called from exception handlers
- For Python 3.14+ memory/GC issues: look for test files with `@unittest.skipIf(sys.version_info >= (3, 14))` decorators—your fix should make these tests pass, so remove those skips
- Breaking reference cycles requires multi-layer approach: preserve references needed for cleanup (add separate fields like `*_for_cleanup`), clear node metadata before erasing nodes (see `torch/fx/graph.py` for node cleanup patterns), and clear tracked objects in related subsystems (e.g., `shape_env.tracked_fakes`)
- When adding cleanup for graph nodes, always use `graph.erase_node()` in reverse order after clearing `node.meta`, never just set `graph = None`

## Cross-Language Feature Implementation

- When enabling platform-specific features (CUDA/ROCm/XPU), check the full stack: Python logic, C++ bindings (`torch/csrc/`), and type stubs (`torch/_C/__init__.pyi.in`)
- If Python code checks `hasattr(props, "property_name")`, verify the property is actually exposed in the corresponding C++ module file (e.g., `torch/csrc/cuda/Module.cpp`)
- Never assume Python properties exist at runtime; trace to `.def_readonly()` or similar bindings in C++ source
- For ROCm/CUDA parity: search for `#if USE_ROCM` or `#if !USE_ROCM` blocks to understand platform-specific exposures

## Test Coverage for Platform Features

- When enabling a feature for a previously-unsupported platform, search for test files with skip decorators (`@skipIfRocm`, `@skipIfXpu`) that may now be removable
- Use Grep to find test files importing or using skip decorators related to the platform being fixed
- If a feature now works on ROCm, tests should instantiate ROCm-specific helper classes (e.g., `ROCmConfigHeuristic`) not just CUDA ones
- Never stop at fixing the implementation; always check if tests need platform-conditional logic or decorator removal

## Test Completeness for Conceptual Fixes

- When fixing bugs caused by misunderstanding an API contract (e.g., what "constexpr" means to an external library), always add a regression test demonstrating the correct behavior
- Search existing tests for patterns that might encode the same incorrect assumption and update them
- For fixes involving external library semantics, write tests that assert on the library's actual behavior (e.g., checking TTIR output), not just that your code runs without error

## Test Organization and Bug Fix Validation

- Bug fixes should include test cases that reproduce the issue; check if the PR description or linked issues contain reproduction cases
- When adding tests for fixes, place them in the appropriate test file based on the feature area (e.g., context manager bugs go in `test_ctx_manager.py`, not `test_repros.py`)
- If existing tests in `test_repros.py` are actually feature-specific, consider moving them to the appropriate test module as part of the fix
- Add one test per distinct failure mode mentioned in the issue

## Thread Safety and Lock Optimization

- When adding mutex protection, check if locks are already held at call sites before adding wrapper methods that acquire locks
- Prefer inlining synchronized code directly in methods that already hold locks over adding mutex-acquiring wrappers called from macros
- Document lock invariants with inline comments (e.g., "We already hold the mutex_ lock here") when making direct unsafe API calls safe through existing synchronization

## API Contract Preservation

- When wrapping external API calls (e.g., NCCL functions), preserve the original return value semantics exactly
- Never change what a function returns when adding thread-safety wrappers; if `ncclCommGetAsyncError` returns `ncclResult_t`, your wrapper must return `ncclResult_t` with the same meaning
- Use output parameters the same way as the original API—don't dereference and return them unless that matches the original contract
- Maintain consistency in how wrappers are passed to macros (e.g., pass shared_ptr wrappers, not raw pointers via `.get()`, if the macro expects wrapper objects)

## Data Structure Key Selection

- When building dictionaries/mappings for external APIs, check the API's expected key format—some APIs expect positional indices as tuples `(i,)`, others expect string names
- If changing from string keys to positional keys, verify all downstream consumers expect the new format

## GitHub Workflow Triggers and Version Pattern Matching

- When modifying workflow triggers with multiple conditions, always identify ALL distinct patterns that need separate matchers; never assume one regex can cover multiple semantic requirements
- For release versioning tasks: "final RC" typically means the actual release tag without -rc suffix (e.g., v1.2.3), not the last -rc build; these require separate tag patterns
- Never remove existing tag patterns without confirming they're truly redundant; adding selective patterns often means augmenting the list, not replacing
```

---

## Suggested Skills

### Skill 1: PyTorch Dynamo State Function Integration

```markdown
---
name: dynamo-state-function
description: Use when adding new runtime state checking functions to PyTorch's dynamo tracing system (e.g., _is_in_optimized_module, _is_compiling). Ensures proper registration in trace_rules.py, variables/torch.py, and test coverage for graph break prevention.
---

# PyTorch Dynamo State Function Integration

## Overview

This skill helps implement new runtime state checking functions in PyTorch's dynamo tracing infrastructure. When adding functions like `_is_in_optimized_module()` or similar state checkers, they must be registered in multiple locations within the dynamo system to prevent graph breaks and ensure proper tracing behavior.

## Instructions

### Step 1: Implement Core State Management

- Create global flag variable (e.g., `_in_optimized_module = False`)
- Implement context manager using `@contextlib.contextmanager` to set/unset the flag
- Create public checker function (e.g., `def _is_in_optimized_module() -> bool:`)
- Place new functions in appropriate module (e.g., `torch/_dynamo/eval_frame.py`)

### Step 2: Register in Trace Rules

Add the checker function to `torch/_dynamo/trace_rules.py`:

- Import the function at the top of the file
- Add entry to `MANUAL_FUNCTIONS` dict: `"torch._dynamo.eval_frame._is_in_optimized_module": TorchInGraphFunctionVariable`
- The `TorchInGraphFunctionVariable` type allows the function to be called during tracing without graph breaks

### Step 3: Register in Torch Variables

Update `torch/_dynamo/variables/torch.py`:

- Add to `tracing_state_functions()` dict: `"_is_in_optimized_module": "_is_in_optimized_module"`
- Implement handling in `handle_tracing_state_functions()` method to return `ConstantVariable.create(value=fn())`

### Step 4: Add Test Coverage

- Create test case using `torch.compile(..., fullgraph=True)` to verify no graph breaks occur
- Test should validate the state function correctly returns different values inside vs outside compiled regions
- Place test in appropriate test file (e.g., `test_dynamic_shapes.py` or `test_ctx_manager.py`)

## Patterns to Follow

- Always register in all three locations: trace_rules.py, tracing_state_functions(), and handle_tracing_state_functions()
- Use thread-local storage if the state needs to be thread-specific
- Name checker functions with underscore prefix to indicate internal API
- Return boolean from checker functions for consistency with existing patterns

## Anti-patterns to Avoid

- Never add state-checking functions without trace registration (causes graph breaks)
- Never skip test validation with fullgraph=True
- Never register only in trace_rules without updating torch.py variables
- Never use module-level state without considering thread safety
```

### Skill 2: PyTorch Platform Feature Parity

```markdown
---
name: pytorch-platform-parity
description: Use when enabling PyTorch features for different hardware platforms (ROCm, XPU, etc.) that already work on CUDA. Ensures complete implementation across Python, C++, type stubs, and test coverage. Use when the task mentions "ROCm", "CUDA parity", "enable for XPU", or platform-specific features.
---

# PyTorch Platform Feature Parity Implementation

## Overview

When enabling PyTorch features for platforms like ROCm or XPU that already work on CUDA, changes span multiple layers: Python logic, C++ bindings, type stubs, and tests. This skill ensures complete cross-platform implementation.

## Instructions

### Step 1: Analyze Python Implementation

- Identify Python code that checks platform-specific properties (e.g., `hasattr(props, "shared_memory_per_block_optin")`)
- Check if alternative property names exist for target platform (e.g., ROCm uses `shared_memory_per_block` instead of `shared_memory_per_block_optin`)
- Update conditional logic to check for both property names using OR conditions

### Step 2: Verify C++ Bindings

Search `torch/csrc/cuda/Module.cpp` (or relevant platform module):

- Look for `#if USE_ROCM` or `#if !USE_ROCM` preprocessor blocks
- Verify properties are exposed using `.def_readonly()` or similar PyBind11 bindings
- Add missing property exposures for target platform within appropriate `#if` blocks
- Ensure property names match what Python code expects

### Step 3: Update Type Stubs

Edit `torch/_C/__init__.pyi.in`:

- Add property declarations to relevant classes (e.g., `class _CudaDeviceProperties`)
- Use platform-conditional comments if property availability differs by platform
- Ensure type hints match C++ binding return types

### Step 4: Update Test Coverage

Search for platform skip decorators:

- Use Grep to find `@skipIfRocm`, `@skipIfXpu`, etc. in test files
- Evaluate if skipped tests should now pass with your changes
- Remove skip decorators or add platform-specific test branches
- For heuristic/config tests, instantiate platform-specific helper classes (e.g., both `CUDAConfigHeuristic` and `ROCmConfigHeuristic`)

### Step 5: Search for Feature-Specific Skip Patterns

- Use Grep to search test directories for the feature name combined with skip decorators
- Check if any tests explicitly document platform limitations in comments
- Update or remove these after verifying feature now works

## Patterns to Follow

- Check all four layers: Python logic, C++ bindings, type stubs, tests
- Use `hasattr()` checks in Python for properties that may not exist on all platforms
- Match existing C++ binding patterns (use same `.def_readonly()` style as other properties)
- Add platform-specific test helper instantiation rather than removing all platform awareness

## Anti-patterns to Avoid

- Never assume Python properties exist without verifying C++ exposes them
- Never stop at fixing Python logic without checking if tests need decorator removal
- Never add properties to type stubs without corresponding C++ bindings
- Never use different property access patterns (e.g., `.get()`) than existing code
```

### Skill 3: PyTorch Bug Root Cause Analysis

```markdown
---
name: pytorch-bug-root-cause
description: Use when fixing bugs in PyTorch that involve data structure design issues, key collisions, or reference cycles. Use when the prompt mentions KeyError, graph breaks, reference cycles, memory leaks, or cleanup issues. Helps distinguish between root causes requiring architectural changes vs. symptoms that need defensive patching.
---

# PyTorch Bug Root Cause Analysis and Fix Strategy

## Overview

Many PyTorch bugs stem from architectural issues rather than simple logic errors. This skill helps identify whether a bug requires data structure redesign, reference cycle breaking, or defensive patching.

## Instructions

### Step 1: Classify the Bug Type

Determine bug category:

- **Key collision**: KeyError that occurs when same key represents different scenarios (requires key structure change)
- **Reference cycle**: Memory not released, GC issues, Python 3.14+ test failures (requires explicit cleanup)
- **Conceptual mismatch**: Feature misunderstood (e.g., Triton constexpr semantics) (requires refactoring)
- **Unnecessary code**: Cleanup methods causing issues (requires deletion, not fixing)

### Step 2: For KeyError and Dictionary Issues

Investigate dictionary key design:

- Check if single value keys (e.g., `offset`) can represent multiple distinct scenarios
- Look for comments mentioning "resume", "initial", "entry point" that suggest multiple contexts
- If collision possible, change key to tuple capturing all relevant context: `(init_offset, resume_offset)`
- Thread new context through entire call chain: update all callers to pass additional parameters
- Update dictionary access sites to use new tuple keys

Never add defensive fallback logic (try-except, `.get()` with defaults) when root cause is key collision.

### Step 3: For Reference Cycles and Cleanup

Identify cleanup requirements:

- For "failed" operations: add cleanup at exception handling sites, not in normal cleanup methods
- Create separate `*_for_cleanup` fields to preserve references needed during error handling
- For graph nodes: call `graph.erase_node()` in reverse order after clearing `node.meta`
- Clear tracked collections in subsystems (e.g., `shape_env.tracked_fakes`)
- Check for Python version skip decorators (`@unittest.skipIf(sys.version_info >= (3, 14))`) and remove if fix resolves GC issues

### Step 4: For Conceptual Mismatches

Trace incorrect concept through codebase:

- Identify helper functions encoding wrong logic (consider removing them)
- Rename variables to reflect correct domain model (e.g., `ordered_tensor_names` → `ordered_arg_names`)
- Update all callsites and downstream usage
- Add regression tests asserting on external library behavior (e.g., TTIR output for Triton)
- Search existing tests for patterns encoding same incorrect assumption

### Step 5: For Unnecessary Code

Evaluate if code should exist:

- Check if cleanup/teardown methods are actually needed
- If method only contains error-prone operations with no clear purpose, prefer deletion
- Don't replace buggy cleanup with `pass` statements or defensive wrappers
- Remove entire methods and verify callers work without them

## Patterns to Follow

- Change data structures to prevent problems rather than adding defensive code
- Pass context through call chains when needed for disambiguation
- Create targeted cleanup methods for error cases, not generic cleanup
- Refactor comprehensively when fixing conceptual misunderstandings
- Delete unnecessary code rather than making it "safer"

## Anti-patterns to Avoid

- Never add try-except or `.get()` fallbacks for KeyError without investigating key design
- Never add cleanup to existing `cleanup()` methods when problem is error-specific
- Never keep cleanup methods that serve no purpose
- Never patch symptoms (one file) without tracing root cause through related files
- Never fix implementation without updating tests that encode incorrect assumptions
```

---

## Key Insights from Analysis

- **Prefer deletion over defensive programming**: Claude consistently added defensive error handling and try-finally blocks when the actual fix was to remove unnecessary code entirely. (From: "Avoid closing random file handles in Inductor", "[Resubmit] Fix _split_iteration_ranges handling gt handling for two-dimensional tiling")

- **Root cause analysis over symptom patching**: When fixing KeyError bugs, Claude added fallback logic and defensive lookups instead of recognizing that dictionary key structures needed redesign to prevent collisions. The human solution changed keys from single values to tuples capturing full context. (From: "[dynamo] fix keyerror in resume_execution, fix store attr")

- **Cross-language feature implementation**: When enabling platform-specific features, Claude fixed Python logic but missed C++ bindings, type stubs, and test decorator updates. Platform parity requires checking all four layers: Python, C++ (`torch/csrc/`), type stubs (`.pyi.in`), and test skip decorators. (From: "[ROCm] Enable shared memory based pruning for Triton configs")

- **Dynamo integration requires multi-point registration**: Adding new runtime state checking functions like `_is_in_optimized_module()` requires registration in three places: `torch/_dynamo/trace_rules.py` MANUAL_FUNCTIONS, `variables/torch.py` tracing_state_functions(), and handle_tracing_state_functions(). Claude implemented the function but missed trace registration. (From: "[dynamo][DebugMode] make ModTracker a no-op in compiled regions")

- **Conceptual bugs need comprehensive refactoring**: When fixing bugs caused by misunderstanding external APIs (e.g., Triton constexpr semantics), Claude patched immediate symptoms rather than tracing the incorrect concept through variable names, helper functions, and test assumptions that needed updating. (From: "[Inductor] Fix constants handling for Triton constexpr (triton#8248)")

- **Error-case cleanup belongs at exception sites**: When fixing reference cycles in failed operations, Claude added cleanup to normal cleanup() methods rather than creating targeted cleanup called from exception handlers, missing the need for separate `*_for_cleanup` fields and Python 3.14 test skip removal. (From: "[Py 3.14] Cleanup graphs for failed tracer outputs")

- **Minimal structural changes to conditionals**: When fixing boolean conditions, Claude introduced intermediate variables and restructured control flow instead of simply extending existing conditions with OR clauses, unnecessarily increasing diff size and nesting depth. (From: "[Resubmit] Fix _split_iteration_ranges handling gt handling for two-dimensional tiling")
