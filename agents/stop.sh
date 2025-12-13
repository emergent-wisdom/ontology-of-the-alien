#!/bin/bash
# Stop all agents

echo "Stopping agents..."
tmux kill-session -t taxonomist 2>/dev/null && echo "  Killed taxonomist"
tmux kill-session -t explorer 2>/dev/null && echo "  Killed explorer"
tmux kill-session -t relay 2>/dev/null  # In case old relay is running
echo "Done."
