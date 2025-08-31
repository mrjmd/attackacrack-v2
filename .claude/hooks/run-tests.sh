#!/bin/bash
# run-tests.sh - Automatically run tests after code changes

FILE_PATH="${1:-$CLAUDE_FILE_PATH}"

# Skip if not implementation file
if [[ ! "$FILE_PATH" =~ \.(py|ts|svelte)$ ]]; then
    exit 0
fi

echo "🧪 Running tests for $FILE_PATH..."

if [[ "$FILE_PATH" =~ backend/ ]]; then
    # Python backend tests
    if [[ "$FILE_PATH" =~ backend/app/(.*)\.py$ ]]; then
        MODULE_NAME=$(basename "$FILE_PATH" .py)
        
        # First run unit tests if they exist
        if [ -d "backend/tests/unit" ]; then
            echo "Running unit tests..."
            docker-compose exec -T backend pytest "backend/tests/unit/test_${MODULE_NAME}.py" -xvs --tb=short 2>&1 | tail -20
        fi
        
        # Check coverage
        echo "📊 Checking coverage..."
        COVERAGE=$(docker-compose exec -T backend pytest --cov=app --cov-report=term 2>&1 | grep TOTAL | awk '{print $4}' | sed 's/%//')
        
        if [ -n "$COVERAGE" ]; then
            COVERAGE_NUM=${COVERAGE%.*}
            if [ "$COVERAGE_NUM" -lt 95 ]; then
                echo "⚠️ WARNING: Coverage is ${COVERAGE}% (minimum is 95%)"
                echo "💡 Add more tests to reach coverage target"
            else
                echo "✅ Coverage: ${COVERAGE}%"
            fi
        fi
    fi
    
elif [[ "$FILE_PATH" =~ frontend/ ]]; then
    # Frontend tests with Playwright
    if which npx >/dev/null 2>&1; then
        echo "Running Playwright tests..."
        npx playwright test --grep @component --reporter=line 2>&1 | head -30
        
        # Remind about screenshot requirement
        echo ""
        echo "📸 Remember: Feature is not 'done' without browser screenshot!"
        echo "💡 Run: npx playwright test --screenshot=on"
    else
        echo "⚠️ Playwright not installed - skipping frontend tests"
    fi
fi

exit 0  # Don't block on test failures (yet)