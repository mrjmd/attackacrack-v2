#!/bin/bash
# enforce-todo-tracking.sh - BLOCK code changes without recent todo tracking
# Forces use of todo-manager agent before writing code

# Check if todo-manager has been invoked recently
TODO_FILE=".claude/todos/current.md"
if [ ! -f "$TODO_FILE" ]; then
    echo "❌ BLOCKED: No todo tracking found!"
    echo "📝 You MUST invoke todo-manager agent first to track this task"
    echo "💡 Use: Task tool with subagent_type='todo-manager'"
    echo ""
    echo "Example:"
    echo "  Task(description='Track current work', subagent_type='todo-manager', prompt='...')"
    exit 1
fi

# Check if file was updated in last 5 minutes (300 seconds)
if [ "$(uname)" = "Darwin" ]; then
    # macOS
    FILE_MOD_TIME=$(stat -f %m "$TODO_FILE")
else
    # Linux
    FILE_MOD_TIME=$(stat -c %Y "$TODO_FILE")
fi
CURRENT_TIME=$(date +%s)
TIME_DIFF=$((CURRENT_TIME - FILE_MOD_TIME))

if [ $TIME_DIFF -gt 300 ]; then
    echo "❌ BLOCKED: Todo list is stale (last updated $((TIME_DIFF / 60)) minutes ago)"
    echo "📝 You MUST invoke todo-manager to track current task before writing code"
    echo ""
    echo "This ensures:"
    echo "  1. All work is tracked and documented"
    echo "  2. Context is preserved for session recovery"
    echo "  3. Progress is visible and measurable"
    echo ""
    echo "💡 Use: Task tool with subagent_type='todo-manager'"
    exit 1
fi

# Check if there's an in_progress task
if grep -q "\[in_progress\]" "$TODO_FILE" || grep -q "in_progress" "$TODO_FILE"; then
    echo "✅ Todo tracking active - proceeding with code changes"
else
    echo "⚠️  No task marked as in_progress in todo list"
    echo "📝 Consider updating todo-manager to mark current task as in_progress"
fi

exit 0