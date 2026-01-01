# Coding Agent Repo Report

- **Repository**: redis/redis
- **Sessions Analyzed**: 17

---

## Synthesized CLAUDE.md / AGENTS.md

```markdown
# Redis Codebase Guide for AI Agents

## Comprehensive Feature Implementation

- When adding resource tracking features (memory, CPU, I/O), instrument at every mutation point across all affected data structures, not just high-level operations; examine existing patterns for similar features to identify the full scope
- Never use expensive on-demand calculations in hot paths; prefer incremental tracking with delta updates at each mutation site
- For cross-cutting features, search exhaustively for all mutation sites of target data structures using Grep patterns (e.g., `listTypePush`, `hashTypeSet`, `setTypeAdd`, `zsetAdd`)
- Add debug assertion helpers that verify correctness in testing; check existing similar features for instrumentation patterns to replicate
- Resource tracking features require conditional guards at every update site due to performance overhead; see memory tracking patterns with `if (server.memory_tracking_per_slot)`

## Authentication and Security

- When adding optional authentication mechanisms, never reject connections on auth failure; prefer silent fallback to default user with logging via the ACL system (see `src/acl.c:2650`)
- New ACL denial reasons require: (1) constant in server.h ACL_DENIED_* section, (2) case in `aclCommand()` for string mapping, (3) dedicated counter in `aclInfo` struct, (4) INFO stats output line
- Stats counter names should match ACL reason strings: `ACL_INVALID_TLS_CERT_AUTH` → `acl_access_denied_tls_cert`
- For security-sensitive code (ACL, auth, permissions): prefer explicit, minimal scope conditions over reusing broader utility functions; be maximally conservative
- Never assume helper functions like `mustObeyClient()` are appropriate substitutes without verifying their exact scope matches the security requirement

## Configuration Storage Patterns

- TLS-specific config belongs in `server.tls_ctx_config.*`, not top-level `server.*` fields; follow existing patterns where `tls-cert-file` maps to `server.tls_ctx_config.cert_file`
- Module-facing feature state belongs in `server` struct, not in subsystem managers (e.g., `asmManager`)
- Config placement signals intent: placement near fundamental limits (maxclients, cluster settings) suggests core functionality
- When replacing boolean flags with size limits, use `> 0` checks consistently; a size of 0 means "disabled"

## Redis Command Implementation

- When extending command families, study similar command implementations to identify shared parsing infrastructure; prefer extending existing parser functions like `parseExtendedStringArgumentsOrReply()`
- For argument parsing, never write custom parsing loops from scratch; use existing parsers that handle flag validation and mutual exclusivity
- Command definitions in `commands.def` must match the JSON schema; verify key_specs (KSPEC_BS_*, KSPEC_FK_*) match actual command syntax
- When prompts mention specific syntax like "KEYS keyword" or "numkeys parameter", this indicates structured argument format (see ZUNION/ZINTER) rather than flat key-value pairs
- Redis replication requires converting relative expiration times (EX/PX) to absolute timestamps (PXAT) before propagation; see `setCommand()` for rewriteClientCommandArgument patterns

## Parsing and Argument Flexibility

- When a prompt requests "flexible argument ordering" across related commands, look for shared parsing patterns first; prefer extracting a unified parser function over modifying each command individually
- Never implement flexibility for one command family while ignoring closely related commands mentioned in the same context
- For commands with similar argument structures, create a single parameterized parser that handles command-specific validation via flags or enums
- When "any order" is specified, avoid maintaining rigid position requirements; prefer true keyword-based parsing that scans all positions
- Loop-based argument parsing: use `continue` to skip over fully-processed argument blocks; for variable-length groups, calculate and validate total required arguments

## Module API Integration

- When refactoring internal APIs that modules use, check `src/module.c` for how the module API wraps those functions
- Never create *Alloc wrapper functions for module compatibility without checking if modules actually need heap allocation for lifecycle reasons
- Module API tests should demonstrate proper usage patterns that serve as examples for module developers
- When modules need to query system state, add `REDISMODULE_CTX_FLAGS_*` returned by `RM_GetContextFlags()` rather than creating dedicated query APIs
- Features that prevent operations need guards at all entry points: task start, command handlers, job scheduling, and active cycles

## Redis Key Lookup and Lifecycle

- When adding new key lifecycle states (expired, trimmed, etc.), integrate with the `expireIfNeeded()` path in `src/db.c`
- Add new `LOOKUP_*` flags in `src/server.h` and corresponding `REDISMODULE_OPEN_KEY_*` flags for module API consistency
- Return new `keyStatus` enum values rather than creating separate query functions
- Never bypass the unified lookup path; prefer adding flags to `lookupKey()` over creating parallel access mechanisms
- When features control deletion behavior, refactor `*DelIfNeeded()` functions into query functions (`*IsKeyInJob()`) and move deletion logic to callers

## Data Structure and Memory Patterns

- When adding memory tracking or allocation features, examine existing allocation patterns first; search for `zmalloc`, `zrealloc`, `*_malloc_usable` functions
- Redis uses `size_t *usable` output parameters pervasively; thread this parameter through the call chain from high-level operations down to allocations
- Data structure back-pointers for accounting: use patterns like `rax->alloc_size = &s->alloc_size` to update parent structures automatically
- When adding memory accounting to data structures, always check defragmentation code (`src/defrag.c`) which must update accounting after reallocations
- For performance-critical paths, prefer adding cached/derived fields over refactoring data structures with external interface constraints

## Refactoring and Code Quality

- When decoupling modules, eliminate old APIs completely rather than wrapping them with compatibility shims
- Remove obsolete struct definitions and allocations entirely; don't just comment them out
- When replacing duplicated code blocks (>10 lines appearing 2+ times), extract a helper function even if not explicitly requested
- For multi-file refactoring tasks (e.g., "hashes, lists, sets, and kvstores"), search exhaustively for ALL files using each type before implementing; use Grep with appropriate patterns
- When changing cleanup functions (Release → Reset), audit all early return/goto paths to ensure cleanup still happens at all exit points

## Performance Optimization

- When optimizing hot paths, prefer adding cached/derived fields over refactoring data structures; dual representation (raw + decoded) is acceptable for fast access
- Never remove pre-computed data used by external APIs; preserve them and add companion fields for fast access rather than refactoring
- For byte-swapping or endian conversion, check for compiler builtin alternatives (`__builtin_bswap64`) before using generic functions
- Adding redundant fields for fast access (cached/decoded values) is preferable to clean refactoring when hot path performance is the goal
- Performance-critical changes should examine both the hot path AND the primitives it uses

## SIMD and Vectorization

- When adding SIMD optimizations, preserve the original function structure and add SIMD paths as parallel implementations rather than refactoring scalar code into separate helpers
- Use preprocessor-based conditional compilation with compile-time feature detection macros for CPU dispatch rather than runtime static variables
- Place SIMD function prototypes in the existing prototypes section rather than defining everything inline
- For branchless comparisons, prefer simple macro definitions (`#define MAX(a,b) ((a)>(b)?(a):(b))`) over manual bit manipulation
- When porting x86 SIMD to ARM NEON, maintain the same data flow and chunking strategy; use true vector operations throughout

## Stream and Time-Based Features

- When adding features that query by time/age/priority, consider if existing data structures support efficient queries or if auxiliary indexes are needed
- Never implement linear scans (O(N)) for operations that may run frequently on large collections; prefer adding sorted indexes (radix trees, skip lists)
- Commands that change delivery semantics require updates across: command definitions, JSON schemas, RDB persistence, replication, defragmentation, and event loop hooks
- Blocking commands that wait for time-based conditions require database-level tracking structures and periodic timeout checks in `blockedBeforeSleep()`
- For multi-client coordination on same keys, store minimum/earliest timeout values in shared dictionaries

## Protocol and Replication

- When implementing distributed system optimizations, prefer explicit capability negotiation over implicit detection based on capabilities
- Let clients request what they need (push model), rather than having the server detect and decide (pull model)
- Distinguish between capability flags (what a peer can do) and request flags (what a peer wants now); never use `SLAVE_CAPA_*` bits to control per-request behavior
- For Redis RDB operations: configuration changes that affect child behavior must happen in the child after `redisFork()` returns 0, not in parent
- When adding new REPLCONF options, make them non-critical: log and continue if older versions don't understand them

## Test Coverage

- Always add test cases when fixing bugs, especially for security or data-loading issues
- Redis tests show comprehensive patterns: basic functionality, edge cases, replication, blocking, error cases, and cross-feature interactions
- Flexible parsing requires testing: traditional order, reversed order, keyword-like field names, numeric field names, and multiple keyword combinations
- For claiming/ownership features, test: delivery count updates, ownership transfer, deleted entries, timeout thresholds, blocking semantics, replication propagation
- Include argument validation tests for all new parameters (non-integer, negative, boundary values, position variations)

## Callback Structures and Abstraction

- When introducing callback structures (like kvstoreType), keep them minimal—only add callbacks that are actually used
- Don't add accessor functions if direct member access is the existing pattern
- Avoid userdata fields in callback structures unless actively used; prefer storing context in the main struct
- When adding callback-based refactorings, trust the new abstraction—if metadata should always exist, use helper functions sparingly rather than adding null checks everywhere

## CI/CD and Test Integration

- When adding new CI jobs, examine existing job definitions to match naming conventions (e.g., 'test-X' not 'test-X-module')
- Before creating test files, search for existing tests of the same type to discover path conventions
- When wrapping external test suites, use open pipe patterns that stream output in real-time rather than capturing with exec
- Ensure wrapped test suites propagate failure exit codes so CI jobs can detect failures correctly
- Test path arguments often follow conventions that differ from filesystem paths; validate by searching workflow files

## Complex Tasks and Planning

- For tasks involving multiple subsystems (build system, dependencies, core functionality), use the Task tool with subagent_type='Plan' before making changes
- When a task involves >3 major components, create a TodoWrite checklist and work through items systematically
- If a prompt requires implementing features in an unfamiliar area, use the Task tool with subagent_type='Explore' to understand existing patterns first
- Never freeze or produce no output when uncertain; prefer using AskUserQuestion to clarify or requesting to explore the codebase
- When analyzing PRs, count modified files and changed lines to assess scope—20+ files with 3000+ lines indicates architectural refactoring, not feature addition
```

---

## Suggested Skills

### Skill 1: Redis Memory Tracking Feature

```markdown
---
name: redis-memory-tracking
description: Use when implementing memory accounting, per-slot tracking, resource monitoring, or instrumentation features in Redis. Helps ensure comprehensive mutation-point coverage and incremental tracking patterns.
---

## Overview

This skill provides guidance for implementing memory tracking and resource accounting features in Redis, ensuring comprehensive coverage across all data structures and mutation points.

## Instructions

When implementing memory or resource tracking features:

1. **Identify all mutation points**: Use Grep to search for patterns like `listTypePush`, `hashTypeSet`, `setTypeAdd`, `zsetAdd`, `streamAppendItem` across the entire codebase
2. **Never use on-demand calculations in hot paths**: Replace expensive `kvobjComputeSize()` calls with incremental delta tracking
3. **Add type-specific allocation functions**: Create helpers like `listTypeAllocSize`, `hashTypeAllocSize` for each data structure type
4. **Check existing similar features**: Search for patterns like `updateKeysizesHist` to identify instrumentation approaches
5. **Review all data structure files**: Examine src/t_list.c, src/t_hash.c, src/t_set.c, src/t_zset.c, src/t_stream.c, src/module.c for all modification sites

## Patterns to Follow

- Add conditional guards at every update site: `if (server.memory_tracking_per_slot)` due to performance overhead
- Thread `size_t *usable` parameters through allocation chains from high-level operations to `zmalloc_usable`/`zrealloc_usable` calls
- Use data structure back-pointers: `rax->alloc_size = &stream->alloc_size` to automatically update parent structures
- Handle deallocation tracking in destructors: see `dictDestructorKV` and `kvstoreTrackDeallocation` patterns
- Add `oldsize`/`newsize` delta calculations at each mutation wrapped with conditional checks
- Check defragmentation code in `src/defrag.c`—after reallocations, back-pointers must be updated
- Add debug assertion helpers like `dbgAssertAllocSizePerSlot` for testing correctness
- Allocation size functions must account for all overhead: headers, padding, null terminators (see `sdsAllocSize()` in `src/sds.h`)

## Anti-patterns to Avoid

- Don't add tracking only to high-level DB operations (dbAddRDBLoad, dbSetValue, dbGenericDelete)—this misses intermediate size changes
- Don't compute sizes on-demand in hot paths—prefer incremental tracking
- Don't ignore encoding conversions, lazy expiration, or defragmentation paths that change sizes outside normal mutations
- Don't assume high-level operations capture all size changes—data structure encoding conversions change sizes independently
- Don't add tracking without conditional compilation guards—overhead matters in production
```

### Skill 2: Redis Command Argument Parser

```markdown
---
name: redis-command-parsing
description: Use when implementing new Redis commands or adding flexible argument parsing, especially for commands with multiple optional keywords (EX, NX, KEYS, etc.) that can appear in any order. Helps create unified parsers and avoid rigid positional requirements.
---

## Overview

This skill guides implementation of Redis command parsing, especially for commands requiring flexible keyword-based argument ordering and proper replication handling.

## Instructions

When implementing or extending Redis command parsing:

1. **Search for similar command patterns**: Use Grep to find commands with similar argument structures (e.g., `ZADD`, `SET`, `ZUNION`)
2. **Identify shared parsing infrastructure**: Look for `parseExtendedStringArgumentsOrReply()` or similar parsers that handle keyword validation
3. **Check command family relationships**: If extending HEXPIRE, also check HSETEX, HGETEX for shared parsing opportunities
4. **Examine key_specs in command definitions**: Match KSPEC_BS_* (begin_search) and KSPEC_FK_* (find_keys) to your command syntax
5. **Review replication requirements**: Check if similar commands use `rewriteClientCommandArgument` or `replaceClientCommandVector`

## Patterns to Follow

- Prefer extracting unified parser functions (e.g., `parseHashCommandArgs`) over modifying each command individually
- Create parameterized parsers that handle command-specific validation via flags or enums (e.g., `HASH_CMD_HGETEX`, `HASH_CMD_HSETEX`)
- Implement true keyword-based parsing by scanning all positions, not just specific indices
- Use loop continuation to skip parsed argument blocks: `i = firstFieldPos + fieldCount - 1; continue`
- For variable-length groups (FIELDS + numfields + field list), validate: `firstFieldPos + (fieldCount * argsPerField) <= argc`
- When command types require different argument counts per field (HGETEX=1, HSETEX=2), parameterize with `args_per_field`
- Convert relative expiration times (EX/PX) to absolute timestamps (PXAT) before replication using `rewriteClientCommandArgument`
- For KEYS keyword syntax, use `KSPEC_BS_KEYWORD` with `keyword="KEYS"` and `KSPEC_FK_KEYNUM` for key location
- Add overflow protection for numkeys values and validate the KEYS keyword is present
- Build canonical command representations for replication rather than inline rewriting

## Anti-patterns to Avoid

- Don't implement flexibility for one command family while ignoring related commands in the same feature area
- Don't maintain rigid position requirements when "any order" is specified (e.g., "time must be at position 2")
- Don't write custom parsing loops from scratch—extend existing parsers
- Don't create dedicated parsers for each command variant—parameterize shared logic
- Don't skip replication logic when refactoring parsers—migrate existing propagation to the new argument structure
- Don't use nested code blocks for traditional vs new syntax—prefer unified handling with backward compatibility tests
- Don't forget to test: traditional order, reversed order, keyword-like field names ("EX", "NX"), numeric field names, field count mismatches
```

### Skill 3: Redis Security and ACL

```markdown
---
name: redis-acl-security
description: Use when implementing authentication mechanisms, ACL features, permission checks, or security-sensitive validation. Ensures minimal scope, proper fallback behavior, and comprehensive logging.
---

## Overview

This skill provides guidance for implementing security-sensitive features in Redis, particularly authentication fallback patterns and ACL integration.

## Instructions

When implementing authentication or ACL features:

1. **Review existing ACL constants**: Search `src/server.h` for `ACL_DENIED_*` patterns to understand existing denial reasons
2. **Examine ACL logging patterns**: Check `addACLLogEntry()` usage in `src/acl.c` to understand proper context passing
3. **Verify security helper functions**: Before using functions like `mustObeyClient()`, grep for all call sites to understand exact scope
4. **Check INFO stats integration**: Find existing ACL counters in `src/server.c` INFO command output around line 5922
5. **Study authentication flow**: Review `networking.c` client acceptance and authentication handler patterns

## Patterns to Follow

- Make optional authentication mechanisms opportunistic: extract username → lookup user → authenticate if valid → otherwise connect as default user
- Log authentication failures via ACL system with `addACLLogEntry()` using appropriate reason constant, not generic AUTH failures
- For each new ACL denial reason: (1) add constant to `src/server.h` ACL_DENIED_* section, (2) add case in `aclCommand()` for string mapping, (3) add counter to `aclInfo` struct, (4) add INFO stats output line
- Match stats counter names to ACL reason strings: `ACL_INVALID_TLS_CERT_AUTH` becomes `acl_access_denied_tls_cert`
- Use explicit, minimal scope conditions: `if (server.loading && c->id == CLIENT_ID_AOF)` rather than `if (mustObeyClient(c))`
- Never skip validation for broader client types than the specific bug requires
- For TLS cert auth: extract field → check if enabled → authenticate → silent fallback on failure
- Test both non-existent and disabled users for auth features
- Verify fallback behavior: failed cert auth → still connected as default → can AUTH with password afterward

## Anti-patterns to Avoid

- Don't reject connections when optional authentication fails—prefer silent fallback with logging
- Don't treat certificate authentication as a gate—make it an opportunistic upgrade
- Don't use helper functions like `mustObeyClient()` in security contexts without verifying exact scope matches the requirement
- Don't hardcode single certificate field extraction—prefer generic helper functions like `getCertFieldByName(cert, "CN", out, outlen)`
- Don't add fields to `client` struct for transient authentication data—use local variables in handler functions
- Don't assume helper functions are appropriate security substitutes—be maximally conservative
- Don't store redundant client state—certificate usernames are only needed during `clientAcceptHandler()`
- Don't skip ACL LOG inspection and INFO stats counter verification in tests
```

---

## Key Insights from Analysis

- **Memory Tracking Requires Comprehensive Instrumentation**: Claude's implementations consistently attempted high-level, sampling-based approaches when Redis required low-level, per-allocation tracking. The human added tracking at 30+ mutation points across lists, hashes, sets, streams, and modules, while Claude focused on 3-4 high-level operations. (From: "Add per slot memory accounting", "Add per key memory accounting")

- **Authentication Should Use Fallback, Not Gates**: Claude rejected TLS certificate authentication failures as hard errors, while the human implementation allowed clients with invalid certificates to connect as default users with ACL logging. This reveals a pattern where Claude treats new auth mechanisms as strict requirements rather than opportunistic enhancements. (From: "Add TLS certificate-based automatic client authentication")

- **Flexible Parsing Requires Unified Solutions**: When implementing flexible argument ordering for hash field expiration commands, Claude modified only the HEXPIRE family while the human created unified parsers covering HSETEX, HGETEX, and HEXPIRE, plus added PERSIST keyword support and proper replication rewriting. Claude's implementation still required expiration time at position 2, missing true "any order" flexibility. (From: "Fix the flexibility of argument positions in the Redis API's")

- **Security Fixes Need Minimal Scope**: For the AOF loading ACL bug, Claude used `mustObeyClient()` which skips ACL for multiple privileged client types, while the human used explicit `server.loading && c->id == CLIENT_ID_AOF` to target exactly the problematic scenario. This pattern shows Claude reaching for utility functions in security contexts where explicit conditions are safer. (From: "Fixes an issue where EXEC checks ACL during AOF loading")

- **Iterator Refactoring Requires Exhaustive Search**: Claude partially implemented stack allocation for list, set, and hash iterators but completely missed kvstore iterators affecting 8 files, and missed error path cleanup with new goto labels. The human's comprehensive approach touched 24 files after exhaustive grep searches. (From: "Avoid allocation when iterating over hashes, lists, sets and kvstores")

- **Performance Optimization Needs Multiple Layers**: For stream ID comparison optimization, Claude created cleaner structs but missed the low-level endian conversion optimization using `__builtin_bswap64`. The human added both cached decoded fields AND compiler builtin optimizations, understanding that hot path work requires attention to algorithmic and hardware layers. (From: "Optimize stream ID comparison and endian conversion hot paths")

- **Protocol Design Favors Explicit Negotiation**: Claude implemented auto-detection of diskless replication capabilities to disable compression, while the human added explicit REPLCONF negotiation with `rdb-no-compress` requests and per-replica control. Claude's approach couldn't handle mixed replica scenarios and incorrectly tried to modify config in the parent process after fork. (From: "Disable RDB compression when diskless replication is used")