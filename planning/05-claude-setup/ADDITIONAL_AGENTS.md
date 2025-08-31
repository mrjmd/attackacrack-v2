# Additional Specialized Agents for Attack-a-Crack v2

## 🔍 Research & Analysis Agents

### deep-research-analyst
**Purpose**: Deep technical research and architecture decisions
**Tools**: WebSearch, WebFetch, Read, Grep
**When to Use**:
- Researching best practices for complex features
- Investigating library choices
- Analyzing security vulnerabilities
- Competitive analysis

**Example Invocation**:
```
Task: Research best SMS rate limiting strategies for OpenPhone API in 2025
```

### codebase-archaeologist
**Purpose**: Understanding existing code patterns and finding hidden implementations
**Tools**: Grep, Glob, Read, MultiEdit
**When to Use**:
- Before implementing new features (check for existing code)
- Finding all usages of a pattern
- Refactoring preparation
- Dependency analysis

## 🔧 Implementation Specialists

### celery-task-specialist
**Purpose**: Async task queue implementation with Celery/Redis
**Tools**: Read, Write, MultiEdit, Bash
**Expertise**:
- Task scheduling and retries
- Queue management
- Worker configuration
- Beat scheduling
- Result backend setup

**Key Responsibilities**:
- Campaign message queuing
- Webhook processing
- Bulk operations
- Scheduled tasks

### docker-compose-specialist
**Purpose**: Container orchestration and environment setup
**Tools**: Read, Write, Edit, Bash
**Expertise**:
- Multi-container applications
- Environment variables
- Volume management
- Network configuration
- Health checks

### alembic-migration-specialist
**Purpose**: Database schema migrations
**Tools**: Read, Write, Bash, MultiEdit
**Expertise**:
- Schema versioning
- Migration scripts
- Rollback strategies
- Data migrations
- Multi-database support

## 📊 Data & Analytics Agents

### data-model-architect
**Purpose**: Design and optimize database schemas
**Tools**: Read, Write, MultiEdit
**Expertise**:
- Normalization/denormalization
- Index optimization
- Query performance
- Relationship design
- Constraints and triggers

### analytics-implementation-specialist
**Purpose**: Metrics, tracking, and reporting
**Tools**: Read, Write, MultiEdit, Bash
**Expertise**:
- Event tracking
- A/B test analytics
- Performance metrics
- User behavior tracking
- Dashboard queries

## 🔒 Security & Compliance Agents

### security-audit-specialist
**Purpose**: Security review and vulnerability assessment
**Tools**: Read, Grep, Bash
**Expertise**:
- OWASP compliance
- SQL injection prevention
- XSS protection
- Authentication/authorization
- Secret management

### api-security-specialist
**Purpose**: API security and rate limiting
**Tools**: Read, Write, MultiEdit
**Expertise**:
- JWT implementation
- Rate limiting
- API key management
- CORS configuration
- Request validation

## 🎨 Frontend Specialists

### svelte-store-specialist
**Purpose**: State management in SvelteKit
**Tools**: Read, Write, MultiEdit
**Expertise**:
- Writable/readable stores
- Derived stores
- Custom stores
- Context API
- Store persistence

### tailwind-ui-specialist
**Purpose**: Rapid UI development with Tailwind CSS
**Tools**: Read, Write, MultiEdit
**Expertise**:
- Component styling
- Responsive design
- Dark mode
- Animation utilities
- Custom configurations

## 📡 Integration Specialists

### webhook-processing-specialist
**Purpose**: Robust webhook handling
**Tools**: Read, Write, MultiEdit, Bash
**Expertise**:
- Webhook validation
- Retry logic
- Deduplication
- Queue processing
- Error handling

### api-client-specialist
**Purpose**: External API integrations
**Tools**: Read, Write, MultiEdit
**Expertise**:
- Rate limiting
- Retry strategies
- Error handling
- Response caching
- Mock implementations

## 🧪 Testing Specialists

### load-testing-specialist
**Purpose**: Performance and load testing
**Tools**: Read, Write, Bash
**Expertise**:
- k6 scripts
- Locust tests
- Stress testing
- Performance benchmarks
- Bottleneck analysis

### mock-data-specialist
**Purpose**: Test data generation and factories
**Tools**: Read, Write, MultiEdit
**Expertise**:
- Factory patterns
- Faker library
- Fixture management
- Seed data
- Test isolation

## 📝 Documentation Specialists

### api-documentation-specialist
**Purpose**: OpenAPI/Swagger documentation
**Tools**: Read, Write, MultiEdit
**Expertise**:
- OpenAPI schemas
- Request/response examples
- Authentication docs
- Error documentation
- Interactive documentation

### architecture-diagram-specialist
**Purpose**: Technical diagrams and flowcharts
**Tools**: Read, Write
**Expertise**:
- Mermaid diagrams
- PlantUML
- System architecture
- Sequence diagrams
- ER diagrams

## 🚀 DevOps Specialists

### github-actions-specialist
**Purpose**: CI/CD pipeline configuration
**Tools**: Read, Write, MultiEdit
**Expertise**:
- Workflow automation
- Matrix builds
- Secret management
- Deployment gates
- Artifact handling

### monitoring-observability-specialist
**Purpose**: Application monitoring and logging
**Tools**: Read, Write, MultiEdit
**Expertise**:
- Structured logging
- Error tracking (Sentry)
- Performance monitoring
- Health checks
- Alert configuration

## 💡 Recommended Agent Workflow Patterns

### Pattern 1: Feature Development
```
1. codebase-archaeologist → Check for existing implementations
2. deep-research-analyst → Research best practices
3. data-model-architect → Design schema if needed
4. tdd-enforcer → Write tests
5. [domain-specialist] → Implement feature
6. playwright-test-specialist → Browser validation
```

### Pattern 2: Bug Investigation
```
1. codebase-archaeologist → Find all related code
2. integration-test-specialist → Write failing test
3. [domain-specialist] → Fix implementation
4. load-testing-specialist → Verify performance
```

### Pattern 3: Integration Development
```
1. deep-research-analyst → Research API documentation
2. api-client-specialist → Design client
3. webhook-processing-specialist → Handle callbacks
4. mock-data-specialist → Create test fixtures
```

## 🎯 Priority Agents for v2

Based on your architecture, prioritize adding these agents:

1. **celery-task-specialist** - Critical for campaign queuing
2. **webhook-processing-specialist** - Essential for OpenPhone
3. **alembic-migration-specialist** - Database evolution
4. **docker-compose-specialist** - Environment management
5. **api-security-specialist** - Prevent v1 security issues

## 📋 Agent Definition Template

When creating new agents, use this template:

```python
agent_definition = {
    "name": "agent-name-specialist",
    "description": "One-line description",
    "tools": ["Read", "Write", "MultiEdit", "Bash"],
    "expertise": [
        "Specific skill 1",
        "Specific skill 2"
    ],
    "triggers": [
        "When user mentions X",
        "When working on Y files",
        "Before implementing Z"
    ],
    "handoff_format": {
        "inputs": ["test_file", "requirements"],
        "outputs": ["implementation", "coverage_report"]
    }
}
```

---

*These specialized agents complement the existing agents in CLAUDE.md and ensure all aspects of development are handled by domain experts.*