# PropertyRadar Discovery Session - Current State
*Last Updated: August 28, 2025*
*Status: In Progress - Paused for Travel*

## 🏢 Business Context Discovered

### Company: Attack-a-Crack Foundation Repair
- **Primary Service**: Repairing cracks in poured concrete foundations
- **Secondary Services**: 
  - Concrete resurfacing (stairways, patios, pool decks)
  - Field stone and cinderblock work (not marketed)
- **Target Properties**: 
  - Single-family homes built after 1950 (proxy for poured concrete)
  - Properties with basements
  - Properties with pools (concrete deck opportunities)
- **Service Area**: Greater Boston area, Massachusetts

## 📊 PropertyRadar Strategy Confirmed

### Two-Tier Approach
1. **Database Building**: 50k properties/month to build comprehensive database before canceling $599/month subscription
2. **Active Campaigns**: 2.5k contacts/month with phone/email for immediate SMS campaigns

### Current Pain Points
- v1 CSV import completely broken (only importing 72 of 2,964 contacts)
- Can't run any automated campaigns despite having the data
- Paying $599/month for PropertyRadar but can't use it effectively
- Phone data quality issues (wrong numbers, landlines marked as mobile)

### Data Quality Issues Documented
- PropertyRadar phone data unreliable
- Need NumVerify validation for all numbers
- Email data secondary priority
- Manual verification taking too much time

## 📁 Documents Created So Far

### 1. ✅ REQUIREMENTS.md
- Current state and pain points documented
- Two-tier strategy explained
- Must-have vs nice-to-have features defined
- Success criteria established

### 2. ✅ DATA_MODEL.md  
- All 39 CSV fields mapped and prioritized
- Database schema designed for properties, owners, contacts
- Two-tier import strategy defined
- Contact validation flow created

### 3. ✅ DISCOVERY_SESSION_STATE.md (This Document)
- Current progress saved
- Outstanding questions preserved
- Ready for continuation after travel

## ❓ Outstanding Questions for Next Session

### 1. Campaign Automation Workflow
**Need to define the complete flow:**
```
PropertyRadar Export (2,500 contacts)
    ↓
CSV Import to System
    ↓
NumVerify Validation
    ↓
[NEED INPUT: What happens next?]
```

**Questions to answer:**
- After validation: straight to campaign or review queue?
- How many texts per day? (throttling limits)
- What time of day for sending?
- Skip weekends?
- Response handling:
  - Positive responses → ?
  - "Wrong number" → ?
  - "STOP" requests → ?
- Campaign duration before pausing?

### 2. Message Templates and Personalization
- Example messages for foundation repair?
- Personalization tokens needed? (name, address, year built?)
- A/B testing different messages?
- Seasonal messaging? (spring thaw = more cracks?)

### 3. Geographic and Business Rules
- What's Attack-a-Crack's business address?
- Maximum service radius?
- Should closer properties get priority?
- Certain towns/neighborhoods prioritized?
- Route optimization for crew scheduling?

### 4. NumVerify Integration Details
- PropertyRadar "Primary Mobile 1 Status" values?
- Conflict resolution: PR says verified, NumVerify says landline?
- Validate all 2,500 upfront or on-demand?
- Budget for validation costs?

### 5. The 50k Property Database Vision
- Specific filters for "likely customer"?
  - Year built > 1950
  - Has basement?
  - Pool on property?
  - Property value range?
  - Other indicators?
- Store properties without contact info?
- Auto-match when contact info obtained later?
- Future use cases for this database?

### 6. Success Metrics
- Target texts sent per day?
- Expected response rate?
- Cost per acquired customer goal?
- Time savings target?
- Campaign ROI expectations?

### 7. Integration with Other Systems
- How should PropertyRadar data appear in OpenPhone conversations?
- Google Maps integration for distance/directions?
- Should property data influence quote generation?
- Connection to QuickBooks for customer tracking?

## 🎯 Next Session Agenda

### Priority 1: Complete Campaign Workflow Design
- Define exact automation steps
- Set throttling and timing rules
- Design response handling

### Priority 2: Message Strategy
- Create template examples
- Define personalization approach
- Plan seasonal campaigns

### Priority 3: Technical Implementation
- NumVerify integration specifics
- PropertyRadar API exploration
- Database optimization for 100k+ properties

### Priority 4: Move to Next Integration
- OpenPhone webhook strategy
- QuickBooks customer sync
- Google Calendar scheduling

## 💡 Key Insights So Far

1. **Foundation repair context changes everything** - Now we understand why year built, basements, and pools matter
2. **Two-tier strategy is smart** - Build database before canceling expensive subscription
3. **CSV import is critical path** - This must work perfectly in v2
4. **Phone validation is non-negotiable** - Too many bad numbers from PropertyRadar
5. **Automation is the goal** - Manual process is killing productivity

## 📝 Session Notes

### What's Working Well
- Clear business model understanding
- Detailed CSV structure documented
- Two-tier strategy well-defined
- Pain points clearly identified

### What Needs More Discovery
- Complete campaign automation flow
- Message templates and timing
- Geographic targeting strategy
- Success metrics and KPIs

## 🚀 Ready to Resume

This document preserves our complete discovery state. When you return from travel, we'll pick up exactly here with the outstanding questions, starting with the campaign automation workflow.

Safe travels! We've made excellent progress understanding Attack-a-Crack's needs and PropertyRadar's role. The foundation (pun intended!) for v2 planning is solid.

---

*To Continue: Open this document and work through the "Outstanding Questions for Next Session" section*