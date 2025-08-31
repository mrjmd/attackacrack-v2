# Development Experience Requirements - Attack-a-Crack v2

## 🔴 Critical V1 Pain Points

### The "It's Working!" Lie
**Problem**: Claude Code would claim features were complete and working when they were actually broken with errors everywhere.

**Solution Requirements**:
1. **Mandatory browser validation** - Claude Code MUST test in real browser
2. **Self-verification loop** - Keep iterating until it actually works
3. **Error detection** - Claude must see and fix its own errors
4. **No "done" without proof** - Must show passing browser tests

### Missing Real-World Testing
**Problem**: Only unit tests were run, missing real integration issues

**Solution Requirements**:
1. **Three-layer testing**:
   - Unit tests (fast, focused)
   - Integration tests (API + database)
   - Browser tests (Playwright - REAL validation)
2. **Playwright MCP integration** from day one
3. **Visual validation** - Screenshots of working features
4. **Error monitoring** - Catch console errors, network failures

### Claude Configuration Enforcement
**Problem**: Constantly had to remind about sub-agents and TDD despite clear CLAUDE.md

**Solution Requirements**:
1. **Aggressive enforcement hooks**
2. **Pre-commit validation**
3. **Automatic sub-agent routing**
4. **TDD enforcement that can't be bypassed**
5. **Context preservation between sessions**

## 🎯 V2 Development Experience Vision

### The Development Loop
```
1. TDD First (enforced)
   ↓
2. Write failing test
   ↓
3. Implement minimal code
   ↓
4. Run unit tests
   ↓
5. Run integration tests
   ↓
6. Run Playwright browser tests
   ↓
7. Claude SEES the browser results
   ↓
8. If errors → Fix and repeat
   ↓
9. Only when ALL pass → "Done"
```

### Self-Validation Requirements
- Claude Code must be able to:
  - Start the development server
  - Open browser via Playwright
  - Navigate through the app
  - Perform user actions
  - Verify expected outcomes
  - See console errors
  - Read network responses
  - Take screenshots for proof

### CI/CD Monitoring
- Pre-commit hooks that can't be skipped
- Automated test runs on every commit
- Branch protection requiring passing tests
- Deployment gates with test validation

## 🛠️ Tooling Requirements

### Essential MCPs
1. **Playwright MCP** - Browser automation and testing
2. **Database MCP** - Direct database validation
3. **Server MCP** - Start/stop/monitor dev servers
4. **Git MCP** - Enforce commit standards

### Claude Code Hooks
1. **Pre-task hook** - Force sub-agent selection
2. **Pre-code hook** - Enforce TDD workflow
3. **Post-implementation hook** - Force browser testing
4. **Pre-commit hook** - Validate all tests pass

### Sub-Agent Strategy
1. **Specialized agents from day one**:
   - `fastapi-v2-agent` - Backend development
   - `sveltekit-v2-agent` - Frontend development
   - `playwright-test-agent` - Browser testing
   - `tdd-enforcer-agent` - Test-first enforcement
   - `integration-agent` - API integrations
   - `devops-agent` - CI/CD and deployment

2. **Automatic routing** based on task type
3. **No direct implementation** in main Claude

## 🔄 Session Management

### Context Preservation
- Session handoff documents auto-generated
- Todo persistence with current state
- Test results tracked between sessions
- Error logs preserved for debugging

### Validation Gates
No feature is "complete" until:
1. ✅ Unit tests pass
2. ✅ Integration tests pass
3. ✅ Playwright browser tests pass
4. ✅ No console errors in browser
5. ✅ Screenshots prove it works
6. ✅ Code coverage > 90%

## 📋 Development Workflow

### For Every Feature
```bash
# 1. TDD agent writes test first
npm run test:unit -- --watch

# 2. Implementation agent writes code
# (minimal to pass test)

# 3. Integration testing
npm run test:integration

# 4. Playwright validation
npm run test:e2e

# 5. Claude reviews browser results
# If failures, loop back to step 2

# 6. Only when all green:
git commit -m "Feature complete with validation"
```

---

*This is a living document. We'll refine based on integration requirements.*