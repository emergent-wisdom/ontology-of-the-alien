#!/bin/bash
# Setup the Taxonomist + Explorer multi-agent system

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPERIMENT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Taxonomy Multi-Agent System ===${NC}"
echo ""

# Kill existing sessions
tmux kill-session -t taxonomist 2>/dev/null
tmux kill-session -t explorer 2>/dev/null

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Start Taxonomist (persistent)
echo -e "${BLUE}Starting Taxonomist...${NC}"
tmux new-session -d -s taxonomist -c "$EXPERIMENT_DIR"

# Build taxonomist prompt with graph tools context
TAXONOMIST_PROMPT=$(cat "$SCRIPT_DIR/taxonomist.md")
TAXONOMIST_PROMPT="$TAXONOMIST_PROMPT

## Current Working Directory
$EXPERIMENT_DIR

## Graph Database
taxonomy/taxonomy.db

## Active Agents
- taxonomist (you) - persistent, owns the graph
- explorer - spawns fresh, proposes solutions

## To send message to Explorer:
Just output your message starting with [Taxonomist]
The human will relay it, or use: tmux send-keys -t explorer '[Taxonomist] your message' Enter
"

# Write temp prompt file
echo "$TAXONOMIST_PROMPT" > "$SCRIPT_DIR/.taxonomist_prompt.tmp"

# Launch taxonomist with prompt
tmux send-keys -t taxonomist "cd $EXPERIMENT_DIR && claude --dangerously-skip-permissions --append-system-prompt \"\$(cat $SCRIPT_DIR/.taxonomist_prompt.tmp)\"" Enter

# Enable logging
tmux pipe-pane -t taxonomist -o "cat >> $SCRIPT_DIR/logs/taxonomist.log"

# Start Explorer
echo -e "${BLUE}Starting Explorer...${NC}"
tmux new-session -d -s explorer -c "$EXPERIMENT_DIR"

EXPLORER_PROMPT=$(cat "$SCRIPT_DIR/explorer.md")
EXPLORER_PROMPT="$EXPLORER_PROMPT

## Current Working Directory
$EXPERIMENT_DIR

## Active Agents
- taxonomist - persistent, owns the graph
- explorer (you) - proposes solutions

## To send message to Taxonomist:
Just output your message starting with [Explorer]
The human will relay it, or use: tmux send-keys -t taxonomist '[Explorer] your message' Enter
"

echo "$EXPLORER_PROMPT" > "$SCRIPT_DIR/.explorer_prompt.tmp"

tmux send-keys -t explorer "cd $EXPERIMENT_DIR && claude --dangerously-skip-permissions --append-system-prompt \"\$(cat $SCRIPT_DIR/.explorer_prompt.tmp)\"" Enter

# Enable logging
tmux pipe-pane -t explorer -o "cat >> $SCRIPT_DIR/logs/explorer.log"

echo ""
echo -e "${GREEN}Agents started!${NC}"
echo ""
echo "To attach to agents:"
echo "  tmux attach -t taxonomist"
echo "  tmux attach -t explorer"
echo ""
echo "To send messages between them:"
echo "  ./send.sh taxonomist '[Explorer] message'"
echo "  ./send.sh explorer '[Taxonomist] message'"
echo ""
echo "To stop:"
echo "  ./stop.sh"
echo ""

# Wait for agents to initialize
echo "Waiting for agents to initialize..."
sleep 5

# Kickstart the loop
echo -e "${BLUE}Kickstarting the Taxonomist...${NC}"
"$SCRIPT_DIR/send.sh" taxonomist "System initialized. Review the current graph state with 'python agents/graph_cli.py state' and begin the experiment by directing the Explorer."

echo ""
echo -e "${GREEN}System is running!${NC}"
echo "Watch progress: tail -f agents/logs/taxonomist.log"
