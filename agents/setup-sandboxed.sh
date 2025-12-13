#!/bin/bash
# Sandboxed agent setup using macOS sandbox-exec
# Agents communicate DIRECTLY via tmux send-keys (no relay needed)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPERIMENT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Sandboxed Taxonomy Multi-Agent System ===${NC}"
echo ""
echo -e "${YELLOW}SAFETY: Agents can ONLY write to:${NC}"
echo "  $EXPERIMENT_DIR"
echo -e "${YELLOW}Your home directory is PROTECTED${NC}"
echo ""

# Kill existing sessions (clean slate)
tmux kill-session -t taxonomist 2>/dev/null
tmux kill-session -t explorer 2>/dev/null

# Create directories
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$EXPERIMENT_DIR/taxonomy"

# Sandbox profile path (stable, not temp)
PROFILE_PATH="$SCRIPT_DIR/sandbox.sb"

# Verify sandbox profile exists
if [ ! -f "$PROFILE_PATH" ]; then
    echo "ERROR: Sandbox profile not found at $PROFILE_PATH"
    exit 1
fi

echo -e "${BLUE}Using sandbox profile: $PROFILE_PATH${NC}"

# Build taxonomist prompt with DIRECT MESSAGING instructions
cat > "$SCRIPT_DIR/.taxonomist_prompt.tmp" << EOF
$(cat "$SCRIPT_DIR/taxonomist.md")

## Current Working Directory
$EXPERIMENT_DIR

## Graph Database
taxonomy/taxonomy.db

## DIRECT MESSAGING TO EXPLORER
To send a message to the Explorer, use this command:
\`\`\`bash
tmux send-keys -t explorer '[Taxonomist] Your message here' Enter
\`\`\`

The Explorer will see your message directly in their terminal.

## REASONING
Think deeply about each decision. Show your full reasoning before acting.
Consider: What does this teach me about the structure of the solution space?
EOF

# Build explorer prompt with DIRECT MESSAGING instructions
cat > "$SCRIPT_DIR/.explorer_prompt.tmp" << EOF
$(cat "$SCRIPT_DIR/explorer.md")

## Current Working Directory
$EXPERIMENT_DIR

## DIRECT MESSAGING TO TAXONOMIST
To send a message to the Taxonomist, use this command:
\`\`\`bash
tmux send-keys -t taxonomist '[Explorer] Your message here' Enter
\`\`\`

The Taxonomist will see your message directly in their terminal.

## REASONING
Think deeply about each proposal. Show your full reasoning.
Explain why this solution is novel and what gap it fills.
EOF

# Start Taxonomist (sandboxed with full reasoning)
echo -e "${BLUE}Starting Taxonomist (sandboxed)...${NC}"
tmux new-session -d -s taxonomist -c "$EXPERIMENT_DIR"
tmux send-keys -t taxonomist "sandbox-exec -f '$PROFILE_PATH' -D HOME='$HOME' -D PROJECT_DIR='$EXPERIMENT_DIR' claude --dangerously-skip-permissions --verbose --append-system-prompt \"\$(cat $SCRIPT_DIR/.taxonomist_prompt.tmp)\" 2>&1 | tee $SCRIPT_DIR/logs/taxonomist.log" Enter

# Start Explorer (sandboxed with full reasoning)
echo -e "${BLUE}Starting Explorer (sandboxed)...${NC}"
tmux new-session -d -s explorer -c "$EXPERIMENT_DIR"
tmux send-keys -t explorer "sandbox-exec -f '$PROFILE_PATH' -D HOME='$HOME' -D PROJECT_DIR='$EXPERIMENT_DIR' claude --dangerously-skip-permissions --verbose --append-system-prompt \"\$(cat $SCRIPT_DIR/.explorer_prompt.tmp)\" 2>&1 | tee $SCRIPT_DIR/logs/explorer.log" Enter

echo ""
echo -e "${GREEN}Agents started!${NC}"
echo ""
echo "Sessions:"
echo "  tmux attach -t taxonomist   # The graph owner"
echo "  tmux attach -t explorer     # The solution proposer"
echo ""
echo "Agents communicate DIRECTLY via tmux send-keys."
echo "No relay needed - watch both terminals."
echo ""
echo "To stop everything:"
echo "  ./agents/stop.sh"
echo ""

# Wait for Claude to initialize
echo "Waiting for agents to initialize..."
sleep 8

# Kickstart the Taxonomist
echo -e "${BLUE}Kickstarting the Taxonomist...${NC}"
tmux send-keys -t taxonomist "System initialized. First, check the graph state with 'python agents/graph_cli.py state'. Then send your first request to the Explorer using: tmux send-keys -t explorer '[Taxonomist] your request' Enter" Enter

echo ""
echo -e "${GREEN}System is running!${NC}"
echo ""
echo "Watch in split terminal:"
echo "  Terminal 1: tmux attach -t taxonomist"
echo "  Terminal 2: tmux attach -t explorer"
