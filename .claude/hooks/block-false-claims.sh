#!/bin/bash
# BLOCK ANY FALSE CLAIMS OF COMPLETION

# Words that indicate completion claims
COMPLETION_WORDS="done|complete|finished|working|success|ready|achieved|accomplished"

# Check if message contains completion claims
# This would need to be integrated with message content somehow
# For now, check test status whenever code is touched

echo "⚔️ Verifying claims against reality..."

# Get test status
TEST_STATUS=$(docker-compose exec -T backend pytest tests/ --tb=no -q 2>&1 | tail -1)

if echo "$TEST_STATUS" | grep -q "failed"; then
    echo ""
    echo "🚨🚨🚨 FALSE CLAIM DETECTED! 🚨🚨🚨"
    echo ""
    echo "You CANNOT claim success with failing tests!"
    echo ""
    echo "Reality: $TEST_STATUS"
    echo ""
    echo "Fix the tests or retract your claim!"
    exit 1
fi

# Check if todos are up to date
TODO_FILE=".claude/todos/current.md"
if [ -f "$TODO_FILE" ]; then
    # Check if any "in_progress" items exist when claiming done
    if grep -q "in_progress" "$TODO_FILE"; then
        echo ""
        echo "🚨 INCOMPLETE WORK DETECTED!"
        echo ""
        echo "You have tasks marked as 'in_progress' in todos!"
        echo "You must update todos before claiming completion!"
        exit 1
    fi
fi

exit 0