#!/bin/bash
# session-recovery.sh - Recover context from previous session

echo "🔄 Session Recovery Starting..."
echo "================================"

# Check for existing todos
if [ -f ".claude/todos/current.md" ]; then
    echo "📋 Found previous todo list:"
    echo ""
    grep -A 3 "## 🚀 Working On" .claude/todos/current.md
    echo ""
fi

# Check for uncommitted changes
if git status --porcelain | grep -q .; then
    echo "📝 Uncommitted changes detected:"
    git status --short | head -10
    echo ""
fi

# Check last test run results
if [ -f ".claude/metrics/last_test_run.txt" ]; then
    echo "🧪 Last test run:"
    tail -5 .claude/metrics/last_test_run.txt
    echo ""
fi

# Check if docker is running
if docker-compose ps 2>/dev/null | grep -q Up; then
    echo "🐳 Docker services are running"
else
    echo "⚠️ Docker services are not running"
    echo "💡 Run: docker-compose up -d"
fi

# Remind about TDD workflow
echo ""
echo "📚 TDD Workflow Reminder:"
echo "1. Write failing test (RED)"
echo "2. Write minimal code to pass (GREEN)"
echo "3. Refactor if needed (REFACTOR)"
echo "4. Validate with browser screenshot"
echo ""
echo "🤖 Agent workflow: todo-manager → tdd-enforcer → test-handoff → implementation → validation"
echo ""

# Check for any WIP (work in progress) markers
if grep -r "WIP\|TODO\|FIXME" backend/app frontend/src 2>/dev/null | head -5; then
    echo ""
    echo "⚠️ Found WIP/TODO markers in code:"
    grep -r "WIP\|TODO\|FIXME" backend/app frontend/src 2>/dev/null | head -5
fi

echo ""
echo "✅ Session recovery complete"
echo "================================"