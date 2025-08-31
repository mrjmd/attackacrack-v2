# v1 Reference Guide - What to Keep vs Avoid

## 📁 v1 Location
**Path**: `../openphone-sms/`

## ✅ What Worked Well in v1 (Reference These)

### OpenPhone Integration
- `services/openphone_api_client.py` - Basic API client structure
- `services/openphone_webhook_service_refactored.py` - Webhook handling patterns
- Look for: Rate limiting, retry logic, webhook validation

### CSV Import (Despite Issues)
- `services/csv_import_service.py` - Core import logic (fix the commit issue!)
- Has deduplication logic worth studying
- Progress tracking patterns

### Database Models
- `models/` - Basic schema worked
- Relationships between contacts, campaigns, messages

### Celery Tasks
- `tasks/` - Task queue patterns
- Async processing approach

## ❌ What Failed in v1 (Avoid These)

### Service Explosion
- **49 service files** - Way too many!
- Multiple versions of same service:
  - `openphone_service.py`
  - `openphone_sync_service.py`
  - `openphone_reconciliation_service.py`
  - `openphone_api_client.py`
  
### Repository Over-Abstraction
- **38 repository files** - Unnecessary abstraction
- Direct SQLAlchemy would have been simpler
- Repository pattern violations everywhere

### The CSV Import Bug
```python
# THE FATAL BUG - Only committed every 100 records
if index % 100 == 0:
    db.commit()
# Final batch never committed if not divisible by 100!
```

### Sync/Async Duplication
- Many services had both sync and async versions
- Example: `get_contact()` AND `get_contact_async()`
- Doubled the code, doubled the bugs

### Service Registry Complexity
- Circular dependency hell
- Complex initialization
- Hard to debug

## 🎯 v2 Strategy: Learn from v1

### When Referencing v1:
1. **Look for business logic** - The WHAT, not the HOW
2. **Study API integrations** - OpenPhone patterns
3. **Understand data relationships** - Models structure
4. **Learn from bugs** - What went wrong

### But Remember:
- **Don't copy architecture** - It was over-engineered
- **Don't duplicate patterns** - One way to do things
- **Don't abstract prematurely** - Start simple
- **Don't skip tests** - v1 had poor coverage

## 📊 Quick Reference Commands

```bash
# Find all OpenPhone related code in v1
grep -r "openphone" ../openphone-sms/services/

# Check v1 models
ls -la ../openphone-sms/models/

# See v1 tests (sparse!)
ls -la ../openphone-sms/tests/

# Find CSV import implementations
grep -r "import.*csv" ../openphone-sms/services/

# Check Celery tasks
ls -la ../openphone-sms/tasks/
```

## 🚨 Critical Files to Review

When implementing v2 features, check these v1 files:

### For OpenPhone Webhook:
- `../openphone-sms/services/openphone_webhook_service_refactored.py`
- Has signature validation
- Has deduplication logic
- BUT: Over-complicated, simplify in v2

### For CSV Import:
- `../openphone-sms/services/csv_import_service.py`
- Line 580+ has the fatal commit bug
- BUT: Has good validation logic
- BUT: Multiple implementations exist

### For Campaign Logic:
- `../openphone-sms/services/campaign_service_refactored.py`
- Has A/B testing logic
- Has daily limit enforcement
- BUT: Too complex, simplify

### For Contact Management:
- `../openphone-sms/services/contact_service_refactored.py`
- Has deduplication
- Has phone normalization
- BUT: Both sync and async versions

## 💡 Key Lessons

1. **One Implementation Per Feature** - v1 had 3+ CSV importers!
2. **Commit Frequently** - The 97% data loss bug
3. **Test Everything** - v1 had minimal test coverage
4. **Simple > Complex** - Service registry was overkill
5. **Clear Boundaries** - Services imported from everywhere

---

*Use v1 as a cautionary tale and a source of business logic, not as an architectural template.*