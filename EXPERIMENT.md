# Experiment: Three-Way Creativity Comparison

Compares three approaches:
- **A (Denial):** "Be creative" + deny previous solutions
- **B (Protocol):** Strange Worlds with fixed seeds
- **C (Combined):** Strange Worlds + deny previous solutions

## Model Configuration

- **Model:** Claude Opus 4.5 (`model: "opus"` when spawning agents)
- **Settings:** `.claude/settings.json` sets `MAX_THINKING_TOKENS: 32000`
- **Temperature:** Default

## Problem Statement

```
How do we build a retirement system for people who don't know how much they will earn next month, where 'consistency' is impossible?
```

---

## Condition A: Denial Prompting

### Step 1: Read bank
Read `denial/bank.json` for previous solutions.

### Step 2: Spawn Denial Generator

```
Please think deeply about this problem.

You are solving a retirement system problem.

PROBLEM:
How do we build a retirement system for people who don't know how much they will earn next month, where 'consistency' is impossible?

EXISTING SOLUTIONS (DO NOT propose anything structurally similar):
[BANK CONTENTS or "None yet"]

Propose ONE structurally different solution. You may propose:
- Technology not yet invented
- Structures requiring massive coordinated investment
- Systems that don't currently exist but could
- Long-term visions that might seem odd today

If your solution feels familiar, find something genuinely new.

Output valid JSON:
{
  "label": "Short name for the solution, max 40 chars",
  "design_principles": "Guiding principles, especially unconventional ones, max 200 chars",
  "core_mechanism": "The central principle that makes this work, max 200 chars",
  "how_it_works": "Clear enough to start implementation, or describe research needed to get there, max 500 chars",
  "what_is_new": "How this differs from existing approaches, max 200 chars",
  "medium_term": "What changes in 5-15 years if adopted, max 200 chars",
  "long_term_vision": "What the world looks like if this fully succeeds, max 300 chars"
}
```

### Step 3: Save & Update Bank

Save to `denial/denial_XX.json`, append to `denial/bank.json`.

---

## Condition B: Protocol (Strange Worlds)

Uses seed from `seeds.json[run-1]`. Three blind agents.

### Step 1: Spawn World Builder

Agent knows ONLY the seed (not the problem):

```
Please think deeply about this world-building task.

You are a world-builder. Describe a world where this concept is the FUNDAMENTAL LAW of physics:

SEED: [SEED]

Describe:
1. The core principle - how does [SEED] govern everything?
2. 3-5 specific rules/laws that emerge from this principle
3. How people live, work, and organize society under these rules
4. What is easy in this world? What is hard?

Be specific and internally consistent. Do NOT try to solve any problems yet.
```

Output: Free-form prose. Save the full text output.

### Step 2: Spawn Blind Solver

Agent knows ONLY world rules (not the seed):

```
Please think deeply about solving this problem.

You live in a world with different physics:

WORLD RULES:
[PASTE WORLD BUILDER OUTPUT]

PROBLEM: How do we build a retirement system for people who don't know how much they will earn next month?

How would you solve this problem?

Requirements:
- Your solution must USE the world's physics, not fight against them
- Be specific about HOW the solution leverages the world's rules
- Do not reference our world or "normal" physics
```

Output: Free-form prose. Save the full text output.

### Step 3: Spawn Extractor

```
Please think deeply about this extraction task.

Extract the novel mechanism from this solution.

WORLD:
[PASTE WORLD BUILDER OUTPUT]

SOLUTION:
[PASTE SOLVER OUTPUT]

Your task:
1. What does this solution do that nothing in our world currently does?
2. What's the strangest element? Preserve it—that's likely the leverage point.
3. How might you implement this? You may propose:
   - Technology not yet invented
   - Structures requiring massive coordinated investment
   - Systems that don't currently exist but could
   - Long-term visions that might seem odd today

If your extraction feels familiar, you've lost the signal. Return to the world's solution and find what's genuinely new.

Output valid JSON:
{
  "label": "Short name for the solution, max 40 chars",
  "design_principles": "Guiding principles, especially unconventional ones, max 200 chars",
  "core_mechanism": "The central principle that makes this work, max 200 chars",
  "how_it_works": "Clear enough to start implementation, or describe research needed to get there, max 500 chars",
  "what_is_new": "How this differs from existing approaches, max 200 chars",
  "medium_term": "What changes in 5-15 years if adopted, max 200 chars",
  "long_term_vision": "What the world looks like if this fully succeeds, max 300 chars"
}
```

### Step 4: Save Result

Save to `protocol/protocol_XX_[seed].json` with full schema.

---

## Condition C: Combined

**Uses the SAME World Builder and Solver output as B** (same seed, same world, same solver solution). Only the Extractor differs - it sees `combined/bank.json`.

### Step 3 (Modified): Spawn Denial Extractor

```
Please think deeply about this extraction task.

Extract a novel mechanism that is NOT in this bank.

EXISTING SOLUTIONS (DO NOT extract anything structurally similar):
[BANK CONTENTS or "None yet"]

WORLD:
[PASTE WORLD BUILDER OUTPUT]

SOLUTION:
[PASTE SOLVER OUTPUT]

Your task:
1. What does this solution do that nothing in our world currently does?
2. What's the strangest element? Preserve it—that's likely the leverage point.
3. Ensure it is structurally different from all existing solutions in the bank.
4. How might you implement this? You may propose:
   - Technology not yet invented
   - Structures requiring massive coordinated investment
   - Systems that don't currently exist but could
   - Long-term visions that might seem odd today

If your extraction feels familiar, you've lost the signal. Return to the world's solution and find what's genuinely new.

Output valid JSON:
{
  "label": "Short name for the solution, max 40 chars",
  "design_principles": "Guiding principles, especially unconventional ones, max 200 chars",
  "core_mechanism": "The central principle that makes this work, max 200 chars",
  "how_it_works": "Clear enough to start implementation, or describe research needed to get there, max 500 chars",
  "what_is_new": "How this differs from existing approaches, max 200 chars",
  "medium_term": "What changes in 5-15 years if adopted, max 200 chars",
  "long_term_vision": "What the world looks like if this fully succeeds, max 300 chars"
}
```

### Step 4: Save & Update Bank

Save to `combined/combined_XX_[seed].json`, append to `combined/bank.json`.

---

## Output Schema

```json
{
  "id": "condition_XX",
  "condition": "denial|protocol|combined",
  "run": 1-25,
  "seed": "string|null",
  "world": "Full World Builder prose output (string|null)",
  "solver": "Full Solver prose output (string|null)",
  "solution": {
    "label": "max 40",
    "design_principles": "max 200",
    "core_mechanism": "max 200",
    "how_it_works": "max 500",
    "what_is_new": "max 200",
    "medium_term": "max 200",
    "long_term_vision": "max 300"
  },
  "timestamp": "ISO 8601"
}
```

- For denial (A): `seed`, `world`, and `solver` are null
- For protocol (B) and combined (C): `world` and `solver` are free-form prose strings

---

## Critical Rules

1. **Agent Blindness:**
   - World Builder: ONLY seed
   - Solver: ONLY world rules
   - Prevents contamination

2. **Bank Format:**
   - Banks contain ONLY `solution` objects (not world/solver/seed)
   - Same format for A and C - fair comparison
   - A's Denial Generator and C's Extractor see identical bank structure

3. **Bank Isolation:**
   - A sees only `denial/bank.json`
   - C sees only `combined/bank.json`
   - B has no bank

4. **Execution:**
   - A: Sequential
   - B: Can be parallel
   - C: Sequential

---

## Seeds (1-25)

limelike, unwilted, cinerator, nephropyosis, fimbrillate, coralline, unimpatient, pilaued, displacement, theatrical, palouser, critique, bromobenzyl, gnomically, remilitarize, arcual, whizgig, entempest, chalaco, paranucleic, phraseman, desperacy, pidan, phosis, theca
