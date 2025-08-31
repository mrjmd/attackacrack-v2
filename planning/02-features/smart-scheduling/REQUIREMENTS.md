# Smart Scheduling Requirements - Attack-a-Crack v2

## Vision
An intelligent scheduling system that maximizes crew efficiency, minimizes drive time, and automatically suggests optimal appointment slots while considering job complexity, weather, location, and business patterns.

## The Scheduling Challenge

### Current Pain Points
- Manual calculation of drive times
- No automatic buffering between jobs  
- Difficult to optimize route efficiency
- Weather conflicts discovered too late
- Over/under booking without visibility

### Dream State
"The system knows my business patterns better than I do. It suggests the perfect time slot considering everything - distance, job complexity, weather, crew capacity, and even customer preferences."

## Core Intelligence Factors

### 1. Job Duration Estimation

**Base Durations:**
- Assessment: 30 minutes standard
- Crack repair: 1-4 hours based on:
  - Linear feet of crack
  - Accessibility (crawl space vs open basement)
  - Number of cracks
- Waterproofing: 2-6 hours based on:
  - Square footage
  - Prep work required
- Bulkhead: 3-5 hours standard
- Resurfacing: 2-8 hours based on:
  - Square footage
  - Surface condition

**Learning Component:**
- Track actual vs estimated times
- Adjust estimates based on technician
- Factor in job complexity indicators from photos

### 2. Travel Time Intelligence

**Distance Calculation:**
- Google Maps API integration
- Real-time traffic consideration
- Time-of-day patterns (rush hour)
- Historical travel time data

**Smart Routing:**
- Cluster jobs by geography when possible
- Suggest "route days" for distant areas
- Alert when job is >30 min from others that day

**Buffer Rules:**
- Minimum 15 min between jobs <10 min apart
- Minimum 30 min between jobs 10-20 min apart  
- Minimum 45 min between jobs >20 min apart
- Extra buffer for first job after lunch

### 3. Weather-Aware Scheduling

**Weather Rules:**
- No exterior work if >60% rain chance
- Warning for exterior if >40% rain chance
- Suggest interior work on rain days
- Auto-propose rescheduling for weather conflicts

**Seasonal Patterns:**
- Shorter days in winter (adjust last job time)
- Higher callback rate in extreme temperatures
- Spring = busy season (tighter scheduling)
- Winter = maintenance and interior focus

### 4. Customer Preference Learning

**Patterns to Track:**
- Preferred days of week
- Morning vs afternoon preference
- How far out they schedule
- Flexibility indicators from conversation

**Smart Suggestions:**
"This customer typically prefers Tuesday/Thursday mornings"

### 5. Crew Capacity Management

**Daily Limits:**
- Max 6 assessments OR
- Max 3 repair jobs OR
- Mix: 2 repairs + 2 assessments typical

**Fatigue Factors:**
- Heavy jobs early in week
- Lighter Friday schedule
- No crawl space jobs back-to-back
- Alternate physical with assessment

## Scheduling Interface

### Smart Slot Suggestion
When scheduling a job, system shows:

```
📍 123 Main St, Boston (Crack Repair - 2 hrs)

RECOMMENDED SLOTS:
⭐ Thu 11/14 10:00 AM
   ✓ 15 min from previous job
   ✓ Good weather forecast
   ✓ Fits 2-hour window perfectly
   
🔵 Fri 11/15 2:00 PM  
   ✓ End of route in area
   ⚠️ 30 min from other jobs
   
🔵 Mon 11/18 8:00 AM
   ✓ Start day in this area
   ⚠️ Customer may prefer afternoon

⚠️ Wed 11/13 3:00 PM
   ⚠️ Would create 4th job (heavy day)
   ⚠️ Only 1.5 hours before day end
```

### Visual Calendar Optimization

**Color Coding:**
- Green: Optimal routing (jobs clustered)
- Yellow: Acceptable but not optimal
- Red: Over capacity or conflicts
- Blue: Assessments
- Purple: Repair jobs

**Map View:**
- See all jobs for day on map
- Suggested route overlay
- Click to see drive times
- Drag to reorder route

## Automated Scheduling Actions

### Daily Optimization Check (6 AM)
- Review today's schedule for conflicts
- Check weather impact
- Suggest route optimization if >15 min savings
- Alert if over capacity

### Booking Rules Engine
**Auto-Accept Conditions:**
- Assessment in existing route area
- Good weather for job type
- Within capacity limits
- Customer is repeat (trusted)

**Flag for Review:**
- Job would be 4th+ of day
- >30 min from other jobs
- Weather risk for exterior
- Unknown job duration

### Rescheduling Intelligence
**Automatic Proposals:**
- Weather conflict → Suggest next good weather day
- Cancellation → Fill slot with waitlist
- Emergency → Shuffle non-urgent jobs

**Customer Communication:**
"Hi [Name], rain is forecast for your Thursday resurfacing. Would Monday or Tuesday work instead?"

## Machine Learning Opportunities

### Historical Pattern Analysis
- Job duration by type, season, technician
- Travel time by time of day, day of week
- Customer flexibility patterns
- Callback likelihood by job type

### Predictive Scheduling
- Anticipate busy periods
- Suggest block scheduling for areas
- Predict cancellation likelihood
- Optimize for profitability not just efficiency

## Integration Requirements

### Google Calendar
- Read/write events
- Check availability
- Set buffer times as separate events
- Color coding for job types

### Google Maps
- Distance matrix API for multi-stop optimization
- Real-time traffic data
- Drive time calculations
- Turn-by-turn directions for technician

### Weather API
- 10-day forecast
- Hourly precipitation probability
- Temperature extremes
- Wind speed (for roof work)

### OpenPhone
- Send scheduling confirmations
- Rescheduling proposals
- Day-before reminders
- Running late notifications

## Success Metrics

### Efficiency Metrics
- Drive time reduction: >20%
- Jobs per day increase: 15%
- Weather delays: <5%
- Same-day rescheduling: <10%

### Quality Metrics
- On-time arrival: >90%
- Customer satisfaction: >4.5 stars
- Technician satisfaction: Reduced stress
- Callback rate: <5%

## Implementation Phases

### MVP (Basic Smart Suggestions)
- Manual duration estimates
- Simple distance calculation
- Basic weather checking
- Show 3 best slots

### Phase 2 (Route Optimization)
- Multi-stop optimization
- Real-time traffic
- Visual route mapping
- Capacity warnings

### Phase 3 (ML-Powered)
- Learning from historicals
- Predictive scheduling
- Auto-optimization
- Customer preference learning

## Questions for Next Session

1. **Lunch Break**: Fixed time or flexible? How long?
2. **Start/End Times**: Typical work day hours? Vary by season?
3. **Emergency Buffer**: Keep slots open for urgent calls?
4. **Geographic Limits**: Max distance you'll travel? Extra charge zones?
5. **Technician Skills**: Will different techs have specialties?
6. **Commercial vs Residential**: Different scheduling rules?

## Smart Scheduling Examples

### Example 1: Perfect Day
```
8:00 AM - Assessment (Newton) 
8:45 AM - Travel (5 min)
9:00 AM - Crack Repair (Brookline) 2 hrs
11:15 AM - Travel (10 min) 
11:30 AM - Assessment (Brighton)
12:15 PM - Lunch
1:00 PM - Waterproofing (Brighton) 3 hrs
4:00 PM - Day ends

Route efficiency: 98% (minimal travel)
```

### Example 2: Weather Adjustment
```
Original: Thursday exterior resurfacing
Weather: 80% rain Thursday
System: Auto-proposes Monday (sunny)
Customer: Accepts via text
Calendar: Auto-updates
Tech: Notified of change
```

### Example 3: Smart Fill
```
Cancellation: Tuesday 10 AM (2-hr slot)
System: Checks waitlist + nearby jobs
Finds: Customer 5 min away needs 2-hr repair
Auto-sends: "We had an opening Tuesday 10 AM..."
Result: Slot filled within 1 hour
```

---

*Smart Scheduling will transform operations from reactive to proactive, saving hours per week while improving customer satisfaction.*