# TDD Test Suite Design - FINAL

*Finalized: August 31, 2025*
*Based on extensive research and planning discussions*

## Executive Summary

Attack-a-Crack v2 will use strict Test-Driven Development with real browser testing via Playwright, even though it's slower than JSDOM. The trade-off is worth it: no more false "it works" claims. We'll use smart parallelization and sharding to keep test times manageable.

## Core Testing Philosophy

### The Three Commandments
1. **No code without a failing test first** (RED phase)
2. **Write minimal code to pass tests** (GREEN phase)  
3. **Browser validation required for "done"** (VALIDATE phase)

### The Test Pyramid for Attack-a-Crack

```
Production Monitoring (Continuous)
├─ Operational health checks (business hours only)
├─ Webhook monitoring (24/7 with second phone)
└─ Performance metrics (real user monitoring)

Security & Compliance (Every Deploy)
├─ OWASP dependency scanning
├─ Supply chain security check
└─ NO accessibility testing (internal tool, 2-3 users)

E2E Tests (Nightly) - Playwright
├─ Full user journeys
├─ Mobile responsiveness
├─ Cross-browser validation

Integration Tests (Every PR)
├─ API contract validation
├─ Business rule verification
├─ Database migration testing

Smoke Tests (Every PR) - 12 Deterministic Tests
├─ <2 minutes runtime
├─ Core functionality only
└─ Time-independent (work weekends/nights)

Unit Tests (Every Save)
├─ 95% coverage target
├─ <100ms per test
└─ Pure logic validation
```

## Testing Stack - Final Decisions

### Backend (FastAPI)
- **pytest** + **httpx** for async API testing
- **PostgreSQL test database** via Docker (not SQLite - match production)
- **95% coverage minimum** for all new code
- **Alembic** migration testing on every change

### Frontend (SvelteKit)
- **Playwright** for ALL browser testing (no JSDOM)
- **Real browsers** even for component tests
- **Headed mode locally** so you can watch
- **Screenshot evidence** for every feature claim

### Why Playwright Over JSDOM
- **Honesty**: Real browser = real results
- **No lies**: Can't fake screenshot proof
- **Worth slowness**: Better slow truth than fast lies
- **Parallelization**: 4-8 way sharding makes it manageable

## The 12 MVP Smoke Tests

These run ANYTIME, are deterministic, and complete in <2 minutes:

```python
# 1. Auth (15s)
@smoke test('Owner can log in')
@smoke test('Protected routes require auth')

# 2. Contacts (15s)
@smoke test('Can create a contact')
@smoke test('Contact appears in list')

# 3. CSV Import (15s)
@smoke test('Can upload CSV with 5 contacts')
@smoke test('Imported contacts appear')

# 4. Campaign Setup (15s) - Just creation, not sending!
@smoke test('Can create campaign with A/B templates')
@smoke test('Campaign appears in campaign list')

# 5. Webhook Validation (30s) - Works 24/7!
@smoke test('Webhook receives inbound SMS')
@smoke test('Received message appears in conversations')

# 6. Health (15s)
@smoke test('Health endpoint returns 200')
```

### Critical Insight: Time-Dependent vs Deterministic
- **Campaigns sending during business hours** → Operational health check
- **Daily limit enforcement** → Integration test
- **Creating a campaign** → Smoke test ✓

## Operational Health Checks

Run IN PRODUCTION during business hours only:

```python
# Runs every hour, Mon-Fri 10am-5pm ET
async def operational_health_check():
    # Use second OpenPhone number (~$15/month)
    await send_test_sms()
    await verify_webhook_received()
    await verify_campaign_sends()
    
    if any_failures:
        alert_owner("System issue detected")
```

## TDD Workflow for Every Feature

### Which Tests to Write When

```
New API Endpoint?
├─ YES → Write integration test first
└─ NO → Continue

Has Business Logic?
├─ YES → Write unit tests for each rule
└─ NO → Continue

Could Break System?
├─ YES → Add to smoke tests
└─ NO → Continue

Handles User Input?
├─ YES → Add security validation tests
└─ NO → Continue

Processes Lots of Data?
├─ YES → Add performance test (k6)
└─ NO → Done
```

### The Implementation Flow

```
1. ANALYZE REQUIREMENTS
   └─> Identify all test cases needed

2. WRITE TESTS (tdd-enforcer agent)
   └─> Integration test (API contract)
   └─> Unit tests (business logic)
   └─> Security tests (if input validation)
   └─> Performance test (if high volume)

3. RUN TESTS - SEE RED
   └─> All must fail meaningfully
   └─> Commit: "test: Add tests for [feature] (RED)"

4. IMPLEMENT MINIMUM (implementation agent)
   └─> Just enough to pass
   └─> No extra features
   └─> Commit: "feat: Implement [feature] (GREEN)"

5. REFACTOR IF NEEDED
   └─> Tests stay green
   └─> Commit: "refactor: Clean up [feature]"

6. VALIDATE WITH BROWSER
   └─> Playwright test must pass
   └─> Screenshot required as proof
```

## Playwright Scaling Strategy

### Local Development (<2 min feedback)
- Run `@smoke` tests only
- Single browser (Chromium)
- Headed mode to watch
- ~12 tests maximum

### PR Validation (<10 min)
- 4-way sharding in GitHub Actions
- Chromium + Firefox
- All `@critical` tests
- Automatic retries for flakes

### Main Branch (<15 min)
- 8-way sharding
- All browsers
- Full test suite
- Video on failures

### Implementation in GitHub Actions
```yaml
strategy:
  matrix:
    shardIndex: [1, 2, 3, 4]
    shardTotal: [4]
steps:
  - run: npx playwright test --shard=${{ matrix.shardIndex }}/${{ matrix.shardTotal }}
```

## Test Data Management

### Database Strategy
- **Separate test database** in Docker
- **Transaction rollback** after each test
- **Factory pattern** for test data
- **NO production data** in tests

### Test Data Factories
```python
# tests/factories.py
class ContactFactory:
    @staticmethod
    def create(phone=None, name=None):
        return Contact(
            phone=phone or f"+1555{random.randint(1000000, 9999999)}",
            name=name or f"Test User {random.randint(1, 1000)}"
        )

class CampaignFactory:
    @staticmethod
    def create_with_contacts(num_contacts=10):
        campaign = Campaign(
            name="Test Campaign",
            template_a="Hi {name}",
            template_b="Hello {name}"
        )
        for i in range(num_contacts):
            campaign.contacts.append(ContactFactory.create())
        return campaign
```

## Claude Enforcement Strategy

### The Agent System
1. **todo-manager** - Tracks all tasks, persists to disk
2. **tdd-enforcer** - Writes tests BEFORE implementation
3. **test-handoff** - Creates detailed implementation specs
4. **implementation agents** - Write code to pass tests
5. **integration-test-specialist** - Complex test scenarios

### Enforcement Gates
```yaml
claude_cannot_proceed_without:
  - failing_test_shown_first
  - all_tests_passing
  - coverage_report_>95%
  - playwright_screenshot_proof
  
automatic_blocks:
  - code_before_tests: "STOP - Write tests first!"
  - modifying_tests_to_pass: "STOP - Fix implementation!"
  - claiming_done_without_screenshot: "STOP - Show browser proof!"
```

## Performance Testing Strategy

### Load Testing with k6
```javascript
// tests/performance/campaign_load.js
export const options = {
  stages: [
    { duration: '1m', target: 100 },
    { duration: '3m', target: 100 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'], // 95% under 200ms
    http_req_failed: ['rate<0.01'],   // <1% errors
  },
};
```

### Performance Requirements
- API responses: <200ms (p95)
- CSV import: <5 seconds for 5,000 rows
- Campaign sending: 125 messages/minute max
- Page loads: <3 seconds

## Security Testing

### Automated Security Scanning
```yaml
# GitHub Actions
- name: OWASP Dependency Check
  uses: dependency-check/action@v3
  
- name: Snyk Security Scan
  uses: snyk/actions/python@master
```

### Security Test Requirements
- All API endpoints with input validation tests
- SQL injection prevention tests
- Rate limiting verification
- Authentication/authorization tests

## Coverage Requirements

### Targets
- **New code**: 95% minimum
- **Overall**: 90% minimum
- **Critical paths**: 100% required

### Enforcement
```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=95"
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
name: Test Pipeline
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Unit Tests
        run: |
          docker-compose up -d db redis
          docker-compose exec -T backend pytest tests/unit/ --cov

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run Integration Tests
        run: |
          docker-compose up -d
          docker-compose exec -T backend pytest tests/integration/

  e2e-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - name: Run E2E Tests (Shard ${{ matrix.shard }}/4)
        run: |
          docker-compose up -d
          npx playwright test --shard=${{ matrix.shard }}/4

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Security Scanning
        run: |
          snyk test
          safety check
```

## MCP Server Configuration

Based on our discussion, minimal is better:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/test"],
      "description": "Browser testing - CRITICAL for validation"
    },
    "ref": {
      "command": "ref-mcp",
      "args": ["--docs", "./docs", "--max-tokens", "5000"],
      "description": "Token optimization - 85% reduction"
    }
  }
}
```

Why not others?
- **GitHub MCP**: CLI works fine (`gh` command)
- **PostgreSQL MCP**: Docker exec is sufficient
- **Docker MCP**: CLI is enough
- **Filesystem MCP**: Native operations work

## Common Testing Patterns

### Testing Time-Dependent Logic
```python
from freezegun import freeze_time

@freeze_time("2024-01-15 17:45:00")  # 5:45 PM
def test_business_hours_cutoff():
    # Test stops at 6 PM
    pass
```

### Testing Webhooks
```python
async def test_webhook_processing():
    # Use second phone number for real tests
    await send_from_test_phone(MAIN_NUMBER, "Test message")
    await wait_for_webhook(timeout=10)
    assert message_received()
```

### Testing Campaign Logic
```python
async def test_daily_limit():
    # Create campaign with 200 contacts
    # Execute campaign
    # Assert exactly 125 sent
    # Assert 75 queued
```

## Definition of Done

A feature is ONLY complete when:
- [ ] Tests written first and shown failing
- [ ] Implementation passes all tests
- [ ] Coverage >95% for new code
- [ ] Integration tests pass
- [ ] Playwright browser test passes
- [ ] Screenshot captured as proof
- [ ] No duplicate code
- [ ] Performance benchmarks met
- [ ] Security scan passes

## Key Decisions Made

1. **Playwright everywhere** - Even though slower, truth > speed
2. **Smoke tests deterministic** - Must work nights/weekends
3. **Operational health checks** - For time-dependent validation
4. **Second phone number** - $15/month for webhook testing
5. **No accessibility testing** - Internal tool, 2-3 users only
6. **Minimal MCP servers** - Just Playwright and Ref
7. **95% coverage enforced** - Non-negotiable for new code
8. **Agent handoffs** - Tests by one agent, implementation by another

## The Most Important Thing

**Browser-based testing with mandatory screenshot evidence is the only way to prevent AI coding assistants from false "it works" claims.**

Every feature must be validated in a real browser. No exceptions.

---

*This document represents the complete TDD strategy for Attack-a-Crack v2, incorporating all research findings and architectural decisions.*