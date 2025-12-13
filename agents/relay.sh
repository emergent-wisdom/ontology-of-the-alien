#!/bin/bash
# Auto-relay messages between Taxonomist and Explorer
# Watches logs and forwards [Agent] prefixed messages to the other agent

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Message Relay Active ==="
echo "Watching for [Taxonomist] and [Explorer] messages..."
echo "Press Ctrl+C to stop"
echo ""

# Track last positions in logs
TAX_POS=0
EXP_POS=0

# Ensure log files exist
touch "$SCRIPT_DIR/logs/taxonomist.log"
touch "$SCRIPT_DIR/logs/explorer.log"

while true; do
    # Check taxonomist log for [Taxonomist] messages -> send to explorer
    NEW_TAX=$(tail -c +$TAX_POS "$SCRIPT_DIR/logs/taxonomist.log" 2>/dev/null)
    if [ -n "$NEW_TAX" ]; then
        # Look for [Taxonomist] prefixed lines
        echo "$NEW_TAX" | grep -o '\[Taxonomist\].*' | while read -r line; do
            if [ -n "$line" ]; then
                echo "-> Explorer: $line"
                tmux send-keys -t explorer "$line" Enter 2>/dev/null
            fi
        done
        TAX_POS=$(wc -c < "$SCRIPT_DIR/logs/taxonomist.log")
    fi

    # Check explorer log for [Explorer] messages -> send to taxonomist
    NEW_EXP=$(tail -c +$EXP_POS "$SCRIPT_DIR/logs/explorer.log" 2>/dev/null)
    if [ -n "$NEW_EXP" ]; then
        # Look for [Explorer] prefixed lines
        echo "$NEW_EXP" | grep -o '\[Explorer\].*' | while read -r line; do
            if [ -n "$line" ]; then
                echo "-> Taxonomist: $line"
                tmux send-keys -t taxonomist "$line" Enter 2>/dev/null
            fi
        done
        EXP_POS=$(wc -c < "$SCRIPT_DIR/logs/explorer.log")
    fi

    sleep 1
done
