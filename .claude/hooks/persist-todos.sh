#!/bin/bash
# persist-todos.sh - Smart history tracking for todos
# Only called manually or by todo-manager agent, NOT by TodoWrite

TODOS_DIR=".claude/todos"
HISTORY_DIR=".claude/todos/history"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE_STAMP=$(date +"%Y-%m-%d")
CURRENT_FILE="$TODOS_DIR/current.md"
HISTORY_FILE="$HISTORY_DIR/${DATE_STAMP}.md"

# Create directories if don't exist
mkdir -p "$TODOS_DIR" "$HISTORY_DIR"

# If current file exists, check if it's actually different before appending
if [ -f "$CURRENT_FILE" ]; then
    # Get the last snapshot from history if it exists
    if [ -f "$HISTORY_FILE" ]; then
        # Extract last snapshot (everything after the last "### Snapshot at")
        LAST_SNAPSHOT=$(tac "$HISTORY_FILE" | sed '/### Snapshot at/q' | tac | tail -n +2)
        CURRENT_CONTENT=$(tail -n +3 "$CURRENT_FILE")  # Skip header lines
        
        # Only append if content has actually changed
        if [ "$LAST_SNAPSHOT" != "$CURRENT_CONTENT" ]; then
            echo "" >> "$HISTORY_FILE"
            echo "---" >> "$HISTORY_FILE"
            echo "### Snapshot at $(date +"%H:%M:%S")" >> "$HISTORY_FILE"
            cat "$CURRENT_FILE" >> "$HISTORY_FILE"
            echo "📚 History snapshot saved (content changed)"
        else
            echo "⏭️  Skipping history snapshot (no changes detected)"
        fi
    else
        # First snapshot of the day
        echo "### Snapshot at $(date +"%H:%M:%S")" >> "$HISTORY_FILE"
        cat "$CURRENT_FILE" >> "$HISTORY_FILE"
        echo "📚 First history snapshot of the day saved"
    fi
    
    # Update timestamp in current file
    sed -i.bak "2s/.*/*Last updated: $(date)*/" "$CURRENT_FILE"
else
    # Create new template
    cat > "$CURRENT_FILE" << EOF
# Current Todo List
*Last updated: $(date)*

## 🚀 Working On
Nothing currently - all tasks completed!

## 📋 Pending
- Initialize FastAPI project structure
- Set up PostgreSQL schema with Alembic
- Implement OpenPhone webhook receiver with queue
- Configure Celery with Redis for async processing

## 📝 Session Notes
- Session started: $(date)
- Context: Docker environment setup complete
EOF
fi

# Create or update the master history index
INDEX_FILE="$HISTORY_DIR/INDEX.md"
if [ ! -f "$INDEX_FILE" ]; then
    cat > "$INDEX_FILE" << EOF
# Todo History Index

This directory contains complete history of all todos and context.

## Structure
- \`current.md\` - Active todo list
- \`history/YYYY-MM-DD.md\` - Daily consolidated history
- \`history/archive_*.md\` - Timestamped snapshots
- \`history/INDEX.md\` - This file

## Quick Access
EOF
fi

# Add today's entry to index if not already there
if ! grep -q "$DATE_STAMP" "$INDEX_FILE"; then
    echo "- [$DATE_STAMP](./${DATE_STAMP}.md) - $(date +"%B %d, %Y")" >> "$INDEX_FILE"
fi

# Keep last 100 archive files (about 2 weeks of heavy usage)
ls -t "$HISTORY_DIR"/archive_*.md 2>/dev/null | tail -n +101 | xargs rm -f 2>/dev/null

echo "📝 Todos persisted to $CURRENT_FILE"
echo "📚 History saved to $HISTORY_FILE"
echo "🗂️ Archive created at $ARCHIVE_FILE"