#!/bin/bash
# ENFORCE USE OF TASK TOOL FOR ALL IMPLEMENTATION

# Check if we're in a coding session (recent Edit/Write operations)
LAST_EDIT=$(find . -name "*.py" -type f -mmin -5 2>/dev/null | head -1)

if [ ! -z "$LAST_EDIT" ]; then
    echo "⚠️ ================================="
    echo "⚠️ CODE CHANGES DETECTED!"
    echo "⚠️ ================================="
    echo ""
    echo "YOU MUST USE THE TASK TOOL WITH APPROPRIATE AGENTS!"
    echo ""
    echo "Required workflow:"
    echo "1. Use 'integration-test-specialist' to write tests"
    echo "2. Use 'test-handoff' to create implementation spec"
    echo "3. Use 'fastapi-implementation' to implement"
    echo "4. Use 'playwright-test-specialist' for browser validation"
    echo ""
    echo "DO NOT write code directly without agents!"
    echo ""
    
    # Check if Task tool was used recently
    TASK_LOG=".claude/tasks_used.log"
    if [ -f "$TASK_LOG" ]; then
        LAST_TASK_TIME=$(stat -f %m "$TASK_LOG" 2>/dev/null || stat -c %Y "$TASK_LOG" 2>/dev/null || echo "0")
        CURRENT_TIME=$(date +%s)
        
        # Handle if stat failed
        if [ "$LAST_TASK_TIME" = "0" ]; then
            echo "⚠️  WARNING: Could not check Task tool usage"
            exit 0
        fi
        
        TIME_DIFF=$((CURRENT_TIME - LAST_TASK_TIME))
        
        if [ $TIME_DIFF -gt 300 ]; then  # 5 minutes
            echo "❌ VIOLATION: No Task tool used in last 5 minutes!"
            echo "❌ You CANNOT proceed without using proper agents!"
            exit 1
        fi
    else
        # Log doesn't exist yet - this is okay for first run
        echo "⚠️  Task tool usage log not found - creating it"
        touch "$TASK_LOG"
        exit 0
    fi
fi

exit 0