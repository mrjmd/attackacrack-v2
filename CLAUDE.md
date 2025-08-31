# CLAUDE.md - Attack-a-Crack v2 Development Rules & Architecture

## 🚀 SESSION START PROTOCOL 🚀

**EVERY new session MUST begin with:**
1. Read this CLAUDE.md file completely
2. Read `.claude/todos/current.md` for current state and pending tasks
3. Continue with pending tasks using appropriate agents

**Single Source of Truth**: `.claude/todos/current.md` contains ALL current context

## 🚨 MANDATORY AGENT-BASED TDD WORKFLOW 🚨

### ⚠️ AUTOMATIC WORKFLOW - NO MANUAL INTERVENTION ⚠️

**EVERY feature request MUST automatically trigger this workflow:**

1. **todo-manager agent** → Track task and persist to disk
2. **tdd-enforcer agent** → Write comprehensive tests FIRST
3. **test-handoff agent** → Create implementation specification
4. **[specialist] agent** → Implement to pass tests
5. **playwright-test-specialist** → Validate in browser with screenshot

**You are NOT ALLOWED to:**
- Write code directly without using agents
- Skip any step in the workflow
- Claim completion without browser screenshot
- Modify tests to match buggy implementation

### 🤖 AGENT INVOCATION IS MANDATORY

When user requests ANY feature or fix:
```
1. IMMEDIATELY invoke todo-manager to track
2. IMMEDIATELY invoke appropriate test specialist
3. DO NOT write any code yourself
4. DO NOT proceed without agent handoff
```

### You CANNOT Claim "Done" Without:
- [ ] todo-manager has tracked the task
- [ ] Test specialist wrote failing tests (RED)
- [ ] Implementation agent made tests pass (GREEN)
- [ ] playwright-test-specialist validated with screenshot
- [ ] Coverage report showing >95% for new code

## 🤖 AGENT SELECTION MATRIX

### Which Agent to Use When:

| Task Type | Test Agent | Implementation Agent |
|-----------|------------|---------------------|
| API Endpoint | integration-test-specialist | fastapi-implementation |
| UI Component | playwright-test-specialist | sveltekit-implementation |
| Business Logic | unit-test-specialist | [domain]-specialist |
| Database Operation | integration-test-specialist | database-specialist |
| Campaign Logic | unit-test-specialist | campaign-specialist |
| OpenPhone Integration | integration-test-specialist | openphone-specialist |
| Pure Functions | unit-test-specialist | fastapi-implementation |
| E2E Flow | playwright-test-specialist | Multiple agents |

### Agent Workflow Example:
```
User: "Add daily limit to campaigns"
Claude: 
1. → todo-manager (tracks task)
2. → unit-test-specialist (writes business logic tests)
3. → integration-test-specialist (writes API tests)
4. → test-handoff (creates implementation spec)
5. → campaign-specialist (implements logic)
6. → playwright-test-specialist (validates in browser)
```

## 📁 v1 Reference Location
**Attack-a-Crack v1 location**: `../openphone-sms/`

When implementing v2 features, reference v1 for:
- What worked well (to keep)
- What failed (to avoid)
- Existing patterns (to improve)

Key v1 directories for reference:
- `../openphone-sms/services/` - 49 service files (too many!)
- `../openphone-sms/repositories/` - 38 repository files (over-abstracted)
- `../openphone-sms/models/` - Database models
- `../openphone-sms/tasks/` - Celery tasks

## 🔴 INSTANT FAILURE CONDITIONS
If you do ANY of these, STOP immediately:
- Writing implementation before test exists
- Claiming "it works" without browser screenshot
- Creating duplicate functionality
- Modifying tests to match buggy code
- Skipping edge case tests
- Using `if TEST_MODE:` or any test bypasses
- **NOT USING AGENTS FOR IMPLEMENTATION**

## 📁 Project Architecture

### Tech Stack
- **Backend**: FastAPI (async throughout, no sync/async duplication)
- **Frontend**: SvelteKit (SSR, file-based routing)
- **Database**: PostgreSQL (via Docker)
- **Queue**: Celery + Redis (async tasks)
- **Testing**: Pytest + Playwright (real browsers only)

### Directory Structure
```
attackacrack-v2/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── api/            # Route handlers
│   │   └── core/           # Shared utilities
│   └── tests/
│       ├── unit/           # Fast, isolated tests
│       ├── integration/    # API tests
│       └── e2e/           # Playwright browser tests
├── frontend/
│   └── src/
│       ├── routes/        # SvelteKit pages
│       └── lib/          # Components & utilities
└── docker-compose.yml
```

### Core Principles
1. **Modular Monolith**: Clear boundaries, single deployment
2. **DRY (Don't Repeat Yourself)**: One implementation per feature
3. **Repository Pattern**: All DB access through repositories
4. **Service Layer**: Business logic separated from routes
5. **Test Coverage**: 95% minimum for new code

## 🧪 Testing Strategy

### Test Types & When to Write Them

#### 1. Smoke Tests (@smoke) - Deterministic, Always Pass
```python
# 12 core tests that verify system is alive
# Run on every PR, <2 minutes total
# Examples:
@smoke test('Owner can log in')
@smoke test('Webhook receives inbound SMS')  # Works 24/7!
@smoke test('Can create campaign')  # Just creation, not sending
```

#### 2. Integration Tests - Business Logic
```python
# Test API endpoints and service methods
# Mock external services, use test database
# Examples:
test('Campaign respects 125 daily limit')
test('Business hours enforced 9am-6pm ET')
test('Opt-out prevents future messages')
```

#### 3. E2E Tests - Critical User Journeys
```python
# Playwright tests with real browser
# Only for critical paths
# Examples:
test('Complete campaign creation flow')
test('CSV import to campaign execution')
```

#### 4. Unit Tests - Pure Logic
```python
# Test individual functions
# No I/O, no database, pure logic
# <100ms per test
```

### The TDD Workflow for Every Feature

```
1. ANALYZE: What needs to be built?
   └─> Identify test cases needed

2. WRITE TESTS: Start with integration test
   └─> API endpoint test (defines contract)
   └─> Unit tests for business logic
   └─> Security tests if handling input
   └─> Performance test if high volume

3. RED PHASE: Run tests, see failures
   └─> Meaningful error messages
   └─> Commit: "test: Add tests for [feature] (RED)"

4. GREEN PHASE: Implement minimum code
   └─> Just enough to pass
   └─> No extra features
   └─> Commit: "feat: Implement [feature] (GREEN)"

5. REFACTOR: Clean up implementation
   └─> Tests stay green
   └─> Extract helpers
   └─> Commit: "refactor: Clean up [feature]"

6. VALIDATE: Browser test with Playwright
   └─> Screenshot proof required
   └─> Add to smoke tests if critical
```

## 🐳 Docker Development

### ALL Commands Run in Docker
```bash
# Backend tests
docker-compose exec backend pytest tests/ -xvs

# Specific test file
docker-compose exec backend pytest tests/test_campaigns.py::test_daily_limit -xvs

# With coverage
docker-compose exec backend pytest --cov=app --cov-report=term-missing

# Frontend tests (Playwright)
docker-compose exec frontend npm test

# Database migrations
docker-compose exec backend alembic upgrade head

# Celery tasks
docker-compose exec celery celery -A app.worker status
```

### Never Run Locally
- ❌ `pytest tests/` - Wrong, not in container
- ✅ `docker-compose exec backend pytest tests/` - Correct

## 🔒 Security Requirements

### Every Input Must Be Validated
```python
# Pydantic schemas enforce validation
class ContactCreate(BaseModel):
    phone: str = Field(..., regex=r'^\+1\d{10}$')
    name: str = Field(..., min_length=1, max_length=100)
    
    @validator('phone')
    def normalize_phone(cls, v):
        return normalize_phone_number(v)
```

### Security Tests Required For:
- All API endpoints accepting user input
- File uploads (CSV import)
- External API integrations
- Authentication/authorization

### Automated Security Scanning
```yaml
# GitHub Actions
- name: OWASP Dependency Check
  uses: dependency-check/action@v3
  
- name: Snyk Security Scan
  uses: snyk/actions/python@master
```

## 📊 Performance Standards

### Response Time Requirements
- API endpoints: <200ms (p95)
- Page loads: <3 seconds
- CSV import: <5 seconds for 5,000 rows
- Campaign sending: 125 messages/minute max

### Performance Tests with k6
```javascript
// Load test for campaign API
export const options = {
  stages: [
    { duration: '1m', target: 100 },  // Ramp up
    { duration: '3m', target: 100 },  // Stay at 100
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],
  },
};
```

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow
```yaml
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2, 3, 4]  # 4-way parallel
    
    steps:
      - name: Run Tests (Shard ${{ matrix.shard }})
        run: |
          docker-compose up -d
          docker-compose exec -T backend pytest --shard=${{ matrix.shard }}/4
          docker-compose exec -T frontend npx playwright test --shard=${{ matrix.shard }}/4
```

### Deployment Gates
1. All tests must pass
2. Coverage must be >95%
3. Security scan must pass
4. Performance benchmarks met
5. Manual approval for production

## 🤖 MCP Server Configuration

### Essential MCPs for Development
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["playwright-mcp"],
      "description": "Browser testing and automation"
    }
  }
}
```

### MCP Best Practices
- Keep server count under 10 for performance
- Use Ref MCP to reduce token usage by 85%
- Configure `MAX_MCP_OUTPUT_TOKENS=50000`
- Clear context periodically in long sessions

## 📝 Documentation Requirements

### Every Feature Needs:
1. **Docstring** explaining purpose and usage
2. **Type hints** for all parameters and returns
3. **Tests** documenting expected behavior
4. **README** updates if adding new patterns

### Docstring Format
```python
def send_campaign(campaign_id: int, test_mode: bool = False) -> CampaignResult:
    """
    Send messages for a campaign respecting daily limits and business hours.
    
    Args:
        campaign_id: The campaign to execute
        test_mode: If True, only sends to test number
        
    Returns:
        CampaignResult with sent/queued/failed counts
        
    Raises:
        CampaignNotFound: If campaign doesn't exist
        RateLimitExceeded: If daily limit would be exceeded
    """
```

## 🎯 Definition of Done

A feature is ONLY complete when:
- [ ] Tests written first and shown failing
- [ ] Implementation passes all tests
- [ ] Coverage >95% for new code
- [ ] Browser test passes with screenshot
- [ ] No duplicate code introduced
- [ ] Performance benchmarks met
- [ ] Security scan passes
- [ ] Documentation updated
- [ ] Code reviewed (if team > 1)
- [ ] Deployed to staging successfully

## ⚠️ Common Pitfalls to Avoid

### From v1 Lessons Learned:
1. **No sync/async duplication** - FastAPI is async throughout
2. **No multiple CSV importers** - One implementation only
3. **No complex service registry** - FastAPI's DI is sufficient
4. **No premature abstraction** - Build for 1, design for 10, architect for 100
5. **No "it works" without proof** - Browser screenshot required

### Database Mistakes to Avoid:
- Not using transactions for multi-step operations
- Forgetting to commit after bulk inserts (97% data loss!)
- Using SQLAlchemy queries outside repositories
- Not indexing foreign keys and common WHERE clauses

## 🔄 Session Recovery

### Todo Persistence
All todos are automatically saved to `.claude/todos/current.md` after every update. If session crashes:
1. Read `.claude/todos/current.md`
2. Check "Working On" section
3. Resume from last known state
4. Continue with pending items

### Context Files to Read on Session Start:
- This file (CLAUDE.md)
- `.claude/todos/current.md`
- Current feature's test file
- Related service/api files

## 🏁 Quick Start Checklist

When implementing a new feature:
- [ ] Read this CLAUDE.md file
- [ ] Use todo-manager agent to track tasks
- [ ] Use tdd-enforcer agent to write tests first
- [ ] Use appropriate specialist agent for implementation
- [ ] Validate with Playwright browser test
- [ ] Update documentation
- [ ] Commit with descriptive message

## 📊 Metrics We Track

### Code Quality:
- Test coverage (target: >95%)
- Code duplication (target: <3%)
- Response times (target: <200ms p95)
- Bundle size (target: <500KB)

### Development Velocity:
- Tests written before code: 100% (mandatory)
- Features completed per week
- Bugs caught by tests vs production
- Time from commit to deployment

---

**Remember**: The goal is to build a system that works reliably, not one that claims to work. Every "it's working!" requires proof, not promises.