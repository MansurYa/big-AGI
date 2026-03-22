# MISSION.md

## Task Identity
Autonomous Reality Check against `CANONICAL_PRODUCT_INTENT.md` for BigAGI Context Management System

## Version
3.0 (2026-03-16)

## Primary Objective
Establish ground truth about what currently exists and works, versus what is claimed in documentation.

**NOT** to build new features.
**NOT** to complete the system.
**NOT** to clean documentation as primary focus.

**YES** to prove or disprove the viability of the current core system.

## Primary Source of Truth
`context-management/CANONICAL_PRODUCT_INTENT.md`

## Trust Hierarchy
1. `CANONICAL_PRODUCT_INTENT.md` - target product behavior
2. Actual runtime behavior
3. Actual code paths
4. Newly created tests and artifacts
5. Existing markdown files - LOW TRUST until proven

## What is Allowed
- Run the project
- Create test harnesses
- Write new tests
- Make minimal blocker fixes (documented)
- Use real API without cost limits

## What is Forbidden
- Develop large new features
- Create UI windows
- "Complete the project"
- Clean docs as main focus
- Rewrite architecture
- Ask user questions
- Trust old reports as proof
- Change tuned prompts v0.2 if they're working

## Blocker Fix Policy
If verification requires a fix:
1. Document the original problem
2. Prove the scenario failed before fix
3. Apply minimal fix
4. Retest
5. Mark as "verification blocker fix"

## API Resources
```
ANTHROPIC_BASE_URL="https://api.kiro.cheap"
ANTHROPIC_API_KEY="sk-aw-f157875b77785becb3514fb6ae770e50"
```

No cost limits. Log all usage.

## Final Verdict Options
- `FOUNDATION OK`
- `FOUNDATION SHAKY`
- `FOUNDATION FALSE`

## Mode
Fully autonomous. No user interaction.
