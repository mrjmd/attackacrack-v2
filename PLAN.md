# Attack-a-Crack CRM v2 - Master Planning Document

## Executive Summary

This document captures the comprehensive planning for a complete rebuild of the Attack-a-Crack CRM system. After experiencing significant technical debt and complexity issues in v1 (61,241 lines of code with massive duplication, multiple implementations of the same features, and a 97% data loss bug that took hours to fix), we are taking a step back to thoroughly plan v2 before writing any code.

## Current State Analysis (v1 Problems)

### The Pain Points
- **61,241 lines of Python code** with massive duplication
- **87 files** between services (49) and repositories (38) creating unnecessary complexity
- **Multiple CSV importers** (3+ different implementations of the same feature)
- **Sync/async duplication** throughout the codebase
- **97% data loss bug** in CSV import that took hours to diagnose and fix
- **Repository pattern** partially implemented with 56+ violations
- **Service registry** with circular dependencies and complex initialization
- **Test complexity** requiring special isolation and registry methods
- **Incomplete features** despite months of development

### Key Insight
The current codebase has become unmaintainable due to over-engineering and premature abstraction before understanding actual requirements. We need to start fresh with a focus on simplicity, clear boundaries, and iterative development.

## Technology Stack Decision

### Backend: FastAPI
**Why FastAPI over Flask/Django:**
- Native async/await support (eliminates sync/async duplication)
- Automatic OpenAPI documentation
- Built-in data validation with Pydantic
- 3-5x faster than Flask
- Modern Python with type hints
- Built-in dependency injection (no complex service registry needed)

### Frontend: SvelteKit
**Why SvelteKit over React/Next.js:**
- 50-70% smaller bundle sizes (critical for mobile users in the field)
- No virtual DOM overhead
- Built-in state management (no Redux complexity)
- Compile-time optimizations
- Server-side rendering built-in
- File-based routing like Next.js
- Simpler mental model than React

### Database: PostgreSQL + Supabase
**Why this combination:**
- Keep existing PostgreSQL expertise
- Supabase adds real-time subscriptions, authentication, and file storage
- Open source and self-hostable if needed
- $25/month for production
- Built-in Row Level Security

### Background Tasks: Celery + Redis
**Keep what works:**
- Proven reliable for async processing
- Existing expertise
- Good monitoring tools available

### Deployment: Docker + DigitalOcean
**Continuity:**
- Current setup works well
- ~$50-75/month total infrastructure
- Easy to scale when needed

## Architecture: Modular Monolith

### Why Modular Monolith over Microservices
Based on 2025 best practices and companies like GitHub and Shopify's success:
- Single deployment unit (simple DevOps)
- Shared database transactions when needed
- No distributed system complexity
- Clear module boundaries prevent spaghetti code
- Can extract to microservices later if actually needed

### Project Structure
```
attackacrack-v2/
├── backend/
│   ├── core/               # Shared utilities, base classes
│   │   ├── database.py     # Database connection
│   │   ├── exceptions.py   # Custom exceptions
│   │   ├── security.py     # Auth, encryption
│   │   └── utils.py        # Shared utilities
│   │
│   ├── modules/
│   │   ├── contacts/       # Contact management domain
│   │   │   ├── models.py   # SQLAlchemy models
│   │   │   ├── schemas.py  # Pydantic schemas
│   │   │   ├── service.py  # Business logic
│   │   │   ├── api.py      # FastAPI routes
│   │   │   └── tests/      # Module-specific tests
│   │   │
│   │   ├── campaigns/      # SMS campaigns domain
│   │   ├── openphone/      # OpenPhone integration
│   │   ├── quickbooks/     # QuickBooks integration
│   │   └── calendar/       # Scheduling domain
│   │
│   └── api/               # Main FastAPI app
│       ├── main.py        # App initialization
│       └── dependencies.py # Shared dependencies
│
├── frontend/
│   └── sveltekit-app/
│       ├── src/
│       │   ├── routes/    # File-based routing
│       │   ├── lib/       # Shared components
│       │   └── stores/    # Global state
│       └── tests/         # Frontend tests
│
├── infrastructure/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
│
└── planning/              # All planning documents
```

## Implementation Phases

### Phase 1: MVP Foundation (Week 1-2)
**Goal:** Minimal working CRM with reliable CSV import

**Features:**
1. Contact management (CRUD operations)
2. **Single, correct CSV import implementation** (no duplication!)
3. PropertyRadar format support
4. Basic SMS sending via OpenPhone
5. User authentication with Supabase

**Success Criteria:**
- Can import 5,000+ contacts without data loss
- Can send individual SMS messages
- Clean, tested codebase under 2,000 lines

### Phase 2: Core Campaigns (Week 3-4)
**Goal:** Fully functional SMS campaign system

**Features:**
1. Campaign creation with templates
2. A/B testing with automatic winner selection
3. Daily sending limits (125/day for cold outreach)
4. Business hours enforcement (9am-6pm ET weekdays)
5. Opt-out management and compliance
6. Real-time progress tracking via WebSockets

**Success Criteria:**
- Can run automated campaigns with 95%+ delivery rate
- A/B tests automatically optimize after statistical significance
- Zero compliance violations

### Phase 3: Integrations (Week 5-6)
**Goal:** Connect all external services

**Features:**
1. OpenPhone webhooks (messages, calls, voicemails)
2. QuickBooks customer/invoice sync
3. Google Calendar appointment scheduling
4. Gmail thread management
5. Media storage for attachments

**Success Criteria:**
- Real-time message sync with <1 second delay
- Automatic invoice creation from quotes
- Calendar availability checking works reliably

### Phase 4: Intelligence Layer (Week 7-8)
**Goal:** AI-powered enhancements

**Features:**
1. Gemini integration for conversation analysis
2. Automatic address extraction and PropertyRadar lookup
3. Smart follow-up suggestions
4. Image analysis for damage assessment and quoting

**Success Criteria:**
- 90%+ accuracy on address extraction
- Quotes generated from images in <30 seconds
- Follow-up suggestions improve response rate by 20%+

## Deep Discovery Process

### Inquiry Framework
For each major feature/integration, we will conduct a structured discovery session:

1. **Current Pain Points** - What's broken in v1?
2. **Dream State** - What would perfect look like?
3. **User Journey** - Step-by-step workflows with detailed interactions
4. **Technical Requirements** - APIs, data models, performance needs
5. **UI/UX Design** - Wireframes and visual representations
6. **Integration Points** - Where it connects to other features
7. **Test Scenarios** - How we'll verify it works correctly
8. **Edge Cases** - What could go wrong and how we handle it

### Example: PropertyRadar Integration Deep Dive

#### Vision
When a customer texts their address, the system instantly enriches the conversation with complete property data, enabling instant, accurate quoting and intelligent follow-up.

#### Key Questions to Answer:
1. **Real-Time Address Detection**
   - How quickly do you need the property data? (Target: <2 seconds)
   - Should it auto-detect addresses in any message or require trigger?
   - How to handle partial addresses or typos?

2. **Property Information Display**
   - What specific data points are most valuable?
     - Property value
     - Square footage
     - Year built
     - Foundation type/condition
     - Previous work history
   - UI presentation: Sidebar? Overlay? Inline?

3. **Geographic Context**
   - Driving time/distance from business
   - Service territory validation
   - Route optimization for multiple properties
   - Visual map integration

4. **Business Logic Integration**
   - Auto-adjust quotes based on property value
   - Flag properties with specific characteristics
   - Track properties worked on previously

5. **Workflow Automation**
   - Auto-generate quote from square footage
   - Pull similar jobs in neighborhood
   - Check for existing quotes/invoices

## Testing Strategy (TDD from Day 1)

### Test-Driven Development Workflow
```python
# 1. Write the test first (RED)
def test_import_csv_creates_contacts():
    """Test that CSV import creates the expected number of contacts"""
    csv_data = "name,phone\nJohn,555-1234"
    result = import_csv(csv_data)
    assert result.contacts_created == 1
    assert Contact.query.count() == 1

# 2. Write minimal code to pass (GREEN)
def import_csv(data):
    # Minimal implementation
    pass

# 3. Refactor with confidence (REFACTOR)
def import_csv(data):
    # Clean, efficient implementation
    pass
```

### Testing Pyramid
```
         /\
        /E2E\        <- 5% - Critical user journeys only
       /------\
      /Integration\  <- 25% - API and database tests
     /------------\
    /   Unit Tests  \ <- 70% - Fast, focused, numerous
   /----------------\
```

### Key Testing Principles
1. **No code without a failing test first**
2. **Each test tests one thing**
3. **Tests are documentation**
4. **If it's not tested, it's broken**
5. **Mock external services, test against real database**

## Development Workflow

### Git Strategy
- `main` - Production-ready code only
- `develop` - Integration branch
- `feature/*` - Individual features
- `fix/*` - Bug fixes

### CI/CD Pipeline
1. Push to feature branch triggers:
   - Linting (Ruff for Python, ESLint for JS)
   - Type checking (mypy, TypeScript)
   - Unit tests
   - Integration tests

2. Merge to develop triggers:
   - Full test suite
   - E2E tests with Playwright
   - Coverage report (must be >90%)

3. Merge to main triggers:
   - Deployment to staging
   - Smoke tests
   - Manual approval
   - Deployment to production

## Claude Integration Strategy

### Subagents for v2
We'll create specialized agents from the start:
- `fastapi-v2-agent` - FastAPI patterns and best practices
- `sveltekit-v2-agent` - Frontend development
- `tdd-v2-agent` - Enforces test-first development
- `integration-v2-agent` - External API integrations

### CLAUDE.md for v2
Will emphasize:
- TDD is mandatory
- No duplicate implementations
- Clear module boundaries
- Every PR must have tests
- Use subagents for specialized work

## Key Improvements Over v1

### 1. Radical Simplification
- One way to do each thing
- No sync/async duplication
- Single source of truth
- Clear module boundaries

### 2. Performance First
- 3-5x faster API responses
- 50% smaller frontend bundles
- Real-time updates via WebSockets
- Optimized database queries from day 1

### 3. Developer Experience
- Type hints throughout
- Automatic API documentation
- Hot reload everything
- Simple, fast tests
- Clear error messages

### 4. Maintainability
- Target: <10,000 lines of code (90% reduction)
- Each module under 1,000 lines
- No file over 200 lines
- Clear separation of concerns

## Success Metrics

### Technical Metrics
- [ ] 90% reduction in code size
- [ ] 100% test coverage for critical paths
- [ ] <100ms API response times (p95)
- [ ] Zero duplicate implementations
- [ ] <5 second CSV import for 5,000 contacts

### Business Metrics
- [ ] Send 1,000+ SMS per day reliably
- [ ] 95%+ delivery rate
- [ ] <1% error rate in production
- [ ] 50% reduction in development time for new features

## Planning Structure

### Directory Organization
```
attackacrack-v2/
├── planning/
│   ├── 00-overview/
│   │   ├── VISION.md                    # Product vision & principles
│   │   ├── ARCHITECTURE.md              # Core architecture decisions
│   │   └── TECHNOLOGY_DECISIONS.md      # Stack choices with rationale
│   │
│   ├── 01-integrations/
│   │   ├── openphone/
│   │   │   ├── REQUIREMENTS.md          # What we need from OpenPhone
│   │   │   ├── API_MAPPING.md           # Every endpoint we'll use
│   │   │   ├── WEBHOOK_STRATEGY.md      # Real-time data flow
│   │   │   └── UI_TOUCHPOINTS.md        # Where it appears in UI
│   │   ├── propertyradar/
│   │   │   ├── REQUIREMENTS.md          # Real-time address lookup, etc.
│   │   │   ├── API_MAPPING.md           # Available endpoints
│   │   │   └── INTEGRATION_POINTS.md    # Where/how we'll use it
│   │   ├── quickbooks/
│   │   ├── google_calendar/
│   │   ├── gmail/
│   │   └── gemini/
│   │
│   ├── 02-features/
│   │   ├── contacts/
│   │   │   ├── USER_STORIES.md          # What users need to do
│   │   │   ├── DATA_MODEL.md            # Schema design
│   │   │   ├── UI_FLOWS.md              # Wireframes & interactions
│   │   │   └── API_SPEC.md              # Endpoints & contracts
│   │   ├── campaigns/
│   │   ├── conversations/
│   │   └── scheduling/
│   │
│   ├── 03-ui-ux/
│   │   ├── DESIGN_SYSTEM.md             # Colors, components, patterns
│   │   ├── LAYOUTS.md                   # Page structures
│   │   ├── REAL_TIME_STRATEGY.md        # WebSocket vs SSE vs polling
│   │   └── MOBILE_FIRST.md              # Responsive approach
│   │
│   ├── 04-development/
│   │   ├── TDD_STRATEGY.md              # How we'll do TDD
│   │   ├── TESTING_PYRAMID.md           # E2E, integration, unit
│   │   ├── CI_CD_PIPELINE.md            # Automation strategy
│   │   └── DEVELOPMENT_WORKFLOW.md      # Git, review, deploy
│   │
│   ├── 05-claude-setup/
│   │   ├── CLAUDE.md                    # Main instructions
│   │   ├── agents/                       # Specialized subagents
│   │   └── TOOL_DECISIONS.md            # Playwright vs alternatives
│   │
│   └── 06-mvp-definition/
│       ├── PHASE_1_MVP.md               # Absolute minimum
│       ├── PHASE_2_CORE.md              # Core business value
│       └── PHASE_3_SCALE.md             # Growth features
```

## Deep Discovery Process

### Session Format
Each major feature/integration will undergo structured discovery:

1. **Current Pain Points** - What's broken in v1?
2. **Dream State** - What would perfect look like?
3. **User Journey** - Step-by-step workflows with detailed interactions
4. **Technical Requirements** - APIs, data models, performance needs
5. **UI/UX Design** - Wireframes and visual representations
6. **Integration Points** - Where it connects to other features
7. **Test Scenarios** - How we'll verify it works correctly
8. **Edge Cases** - What could go wrong and how we handle it

### Documentation Standard
Each planning document follows this structure:
```markdown
# [Feature/Integration Name]

## Vision
What success looks like

## User Stories
As a [user], I want [feature] so that [benefit]

## Requirements
### Must Have (MVP)
### Should Have (v2)
### Could Have (Future)

## Technical Specification
### Data Model
### API Endpoints
### Integration Points

## UI/UX Design
### Wireframes
### User Flow
### Edge Cases

## Test Strategy
### Unit Tests
### Integration Tests
### E2E Scenarios

## Implementation Notes
### Dependencies
### Performance Considerations
### Security Concerns
```

## Next Steps

### Phase 1: Deep Discovery (Weeks 1-2)
Through iterative inquiry sessions, we will:
1. **PropertyRadar Integration** - Complete deep dive with Q&A
2. **OpenPhone Integration** - Webhook strategy, real-time sync
3. **QuickBooks Integration** - Financial data flow
4. **Contact Management** - Core data model and operations
5. **Campaign System** - Scheduling, templating, analytics

### Phase 2: Technical Foundation (Week 3)
1. Set up FastAPI project structure
2. Create SvelteKit application
3. Configure Docker development environment
4. Set up testing infrastructure
5. Implement CI/CD pipeline

### Phase 3: MVP Implementation (Weeks 4-5)
1. Build contact management
2. Implement single CSV importer
3. Add OpenPhone SMS sending
4. Create basic UI
5. Deploy to staging

### Phase 4: Feature Development (Weeks 6-8)
Follow phases 2-4 as outlined above

## Open Questions to Resolve

1. **PropertyRadar API** - What level of access do we have?
2. **OpenPhone Numbers** - How many numbers? Rate limits?
3. **QuickBooks Sync** - One-way or bidirectional?
4. **User Management** - Single user or multi-user from start?
5. **Mobile App** - Progressive Web App or native eventually?

## Documentation Standards

Every feature will have:
1. User stories with acceptance criteria
2. Technical specification
3. API documentation
4. Test scenarios
5. Deployment notes

## Risk Mitigation

### Technical Risks
- **Risk:** New technology learning curve
- **Mitigation:** Start with familiar patterns, add complexity gradually

- **Risk:** Integration API changes
- **Mitigation:** Abstract all external APIs behind interfaces

### Business Risks
- **Risk:** Feature creep
- **Mitigation:** Strict MVP definition, iterate after launch

- **Risk:** Data loss during migration
- **Mitigation:** No migration - fresh start with external system sync

## Conclusion

This rebuild is an opportunity to apply all lessons learned from v1 while building a foundation that can scale to millions of users without the complexity that's currently hampering development. By focusing on simplicity, clear boundaries, and test-driven development from day 1, we'll build a system that's a joy to work with and extend.

The key insight: **Build for one user first, design for thousands, architect for millions - but only when actually needed.**

---

*This is a living document. As we complete discovery sessions, we'll update this plan with decisions and refinements.*