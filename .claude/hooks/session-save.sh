#!/bin/bash
# session-save.sh - Save session state for handoff

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SESSION_FILE=".claude/sessions/session_${TIMESTAMP}.md"

mkdir -p .claude/sessions

cat > "$SESSION_FILE" << EOF
# Session Summary - $(date)

## Work Completed
$(git log --oneline -5 2>/dev/null || echo "No commits yet")

## Current Branch
$(git branch --show-current 2>/dev/null || echo "Not in git repo")

## Files Modified
$(git diff --name-only 2>/dev/null | head -10)

## Test Status
$(if [ -f ".claude/metrics/last_test_run.txt" ]; then tail -3 .claude/metrics/last_test_run.txt; else echo "No test results"; fi)

## Open Todos
$(if [ -f ".claude/todos/current.md" ]; then grep -A 5 "## 📋 Pending" .claude/todos/current.md; else echo "No todos"; fi)

## Next Steps
- Review uncommitted changes
- Run test suite
- Update documentation
- Create PR if ready

EOF

echo "💾 Session saved to $SESSION_FILE"

# Clean up old sessions (keep last 20)
ls -t .claude/sessions/session_*.md 2>/dev/null | tail -n +21 | xargs rm -f 2>/dev/null