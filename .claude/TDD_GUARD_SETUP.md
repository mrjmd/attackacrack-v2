# TDD Guard Setup for Attack-a-Crack v2

## Installation

### 1. Install TDD Guard Globally
```bash
npm install -g tdd-guard
```

### 2. Initialize TDD Guard in Project
```bash
tdd-guard init
```

This creates `.tdd-guard/config.json` with project-specific settings.

### 3. Install Language-Specific Reporters

For Python (pytest):
```bash
pip install pytest-json-report
```

For JavaScript/TypeScript (Vitest):
```bash
npm install -D tdd-guard-vitest
```

For Playwright:
```bash
npm install -D @playwright/test
```

## Configuration

### .tdd-guard/config.json
```json
{
  "version": "1.0.0",
  "project": "attackacrack-v2",
  "languages": {
    "python": {
      "testRunner": "pytest",
      "testPattern": "tests/**/test_*.py",
      "coverageThreshold": 95
    },
    "typescript": {
      "testRunner": "vitest",
      "testPattern": "**/*.test.ts",
      "coverageThreshold": 95
    },
    "svelte": {
      "testRunner": "playwright",
      "testPattern": "tests/**/*.spec.ts",
      "requireScreenshot": true
    }
  },
  "rules": {
    "blockWithoutTest": true,
    "requireFailingTestFirst": true,
    "preventTestModification": true,
    "enforceMinimalImplementation": true
  },
  "validationMessages": {
    "noTest": "❌ BLOCKED: Write test first! Use: Task agent=tdd-enforcer",
    "passingTest": "❌ BLOCKED: Test must fail first (RED phase)",
    "modifyingTest": "❌ BLOCKED: Fix implementation, not test!",
    "overImplementation": "⚠️ WARNING: Implementing more than test requires"
  }
}
```

## Integration with Claude Code

### Add to Claude Hooks
Update `.claude/settings.local.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "tdd-guard check",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Configure Test Reporters

#### Python (pytest.ini)
```ini
[tool:pytest]
addopts = --json-report --json-report-file=.tdd-guard/test-results.json
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

#### TypeScript (vitest.config.ts)
```typescript
import { defineConfig } from 'vitest/config'
import { tddGuardReporter } from 'tdd-guard-vitest'

export default defineConfig({
  test: {
    reporters: ['default', tddGuardReporter()],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      threshold: {
        lines: 95,
        functions: 95,
        branches: 95,
        statements: 95
      }
    }
  }
})
```

#### Playwright (playwright.config.ts)
```typescript
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  reporter: [
    ['line'],
    ['json', { outputFile: '.tdd-guard/playwright-results.json' }]
  ],
  use: {
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  }
})
```

## Usage

### Manual Check
```bash
# Check if implementation can proceed
tdd-guard check

# Run with specific file
tdd-guard check backend/app/services/campaign.py

# Force validation
tdd-guard validate --strict
```

### Automatic via Hooks
Once configured, TDD Guard automatically:
1. Blocks code without tests
2. Ensures tests fail first
3. Prevents test modification to pass
4. Validates coverage thresholds

## Common Workflows

### Starting New Feature
```bash
# 1. TDD Guard blocks implementation
$ claude-code "implement user authentication"
❌ BLOCKED: No test file found

# 2. Write tests first
$ claude-code "Task agent=tdd-enforcer feature=authentication"
✅ Tests written: tests/test_authentication.py

# 3. Verify tests fail
$ tdd-guard validate
✅ Tests failing (RED phase)

# 4. Now implementation allowed
$ claude-code "implement authentication to pass tests"
✅ Implementation proceeding...
```

### Fixing Bug
```bash
# 1. Write failing test for bug
$ claude-code "Task agent=tdd-enforcer bug='login fails with special chars'"

# 2. TDD Guard ensures test fails
$ tdd-guard check
✅ Bug reproduction test failing

# 3. Fix implementation
$ claude-code "fix login special character bug"

# 4. Validate fix
$ tdd-guard validate
✅ All tests passing
✅ Coverage: 96%
```

## Troubleshooting

### "Permission denied" Error
```bash
chmod +x .claude/hooks/*.sh
chmod +x node_modules/.bin/tdd-guard
```

### Test Results Not Found
Ensure test reporters are configured correctly:
```bash
# Check reporter output
ls -la .tdd-guard/
# Should see: test-results.json, playwright-results.json, etc.
```

### False Positives
If TDD Guard incorrectly blocks:
```bash
# Temporarily disable
tdd-guard disable

# Re-enable
tdd-guard enable
```

### Clean State
```bash
# Reset TDD Guard state
rm -rf .tdd-guard/cache
tdd-guard init --force
```

## Best Practices

1. **Always Start with Tests**: Let TDD Guard enforce this
2. **Small Iterations**: Write one test, implement, repeat
3. **Don't Fight the Tool**: If blocked, you're likely doing TDD wrong
4. **Use Agent Workflow**: Leverage specialized agents for each phase
5. **Commit at Green**: After tests pass, commit immediately

## Integration with CI/CD

### GitHub Actions
```yaml
name: TDD Validation
on: [push, pull_request]

jobs:
  tdd-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install TDD Guard
        run: npm install -g tdd-guard
      - name: Validate TDD Compliance
        run: tdd-guard validate --strict --ci
```

## Metrics and Reporting

TDD Guard tracks:
- Tests written before code: ✅/❌
- Time from RED to GREEN
- Coverage improvements
- Refactoring frequency

View metrics:
```bash
tdd-guard metrics --report
```

---

*TDD Guard ensures Attack-a-Crack v2 maintains strict TDD discipline, preventing the chaos that plagued v1.*