#!/bin/bash
# Send a message to an agent
# Usage: ./send.sh <agent> "message"

if [ $# -lt 2 ]; then
    echo "Usage: ./send.sh <agent> \"message\""
    echo "  agent: taxonomist or explorer"
    exit 1
fi

AGENT=$1
shift
MESSAGE="$*"

# Check if session exists
if ! tmux has-session -t "$AGENT" 2>/dev/null; then
    echo "Error: Agent '$AGENT' is not running"
    exit 1
fi

# Send the message
tmux send-keys -t "$AGENT" "$MESSAGE" Enter

echo "Sent to $AGENT: $MESSAGE"
