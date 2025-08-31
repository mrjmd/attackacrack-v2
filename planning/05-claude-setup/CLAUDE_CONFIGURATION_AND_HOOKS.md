# Claude Configuration and Hooks for Attack-a-Crack v2

*Purpose: Prevent v1 pitfalls through automated enforcement and validation*

## 🎯 Overview

This document outlines Claude Code configuration, hooks, and settings that enforce TDD, prevent false "it works" claims, and maintain code quality throughout development.

## 🔧 Claude Settings Configuration

### .claude/settings.json
```json
{
  "version": "1.0.0",
  "project": "attackacrack-v2",
  "enforcement": {
    "tdd": "mandatory",
    "coverage_minimum": 95,
    "browser_validation": "required",
    "agent_workflow": "enforced"
  },
  "hooks": {
    "pre_implementation": [
      "check_tests_exist",
      "verify_tests_failing",
      "check_coverage_baseline"
    ],
    "post_implementation": [
      "run_all_tests",
      "check_coverage_increased",
      "capture_browser_screenshot"
    ],
    "pre_commit": [
      "run_unit_tests",
      "run_integration_tests",
      "check_coverage_threshold",
      "run_security_scan"
    ],
    "task_start": [
      "invoke_todo_manager",
      "check_for_duplicates"
    ]
  },
  "validation": {
    "require_screenshot_proof": true,
    "require_test_output": true,
    "require_coverage_report": true,
    "block_without_tests": true
  },
  "agents": {
    "auto_invoke": true,
    "default_flow": "todo -> test -> handoff -> implement -> validate"
  },
  "banned_patterns": [
    "if TEST_MODE:",
    "# type: ignore",
    "skip_test",
    "TODO: test later",
    "it works",
    "should work",
    "probably works"
  ],
  "required_patterns": {
    "tests": "tests/test_*.py",
    "implementation": "app/*.py",
    "coverage": ">= 95%"
  }
}
```

## 🪝 Hook Implementations

### Pre-Implementation Hook
```bash
#!/bin/bash
# .claude/hooks/pre-implementation.sh

echo "🔍 Pre-Implementation Checks..."

# Check if tests exist for the feature
if ! find tests -name "*test_${FEATURE_NAME}*" | grep -q .; then
  echo "❌ ERROR: No tests found for ${FEATURE_NAME}"
  echo "📝 Run: claude-code invoke tdd-enforcer --feature ${FEATURE_NAME}"
  exit 1
fi

# Verify tests are failing (RED phase)
if docker-compose exec backend pytest tests/test_${FEATURE_NAME}.py -x 2>/dev/null; then
  echo "❌ ERROR: Tests are already passing!"
  echo "This violates TDD - tests must fail first"
  exit 1
fi

echo "✅ Tests exist and are failing - ready for implementation"
```

### Post-Implementation Hook
```bash
#!/bin/bash
# .claude/hooks/post-implementation.sh

echo "🔍 Post-Implementation Validation..."

# Run tests
if ! docker-compose exec backend pytest tests/test_${FEATURE_NAME}.py -x; then
  echo "❌ ERROR: Tests still failing after implementation"
  exit 1
fi

# Check coverage
COVERAGE=$(docker-compose exec backend pytest tests/test_${FEATURE_NAME}.py --cov=app --cov-report=term | grep TOTAL | awk '{print $4}' | sed 's/%//')
if [ "$COVERAGE" -lt 95 ]; then
  echo "❌ ERROR: Coverage is ${COVERAGE}%, minimum is 95%"
  exit 1
fi

# Require browser screenshot
if [ ! -f "tests/screenshots/${FEATURE_NAME}.png" ]; then
  echo "❌ ERROR: No browser screenshot found"
  echo "📸 Run: docker-compose exec frontend npx playwright test --screenshot"
  exit 1
fi

echo "✅ All validation passed!"
```

### Task Start Hook
```bash
#!/bin/bash
# .claude/hooks/task-start.sh

echo "🚀 Starting new task..."

# Auto-invoke todo-manager
echo "📝 Invoking todo-manager agent..."
claude-code invoke todo-manager --task "$1"

# Check for duplicate implementations
echo "🔍 Checking for existing implementations..."
if grep -r "def $FUNCTION_NAME" app/; then
  echo "⚠️ WARNING: Function $FUNCTION_NAME already exists"
  echo "Check app/ directory before creating duplicate"
fi

# Remind about TDD
echo "📋 TDD Reminder:"
echo "1. Write failing test first (RED)"
echo "2. Write minimal code to pass (GREEN)"
echo "3. Refactor if needed (REFACTOR)"
echo "4. Validate in browser with screenshot"
```

## 🚫 Validation Gates

### The "It Works" Detector
```python
# .claude/validators/works_detector.py
import re
import sys

BANNED_PHRASES = [
    r"it works",
    r"should work",
    r"probably works",
    r"seems to work",
    r"working great",
    r"ready to rock",
    r"good to go",
    r"all set"
]

def check_commit_message(message):
    """Prevent false confidence in commit messages."""
    for phrase in BANNED_PHRASES:
        if re.search(phrase, message, re.IGNORECASE):
            print(f"❌ Banned phrase detected: '{phrase}'")
            print("Provide concrete evidence instead:")
            print("- Test results")
            print("- Coverage report")
            print("- Screenshot proof")
            return False
    return True

if __name__ == "__main__":
    message = sys.argv[1]
    if not check_commit_message(message):
        sys.exit(1)
```

### Coverage Enforcer
```yaml
# .github/workflows/coverage-check.yml
name: Coverage Enforcement

on: [push, pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check coverage
        run: |
          coverage_report=$(docker-compose exec -T backend pytest --cov=app --cov-report=term)
          coverage_percent=$(echo "$coverage_report" | grep TOTAL | awk '{print $4}' | sed 's/%//')
          
          if [ "$coverage_percent" -lt 95 ]; then
            echo "❌ Coverage is ${coverage_percent}%, minimum is 95%"
            exit 1
          fi
          
          echo "✅ Coverage is ${coverage_percent}%"
```

## 🤖 Agent Auto-Invocation

### Claude Commands Configuration
```json
{
  "commands": {
    "new-feature": {
      "description": "Start a new feature with TDD",
      "workflow": [
        "todo-manager create '$1'",
        "tdd-enforcer write-tests '$1'",
        "test-handoff create-spec",
        "auto-select-implementation-agent",
        "playwright-test-specialist validate"
      ]
    },
    "fix-bug": {
      "description": "Fix a bug with test-first approach",
      "workflow": [
        "todo-manager create 'Fix: $1'",
        "tdd-enforcer write-failing-test-for-bug",
        "auto-fix-implementation",
        "validate-fix"
      ]
    }
  }
}
```

## 🔍 Duplicate Detection

### Prevent v1's Multiple Implementations Problem
```python
# .claude/validators/duplicate_detector.py
import ast
import os
from pathlib import Path

def find_duplicates(directory="app"):
    """Find duplicate function/class definitions."""
    functions = {}
    classes = {}
    
    for py_file in Path(directory).glob("**/*.py"):
        tree = ast.parse(py_file.read_text())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in functions:
                    print(f"❌ Duplicate function '{node.name}' found in:")
                    print(f"  - {functions[node.name]}")
                    print(f"  - {py_file}")
                else:
                    functions[node.name] = py_file
            
            elif isinstance(node, ast.ClassDef):
                if node.name in classes:
                    print(f"❌ Duplicate class '{node.name}' found in:")
                    print(f"  - {classes[node.name]}")
                    print(f"  - {py_file}")
                else:
                    classes[node.name] = py_file
    
    return len(functions) + len(classes)

if __name__ == "__main__":
    duplicates = find_duplicates()
    if duplicates > 0:
        print(f"\n❌ Found {duplicates} duplicate definitions!")
        sys.exit(1)
    print("✅ No duplicates found")
```

## 📊 Metrics Tracking

### Development Metrics Logger
```python
# .claude/metrics/tracker.py
import json
import time
from datetime import datetime
from pathlib import Path

class DevelopmentMetrics:
    def __init__(self):
        self.metrics_file = Path(".claude/metrics/metrics.json")
        self.metrics_file.parent.mkdir(exist_ok=True)
        
    def track_feature(self, feature_name, metrics):
        """Track metrics for feature development."""
        data = {
            "feature": feature_name,
            "timestamp": datetime.now().isoformat(),
            "tests_written_first": metrics.get("tests_first", False),
            "coverage": metrics.get("coverage", 0),
            "time_to_implement": metrics.get("implementation_time", 0),
            "browser_validated": metrics.get("browser_test", False),
            "lines_of_code": metrics.get("loc", 0),
            "test_count": metrics.get("test_count", 0)
        }
        
        # Append to metrics file
        existing = []
        if self.metrics_file.exists():
            existing = json.loads(self.metrics_file.read_text())
        existing.append(data)
        self.metrics_file.write_text(json.dumps(existing, indent=2))
        
        # Check TDD compliance
        if not data["tests_written_first"]:
            print("⚠️ WARNING: Feature developed without TDD!")
        
        if data["coverage"] < 95:
            print(f"⚠️ WARNING: Coverage only {data['coverage']}%")
```

## 🚀 Auto-Recovery from Interruption

### Session Recovery Hook
```bash
#!/bin/bash
# .claude/hooks/session-recovery.sh

echo "🔄 Recovering from interruption..."

# Check for active todos
if [ -f ".claude/todos/current.md" ]; then
  echo "📋 Found active todos:"
  grep "IN PROGRESS" .claude/todos/current.md
  
  # Get last working file
  LAST_FILE=$(grep "File:" .claude/todos/current.md | tail -1 | cut -d: -f2)
  if [ -n "$LAST_FILE" ]; then
    echo "📂 Last working on: $LAST_FILE"
  fi
  
  # Get last command
  LAST_CMD=$(grep "docker-compose exec" .claude/todos/current.md | tail -1)
  if [ -n "$LAST_CMD" ]; then
    echo "🔧 Last command: $LAST_CMD"
    echo "Run this to continue testing"
  fi
fi

# Check test status
echo "🧪 Checking test status..."
docker-compose exec backend pytest tests/ --tb=no -q

# Check for uncommitted changes
echo "📝 Checking git status..."
git status --short
```

## 🎯 Key Configuration Points

### 1. Enforce TDD Workflow
- Tests MUST exist before implementation
- Tests MUST fail initially
- Coverage MUST be >95%
- Browser screenshot MUST be captured

### 2. Prevent False Claims
- Ban "it works" phrases
- Require concrete evidence
- Validate in real browser
- Check actual functionality

### 3. Avoid Duplication
- Check for existing implementations
- Prevent multiple versions of same feature
- Single source of truth

### 4. Maintain Context
- Auto-save todos after every change
- Track file paths and line numbers
- Preserve commands for recovery
- Session handoff documentation

### 5. Automate Quality
- Pre-commit hooks
- CI/CD gates
- Coverage enforcement
- Security scanning

## 📋 Implementation Checklist

To set up these hooks and configuration:

1. **Create hook scripts**:
```bash
mkdir -p .claude/hooks
chmod +x .claude/hooks/*.sh
```

2. **Configure Git hooks**:
```bash
git config core.hooksPath .claude/hooks
```

3. **Set up GitHub Actions**:
```bash
cp .claude/workflows/* .github/workflows/
```

4. **Install validation tools**:
```bash
pip install -r .claude/requirements-validation.txt
```

5. **Configure Claude Code**:
```bash
cp .claude/settings.json .
```

## 🔥 The Most Important Configuration

If you implement only ONE thing, make it the pre-implementation hook that blocks code without tests. This single gate prevents 90% of v1's problems:

```bash
# The one hook to rule them all
if [ $(find tests -name "*test_${FEATURE}*" | wc -l) -eq 0 ]; then
  echo "❌ NO TESTS = NO CODE"
  exit 1
fi
```

---

*These configurations and hooks ensure that Attack-a-Crack v2 maintains quality from day one and avoids all the pitfalls that plagued v1.*