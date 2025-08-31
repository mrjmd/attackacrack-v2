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
        
        # Check for any test failures (must be 100% pass rate)
        if [ $TEST_EXIT_CODE -ne 0 ] || echo "$TEST_OUTPUT" | grep -q "FAILED"; then
            echo "❌ BLOCKED: Backend tests are failing!"
            echo ""
            echo "$TEST_OUTPUT" | grep -E "(FAILED|ERROR|passed|failed)" | tail -20
            echo ""
            echo "📋 Test Summary:"
            echo "$TEST_OUTPUT" | grep -E "=.*passed.*failed.*="
            echo ""
            
            # Extract pass/fail counts
            FAILED_COUNT=$(echo "$TEST_OUTPUT" | grep -oE "[0-9]+ failed" | grep -oE "[0-9]+" || echo "0")
            PASSED_COUNT=$(echo "$TEST_OUTPUT" | grep -oE "[0-9]+ passed" | grep -oE "[0-9]+" || echo "0")
            TOTAL_COUNT=$((FAILED_COUNT + PASSED_COUNT))
            
            if [ "$FAILED_COUNT" -gt 0 ]; then
                PASS_RATE=$((PASSED_COUNT * 100 / TOTAL_COUNT))
                echo "🚫 VIOLATION: Only $PASS_RATE% pass rate ($PASSED_COUNT/$TOTAL_COUNT tests passing)"
                echo "📏 REQUIRED: 100% pass rate (all tests must pass)"
            else
                echo "🚫 Tests failed to run or produced errors"
            fi
            
            echo ""
            echo "🚫 You CANNOT mark this task complete with failing tests!"
            echo "🔧 Fix ALL failing tests before proceeding"
            echo ""
            echo "Rules violated:"
            echo "  - CLAUDE.md: 'Tests written first and shown failing'"
            echo "  - CLAUDE.md: 'Implementation passes all tests'"
            echo "  - Definition of Done: Tests must be 100% passing"
            echo "  - TDD: No task completion without GREEN phase"
            exit 1
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