# CANONICAL_PRODUCT_INTENT.md

> Canonical product specification for the BigAGI Context Management System.
>
> This file defines the **desired target behavior** of the system.
> It is the primary product-truth document for autonomous implementation, verification, and refactoring work.
>
> If there is any conflict between:
> - current code,
> - existing markdown documentation,
> - intermediate implementation notes,
> - historical reports,
>
> and this file,
>
> then:
> - current code/docs represent **implementation reality**,
> - this file represents **target product truth**,
> - the difference must be documented explicitly as a gap.
>
> `CLAUDE.md` is repository/development context.
> `CANONICAL_PRODUCT_INTENT.md` is product intent.
>
> ---
>
> **Status:** CANONICAL  
> **Scope:** Product behavior and architecture intent  
> **Priority:** Highest product-level reference  
> **Location:** `/context-management/CANONICAL_PRODUCT_INTENT.md`

---

# 1. PRODUCT MISSION

The system exists to solve a real user problem:

When using BigAGI for long, complex scientific and engineering work, context management becomes an excessive manual burden.
The user should not have to constantly decide:
- what to trim,
- what to summarize,
- what to keep raw,
- what to move out of context,
- what can be safely forgotten,
- how to preserve room for further deep reasoning.

The product must become an **intelligent context and memory management system** for long-running LLM-based work.

It must support:
1. **smart forgetting** — through controlled surgical compression;
2. **smart remembering** — through persistent file-based project memory;
3. **reversible state management** — through rollback and preservation of originals;
4. **high-quality reasoning continuity** — the system must help deep work, not degrade it.

---

# 2. WHAT THE PRODUCT IS NOT

The system is **not**:
- a naive “summarize old chat” feature;
- a whole-chat compression button;
- a simple chronological truncator;
- a pure archival system detached from current reasoning;
- a cosmetic token-saving gadget.

The system must preserve the user's ability to do serious work with LLMs over long time horizons.

---

# 3. PRIMARY PRODUCT MODEL

The context management product is based on **three canonical categories** only.

## 3.1 Category A — System
This is the system-layer of the project.

It includes:
- the effective system prompt;
- persistent system-level instructions;
- project-level global rules;
- relevant content from personas if personas influence system behavior;
- any other content that semantically acts as the system layer.

### Requirements
- must never be auto-compressed;
- must always be included in context budget calculations;
- may change rarely, but changes must be reflected in quota calculations;
- should be treated as a protected layer.

---

## 3.2 Category B — Internet
This is the research/reference layer.

It includes:
- scientific articles;
- excerpts from books;
- web research materials;
- curated reference texts;
- imported external knowledge used for the current project.

### Requirements
- must be managed separately from Dialogue;
- must have a user-configurable maximum size;
- must be compressible;
- must be compressed before Dialogue when Internet itself is the overflowing category.

---

## 3.3 Category C — Dialogue
This is the general conversation layer.

It includes:
- normal user/assistant exchange;
- project conversation history;
- attached materials not explicitly placed into Internet;
- standard working chat context.

### Requirements
- must be compressible;
- must be tracked separately from System and Internet;
- must have a **dynamic effective quota**, not only a static nominal quota.

---

# 4. UI MODEL OF THE PRODUCT

The intended product UI includes **two dedicated windows above the regular chat**.

## 4.1 System Window
A dedicated editable area for system-level content.

### Requirements
- only content from this area belongs to the System category;
- this content must not be compressed;
- personas must be treated as part of the effective system layer when relevant.

---

## 4.2 Internet Window
A dedicated editable/importable area for Internet/research materials.

### Requirements
- this window contains research/reference materials;
- this content belongs to the Internet category;
- it has its own quota and compression behavior;
- user must be able to add large texts and research materials here.

---

## 4.3 Dialogue Area
The normal BigAGI chat remains below the two windows.

### Requirement
All standard chat messages belong to the Dialogue category unless explicitly rerouted by future design.

---

# 5. HARD PRODUCT INVARIANTS

The following are **non-negotiable invariants**.

## 5.1 Only three product categories
The system must operate with:
- System
- Internet
- Dialogue

No uncontrolled proliferation of product categories.

## 5.2 System must not be auto-compressed
No automatic compression of System.

## 5.3 Compression is category-local
When a category exceeds the threshold, only that category is compressed.

## 5.4 Compression trigger
Compression trigger is:

- **90% fill** of the effective category budget

## 5.5 Compression target
Compression target is:

- **75% fill** of that category’s budget

This 75% target supersedes earlier 70% discussions.

## 5.6 Incremental behavior is required
The system must not repeatedly recompute compression from the full raw chat state whenever a new message arrives.

It must support an incremental compressed working state.

## 5.7 Original preservation is required
Compression must be reversible.
The system must preserve enough information to restore original content.

## 5.8 Persistent memory is a first-class product goal
This product is not complete if it only compresses and never remembers.

---

# 6. CONTEXT BUDGET MODEL

The system must work under realistic context-window constraints.

## 6.1 Base assumption
Primary reasoning model context window:
- approximately **200k tokens**

The product must not rely on “just use a larger context window” as the solution.

## 6.2 Reasoning buffer
A dedicated buffer must be reserved for deeper reasoning.

### Default assumption
- about **30k tokens**

### Purpose
- Tree-of-Thought
- deep reasoning
- long-form synthesis
- future advanced reasoning patterns

This buffer is not decorative; it is part of the intended design.

---

## 6.3 Proxy overhead
When using `https://api.kiro.cheap`, the system must account for hidden proxy overhead.

### Canonical assumption
- proxy overhead ≈ **2400 tokens**

The product must include this in available context calculations.

---

## 6.4 Tool description overhead
If the active runtime includes tools (especially memory/file tools), their prompt footprint must be budgeted.

The system must not pretend tools are free.

---

## 6.5 Dynamic Dialogue quota
The effective maximum Dialogue budget must be calculated as:

```text
Dialogue Max =
  Model Context Window
  - Proxy Overhead
  - Tool Descriptions Budget
  - Current System Size
  - Current Internet Size
  - Reasoning Buffer
```

### Example
For a 200k context model:

```text
200000
- 2400 proxy
- 10000 tools
- 2000 system
- 50000 internet
- 30000 reasoning buffer
= 105600 dialogue max
```

This is the intended logic.

---

# 7. FORGETTING ENGINE — PRODUCT INTENT

The forgetting engine is the compression subsystem.

Its purpose is not generic summarization, but **surgical, selective, progressive context reduction**.

---

## 7.1 Compression must be surgical
The system must be able to compress:
- not only the beginning of chat,
- not only the end of chat,
- not only chronological prefixes,
- but any appropriate local blocks inside the target category.

The product intent explicitly rejects simplistic “compress oldest first no matter what” behavior as the core strategy.

---

## 7.2 Compression must be progressive
Compression must happen in local controlled steps.

It is acceptable and desirable to:
- compress a block 4x,
- later re-compress an already compressed block if necessary,
- avoid extreme one-shot destructive compression.

---

## 7.3 Re-compression is allowed
There is no strict conceptual limit on compression levels.

However:
- already compressed regions become information-dense,
- and should generally be avoided by the selector if better candidates exist.

The system should prefer lower-density regions first.

---

## 7.4 No mandatory visible compression tags in context text
The product does not require textual markers like:
- `[Compressed Level 1]`
- `[Compressed Level 2]`

Density may be tracked in metadata rather than in user-visible text.

---

# 8. TWO-AGENT COMPRESSION MODEL

The intended forgetting engine uses at least two logical roles.

## 8.1 Agent 1 — Selector / Planner
Agent 1 decides **what should be compressed**.

### Intended selection priorities
1. compress information that will likely never be needed again;
2. if none exists, compress information not needed for the current active task;
3. avoid dense, critical, or already highly compressed regions if possible.

### Intended properties
- may select multiple blocks;
- may select blocks from any place in the target category;
- must take into account how much space actually needs to be freed;
- should be economically efficient (larger useful blocks are often better than many tiny ones).

### Canonical per-block size limit
Each block selected for compression should fit the compressor’s operational constraints.

Current practical design assumption:
- one selected block for Agent 2 should be at most about **10k tokens**.

---

## 8.2 Agent 2 — Compressor
Agent 2 compresses a selected block while preserving its utility.

### Intended compression behavior
- target about **4x compression** per block;
- preserve critical entities;
- preserve logic;
- preserve local coherence;
- remove fluff, verbosity, dead narrative weight, repeated scaffolding.

### If tradeoff is needed
Preserving information is more important than preserving elegance of wording.

---

# 9. COMPRESSION QUALITY REQUIREMENTS

Compression quality is central to the product.

## 9.1 Entity preservation
The system should preserve critical entities with very high reliability, especially:
- formulas,
- variables,
- numbers,
- scientific constants,
- measurement values,
- technical terms,
- function names,
- API details,
- filenames,
- identifiers,
- architectural decisions,
- constraints and assumptions.

## 9.2 Logic preservation
The system must avoid flattening important causal or inferential structure.

If a block explains:
- why a decision was made,
- why a hypothesis failed,
- what caused a bug,
- what changed a design,
then the compressed version should preserve that logic as much as possible.

## 9.3 Contextual seamlessness
Compressed text should fit back into surrounding context as naturally as possible.

However:
- information preservation is more important than stylistic elegance.

## 9.4 Fluff removal
The system should remove low-value verbal weight such as:
- repetitive scaffolding;
- verbose transition phrases;
- filler reasoning chatter;
- redundant explanatory loops;
- obsolete intermediate logs when their conclusions are already preserved.

---

# 10. PRE-PROCESSING LAYER

Before LLM-based selection and compression, the system should support a pre-processing stage.

## 10.1 Purpose
This stage removes obvious waste algorithmically, without using an LLM.

Examples may include:
- repeated patterns;
- user-specific prompt artifacts;
- boilerplate repetition;
- stable known noise patterns.

## 10.2 MVP allowance
An initial stub implementation is acceptable, but the architectural slot must exist.

This means:
- the pre-processing layer is part of the intended architecture even if the first implementation is minimal.

---

# 11. AGENT 2 CONTEXT POLICY

The compressor should ideally work with as much relevant context as possible.

## 11.1 Preferred behavior
If feasible, Agent 2 should see:
- the full context or the broadest context available,
- while clearly marking the block to compress.

## 11.2 If full context does not fit
The system should use a broad local window around the target block.

This should include:
- the target region;
- surrounding context above and below;
- required system instructions.

The product intent does not support an overly narrow compressor that lacks enough context to preserve local fit.

---

# 12. LARGE-CONTEXT REQUIREMENTS

Large-context support is a required product dimension.

## 12.1 Problem
If the total target context exceeds the selector model’s context window, the system must not simply fail or use a naive truncation trick and call that “support”.

## 12.2 Intended solution direction
The system should support:
- chunking of large contexts into large windows;
- multiple selector passes;
- aggregation of candidate compression regions;
- subsequent compressor execution.

## 12.3 Canonical design direction
An acceptable intended strategy may include:
- chunk sizes around **170k tokens**;
- multiple parallel Agent 1 workers;
- then multiple Agent 2 workers on selected blocks.

Exact implementation details may vary, but the product truth is:

> Large-context support must be real, not marketing.

## 12.4 Important nuance
Chunking must be aware of:
- category semantics,
- task relevance,
- missing target-category chunks,
- the risk that a chunk lacks enough context to judge compressibility well.

Simple slicing is not enough.

---

# 13. INCREMENTAL COMPRESSED STATE

This is one of the most important product requirements.

## 13.1 What is not acceptable
A system that:
- receives a new message,
- reconstructs the full raw history,
- and restarts compression logic from scratch every time

is not aligned with product intent.

## 13.2 What is required
The system should:
- maintain a compressed working state;
- append or integrate new content;
- continue compressing that already-compressed state as needed;
- separately preserve original data for rollback/export.

## 13.3 Edit/delete awareness
The ideal product should eventually handle:
- old message deletion;
- old message editing;
- Internet window edits;
- System layer edits.

If not fully implemented at first, this must remain an explicit requirement and gap, not an ignored concern.

---

# 14. ROLLBACK AND ORIGINAL PRESERVATION

Compression must be reversible.

## 14.1 Required capabilities
The intended product must support:
- rollback of the last compression;
- rollback of all compressions;
- export of current compressed state;
- export of restored/original state.

## 14.2 Original preservation
The system must preserve enough original information and metadata to make these behaviors real.

## 14.3 IndexedDB and local storage
It is acceptable to use:
- browser-side storage,
- IndexedDB,
- local project storage,
- or another suitable storage layer,

as long as the reversibility requirement is satisfied.

---

# 15. REMEMBERING ENGINE — PRODUCT INTENT

Compression alone is not enough.
The product also needs a remembering engine.

---

## 15.1 Core idea
Long-term useful knowledge should not live only inside the transient model context.

Important project knowledge should be stored in project memory files.

---

## 15.2 Canonical memory structure
The intended design includes:
- `CLAUDE.md`
- `MEMORY.md`
- structured topic files
- a project memory tree with limited depth
- load-on-demand behavior

---

## 15.3 `CLAUDE.md`
`CLAUDE.md` acts as a project/system guidance file.

### Intended semantics
- it belongs to the effective system layer;
- it is not to be auto-compressed;
- it should constrain development and agentic behavior.

---

## 15.4 `MEMORY.md`
`MEMORY.md` acts as an index and map of project memory.

### Intended semantics
It should help the system know:
- what matters;
- where detailed knowledge lives;
- what was already learned;
- what architectural gotchas exist.

---

## 15.5 Topic files
Detailed project knowledge should live in topic files.

Examples:
- architecture;
- formulas;
- methods;
- experiments;
- bugs/gotchas;
- validated facts.

---

## 15.6 File splitting
If a memory file grows too large, the intended system may split it logically into multiple files.

The split must preserve knowledge, not destroy it.

---

# 16. `/init` REQUIREMENT

The product should support initialization of persistent project memory from an already large existing chat.

## 16.1 Why
The user may already have a large historical conversation containing critical architectural and scientific information.

Without `/init`, persistent memory would only start from “now”, which is insufficient.

## 16.2 Intended behavior
`/init` should:
- analyze existing chat history;
- identify important topics;
- create or populate memory files;
- create/update `MEMORY.md`;
- avoid losing already-earned project intelligence.

## 16.3 Multi-pass allowance
It is acceptable and expected that `/init` be iterative and multi-pass.

A planner/writer style architecture is acceptable.

---

# 17. BIGAGI-SPECIFIC PRODUCT CONSTRAINTS

The intended product must integrate with BigAGI realities.

## 17.1 Persona handling
Personas must be considered part of the effective system layer if they materially influence model behavior.

## 17.2 Token accounting consistency
Differences between BigAGI-side token accounting and proxy-side token accounting are product-level bugs if they materially affect usability.

The product should strive for consistent accounting, including:
- proxy overhead,
- tool calls and tool responses,
- system-layer contribution,
- hidden prompt overhead.

## 17.3 Browser-side storage reality
Because BigAGI stores chats in browser-managed storage, the intended product must account for:
- persistence;
- exportability;
- project-copy semantics;
- rollback storage behavior.

---

# 18. PROXY LAYER INTENT

A proxy/middleware layer is a valid and preferred implementation direction.

## 18.1 Why proxy is good for this product
A proxy can:
- count tokens;
- detect category overflow;
- orchestrate compression;
- handle custom proxy quirks;
- mediate rollback/export metadata;
- keep context logic out of the core UI where appropriate.

## 18.2 Proxy-specific robustness
The system must tolerate behaviors such as:
- hidden overhead;
- malformed-ish outputs;
- fallback messages like “I need to summarize our conversation…”;
- parser incompatibilities;
- content-encoding anomalies;
- non-standard event sequences.

---

# 19. DEVELOPMENT QUALITY INTENT

The way this system is developed matters.

## 19.1 No “rush all code first”
The intended engineering style is:
1. understand and map;
2. design the next layer;
3. implement one component;
4. test it;
5. document it;
6. move on.

## 19.2 Aggressive self-criticism required
The development process must avoid:
- premature claims of completeness;
- trusting documentation over runtime;
- hand-waving around edge cases;
- optimistic acceptance without real evidence.

## 19.3 Prompt quality matters
Prompts are product components.
They must be:
- tested,
- iterated,
- measured on real data,
- treated as part of the implementation.

---

# 20. CRITICAL EDGE CASES

The intended product must eventually handle, or explicitly account for, the following hard cases:

1. selector input larger than selector context window;
2. proxy returns “I need to summarize our conversation...” instead of a normal API response;
3. malformed structured outputs;
4. repeated re-compression;
5. compressed-state drift;
6. edit/delete after compression;
7. mismatch between BigAGI token estimate and runtime truth;
8. parser/proxy event incompatibilities.

---

# 21. ACCEPTANCE SIGNALS

The product should only be considered close to intended if the following are all true in substance:

- category separation is real;
- System is protected;
- Internet and Dialogue compress correctly;
- trigger 90% and target 75% are real;
- incremental reuse is real;
- rollback is real;
- original preservation is real;
- large-context support is real;
- memory is more than just a dormant MCP server;
- `/init` exists or is honestly recognized as missing;
- proxy anomaly handling is real;
- the UX model is moving toward the intended 3-layer interface.

---

# 22. PRIORITY ORDER FOR FUTURE WORK

If tradeoffs are needed, prioritize in this order:

1. compression core correctness
2. incremental compressed-state correctness
3. rollback/original preservation
4. token accounting correctness
5. proxy robustness
6. large-context correctness
7. proper System/Internet/Dialogue semantics
8. remembering engine integration
9. `/init`
10. UX polish

---

# 23. FINAL PRODUCT STATEMENT

This product is an **LLM working-memory management system** for BigAGI, designed for long scientific and engineering workflows.

It must:
- forget intelligently,
- remember intelligently,
- preserve critical information,
- preserve room for deep reasoning,
- remain reversible,
- and reduce the user's manual burden of context management to near-zero.

This is the canonical intended behavior.
