# Strange Worlds Experiment Runner

## Agent Configuration
- **Model:** Always use `model: "opus"` when spawning agents
- **Thinking:** All prompts in EXPERIMENT.md include "think deeply" phrasing
- **Settings:** `.claude/settings.json` sets `MAX_THINKING_TOKENS: 32000`
- **MCP Servers:** DISABLED for this experiment (no understanding-graph, etc.)

When user asks to run/continue the experiment:

## 1. Check Progress

Count files:
- `denial/denial_*.json` → A count
- `protocol/protocol_*.json` → B count
- `combined/combined_*.json` → C count

Report: "Progress: A: X/25, B: Y/25, C: Z/25"

## 2. Run Next - PARALLELIZATION STRATEGY

Each run has dependencies. Execute in this order with maximum parallelization:

```
PHASE 1 (parallel):
├── A: Denial Generator
└── B: World Builder

PHASE 2 (sequential, depends on B World Builder):
└── B: Solver

PHASE 3 (parallel, depends on B Solver):
├── B: Extractor
└── C: Extractor (same world/solver as B)

PHASE 4 (parallel):
├── Save all files
└── Update all banks
```

**In a single Task tool call, spawn multiple agents when they have no dependencies on each other.**

---

## Condition A (Denial)

1. Read `denial/bank.json`
2. Spawn Denial Generator (see EXPERIMENT.md for prompt)
3. Get structured `solution` JSON from agent
4. **Save to file:**
```json
// denial/denial_XX.json
{
  "id": "denial_XX",
  "condition": "denial",
  "run": XX,
  "seed": null,
  "world": null,
  "solver": null,
  "solution": { /* from agent */ },
  "timestamp": "ISO 8601"
}
```
5. Append `solution` to `denial/bank.json`

---

## Condition B (Protocol)

1. Get seed from `seeds.json[count]`
2. Spawn World Builder → capture full text output
3. Spawn Solver (pass world text) → capture full text output
4. Spawn Extractor → get structured `solution` JSON
5. **Save to file:**
```json
// protocol/protocol_XX_[seed].json
{
  "id": "protocol_XX",
  "condition": "protocol",
  "run": XX,
  "seed": "the_seed",
  "world": "full World Builder output...",
  "solver": "full Solver output...",
  "solution": { /* from Extractor */ },
  "timestamp": "ISO 8601"
}
```

---

## Condition C (Combined)

**Uses the SAME World Builder and Solver output as B** - only the Extractor differs:
1. Spawn Extractor with same world + solver from B, BUT also sees `combined/bank.json`
2. Save to `combined/combined_XX_[seed].json` (copy world/solver from B's run file)
3. Append `solution` to `combined/bank.json`

---

## After Each Run

1. Confirm file was written
2. Report updated counts
3. Ask: continue or stop?

---

## Key Rules

- World Builder and Solver: Save full natural text output
- Extractor: Must output structured JSON solution
- Banks only contain `solution` objects (not world/solver)
- Use Write tool to save files after each run
- **DO NOT use understanding-graph or any MCP tools**

See `EXPERIMENT.md` for prompts, `schema.json` for format.
