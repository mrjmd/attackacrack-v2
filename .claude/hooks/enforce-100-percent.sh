#!/bin/bash
# ABSOLUTELY NO PROGRESS WITHOUT 100% TEST PASS RATE

echo "🔍 Checking test status..."

# Check if Docker is running
if ! docker-compose ps 2>/dev/null | grep -q "backend"; then
    echo "⚠️  Docker backend not running - skipping test enforcement"
    exit 0
fi

# Run tests
TEST_OUTPUT=$(docker-compose exec -T backend pytest tests/ --tb=no -q 2>&1 | tail -20)

# Extract pass/fail counts
if echo "$TEST_OUTPUT" | grep -q "passed"; then
    RESULTS=$(echo "$TEST_OUTPUT" | grep -E "passed|failed|error" | tail -1)
    
    # Check for ANY failures or errors
    if echo "$RESULTS" | grep -qE "failed|error"; then
        echo ""
        echo "❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌"
        echo "❌ ABSOLUTE VIOLATION: TESTS FAILING! ❌"
        echo "❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌"
        echo ""
        echo "$RESULTS"
        echo ""
        echo "YOU ARE FORBIDDEN FROM:"
        echo "  ❌ Claiming ANYTHING is 'done'"
        echo "  ❌ Moving to next task"
        echo "  ❌ Committing code"
        echo "  ❌ Updating todos as 'complete'"
        echo "  ❌ Making any progress claims"
        echo ""
        echo "YOU MUST:"
        echo "  ✅ Fix ALL failing tests NOW"
        echo "  ✅ Achieve 100% pass rate"
        echo "  ✅ Use Task tool with proper agents"
        echo ""
        echo "This is not optional. This is MANDATORY."
        exit 1
    fi
fi

echo "✅ All tests passing - you may proceed"
exit 0