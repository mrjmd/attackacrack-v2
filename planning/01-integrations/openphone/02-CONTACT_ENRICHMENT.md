# One-Time Contact Enrichment Dashboard

## Overview
After importing 7,000 conversations from OpenPhone, we need to enrich bare phone numbers with actual contact information from multiple sources. This is a **ONE-TIME operation** to bootstrap the system.

## The Problem
- OpenPhone API can't access web UI contacts (thousands of names/emails trapped)
- Historical conversations only have phone numbers
- Need to match and merge data from multiple sources

## Data Sources for Enrichment

### Available Sources
1. **PropertyRadar exports** - Names, emails, addresses, property data
2. **QuickBooks customers** - Names, emails, payment history, job records
3. **Other CSVs** - Various formats with contact info
4. **Manual web UI data** - Export from OpenPhone web if possible

## Enrichment Dashboard Design

### Main Interface
```
┌─────────────────────────────────────────────────────────┐
│ Contact Enrichment Dashboard - ONE TIME SETUP            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Unmapped Contacts: 4,234 of 7,000                       │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ Step 1: Import Data Sources                      │    │
│ │                                                   │    │
│ │ PropertyRadar CSVs:  [Upload] ✓ 3 files loaded   │    │
│ │ QuickBooks:          [Sync] ✓ 1,234 customers    │    │
│ │ Other CSVs:          [Upload] ✓ 5 files loaded   │    │
│ │ OpenPhone Export:    [Upload] ⧗ Processing...    │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─────────────────────────────────────────────────┐    │
│ │ Step 2: Automatic Matching                       │    │
│ │                                                   │    │
│ │ Matching by phone number...                      │    │
│ │ [████████░░] 2,456 contacts matched              │    │
│ │                                                   │    │
│ │ Confident matches: 2,103                         │    │
│ │ Conflicts needing review: 353                    │    │
│ │ No matches found: 1,778                          │    │
│ │                                                   │    │
│ │ [Review Conflicts] [Skip to Manual]              │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Conflict Resolution Interface
```
┌─────────────────────────────────────────────────────────┐
│ Resolve Contact Conflicts (353 remaining)               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Phone: (617) 555-0123                                   │
│                                                          │
│ ┌─────────────────┐  ┌─────────────────┐              │
│ │ PropertyRadar    │  │ QuickBooks      │              │
│ │                  │  │                 │              │
│ │ Name: John Smith │  │ Name: J. Smith  │              │
│ │ Email: john@...  │  │ Email: smith@.. │              │
│ │ Addr: 123 Main   │  │ Addr: (none)    │              │
│ │                  │  │ Last Job: 2024  │              │
│ │ [Use This] ✓     │  │ [Use This]      │              │
│ └─────────────────┘  └─────────────────┘              │
│                                                          │
│ Merge Strategy:                                         │
│ ○ Use PropertyRadar (recommended)                       │
│ ○ Use QuickBooks                                        │
│ ● Merge both (custom)                                   │
│   Name: [John Smith        ] (from PropertyRadar)       │
│   Email: [john@example.com ] (from PropertyRadar)       │
│   Keep QuickBooks job history: ✓                        │
│                                                          │
│ [Apply to All Similar] [Skip] [Previous] [Next]         │
└─────────────────────────────────────────────────────────┘
```

## Matching Logic

### Phase 1: Automatic Matching
```python
class ContactEnricher:
    def auto_match_contacts(self):
        # Primary key: Phone number (normalized)
        for conversation in unmapped_conversations:
            phone = normalize_phone(conversation.phone)
            
            matches = []
            
            # Check each source
            if pr_match := property_radar_data.get(phone):
                matches.append(('propertyradar', pr_match))
            
            if qb_match := quickbooks_data.get(phone):
                matches.append(('quickbooks', qb_match))
            
            if csv_match := other_csv_data.get(phone):
                matches.append(('csv', csv_match))
            
            if len(matches) == 0:
                mark_as_unmapped(conversation)
            elif len(matches) == 1:
                auto_apply_match(conversation, matches[0])
            else:
                queue_for_conflict_resolution(conversation, matches)
```

### Phase 2: Manual Review
- Present conflicts one by one
- Allow bulk operations ("Apply to all similar")
- Track decisions for consistency

### Phase 3: Remaining Unmapped
- Export list of unmapped numbers
- Allow manual entry
- Or leave as phone-only contacts

## Database Schema
```sql
CREATE TABLE enrichment_sources (
    id UUID PRIMARY KEY,
    source_type VARCHAR(50), -- 'propertyradar', 'quickbooks', 'csv'
    file_name VARCHAR(255),
    
    -- Statistics
    total_records INTEGER,
    matched_records INTEGER,
    conflict_records INTEGER,
    
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE enrichment_matches (
    id UUID PRIMARY KEY,
    phone_number VARCHAR(20),
    conversation_id UUID,
    
    -- Match data
    source_type VARCHAR(50),
    source_data JSONB,
    confidence_score DECIMAL(3,2),
    
    -- Resolution
    status VARCHAR(20), -- 'pending', 'applied', 'rejected'
    applied_at TIMESTAMP,
    applied_by VARCHAR(100)
);
```

## After Enrichment

### Push to OpenPhone
Once contacts are enriched:
1. Create API contacts in OpenPhone
2. Link to existing conversations
3. We become source of truth
4. Future updates sync back to OpenPhone

### Verification
- Total contacts created
- Contacts with names vs phone-only
- Contacts with emails
- QuickBooks customers matched

## Success Metrics
- [ ] 80%+ of conversations have named contacts
- [ ] 50%+ have email addresses
- [ ] All QuickBooks customers matched
- [ ] Zero duplicate contacts created

---

*This is a ONE-TIME operation to bootstrap the system. After this, all new contacts are created with full information from the start.*