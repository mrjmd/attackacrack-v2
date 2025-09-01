#!/bin/bash
# enforce-tests-pass.sh - BLOCK moving to next task if tests are failing

# This hook should run when marking tasks complete or starting new ones

# Check if we're in a directory with tests
if [ -d "backend/tests" ] || [ -d "frontend/tests" ] || [ -d "tests" ]; then
    echo "🧪 Running tests to verify all pass..."
    
    # Try to run backend tests if they exist
    if [ -d "backend/tests" ]; then
        echo "Running backend tests..."
        
        # Check if we're in Docker or local
        if [ -f "docker-compose.yml" ] && docker-compose ps | grep -q "backend.*Up"; then
            # Run tests in Docker
            TEST_OUTPUT=$(docker-compose exec -T backend pytest tests/ --tb=short 2>&1)
            TEST_EXIT_CODE=$?
        else
            # Run tests locally (fallback)
            cd backend && TEST_OUTPUT=$(python -m pytest tests/ --tb=short 2>&1) && cd ..
            TEST_EXIT_CODE=$?
        fi
        
        # Extract test counts
        FAILED_COUNT=$(echo "$TEST_OUTPUT" | grep -oE "[0-9]+ failed" | grep -oE "[0-9]+" | head -1 || echo "0")
        PASSED_COUNT=$(echo "$TEST_OUTPUT" | grep -oE "[0-9]+ passed" | grep -oE "[0-9]+" | head -1 || echo "0")
        ERROR_COUNT=$(echo "$TEST_OUTPUT" | grep -oE "[0-9]+ error" | grep -oE "[0-9]+" | head -1 || echo "0")
        SKIPPED_COUNT=$(echo "$TEST_OUTPUT" | grep -oE "[0-9]+ skipped" | grep -oE "[0-9]+" | head -1 || echo "0")
        
        # Set defaults if empty
        FAILED_COUNT=${FAILED_COUNT:-0}
        PASSED_COUNT=${PASSED_COUNT:-0}
        ERROR_COUNT=${ERROR_COUNT:-0}
        SKIPPED_COUNT=${SKIPPED_COUNT:-0}
        
        # Check for ANY issues: failures, errors, or skipped tests
        if [ $TEST_EXIT_CODE -ne 0 ] || [ "$FAILED_COUNT" -gt 0 ] || [ "$ERROR_COUNT" -gt 0 ] || [ "$SKIPPED_COUNT" -gt 0 ]; then
            echo "❌ BLOCKED: Tests are NOT acceptable!"
            echo ""
            echo "📊 Test Results:"
            echo "  ✅ Passed: $PASSED_COUNT"
            echo "  ❌ Failed: $FAILED_COUNT"
            echo "  ❌ Errors: $ERROR_COUNT"
            echo "  ⏭️  Skipped: $SKIPPED_COUNT"
            echo ""
            
            if [ "$SKIPPED_COUNT" -gt 0 ]; then
                echo "🚫 SKIPPED TESTS ARE NOT ACCEPTABLE!"
                echo "   Skipped tests are a form of technical debt and false completion."
                echo "   Either:"
                echo "   1. Fix the test to pass"
                echo "   2. Remove it and document why in a TODO"
                echo ""
            fi
            
            if [ "$FAILED_COUNT" -gt 0 ] || [ "$ERROR_COUNT" -gt 0 ]; then
                TOTAL_COUNT=$((PASSED_COUNT + FAILED_COUNT + ERROR_COUNT))
                if [ "$TOTAL_COUNT" -gt 0 ]; then
                    PASS_RATE=$((PASSED_COUNT * 100 / TOTAL_COUNT))
                    echo "🚫 VIOLATION: Only $PASS_RATE% pass rate"
                else
                    echo "🚫 Tests failed to run properly"
                fi
            fi
            
            echo ""
            echo "$TEST_OUTPUT" | grep -E "(FAILED|ERROR|SKIPPED|passed|failed|skipped)" | tail -20
            echo ""
            echo "📏 REQUIREMENTS:"
            echo "  ✅ 100% pass rate (NO failures)"
            echo "  ✅ 0 errors"
            echo "  ✅ 0 skipped tests"
            echo ""
            echo "🚫 You CANNOT mark this task complete!"
            echo ""
            echo "Rules violated:"
            echo "  - CLAUDE.md: Implementation must pass ALL tests (100%)"
            echo "  - No skipped tests - all tests must run and pass"
            echo "  - Definition of Done: 100% pass rate with no skips"
            echo ""
            echo "📝 If tests must be deferred/removed:"
            echo "  1. Remove the test completely (don't skip)"
            echo "  2. Add TODO comment in test file with:"
            echo "     - What the test was testing"
            echo "     - Why it was removed"
            echo "     - When to add it back"
            echo "  3. Document in backend/tests/DEFERRED_TESTS.md"
            exit 1
        fi
        
        # Check if DEFERRED_TESTS.md was updated when tests were removed
        if [ -f "backend/tests/DEFERRED_TESTS.md" ]; then
            # Check if file was modified recently (within last 10 minutes)
            DEFERRED_FILE="backend/tests/DEFERRED_TESTS.md"
            if [ "$(uname)" = "Darwin" ]; then
                FILE_MOD_TIME=$(stat -f %m "$DEFERRED_FILE")
            else
                FILE_MOD_TIME=$(stat -c %Y "$DEFERRED_FILE")
            fi
            CURRENT_TIME=$(date +%s)
            TIME_DIFF=$((CURRENT_TIME - FILE_MOD_TIME))
            
            # If tests were removed (check git diff), ensure documentation exists
            if git diff --cached --name-only | grep -q "test_.*\.py"; then
                REMOVED_TESTS=$(git diff --cached | grep -E "^-.*def test_" | wc -l)
                if [ "$REMOVED_TESTS" -gt 0 ] && [ "$TIME_DIFF" -gt 600 ]; then
                    echo "⚠️  WARNING: Tests appear to be removed but DEFERRED_TESTS.md not updated"
                    echo "   Ensure all removed tests are documented!"
                fi
            fi
        fi
        
        echo "✅ Backend tests passing"
    fi
    
    # Try to run frontend tests if they exist
    if [ -d "frontend/tests" ] || [ -f "frontend/package.json" ]; then
        if grep -q "test" frontend/package.json 2>/dev/null; then
            echo "Running frontend tests..."
            
            if [ -f "docker-compose.yml" ] && docker-compose ps | grep -q "frontend.*Up"; then
                # Run tests in Docker
                TEST_OUTPUT=$(docker-compose exec -T frontend npm test 2>&1)
                TEST_EXIT_CODE=$?
            else
                # Run tests locally (fallback)
                cd frontend && TEST_OUTPUT=$(npm test 2>&1) && cd ..
                TEST_EXIT_CODE=$?
            fi
            
            if [ $TEST_EXIT_CODE -ne 0 ]; then
                echo "❌ BLOCKED: Frontend tests are failing!"
                echo ""
                echo "$TEST_OUTPUT" | tail -20
                echo ""
                echo "🚫 You CANNOT mark this task complete with failing tests!"
                exit 1
            fi
            
            echo "✅ Frontend tests passing"
        fi
    fi
    
    echo "✅ All tests passing - safe to proceed"
else
    echo "⚠️  No test directory found - skipping test verification"
fi

exit 0