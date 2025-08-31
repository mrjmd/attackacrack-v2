#!/bin/bash
# check-test-first.sh - Enforce test-first development

# Get the file being written/edited from environment or stdin
if [ -n "$1" ]; then
    FILE_PATH="$1"
elif [ -n "$CLAUDE_FILE_PATH" ]; then
    FILE_PATH="$CLAUDE_FILE_PATH"
else
    # Try to extract from stdin if it's JSON from Claude
    JSON_INPUT=$(cat)
    if [ -n "$JSON_INPUT" ]; then
        FILE_PATH=$(echo "$JSON_INPUT" | grep -o '"path":"[^"]*"' | cut -d'"' -f4)
    fi
fi

# Skip if not a Python or TypeScript implementation file
if [[ ! "$FILE_PATH" =~ \.(py|ts|svelte)$ ]]; then
    exit 0
fi

# Skip test files themselves
if [[ "$FILE_PATH" =~ test_ ]] || [[ "$FILE_PATH" =~ \.test\. ]] || [[ "$FILE_PATH" =~ \.spec\. ]]; then
    exit 0
fi

echo "🔍 Checking for test-first development..."

# Determine test file location based on implementation file
if [[ "$FILE_PATH" =~ backend/app/(.*)\.py$ ]]; then
    # Python backend file
    BASE_NAME=$(basename "$FILE_PATH" .py)
    TEST_FILE="backend/tests/test_${BASE_NAME}.py"
    
    if [ ! -f "$TEST_FILE" ]; then
        echo "❌ BLOCKED: No test file found at $TEST_FILE"
        echo "📝 TDD Rule: Write failing tests BEFORE implementation"
        echo "💡 Run: Task agent=tdd-enforcer to write tests first"
        exit 1
    fi
    
    # Check if tests are failing (they should be for new implementation)
    if docker-compose exec -T backend pytest "$TEST_FILE" -xvs 2>/dev/null; then
        echo "⚠️ WARNING: Tests are already passing!"
        echo "📝 TDD expects tests to fail first (RED phase)"
    fi
    
elif [[ "$FILE_PATH" =~ frontend/src/(.*)\.svelte$ ]] || [[ "$FILE_PATH" =~ frontend/src/(.*)\.ts$ ]]; then
    # Frontend file
    BASE_NAME=$(basename "$FILE_PATH" | sed 's/\.\(svelte\|ts\)$//')
    TEST_FILE="frontend/tests/${BASE_NAME}.test.ts"
    
    if [ ! -f "$TEST_FILE" ]; then
        echo "❌ BLOCKED: No test file found at $TEST_FILE"
        echo "📝 TDD Rule: Write Playwright tests BEFORE implementation"
        echo "💡 Run: Task agent=playwright-test-specialist to write tests first"
        exit 1
    fi
fi

echo "✅ Test file exists - proceeding with implementation"
exit 0