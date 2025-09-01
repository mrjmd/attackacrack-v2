# Property Model Gap Analysis - CRITICAL MVP REQUIREMENT

## 🚨 CRITICAL GAP IDENTIFIED
We have NO Property model implemented despite it being essential for MVP!

## What the Planning Documents Say

### From contacts-properties-jobs/REQUIREMENTS.md:
- **PropertyRadar CSV Import**: Monthly imports of 2,500-3,000 contacts
- Properties accumulate to 30,000+ annually  
- Many-to-many relationships between contacts and properties
- Each PropertyRadar record may have 2 contacts (primary & secondary)

### From propertyradar/DATA_MODEL.md:
- Detailed schema for properties table with 30+ fields
- property_owners table for owner information
- property_contacts table for contact relationships
- Two-tier import strategy (database building vs campaign)

## What We Currently Have

### ✅ Implemented:
- Contact model (but missing property relationships)
- Campaign model
- Message model
- User model
- WebhookEvent model

### ❌ MISSING (Critical for MVP):
1. **Property model** - Core entity for PropertyRadar data
2. **ContactPropertyRelationship** - Many-to-many relationships
3. **List model** - Track import batches
4. **Job model** - Auto-created work containers
5. **JobParticipant model** - Multiple people per job

## Required Models for MVP

### 1. Property Model
```python
class Property(BaseModel):
    # Identity
    property_radar_id: str  # Unique identifier from PropertyRadar
    
    # Location
    address: str
    city: str
    state: str
    zip: str
    latitude: float
    longitude: float
    
    # Characteristics
    property_type: str
    year_built: int
    square_feet: int
    bedrooms: int
    bathrooms: float
    
    # Valuation
    estimated_value: float
    estimated_equity_amount: float
    estimated_equity_percent: float
    
    # Status
    owner_occupied: bool
    listed_for_sale: bool
    in_foreclosure: bool
    
    # Relationships
    contacts: List[Contact]  # Via ContactPropertyRelationship
    jobs: List[Job]
```

### 2. ContactPropertyRelationship Model
```python
class ContactPropertyRelationship(BaseModel):
    contact_id: UUID
    property_id: UUID
    relationship_type: str  # "owner", "tenant", "manager"
    is_primary: bool
    start_date: date
    end_date: Optional[date]
```

### 3. List Model (Import Tracking)
```python
class List(BaseModel):
    name: str  # "Salem October 2024 Import"
    source: str  # "propertyradar_import"
    import_file: str
    contact_count: int
    property_count: int
    created_at: datetime
```

### 4. Job Model
```python
class Job(BaseModel):
    property_id: UUID
    primary_contact_id: UUID
    status: str  # "Quoted", "Active", "Complete"
    # Auto-created when quote/assessment created
```

## Required API Endpoints

### Property Endpoints
- `GET /api/v1/properties` - List with pagination
- `GET /api/v1/properties/{id}` - Get single property
- `GET /api/v1/properties/{id}/contacts` - Get property contacts
- `GET /api/v1/properties/{id}/jobs` - Get property jobs
- `POST /api/v1/properties/search` - Search by address

### Import Endpoints  
- `POST /api/v1/import/propertyradar` - Import CSV
- `GET /api/v1/import/lists` - Get import lists
- `GET /api/v1/import/lists/{id}` - Get list details

### Contact-Property Relationships
- `POST /api/v1/contacts/{id}/properties` - Link contact to property
- `DELETE /api/v1/contacts/{id}/properties/{property_id}` - Unlink

## Required Services

### PropertyRadarImportService
- Parse CSV with 50+ columns
- Create/update properties
- Create/update contacts  
- Establish relationships
- Track import as List
- Handle deduplication
- Validate phone numbers

### PropertyService
- CRUD operations
- Search by address
- Get related contacts
- Get related jobs

## Database Migrations Needed

1. Create properties table
2. Create contact_property_relationships table
3. Create lists table
4. Create jobs table
5. Create job_participants table
6. Add indexes for performance

## UI Requirements

### Property Views
- Property search/list page
- Property detail with contacts & jobs
- Bulk import interface for CSV

### Contact Views (Updates)
- Show associated properties
- Property relationship management

### Campaign Views (Updates)
- Create campaigns from Lists
- Show import source

## Import Workflow

```
1. User uploads PropertyRadar CSV
2. System parses 2,500-3,000 records
3. For each record:
   - Create/update property
   - Create/update primary contact
   - Create/update secondary contact
   - Link contacts to property
4. Create List entity for this import
5. User can create campaign from List
```

## Performance Considerations

- Must handle 30,000+ properties efficiently
- Search must be sub-second
- Import of 3,000 records < 30 seconds
- Proper indexes on address, phone, etc.

## Testing Requirements

- Property model tests
- Import service tests
- Deduplication tests
- Relationship management tests
- Performance tests for large datasets

## Implementation Priority

### Phase 1: Data Models (IMMEDIATE)
1. Create Property model
2. Create relationship models
3. Update Contact model
4. Create migrations

### Phase 2: Import Foundation
1. PropertyRadar CSV parser
2. Import service
3. Deduplication logic

### Phase 3: APIs
1. Property CRUD endpoints
2. Import endpoint
3. Search endpoints

### Phase 4: UI
1. Import interface
2. Property views
3. Relationship management

## Conclusion

**This is a CRITICAL GAP that must be addressed before we can claim MVP is complete.**

The PropertyRadar CSV import with proper property/contact relationships is the foundation of the business - without it, there's no way to:
- Import the 2,500-3,000 monthly contacts
- Track which contacts belong to which properties
- Manage the complex relationships (owners, tenants, etc.)
- Build the property database needed for campaigns

**Recommendation**: Start immediately with Property model creation using TDD approach.