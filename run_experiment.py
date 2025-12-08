#!/usr/bin/env python3
"""
Strange Worlds Experiment Runner

Eight-way comparison (grouped by inspiration source):

No external inspiration:
- A (Semantic Tabu): "Be creative" + tabu list of previous solutions
- B (SolutionTaxonomy): Graph-based novelty enforcement with agentic graph control

Seed word inspiration:
- C (Random Seed): Direct solution inspired by random seed word
- D (Seed + Tabu): Random seed + semantic tabu list
- E (Taxonomy + Seed): Random seed + graph-based novelty

Strange Worlds inspiration:
- F (Strange Worlds): World → solver → extract pipeline
- G (Strange Worlds + Tabu): Strange Worlds + semantic tabu list
- H (Taxonomy + Worlds): Strange Worlds + graph-based novelty

Uses claude-code-sdk to run via Claude Code CLI.
Install: pip install claude-code-sdk
"""

import json
from pathlib import Path
from datetime import datetime
import asyncio
import subprocess
import time
import os
import re
import logging

from claude_code_sdk import query, ClaudeCodeOptions, Message


# Setup logging
LOG_DIR = Path(__file__).parent / "agents" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# File handler with timestamps
file_handler = logging.FileHandler(LOG_DIR / "experiment.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

# Console handler without timestamps (cleaner output)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('  %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)


def log_event(event_type: str, condition: str, run_num: int = None, **data):
    """Log structured event to JSON-lines file for analysis."""
    event = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "condition": condition,
        "run": run_num,
        **data
    }
    events_file = LOG_DIR / "events.jsonl"
    with open(events_file, "a") as f:
        f.write(json.dumps(event) + "\n")


def capture_reasoning_trace(explorer_session: str, taxonomist_session: str) -> dict:
    """Capture the reasoning trace from both agents.

    Returns dict with explorer_trace and taxonomist_trace.
    """
    traces = {}

    for name, session in [("explorer", explorer_session), ("taxonomist", taxonomist_session)]:
        if tmux_session_exists(session):
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", session, "-p", "-S", "-5000"],
                capture_output=True,
                text=True
            )
            content = strip_ansi(result.stdout)

            # Filter out UI noise but keep actual content
            filtered_lines = []
            skip_patterns = [
                '────', '> ', 'bypass permissions', 'tokens', 'Clauding',
                'Spelunking', 'shift+tab', 'tab to accept', '▐▛', '▝▜',
                'Claude Code v', 'Opus 4.5', '▘▘ ▝▝', 'Try "', 'Thinking',
                'esc to interrupt'
            ]

            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Skip UI chrome
                if any(pattern in line for pattern in skip_patterns):
                    continue
                # Keep substantive content
                if len(line) > 5:  # Skip very short lines
                    filtered_lines.append(line)

            # Keep last 200 lines of substantive content
            traces[f"{name}_trace"] = '\n'.join(filtered_lines[-200:])

    return traces


def save_reasoning_trace(condition: str, run_num: int, traces: dict):
    """Save the reasoning trace to a dedicated file."""
    trace_dir = LOG_DIR / "traces"
    trace_dir.mkdir(exist_ok=True)
    trace_file = trace_dir / f"{condition}_{run_num:02d}_trace.json"
    trace_file.write_text(json.dumps({
        "condition": condition,
        "run": run_num,
        "timestamp": datetime.now().isoformat(),
        **traces
    }, indent=2))


def sanitize_paths(text: str) -> str:
    """Remove private file paths from text."""
    import re
    # Remove /Users/username/... paths
    text = re.sub(r'/Users/[^/\s]+/', '/.../', text)
    # Remove /home/username/... paths
    text = re.sub(r'/home/[^/\s]+/', '/.../', text)
    return text


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences and control characters from text."""
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b[()][AB012]')
    text = ansi_escape.sub('', text)
    # Remove other escape sequences
    text = re.sub(r'\x1b\[\?[0-9;]*[a-zA-Z]', '', text)
    # Remove carriage returns and other control chars (keep newlines)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Remove repeated blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def clean_log_file(log_path) -> None:
    """Clean ANSI escape codes from a log file in place."""
    from pathlib import Path
    log_path = Path(log_path)
    if not log_path.exists():
        return
    try:
        content = log_path.read_text(errors='replace')
        cleaned = strip_ansi(content)
        log_path.write_text(cleaned)
    except Exception as e:
        print(f"  Warning: Could not clean log {log_path}: {e}")


# =============================================================================
# TMUX ORCHESTRATION FOR TAXONOMY CONDITIONS (B, E, H)
# =============================================================================

AGENTS_DIR = Path(__file__).parent / "agents"
SANDBOX_PROFILE = AGENTS_DIR / "sandbox.sb"

def tmux_session_exists(session_name: str) -> bool:
    """Check if a tmux session exists."""
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        capture_output=True
    )
    return result.returncode == 0

def start_taxonomist_session(condition: str, db_path: Path) -> str:
    """Start a persistent Taxonomist session for a taxonomy condition.

    Returns the session name.
    """
    session_name = f"taxonomist_{condition}"

    # Kill existing session if any
    if tmux_session_exists(session_name):
        subprocess.run(["tmux", "kill-session", "-t", session_name], capture_output=True)

    # Read taxonomist prompt
    taxonomist_prompt = (AGENTS_DIR / "taxonomist.md").read_text()

    # Add condition-specific context with STRONG emphasis on restructuring
    taxonomist_prompt += f"""

## Condition
{condition}

## Database
{db_path}

## Your Task - BUILD A BEAUTIFUL TAXONOMY
You are the persistent Taxonomist for this experimental condition.
You will receive 25 proposals from Explorers. Your job is NOT just to accept/reject.
Your job is to BUILD STRUCTURE:

### Before Each Addition, Consider:
1. **Does this reveal a new category?** If so, create a parent node FIRST
2. **Does this fit under an existing category?** Link it as a child
3. **Are two mechanisms actually the same?** MERGE them
4. **Is a category too broad?** SPLIT it with restructuring

### Graph Commands You MUST Use:
```bash
# Check current state (DO THIS FIRST)
python agents/graph_cli.py state

# See hierarchies as trees
python agents/graph_cli.py tree MECHANISM
python agents/graph_cli.py tree OUTCOME

# Add a solution
python agents/graph_cli.py add-inline '<json>'

# Build hierarchy - CREATE PARENT CATEGORIES
python agents/graph_cli.py create-child <parent_id> "Child category"
python agents/graph_cli.py set-parent <child_id> <parent_id>

# Merge redundant nodes
python agents/graph_cli.py merge <keep_id> <remove_id>
```

### Your Response Format
When you receive [EXPLORER from <session>] proposal:

1. First: `python agents/graph_cli.py state` - see current graph
2. Reason about WHERE this fits in the taxonomy
3. If needed: restructure BEFORE adding (create parents, merge redundancies)
4. Add the solution: `python agents/graph_cli.py add-inline '...'`
5. After adding: consider hierarchy placement with set-parent
6. Reply to Explorer using the session name they provided:
   ```bash
   tmux send-keys -t <their_session_name> '[Taxonomist] Your response' Enter
   ```

### IMPORTANT: Reply to the CORRECT Explorer!
- Explorer messages include "Reply to me at: <session_name>"
- USE THAT SESSION NAME when you reply!
- Example: `tmux send-keys -t explorer_taxonomy_3 '[Taxonomist] Added!' Enter`

### Rejection = Negotiation
If you reject, give SPECIFIC feedback:
- "Your mechanism is 90% similar to X. Differentiate by..."
- "This would fit better if you focused on..."
- "The graph already has this. Try exploring [gap]..."

The Explorer will retry with your feedback. NEGOTIATE toward novelty.

Wait for the first [EXPLORER] message...
"""

    # Write temp prompt file
    prompt_file = AGENTS_DIR / f".taxonomist_{condition}_prompt.tmp"
    prompt_file.write_text(taxonomist_prompt)

    # Create log file
    log_file = AGENTS_DIR / "logs" / f"taxonomist_{condition}.log"
    log_file.parent.mkdir(exist_ok=True)

    # Start tmux session with sandboxed Claude
    experiment_dir = Path(__file__).parent
    home = os.environ.get("HOME", "")

    # Create empty session first
    subprocess.run([
        "tmux", "new-session", "-d", "-s", session_name, "-c", str(experiment_dir)
    ])

    # Send the command to the session - set TAXONOMY_DB for correct database
    db_abs_path = (experiment_dir / db_path).resolve()
    cmd = f"""TAXONOMY_DB='{db_abs_path}' script -q {log_file} sandbox-exec -f '{SANDBOX_PROFILE}' -D HOME='{home}' -D PROJECT_DIR='{experiment_dir}' claude --dangerously-skip-permissions --verbose --append-system-prompt "$(cat {prompt_file})" """

    subprocess.run([
        "tmux", "send-keys", "-t", session_name, cmd, "Enter"
    ])

    # Wait for Claude to initialize
    time.sleep(5)

    print(f"  Started Taxonomist session: {session_name} (DB: {db_abs_path})")
    return session_name

def send_to_taxonomist(session_name: str, message: str) -> None:
    """Send a message to the Taxonomist session."""
    # Escape single quotes in message
    escaped = message.replace("'", "'\"'\"'")
    # Send message
    subprocess.run([
        "tmux", "send-keys", "-t", session_name, escaped
    ])
    # Send Enter separately to ensure it's processed
    subprocess.run([
        "tmux", "send-keys", "-t", session_name, "Enter"
    ])


def send_enter_to_session(session_name: str) -> None:
    """Send Enter key to a tmux session."""
    if tmux_session_exists(session_name):
        subprocess.run([
            "tmux", "send-keys", "-t", session_name, "Enter"
        ])


def send_enter_to_all_agents() -> None:
    """Send Enter to all active taxonomy agent sessions."""
    result = subprocess.run(
        ["tmux", "list-sessions", "-F", "#{session_name}"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        for session in result.stdout.strip().split('\n'):
            if session.startswith(('taxonomist_', 'explorer_')):
                subprocess.run([
                    "tmux", "send-keys", "-t", session, "Enter"
                ])

def capture_taxonomist_response(session_name: str, timeout: int = 120) -> str:
    """Wait for and capture Taxonomist's response.

    Watches the tmux pane for [TAXONOMIST] response.
    """
    start_time = time.time()
    last_content = ""
    stable_count = 0

    while time.time() - start_time < timeout:
        # Capture current pane content
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", session_name, "-p", "-S", "-1000"],
            capture_output=True,
            text=True
        )
        content = result.stdout

        # Check if content has stabilized (Claude finished responding)
        if content == last_content:
            stable_count += 1
            if stable_count >= 3:  # Stable for 3 seconds
                break
        else:
            stable_count = 0
            last_content = content

        time.sleep(1)

    # Extract the latest [TAXONOMIST] response
    lines = content.split('\n')
    response_lines = []
    in_response = False

    for line in reversed(lines):
        if '[TAXONOMIST]' in line:
            response_lines.insert(0, line)
            in_response = True
            break
        elif in_response or (not in_response and line.strip()):
            response_lines.insert(0, line)

    return '\n'.join(response_lines)

def stop_taxonomist_session(session_name: str) -> None:
    """Stop a Taxonomist tmux session and clean its log."""
    if tmux_session_exists(session_name):
        subprocess.run(["tmux", "kill-session", "-t", session_name], capture_output=True)
        print(f"  Stopped Taxonomist session: {session_name}")
    # Clean the log file
    log_file = AGENTS_DIR / "logs" / f"{session_name}.log"
    clean_log_file(log_file)


def ensure_taxonomist_alive(condition: str, db_path: Path) -> str:
    """Ensure Taxonomist session is running, restart if dead.

    Returns the session name.
    """
    session_name = f"taxonomist_{condition}"

    if not tmux_session_exists(session_name):
        print(f"  Warning: Taxonomist {session_name} died, restarting...")
        return start_taxonomist_session(condition, db_path)

    # Check if Claude is actually running in the session
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", session_name, "-p"],
        capture_output=True,
        text=True
    )
    pane_content = result.stdout

    # If session exists but seems stuck (no activity indicator), restart
    if "$ " in pane_content.split('\n')[-1] and "claude" not in pane_content.lower():
        print(f"  Warning: Taxonomist {session_name} crashed, restarting...")
        subprocess.run(["tmux", "kill-session", "-t", session_name], capture_output=True)
        return start_taxonomist_session(condition, db_path)

    return session_name

# Note: run_explorer_for_proposal() is defined after constants PROBLEM and SOLUTION_SCHEMA below

# Config
MODEL = "opus"

SEEDS = [
    "limelike", "unwilted", "cinerator", "nephropyosis", "fimbrillate",
    "coralline", "unimpatient", "pilaued", "displacement", "theatrical",
    "palouser", "critique", "bromobenzyl", "gnomically", "remilitarize",
    "arcual", "whizgig", "entempest", "chalaco", "paranucleic",
    "phraseman", "desperacy", "pidan", "phosis", "theca"
]

PROBLEM = "How do we build a retirement system for people who don't know how much they will earn next month, where 'consistency' is impossible?"

SOLUTION_SCHEMA = """{
  "label": "Short name for the solution, max 40 chars",
  "design_principles": "Guiding principles, especially unconventional ones, max 200 chars",
  "core_mechanism": "The central principle that makes this work, max 200 chars",
  "how_it_works": "Clear enough to start implementation, or describe research needed to get there, max 500 chars",
  "what_is_new": "How this differs from existing approaches, max 200 chars",
  "why_it_works": "Steelman: argue why this counterintuitive approach is actually valuable, max 300 chars",
  "why_it_fails": "Steelman the criticism: the strongest argument against this solution, max 300 chars",
  "medium_term": "What changes in 5-15 years if adopted, max 200 chars",
  "long_term_vision": "What the world looks like if this fully succeeds, max 300 chars"
}"""

# Directory setup
BASE_DIR = Path(__file__).parent
WORLDS_DIR = BASE_DIR / "worlds"
STRANGE_WORLDS_DIR = BASE_DIR / "strange_worlds"
WORLDS_TABU_DIR = BASE_DIR / "strange_worlds_tabu"
TABU_DIR = BASE_DIR / "semantic_tabu"
RANDOM_SEED_DIR = BASE_DIR / "random_seed"
SEED_TABU_DIR = BASE_DIR / "seed_tabu"
TAXONOMY_DIR = BASE_DIR / "taxonomy"
TAXONOMY_SEED_DIR = BASE_DIR / "taxonomy_seed"
TAXONOMY_WORLDS_DIR = BASE_DIR / "taxonomy_worlds"

def ensure_dirs():
    WORLDS_DIR.mkdir(exist_ok=True)
    STRANGE_WORLDS_DIR.mkdir(exist_ok=True)
    WORLDS_TABU_DIR.mkdir(exist_ok=True)
    TABU_DIR.mkdir(exist_ok=True)
    RANDOM_SEED_DIR.mkdir(exist_ok=True)
    SEED_TABU_DIR.mkdir(exist_ok=True)
    TAXONOMY_DIR.mkdir(exist_ok=True)
    TAXONOMY_SEED_DIR.mkdir(exist_ok=True)
    TAXONOMY_WORLDS_DIR.mkdir(exist_ok=True)

def load_bank(path: Path) -> list:
    if path.exists():
        return json.loads(path.read_text())
    return []

def save_bank(path: Path, bank: list):
    path.write_text(json.dumps(bank, indent=2))

def save_result(output_dir: Path, filename: str, condition: str, run_num: int, reasoning: str, solution: dict, **extra) -> dict:
    """Save experiment result - DRY helper for all conditions."""
    result = {
        "id": filename.replace(".json", ""),
        "condition": condition,
        "run": run_num,
        "reasoning": reasoning,
        "solution": solution,
        "timestamp": datetime.now().isoformat(),
        **extra
    }
    (output_dir / filename).write_text(json.dumps(result, indent=2))
    return result

async def call_claude_async(prompt: str) -> str:
    """Call Claude via claude-code-sdk."""
    options = ClaudeCodeOptions(
        model=MODEL,
        max_turns=1,
    )

    result_text = ""
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, Message):
            if hasattr(message, 'content') and message.content:
                if isinstance(message.content, str):
                    result_text += message.content
                elif isinstance(message.content, list):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            result_text += block.text

    return result_text

def call_claude(prompt: str) -> str:
    """Sync wrapper for async call."""
    return asyncio.run(call_claude_async(prompt))

def extract_json(text: str) -> dict:
    """Extract JSON from response text."""
    # Try to find JSON in the response
    import re

    # Look for ```json blocks first
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
    if json_match:
        return json.loads(json_match.group(1))

    # Look for { ... } pattern
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        return json.loads(json_match.group(0))

    raise ValueError(f"Could not extract JSON from response: {text[:500]}")


# =============================================================================
# SDK-BASED NEGOTIATION (replaces tmux for taxonomy conditions)
# =============================================================================

async def explorer_propose(
    graph_state: str,
    extra_context: str,
    rejection_feedback: str = None
) -> tuple[str, dict]:
    """Explorer generates a proposal using SDK.

    Returns (reasoning, solution_dict).
    """
    feedback_section = ""
    if rejection_feedback:
        feedback_section = f"""
## Previous Rejection Feedback
The Taxonomist rejected your previous proposal:
{rejection_feedback}

You MUST propose something GENUINELY DIFFERENT - not just rephrased.
Address the specific feedback above.
"""

    prompt = f"""You are the EXPLORER - a creative agent proposing novel solutions.

Think deeply about this problem.

**PROBLEM:** {PROBLEM}

## Current Taxonomy State
{graph_state}

## Your Inspiration
{extra_context if extra_context else "None - generate from pure creativity"}
{feedback_section}
## Your Task
1. Study the taxonomy state - understand what mechanisms and outcomes already exist
2. Find a GAP - what's missing? What hasn't been explored?
3. Generate a NOVEL solution that fills that gap
4. Think deeply about WHY this is genuinely new

## Output Format
First, show your reasoning:
- What patterns do you see in the existing taxonomy?
- What gap or unexplored territory did you identify?
- Why is your proposed mechanism genuinely different?

Then output your proposal as JSON:
```json
{SOLUTION_SCHEMA}
```

Begin with your reasoning, then the JSON proposal."""

    response = await call_claude_async(prompt)

    try:
        solution = extract_json(response)
    except:
        solution = {}

    return response, solution


async def taxonomist_review(
    proposal: dict,
    graph_state: str,
    store  # GraphStore instance
) -> dict:
    """Taxonomist reviews a proposal using SDK.

    Returns dict with:
        - accepted: bool
        - feedback: str (reason for accept/reject)
        - mappings: dict (field -> node_id mappings if accepted)
        - restructure_ops: list (restructuring operations if needed)
    """
    from src.taxonomy_graph.graph_store import NodeType

    # Check novelty first using the graph
    novelty_check = store.check_novelty(proposal)

    novelty_info = ""
    if novelty_check.get('mechanism_overlap'):
        overlap = novelty_check['mechanism_overlap']
        novelty_info = f"""
## Novelty Check Result
Similar mechanism found (similarity: {overlap['similarity']:.2f}):
> {overlap['existing_text'][:200]}

{"This is TOO SIMILAR - reject unless the proposal has a genuinely different approach." if overlap['similarity'] > 0.92 else "This has some overlap - consider carefully."}
"""

    prompt = f"""You are the TAXONOMIST - the gatekeeper of a solution taxonomy.

**PROBLEM:** {PROBLEM}

## Current Taxonomy State
{graph_state}

## Proposal to Review
```json
{json.dumps(proposal, indent=2)}
```
{novelty_info}
## Your Task
Decide whether to ACCEPT or REJECT this proposal.

### Accept if:
- The mechanism is genuinely novel (not just rephrased existing)
- It fills a gap in the taxonomy
- It adds structural value to our understanding

### Reject if:
- The mechanism is too similar to existing ones (>92% similarity)
- It's just a variation/rebranding of something we have
- It doesn't add structural insight

## Output Format
First, reason about:
1. What category/cluster does this belong to?
2. Is the mechanism genuinely new?
3. Does it reveal structure we haven't seen?

Then output your decision as JSON:
```json
{{
    "accepted": true/false,
    "feedback": "Your detailed reasoning for the Explorer",
    "suggested_parent_mechanism": "If accepted, what parent category this belongs under (or 'NEW_CATEGORY' if it creates one)",
    "similar_to": "If rejected, which existing solution it's too similar to"
}}
```"""

    response = await call_claude_async(prompt)

    try:
        decision = extract_json(response)
    except:
        decision = {"accepted": False, "feedback": "Could not parse Taxonomist response"}

    # Add the full reasoning
    decision['full_reasoning'] = response

    return decision


async def run_negotiation(
    condition: str,
    run_num: int,
    seed: str,
    extra_context: str,
    max_attempts: int = 3
) -> dict:
    """Run Explorer-Taxonomist negotiation via SDK.

    Returns dict with:
        - solution: dict (the accepted solution, or {} if all rejected)
        - explorer_reasoning: str
        - taxonomist_feedback: str
        - attempts: int
        - added_to_graph: bool
    """
    from src.taxonomy_graph.graph_store import GraphStore

    # Get the graph store for this condition
    if condition == 'taxonomy':
        db_path = TAXONOMY_DIR / "taxonomy.db"
    elif condition == 'taxonomy_seed':
        db_path = TAXONOMY_SEED_DIR / "taxonomy.db"
    elif condition == 'taxonomy_worlds':
        db_path = TAXONOMY_WORLDS_DIR / "taxonomy.db"
    else:
        raise ValueError(f"Unknown taxonomy condition: {condition}")

    store = GraphStore(str(db_path))

    log_lines = []
    rejection_feedback = None

    for attempt in range(1, max_attempts + 1):
        log_lines.append(f"\n{'='*60}")
        log_lines.append(f"ATTEMPT {attempt}/{max_attempts}")
        log_lines.append('='*60)

        # Get current graph state
        graph_state = store.get_graph_state_for_prompt()

        # Explorer proposes
        log_lines.append("\n[EXPLORER] Generating proposal...")
        explorer_reasoning, proposal = await explorer_propose(
            graph_state, extra_context, rejection_feedback
        )
        log_lines.append(f"\n[EXPLORER REASONING]\n{explorer_reasoning[:2000]}...")

        if not proposal or not proposal.get('label'):
            log_lines.append("\n[ERROR] Explorer failed to generate valid proposal")
            rejection_feedback = "Your previous response did not contain a valid JSON proposal. Please include a complete solution JSON."
            continue

        log_lines.append(f"\n[PROPOSAL] {proposal.get('label', 'Unknown')}")

        # Taxonomist reviews
        log_lines.append("\n[TAXONOMIST] Reviewing proposal...")
        decision = await taxonomist_review(proposal, graph_state, store)
        log_lines.append(f"\n[TAXONOMIST REASONING]\n{decision.get('full_reasoning', '')[:2000]}...")

        if decision.get('accepted'):
            log_lines.append(f"\n[ACCEPTED] Adding to graph...")

            # Add to graph
            result = store.add_solution(proposal)

            if result.get('success'):
                log_lines.append(f"[SUCCESS] Solution added: {result.get('solution_id', 'unknown')[:8]}...")

                combined_reasoning = '\n'.join(log_lines)
                return {
                    'solution': proposal,
                    'explorer_reasoning': explorer_reasoning,
                    'taxonomist_feedback': decision.get('feedback', ''),
                    'attempts': attempt,
                    'added_to_graph': True,
                    'reasoning': combined_reasoning,
                    'graph_stats': store.stats()
                }
            else:
                log_lines.append(f"[ERROR] Failed to add: {result.get('error', 'unknown')}")
                rejection_feedback = f"Graph rejected: {result.get('error')}. Please fix and retry."
        else:
            rejection_feedback = decision.get('feedback', 'No specific feedback provided')
            log_lines.append(f"\n[REJECTED] {rejection_feedback}")

    # All attempts failed
    combined_reasoning = '\n'.join(log_lines)
    return {
        'solution': {},
        'explorer_reasoning': '',
        'taxonomist_feedback': rejection_feedback or 'Max attempts reached',
        'attempts': max_attempts,
        'added_to_graph': False,
        'reasoning': combined_reasoning,
        'graph_stats': store.stats()
    }


async def run_taxonomy_sdk(
    condition: str,
    runs: list[int],
    extra_context_fn  # Function that takes (run_num, seed) and returns extra context string
) -> None:
    """Run taxonomy condition using SDK-based negotiation.

    This replaces run_taxonomy_with_tmux.
    """
    # Determine output directory and file prefix
    if condition == 'taxonomy':
        output_dir = TAXONOMY_DIR
        file_prefix = 'taxonomy'
    elif condition == 'taxonomy_seed':
        output_dir = TAXONOMY_SEED_DIR
        file_prefix = 'taxonomy_seed'
    elif condition == 'taxonomy_worlds':
        output_dir = TAXONOMY_WORLDS_DIR
        file_prefix = 'taxonomy_worlds'
    else:
        raise ValueError(f"Unknown condition: {condition}")

    # Create logs directory
    logs_dir = AGENTS_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    label = condition.upper()

    for run_num in runs:
        seed = SEEDS[run_num - 1] if run_num <= len(SEEDS) else f"run{run_num}"

        print(f"\n[{label}] Run #{run_num} (seed: {seed})")

        # Get extra context for this run
        extra_context = extra_context_fn(run_num, seed) if extra_context_fn else ""

        # Run negotiation
        result = await run_negotiation(
            condition=condition,
            run_num=run_num,
            seed=seed,
            extra_context=extra_context
        )

        # Build filename
        if condition in ['taxonomy_seed', 'taxonomy_worlds']:
            filename = f"{file_prefix}_{run_num:02d}_{seed}.json"
        else:
            filename = f"{file_prefix}_{run_num:02d}.json"

        # Save result
        save_result(
            output_dir, filename, condition, run_num,
            result['reasoning'],
            result['solution'],
            seed=seed if condition != 'taxonomy' else None,
            added_to_graph=result['added_to_graph'],
            attempts=result['attempts'],
            graph_stats=result['graph_stats']
        )

        # Save detailed log
        log_file = logs_dir / f"{condition}_{run_num}.log"
        log_file.write_text(result['reasoning'])

        # Report status
        status = "ADDED" if result['added_to_graph'] else "FAILED"
        label_text = result['solution'].get('label', 'None')
        print(f"  [{label}] #{run_num}: {status} -> {label_text} (attempts: {result['attempts']})")


# === PROMPTS ===

COMMON_INTRO = f"""Please think deeply about this problem.

PROBLEM:
{PROBLEM}

If your solution feels familiar, you've lost the signal. Find something genuinely new.

CRITICAL: Your solution must describe concrete mechanisms—what specifically happens when X occurs.
New laws or technology are fine. Metaphors that sound meaningful but lack mechanical specificity are not.

Counterintuitive solutions are welcome—even preferred—as long as you can argue why the counterintuitive element is valuable, not just strange."""

BANK_TEXT = """
EXISTING SOLUTIONS:
{bank}

Before proposing your solution, first list the core mechanism of each existing solution above.
Then explicitly state which structural approaches you are AVOIDING because they already exist."""

EXTRACTION_GUIDANCE = """
WORLD:
{world}

SOLUTION:
{solution}

Your task is to adapt this solution to our world:
1. First, imagine implementing this solution exactly as described. What would it look like?
2. Identify the "magical" elements—things that work in this world's physics but not ours.
3. For each magical element, iteratively fix it by either:
   - Inventing technology that could achieve the same effect
   - Finding existing technology/structures that approximate it
4. Preserve what's strangest—that's the leverage point. Don't sand it down to something familiar."""

def denial_prompt(bank: list) -> str:
    bank_text = json.dumps(bank, indent=2) if bank else "None yet"
    return COMMON_INTRO + BANK_TEXT.format(bank=bank_text) + f"\n\nOutput valid JSON:\n{SOLUTION_SCHEMA}"

def world_builder_prompt(seed: str) -> str:
    return f"""Please think deeply about this world-building task.

You are a world-builder. Describe a world where this concept is the FUNDAMENTAL LAW of physics:

SEED: {seed}

Describe:
1. The core principle - how does {seed} govern everything?
2. 3-5 specific rules/laws that emerge from this principle
3. How people live, work, and organize society under these rules
4. What is easy in this world? What is hard?

Be specific and internally consistent. Do NOT try to solve any problems yet."""

def solver_prompt(world: str) -> str:
    return f"""Please think deeply about solving this problem.

You live in a world with different physics:

WORLD RULES:
{world}

PROBLEM: {PROBLEM}

How would you solve this problem?

Requirements:
- Your solution must USE the world's physics, not fight against them
- Be specific about HOW the solution leverages the world's rules
- Do not reference our world or "normal" physics"""

def extractor_prompt(world: str, solver: str) -> str:
    return COMMON_INTRO + EXTRACTION_GUIDANCE.format(world=world, solution=solver) + f"\n\nOutput valid JSON:\n{SOLUTION_SCHEMA}"

def combined_extractor_prompt(world: str, solver: str, bank: list) -> str:
    bank_text = json.dumps(bank, indent=2) if bank else "None yet"
    # Bank comes BEFORE extraction guidance so model sees constraints first
    return COMMON_INTRO + BANK_TEXT.format(bank=bank_text) + EXTRACTION_GUIDANCE.format(world=world, solution=solver) + f"\n\nOutput valid JSON:\n{SOLUTION_SCHEMA}"

# === RANDOM SEED PROMPTS ===

SEED_INSPIRATION = """
INSPIRATION SEED: {seed}

Use this word as creative inspiration. Let it guide your thinking in unexpected directions.
The word might suggest metaphors, structures, processes, or principles that could apply to the problem.
Don't force a literal connection—let the word open new conceptual pathways."""

def random_seed_prompt(seed: str) -> str:
    """D condition: Random seed inspiration only (no world-building, no bank)."""
    return COMMON_INTRO + SEED_INSPIRATION.format(seed=seed) + f"\n\nOutput valid JSON:\n{SOLUTION_SCHEMA}"

def seed_tabu_prompt(seed: str, bank: list) -> str:
    """E condition: Random seed + semantic tabu bank."""
    bank_text = json.dumps(bank, indent=2) if bank else "None yet"
    # Bank first (constraints), then seed (inspiration)
    return COMMON_INTRO + BANK_TEXT.format(bank=bank_text) + SEED_INSPIRATION.format(seed=seed) + f"\n\nOutput valid JSON:\n{SOLUTION_SCHEMA}"

def get_graph_store(condition: str = "taxonomy"):
    """Get or create the graph store instance for a condition."""
    from src.taxonomy_graph.graph_store import GraphStore

    if condition == "taxonomy":
        db_path = TAXONOMY_DIR / "taxonomy.db"
    elif condition == "taxonomy_seed":
        db_path = TAXONOMY_SEED_DIR / "taxonomy.db"
    elif condition == "taxonomy_worlds":
        db_path = TAXONOMY_WORLDS_DIR / "taxonomy.db"
    else:
        raise ValueError(f"Unknown condition: {condition}")

    return GraphStore(str(db_path))

def get_graph_taxonomy_state_for_condition(condition: str) -> str:
    """Get graph state for LLM prompt for a specific condition."""
    store = get_graph_store(condition)
    stats = store.stats()
    if stats['solutions'] == 0:
        return "(Empty graph - no solutions yet)"
    return store.get_graph_state_for_prompt()

# === TAXONOMY MULTI-AGENT FUNCTIONS ===

async def run_explorer_for_proposal(
    run_num: int,
    seed: str,
    graph_state: str,
    extra_context: str
) -> tuple[str, dict]:
    """Run a fresh Explorer agent to generate a proposal.

    Returns (explorer_reasoning, solution_dict).
    """
    explorer_prompt = f"""You are the EXPLORER - a creative agent proposing solutions.

Think deeply about this problem.

**PROBLEM:** {PROBLEM}

## Current Graph State (from Taxonomist)
{graph_state}

## Your Inspiration
{extra_context if extra_context else "None - generate from pure creativity"}

## Your Task
1. Study the graph state - understand what mechanisms and outcomes already exist
2. Find a GAP - what's missing? What hasn't been explored?
3. Generate a NOVEL solution that fills that gap
4. Think deeply about WHY this is genuinely new

## Output Format
First, show your full reasoning:
- What patterns do you see in the existing graph?
- What gap or unexplored territory did you identify?
- Why is your proposed mechanism genuinely different?

Then output your proposal as JSON:
```json
{SOLUTION_SCHEMA}
```

Begin with [EXPLORER] and show your full reasoning process."""

    # Run Explorer via claude-code-sdk (fresh agent)
    response = await call_claude_async(explorer_prompt)

    # Extract JSON from response
    try:
        solution = extract_json(response)
    except:
        solution = {}

    return response, solution


def start_explorer_session(condition: str, run_num: int, seed: str, graph_state: str, extra_context: str, taxonomist_session: str) -> str:
    """Start a fresh Explorer session that can communicate with Taxonomist.

    Returns the session name.
    """
    session_name = f"explorer_{condition}_{run_num}"

    # Kill existing session if any
    if tmux_session_exists(session_name):
        subprocess.run(["tmux", "kill-session", "-t", session_name], capture_output=True)

    explorer_prompt = f"""# You are the EXPLORER

You propose novel solutions to this problem:
**PROBLEM:** {PROBLEM}

## Current Graph State
{graph_state}

## Your Inspiration
{extra_context if extra_context else "None - generate from pure creativity"}

## YOUR SESSION NAME: {session_name}
The Taxonomist needs this to reply to you!

## Communication
- Send messages to Taxonomist: `tmux send-keys -t {taxonomist_session} 'message' Enter`
- ALWAYS include your session name so Taxonomist can reply!

## Your Task
1. Study the graph state above
2. Find a GAP - what mechanism/outcome hasn't been explored?
3. Generate a NOVEL solution
4. Send your proposal to the Taxonomist

## Proposal Format - COPY THIS EXACTLY
```bash
tmux send-keys -t {taxonomist_session} '[Explorer from {session_name}]
PROPOSAL:
```json
{SOLUTION_SCHEMA}
```
Reply to me at: {session_name}
' Enter
```

## Negotiation
- If Taxonomist rejects, READ their feedback carefully
- Propose something GENUINELY DIFFERENT (not just rephrased)
- You have up to 3 attempts per solution

BEGIN by sending your first proposal to the Taxonomist!
"""

    # Write temp prompt file
    prompt_file = AGENTS_DIR / f".explorer_{condition}_{run_num}_prompt.tmp"
    prompt_file.write_text(explorer_prompt)

    # Create log file
    log_file = AGENTS_DIR / "logs" / f"explorer_{condition}_{run_num}.log"
    log_file.parent.mkdir(exist_ok=True)

    # Start tmux session with sandboxed Claude
    experiment_dir = Path(__file__).parent
    home = os.environ.get("HOME", "")

    # Create empty session first
    subprocess.run([
        "tmux", "new-session", "-d", "-s", session_name, "-c", str(experiment_dir)
    ])

    # Send the command to the session - use script to capture output while keeping tty
    cmd = f"""script -q {log_file} sandbox-exec -f '{SANDBOX_PROFILE}' -D HOME='{home}' -D PROJECT_DIR='{experiment_dir}' claude --dangerously-skip-permissions --verbose --append-system-prompt "$(cat {prompt_file})" """

    subprocess.run([
        "tmux", "send-keys", "-t", session_name, cmd, "Enter"
    ])

    # Wait for Claude to initialize
    time.sleep(5)

    return session_name


def stop_explorer_session(session_name: str) -> None:
    """Stop an Explorer tmux session and clean its log."""
    if tmux_session_exists(session_name):
        subprocess.run(["tmux", "kill-session", "-t", session_name], capture_output=True)
    # Clean the log file
    log_file = AGENTS_DIR / "logs" / f"{session_name}.log"
    clean_log_file(log_file)


def capture_conversation_logs(taxonomist_log: Path, explorer_log: Path, timeout: int = 300) -> tuple[str, str]:
    """Wait for conversation to stabilize and capture both logs.

    Returns (taxonomist_trace, explorer_trace).
    """
    start_time = time.time()
    last_sizes = (0, 0)
    stable_count = 0

    while time.time() - start_time < timeout:
        tax_size = taxonomist_log.stat().st_size if taxonomist_log.exists() else 0
        exp_size = explorer_log.stat().st_size if explorer_log.exists() else 0

        if (tax_size, exp_size) == last_sizes:
            stable_count += 1
            if stable_count >= 10:  # Stable for 10 seconds
                break
        else:
            stable_count = 0
            last_sizes = (tax_size, exp_size)

        time.sleep(1)

    tax_trace = taxonomist_log.read_text() if taxonomist_log.exists() else ""
    exp_trace = explorer_log.read_text() if explorer_log.exists() else ""

    return tax_trace, exp_trace


async def run_taxonomy_with_tmux(
    condition: str,
    label: str,
    output_dir: Path,
    file_prefix: str,
    run_nums: list[int],
    seeds: list[str],
    get_extra_context,  # callable(run_num, seed, worlds, solvers) -> str
    get_extra_save_fields,  # callable(run_num, seed, worlds, solvers) -> dict
    worlds: dict = None,
    solvers: dict = None
):
    """Run taxonomy condition with BOTH agents in tmux communicating directly.

    TRUE multi-agent flow:
    1. Taxonomist runs in persistent tmux session
    2. For each run: fresh Explorer in tmux
    3. Explorer sends proposals via: tmux send-keys -t taxonomist '[Explorer] ...'
    4. Taxonomist responds via: tmux send-keys -t explorer '[Taxonomist] ...'
    5. They negotiate directly until solution is added or max attempts reached
    """
    from src.taxonomy_graph.graph_store import GraphStore

    runs_needed = [r for r in run_nums if not file_exists_for_run(condition, r)]
    if not runs_needed:
        print(f"  [{label}] {condition}: all exist, skipping")
        return

    # Get database path for this condition
    if condition == "taxonomy":
        db_path = TAXONOMY_DIR / "taxonomy.db"
    elif condition == "taxonomy_seed":
        db_path = TAXONOMY_SEED_DIR / "taxonomy.db"
    elif condition == "taxonomy_worlds":
        db_path = TAXONOMY_WORLDS_DIR / "taxonomy.db"
    else:
        raise ValueError(f"Unknown condition: {condition}")

    print(f"  [{label}] Starting Taxonomist for {condition}...")
    log_event("taxonomist_start", condition, session=f"taxonomist_{condition}")

    # Start persistent Taxonomist session
    taxonomist_session = start_taxonomist_session(condition, db_path)

    # Give Taxonomist time to initialize
    await asyncio.sleep(8)

    try:
        for run_num in runs_needed:
            seed = seeds[run_nums.index(run_num)]
            extra_context = get_extra_context(run_num, seed, worlds, solvers) if worlds else get_extra_context(run_num, seed, {}, {})
            print(f"  [{label}] {condition} #{run_num}: Launching Explorer...")
            log_event("run_start", condition, run_num, seed=seed)

            # Ensure Taxonomist is still alive before each run
            taxonomist_session = ensure_taxonomist_alive(condition, db_path)
            await asyncio.sleep(2)  # Give restarted session time to init

            # Get current graph state
            graph_state = get_graph_taxonomy_state_for_condition(condition)

            # Record solution count before this run
            store_pre = get_graph_store(condition)
            solutions_before = store_pre.stats()['solutions']
            print(f"  [{label}] #{run_num}: negotiating...")
            log_event("negotiation_start", condition, run_num, solutions_before=solutions_before)

            # Start fresh Explorer that will communicate directly with Taxonomist
            explorer_session = start_explorer_session(
                condition, run_num, seed, graph_state, extra_context, taxonomist_session
            )

            # Give Explorer time to start and send first proposal
            await asyncio.sleep(5)

            # Kickstart the Explorer to begin
            send_to_taxonomist(explorer_session, "Begin! Send your proposal to the Taxonomist now.")

            # Wait for conversation to complete with periodic Enter presses
            # (negotiating message already printed above)
            negotiation_time = 180  # 3 minutes total
            enter_interval = 10     # Send Enter every 10 seconds
            elapsed = 0
            while elapsed < negotiation_time:
                await asyncio.sleep(enter_interval)
                elapsed += enter_interval
                send_enter_to_all_agents()
                # Check if solution was added early
                store = get_graph_store(condition)
                current_solutions = store.stats()['solutions']
                if current_solutions > solutions_before:
                    print(f"  [{label}] #{run_num}: solution added!")
                    break
                # Log progress every 30 seconds
                if elapsed % 30 == 0:
                    logger.debug(f"[{label}] #{run_num}: Still negotiating... {elapsed}s elapsed")

            # Capture reasoning trace BEFORE stopping sessions
            traces = capture_reasoning_trace(explorer_session, taxonomist_session)
            save_reasoning_trace(condition, run_num, traces)
            log_event("negotiation_end", condition, run_num, elapsed_seconds=elapsed)

            # Stop Explorer session
            stop_explorer_session(explorer_session)

            # Check if solution was added by looking at graph
            store = get_graph_store(condition)
            stats = store.stats()
            solutions_after = stats['solutions']

            # Get the newly added solution from the database
            # Compare before/after counts to find what was added this run
            final_solution = {}
            added = solutions_after > solutions_before
            try:
                from src.taxonomy_graph.graph_store import NodeType
                solutions = store.get_nodes_by_type(NodeType.SOLUTION)
                if added and solutions:
                    # Get the solution added during this run
                    latest_sol_id, latest_data = solutions[-1]  # Last added
                    full_sol = latest_data.get('metadata', {}).get('full_solution', {})
                    if full_sol:
                        final_solution = full_sol
            except Exception as e:
                print(f"  Warning: Could not retrieve solution from DB: {e}")

            # Generate reasoning from captured traces
            explorer_trace = sanitize_paths(traces.get('explorer_trace', ''))
            taxonomist_trace = sanitize_paths(traces.get('taxonomist_trace', ''))
            combined_reasoning = f"""## Explorer-Taxonomist Negotiation

### Explorer Reasoning:
{explorer_trace}

### Taxonomist Decision:
{taxonomist_trace}

### Result:
Solution: {final_solution.get('label', 'Unknown')}
Graph stats: {stats}"""

            # Build filename
            extra_fields = get_extra_save_fields(run_num, seed, worlds, solvers) if worlds else get_extra_save_fields(run_num, seed, {}, {})
            if 'seed' in extra_fields:
                filename = f"{file_prefix}_{run_num:02d}_{seed}.json"
            else:
                filename = f"{file_prefix}_{run_num:02d}.json"

            save_result(output_dir, filename, condition, run_num,
                       combined_reasoning, final_solution,
                       added_to_graph=added,
                       graph_stats=stats,
                       **extra_fields)

            status = "DONE" if final_solution else "CHECK LOGS"
            if final_solution:
                print(f"  [{label}] #{run_num}: done -> {final_solution.get('label', '?')}")
                log_event("solution_saved", condition, run_num,
                         label=final_solution.get('label'),
                         filename=filename,
                         graph_solutions=stats['solutions'])
            else:
                print(f"  [{label}] #{run_num}: FAILED (check traces)")
                log_event("solution_failed", condition, run_num,
                         filename=filename,
                         graph_solutions=stats['solutions'])

    finally:
        # Always stop Taxonomist session when done
        stop_taxonomist_session(taxonomist_session)

# === RUN FUNCTIONS ===

BATCH_SIZE = 5

def get_progress() -> tuple[int, int, int, int, int, int, int, int]:
    """Get current progress for each condition.

    Returns in logical order (A-H):
    A: Tabu, B: Taxonomy, C: Seed, D: Seed+Tabu, E: Seed+Taxonomy,
    F: Worlds, G: Worlds+Tabu, H: Worlds+Taxonomy
    """
    a = len(list(TABU_DIR.glob("tabu_*.json")))
    b = len(list(TAXONOMY_DIR.glob("taxonomy_*.json")))
    c = len(list(RANDOM_SEED_DIR.glob("seed_*.json")))
    d = len(list(SEED_TABU_DIR.glob("seed_tabu_*.json")))
    e = len(list(TAXONOMY_SEED_DIR.glob("taxonomy_seed_*.json")))
    f = len(list(STRANGE_WORLDS_DIR.glob("worlds_*.json")))
    g = len(list(WORLDS_TABU_DIR.glob("worlds_tabu_*.json")))
    h = len(list(TAXONOMY_WORLDS_DIR.glob("taxonomy_worlds_*.json")))
    return a, b, c, d, e, f, g, h

def file_exists_for_run(condition: str, run_num: int, seed: str = None) -> bool:
    """Check if output file exists for a specific condition and run."""
    if condition == "semantic_tabu":
        return (TABU_DIR / f"tabu_{run_num:02d}.json").exists()
    elif condition == "strange_worlds":
        return len(list(STRANGE_WORLDS_DIR.glob(f"worlds_{run_num:02d}_*.json"))) > 0
    elif condition == "strange_worlds_tabu":
        return len(list(WORLDS_TABU_DIR.glob(f"worlds_tabu_{run_num:02d}_*.json"))) > 0
    elif condition == "random_seed":
        return len(list(RANDOM_SEED_DIR.glob(f"seed_{run_num:02d}_*.json"))) > 0
    elif condition == "seed_tabu":
        return len(list(SEED_TABU_DIR.glob(f"seed_tabu_{run_num:02d}_*.json"))) > 0
    elif condition == "taxonomy":
        return (TAXONOMY_DIR / f"taxonomy_{run_num:02d}.json").exists()
    elif condition == "taxonomy_seed":
        return len(list(TAXONOMY_SEED_DIR.glob(f"taxonomy_seed_{run_num:02d}_*.json"))) > 0
    elif condition == "taxonomy_worlds":
        return len(list(TAXONOMY_WORLDS_DIR.glob(f"taxonomy_worlds_{run_num:02d}_*.json"))) > 0
    return False

async def run_batch_async(run_nums: list[int]):
    """Run a batch of runs with maximum parallelization. Auto-detects existing files."""
    seeds = [SEEDS[r - 1] for r in run_nums]

    print(f"\n{'='*60}")
    print(f"=== BATCH: Runs {run_nums[0]}-{run_nums[-1]} (seeds: {', '.join(seeds)}) ===")
    print(f"{'='*60}")

    worlds = {}
    solvers = {}

    # Check what needs to be built vs loaded
    runs_needing_worlds = []
    runs_needing_solvers = []

    for run_num, seed in zip(run_nums, seeds):
        world_dir = WORLDS_DIR / f"{run_num:02d}_{seed}"
        world_file = world_dir / "world.txt"
        solver_file = world_dir / "solver.txt"

        if world_file.exists():
            worlds[run_num] = (seed, world_file.read_text())
        else:
            runs_needing_worlds.append((run_num, seed))

        if solver_file.exists():
            solvers[run_num] = solver_file.read_text()
        else:
            runs_needing_solvers.append(run_num)

    # PHASE 1: World Builders (only for missing)
    if runs_needing_worlds:
        print(f"\n[PHASE 1] {len(runs_needing_worlds)} World Builders (parallel)...")

        async def world_task(run_num, seed):
            print(f"  [F] World Builder #{run_num} ({seed}): starting...")
            world = await call_claude_async(world_builder_prompt(seed))
            print(f"  [F] World Builder #{run_num}: done ({len(world)} chars)")
            return run_num, seed, world

        world_results = await asyncio.gather(*[world_task(r, s) for r, s in runs_needing_worlds])

        for run_num, seed, world in world_results:
            world_dir = WORLDS_DIR / f"{run_num:02d}_{seed}"
            world_dir.mkdir(exist_ok=True)
            (world_dir / "world.txt").write_text(world)
            worlds[run_num] = (seed, world)
    else:
        print(f"\n[PHASE 1] All worlds exist, skipping...")

    # PHASE 2: Solvers (only for missing)
    runs_needing_solvers = [r for r in runs_needing_solvers if r not in solvers]
    if runs_needing_solvers:
        print(f"\n[PHASE 2] {len(runs_needing_solvers)} Solvers (parallel)...")

        async def solver_task(run_num):
            seed, world = worlds[run_num]
            print(f"  [F] Solver #{run_num}: starting...")
            solver = await call_claude_async(solver_prompt(world))
            print(f"  [F] Solver #{run_num}: done ({len(solver)} chars)")
            return run_num, solver

        solver_results = await asyncio.gather(*[solver_task(r) for r in runs_needing_solvers])

        for run_num, solver in solver_results:
            seed, world = worlds[run_num]
            world_dir = WORLDS_DIR / f"{run_num:02d}_{seed}"
            (world_dir / "solver.txt").write_text(solver)
            solvers[run_num] = solver
    else:
        print(f"\n[PHASE 2] All solvers exist, skipping...")

    # PHASE 3: All five extraction tracks run simultaneously
    # - Strange Worlds: all 5 in parallel (no bank)
    # - Semantic Tabu: sequential (bank accumulates)
    # - Strange Worlds+Tabu: sequential (bank accumulates)
    # - Random Seed: all 5 in parallel (no bank)
    # - Seed+Tabu: sequential (bank accumulates)
    # Parallel tracks don't block each other; sequential tracks interleave!

    print(f"\n[PHASE 3] All 5 conditions running simultaneously")

    async def all_strange_worlds_extractors():
        """Run all strange worlds extractors in parallel (skip existing)."""
        runs_needed = [r for r in run_nums if not file_exists_for_run("strange_worlds", r)]
        if not runs_needed:
            print("  [F] Strange Worlds: all exist, skipping")
            return

        async def worlds_task(run_num):
            seed, world = worlds[run_num]
            solver = solvers[run_num]
            print(f"  [F] Strange Worlds Extractor #{run_num}: starting...")
            response = await call_claude_async(extractor_prompt(world, solver))
            solution = extract_json(response)
            print(f"  [F] Strange Worlds #{run_num}: done -> {solution['label']}")
            return run_num, response, solution

        results = await asyncio.gather(*[worlds_task(r) for r in runs_needed])

        for run_num, response, solution in results:
            seed, _ = worlds[run_num]
            save_result(STRANGE_WORLDS_DIR, f"worlds_{run_num:02d}_{seed}.json",
                       "strange_worlds", run_num, response, solution, seed=seed)

    async def all_tabu_extractors():
        """Run semantic tabu extractors sequentially (bank dependency, skip existing)."""
        runs_needed = [r for r in run_nums if not file_exists_for_run("semantic_tabu", r)]
        if not runs_needed:
            print("  [A] Semantic Tabu: all exist, skipping")
            return

        for run_num in runs_needed:
            print(f"  [A] Semantic Tabu #{run_num}: starting...")
            bank_path = TABU_DIR / "bank.json"
            bank = load_bank(bank_path)
            response = await call_claude_async(denial_prompt(bank))
            solution = extract_json(response)
            print(f"  [A] Semantic Tabu #{run_num}: done -> {solution['label']}")

            save_result(TABU_DIR, f"tabu_{run_num:02d}.json",
                       "semantic_tabu", run_num, response, solution)
            bank.append(solution)
            save_bank(bank_path, bank)

    async def all_worlds_tabu_extractors():
        """Run strange worlds+tabu extractors sequentially (bank dependency, skip existing)."""
        runs_needed = [r for r in run_nums if not file_exists_for_run("strange_worlds_tabu", r)]
        if not runs_needed:
            print("  [G] Strange Worlds+Tabu: all exist, skipping")
            return

        for run_num in runs_needed:
            seed, world = worlds[run_num]
            solver = solvers[run_num]
            print(f"  [G] Strange Worlds+Tabu #{run_num}: starting...")
            bank_path = WORLDS_TABU_DIR / "bank.json"
            bank = load_bank(bank_path)
            response = await call_claude_async(combined_extractor_prompt(world, solver, bank))
            solution = extract_json(response)
            print(f"  [G] Strange Worlds+Tabu #{run_num}: done -> {solution['label']}")

            save_result(WORLDS_TABU_DIR, f"worlds_tabu_{run_num:02d}_{seed}.json",
                       "strange_worlds_tabu", run_num, response, solution, seed=seed)
            bank.append(solution)
            save_bank(bank_path, bank)

    async def all_random_seed_extractors():
        """Run random seed extractors in parallel (no bank dependency, skip existing)."""
        runs_needed = [r for r in run_nums if not file_exists_for_run("random_seed", r)]
        if not runs_needed:
            print("  [C] Random Seed: all exist, skipping")
            return

        async def seed_task(run_num):
            seed = seeds[run_nums.index(run_num)]
            print(f"  [C] Random Seed #{run_num}: starting...")
            response = await call_claude_async(random_seed_prompt(seed))
            solution = extract_json(response)
            print(f"  [C] Random Seed #{run_num}: done -> {solution['label']}")
            return run_num, seed, response, solution

        results = await asyncio.gather(*[seed_task(r) for r in runs_needed])

        for run_num, seed, response, solution in results:
            save_result(RANDOM_SEED_DIR, f"seed_{run_num:02d}_{seed}.json",
                       "random_seed", run_num, response, solution, seed=seed)

    async def all_seed_tabu_extractors():
        """Run seed+tabu extractors sequentially (bank dependency, skip existing)."""
        runs_needed = [r for r in run_nums if not file_exists_for_run("seed_tabu", r)]
        if not runs_needed:
            print("  [D] Seed+Tabu: all exist, skipping")
            return

        for run_num in runs_needed:
            seed = seeds[run_nums.index(run_num)]
            print(f"  [D] Seed+Tabu #{run_num}: starting...")
            bank_path = SEED_TABU_DIR / "bank.json"
            bank = load_bank(bank_path)
            response = await call_claude_async(seed_tabu_prompt(seed, bank))
            solution = extract_json(response)
            print(f"  [D] Seed+Tabu #{run_num}: done -> {solution['label']}")

            save_result(SEED_TABU_DIR, f"seed_tabu_{run_num:02d}_{seed}.json",
                       "seed_tabu", run_num, response, solution, seed=seed)
            bank.append(solution)
            save_bank(bank_path, bank)

    # NOTE: Taxonomy conditions (B, E, H) use run_taxonomy_with_tmux()
    # which implements the Taxonomist+Explorer multi-agent architecture.

    # Define context generators for taxonomy conditions (tmux multi-agent)
    def b_context(run_num, seed, worlds_dict, solvers_dict):
        """B: No external inspiration."""
        return ""

    def b_extra_fields(run_num, seed, worlds_dict, solvers_dict):
        return {}

    def e_context(run_num, seed, worlds_dict, solvers_dict):
        """E: Random seed inspiration."""
        return SEED_INSPIRATION.format(seed=seed)

    def e_extra_fields(run_num, seed, worlds_dict, solvers_dict):
        return {'seed': seed}

    def h_context(run_num, seed, worlds_dict, solvers_dict):
        """H: Strange Worlds inspiration."""
        if run_num not in worlds_dict:
            return ""
        _, world = worlds_dict[run_num]
        solver = solvers_dict.get(run_num, "")
        return EXTRACTION_GUIDANCE.format(world=world, solution=solver)

    def h_extra_fields(run_num, seed, worlds_dict, solvers_dict):
        # Just seed - world/solver already saved in strange_worlds files
        return {'seed': seed}

    async def all_taxonomy_extractors():
        """B: Graph-based novelty with persistent Taxonomist + fresh Explorer (tmux)."""
        await run_taxonomy_with_tmux(
            condition="taxonomy",
            label="B",
            output_dir=TAXONOMY_DIR,
            file_prefix="taxonomy",
            run_nums=run_nums,
            seeds=seeds,
            get_extra_context=b_context,
            get_extra_save_fields=b_extra_fields
        )

    async def all_taxonomy_seed_extractors():
        """E: Graph-based novelty + seed with persistent Taxonomist + fresh Explorer (tmux)."""
        await run_taxonomy_with_tmux(
            condition="taxonomy_seed",
            label="E",
            output_dir=TAXONOMY_SEED_DIR,
            file_prefix="taxonomy_seed",
            run_nums=run_nums,
            seeds=seeds,
            get_extra_context=e_context,
            get_extra_save_fields=e_extra_fields
        )

    async def all_taxonomy_worlds_extractors():
        """H: Graph-based novelty + Strange Worlds with persistent Taxonomist + fresh Explorer (tmux)."""
        await run_taxonomy_with_tmux(
            condition="taxonomy_worlds",
            label="H",
            output_dir=TAXONOMY_WORLDS_DIR,
            file_prefix="taxonomy_worlds",
            run_nums=run_nums,
            seeds=seeds,
            get_extra_context=h_context,
            get_extra_save_fields=h_extra_fields,
            worlds=worlds,
            solvers=solvers
        )

    # Run all eight extraction tracks simultaneously
    await asyncio.gather(
        all_strange_worlds_extractors(),
        all_tabu_extractors(),
        all_worlds_tabu_extractors(),
        all_random_seed_extractors(),
        all_seed_tabu_extractors(),
        all_taxonomy_extractors(),
        all_taxonomy_seed_extractors(),
        all_taxonomy_worlds_extractors()
        )

    a, b, c, d, e, f, g, h = get_progress()
    print(f"\n>>> Batch complete. Progress: A: {a}/25, B: {b}/25, C: {c}/25, D: {d}/25, E: {e}/25, F: {f}/25, G: {g}/25, H: {h}/25")

def run_batch(run_nums: list[int]):
    """Sync wrapper."""
    asyncio.run(run_batch_async(run_nums))

def run_all(start_from: int = 1):
    """Run all remaining iterations in batches."""
    for batch_start in range(start_from, 26, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE - 1, 25)
        run_nums = list(range(batch_start, batch_end + 1))
        run_batch(run_nums)

def main():
    ensure_dirs()

    a, b, c, d, e, f, g, h = get_progress()
    print(f"Current progress: A: {a}/25, B: {b}/25, C: {c}/25, D: {d}/25, E: {e}/25, F: {f}/25, G: {g}/25, H: {h}/25")

    if a == b == c == d == e == f == g == h == 25:
        print("Experiment complete!")
        return

    # Start from run 1 - auto-detects existing worlds/solvers
    run_all(start_from=1)

if __name__ == "__main__":
    main()
