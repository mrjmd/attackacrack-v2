# Contacts, Properties & Jobs - Requirements Discovery

*From conversation on December 30, 2024*

## Core Concepts

### The Business Reality
Attack-a-Crack deals with complex relationships between people and properties in the concrete/foundation repair business:
- **Homeowners** fixing their current house and then calling for their new house
- **Landlords** with multiple rental properties
- **Builders/Contractors** coordinating work for homeowners
- **Realtors** as strong referral partners
- **HOAs** managing community properties
- **Property Managers** overseeing portfolios

## Data Model

### Multi-Location Readiness [IMPORTANT]
**Future Expansion**: Connecticut branch planned for 2025. All models include `location_id` from Day 1 to avoid painful migrations later.

```python
# Default location for MVP (single location)
DEFAULT_LOCATION_ID = "11111111-1111-1111-1111-111111111111"  # New Jersey
```

### Contacts (People)
```python
class Contact:
    id: UUID
    location_id: UUID = DEFAULT_LOCATION_ID  # Branch/location ownership
    first_name: str
    last_name: str
    phone: str  # Primary, unique per location
    email: str
    contact_type: str  # "homeowner", "realtor", "builder", "property_manager", "HOA"
    source: str  # "propertyradar", "referral", "quickbooks"
    created_at: datetime
    
    # Unique constraint: (phone, location_id)
```

### Properties (Locations)
```python
class Property:
    id: UUID
    location_id: UUID = DEFAULT_LOCATION_ID  # Which branch manages this
    address: str  # Full address
    city: str
    state: str
    zip: str
    
    # PropertyRadar enrichment
    owner_name: str
    square_footage: int
    year_built: int
    property_value: float
    
    # Business data
    notes: Text
    
    # Unique constraint: (address, location_id)
```

### Contact-Property Relationships (Many-to-Many)
```python
class ContactPropertyRelationship:
    contact_id: UUID
    property_id: UUID
    relationship_type: str  # "owner", "tenant", "manager", "coordinator"
    is_primary: bool
    start_date: date
    end_date: date  # Null if current
```

### Jobs (Work Containers)
**Key Insight**: Jobs are auto-created containers, NOT manually created

```python
class Job:
    id: UUID
    location_id: UUID = DEFAULT_LOCATION_ID  # Branch handling the job
    property_id: UUID
    primary_contact_id: UUID
    status: str  # "Quoted", "Assessment Scheduled", "Active", "Complete"
    
    # Auto-created when:
    # - Quote is created
    # - Assessment is scheduled
    # - Imported from QuickBooks
    
    # NOT created for:
    # - Initial inquiries
    # - Tire kickers
    
    # Job completion triggers (for automated follow-ups)
    calendar_event_id: UUID  # Links to Google Calendar
    invoice_id: UUID  # Links to QuickBooks
    completed_at: datetime  # Set when BOTH calendar passed AND invoice paid
```

### Job Participants (Multiple people per job)
```python
class JobParticipant:
    job_id: UUID
    contact_id: UUID
    role: str  # "Owner", "Builder", "Realtor", "Payer"
```

### Lists (Import/Campaign Grouping)
```python
class List:
    id: UUID
    location_id: UUID = DEFAULT_LOCATION_ID  # Branch that owns this list
    name: str  # "Salem October 2024 Import"
    source: str  # "propertyradar_import", "manual_search"
    created_at: datetime
    import_file: str  # Original CSV reference
    contact_count: int
```

## MVP Scope Clarifications

### DEFINITELY IN MVP
- **PropertyRadar CSV Import** (NOT API integration)
  - Monthly imports of 2,500-3,000 contacts
  - Accumulates to 30,000+ annually
  - Deduplication critical
- **Contact/Property/Job models** with many-to-many relationships
- **Lists** to track import batches and campaign sources
- **Basic search** by person OR property
- **Campaign system** that uses Lists

### DEFERRED FROM MVP
- **QuickBooks integration** (fast follow)
- **PropertyRadar API** (CSV only for MVP)
- **Skip tracing** (post-MVP)
- **Referral tracking** (cool but not MVP)

### Key MVP Workflows

1. **Monthly PropertyRadar Import**
   - Import CSV → Create List → Deduplicate contacts/properties
   - Each import is tracked as a List
   - Campaigns created FROM Lists

2. **Contact/Property Views**
   - Look up by person OR address
   - See all properties for a contact
   - See all contacts for a property
   - See all jobs for either

3. **Job Auto-Creation**
   - Quote created → Job created
   - Assessment scheduled → Job created
   - Multiple participants linked to same job

## Critical Requirements

### Deduplication
- Same property shouldn't import twice
- Same contact (by phone) shouldn't duplicate
- Merge logic when conflicts arise

### Scalability
- System must stay fast with 50,000+ properties
- Search must be sub-second
- Import of 3,000 records < 30 seconds

### Relationships
- Preserve history when people move
- Track multiple participants per job
- Handle complex builder/owner/realtor scenarios

## Examples from Real Scenarios

### The Builder Coordination Mess
**Current Pain**: Builder texts → OpenPhone contact. Homeowner pays → QuickBooks customer. Calendar has homeowner name. Everything disconnected.

**Solution**: Both builder AND homeowner linked to same property and job. Conversation view shows all participants.

### The Moving Customer
**Scenario**: Customer fixes old house to sell, needs work on new house.

**Solution**: Customer has relationships to BOTH properties. History preserved. Can see all work across all properties.

### The Realtor Referral
**Scenario**: Realtor refers multiple clients, want to track success rate.

**Solution**: Realtor is JobParticipant with role "Referrer". Can later query all jobs referred by specific realtor.

## Future Enhancements (Post-MVP)

- Full referral tracking with metrics
- Skip tracing for properties without contacts
- QuickBooks full sync
- PropertyRadar API integration
- Advanced filtering and segmentation
- Household grouping
- Business hierarchies

---

*This document captures the discovered requirements through conversation. The focus is on getting the data model right from the start, even if the UI remains simple for MVP.*