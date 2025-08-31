# Test Handoff: Campaign Management API
*Created: 2025-08-31 15:05:00*
*From: test-handoff agent*
*To: fastapi-implementation*

## 🧪 TESTS CREATED

### Files Written
- `backend/tests/integration/test_campaigns_api.py` - 37 comprehensive tests

### Current Test Status (RED Phase)
```bash
# Backend test output
docker-compose exec backend pytest tests/integration/test_campaigns_api.py -xvs

FAILED tests/integration/test_campaigns_api.py::TestCampaignsListAPI::test_list_campaigns_empty
... 37 tests total - ALL FAILING (404 Not Found errors)
```

All tests are currently failing with 404 errors because no API endpoints exist yet. This is the expected RED phase of TDD.

## 📝 IMPLEMENTATION REQUIREMENTS

### Backend Implementation Needed

#### 1. API Router Setup
**File**: `backend/app/api/__init__.py`
**Requirement**: Include campaigns router in API routing

**File**: `backend/app/api/campaigns.py`
**Router**: Campaign management endpoints
**Base Path**: `/api/v1/campaigns`

#### 2. Core API Endpoints Required

##### A. Campaign CRUD Operations

###### GET /api/v1/campaigns
**Purpose**: List campaigns with pagination and filtering
**Parameters**:
- `page: int = 1` (query parameter)
- `per_page: int = 10` (query parameter, max 100)
- `status: Optional[str]` (query parameter, filter by status)
**Response**: `CampaignListResponse`
**Authentication**: Required (Bearer token)
**Business Rules**:
- Only return campaigns owned by authenticated user
- Support pagination with proper metadata
- Support filtering by campaign status
- Default sort by created_at DESC

###### GET /api/v1/campaigns/{id}
**Purpose**: Get single campaign by ID
**Parameters**:
- `id: UUID` (path parameter)
**Response**: `CampaignResponse`
**Authentication**: Required
**Business Rules**:
- Only return campaign if owned by authenticated user
- Return 404 if not found or not owned
- Return 400 for invalid UUID format

###### POST /api/v1/campaigns
**Purpose**: Create new campaign
**Request Body**: `CampaignCreate`
**Response**: `CampaignResponse` (status 201)
**Authentication**: Required
**Business Rules**:
- Set status to DRAFT by default
- Set daily_limit to 125 if not provided
- Auto-assign to authenticated user
- Validate all required fields

###### PUT /api/v1/campaigns/{id}
**Purpose**: Update existing campaign
**Parameters**:
- `id: UUID` (path parameter)
**Request Body**: `CampaignUpdate` (partial update)
**Response**: `CampaignResponse`
**Authentication**: Required
**Business Rules**:
- Only update if owned by authenticated user
- ACTIVE campaigns cannot modify message_template
- Return 404 if not found/not owned
- Return 400 if trying to modify restricted fields

###### DELETE /api/v1/campaigns/{id}
**Purpose**: Delete campaign
**Parameters**:
- `id: UUID` (path parameter)
**Response**: 204 No Content
**Authentication**: Required
**Business Rules**:
- Only delete if owned by authenticated user
- Cannot delete ACTIVE campaigns
- CASCADE delete messages (handled by DB)
- Return 404 if not found/not owned

##### B. Campaign Contact Management

###### POST /api/v1/campaigns/{id}/contacts
**Purpose**: Add contacts to campaign
**Parameters**:
- `id: UUID` (path parameter)
**Request Body**: `CampaignContactsAdd`
**Response**: `ContactAddResponse` (status 201)
**Authentication**: Required
**Business Rules**:
- Prevent duplicate contacts within campaign
- Return counts of added vs duplicates
- Validate phone number formats
- Create new contacts if they don't exist

###### POST /api/v1/campaigns/{id}/contacts/import
**Purpose**: Import contacts from CSV
**Parameters**:
- `id: UUID` (path parameter)
- `file: UploadFile` (CSV format)
**Response**: `ContactImportResponse` (status 201)
**Authentication**: Required
**Business Rules**:
- Accept CSV with headers: phone_number, name
- Validate phone number formats
- Skip invalid rows, report errors
- Prevent duplicates
- Performance: <5 seconds for 5000 rows

###### GET /api/v1/campaigns/{id}/contacts
**Purpose**: List campaign contacts
**Parameters**:
- `id: UUID` (path parameter)
- `page: int = 1` (query parameter)
- `per_page: int = 10` (query parameter)
**Response**: `CampaignContactsResponse`
**Authentication**: Required
**Business Rules**:
- Only show contacts for owned campaigns
- Support pagination
- Include opt-out status

##### C. Campaign Execution

###### POST /api/v1/campaigns/{id}/send
**Purpose**: Trigger campaign message sending
**Parameters**:
- `id: UUID` (path parameter)
**Response**: `CampaignSendResponse` (status 202)
**Authentication**: Required
**Business Rules**:
- Only ACTIVE campaigns can be sent
- Respect daily limits (125 messages/day default)
- Exclude opted-out contacts
- Queue for business hours (9am-6pm ET)
- Return task_id for async processing
- Use Celery for background processing

###### GET /api/v1/campaigns/{id}/stats
**Purpose**: Get campaign statistics
**Parameters**:
- `id: UUID` (path parameter)
**Response**: `CampaignStatsResponse`
**Authentication**: Required
**Business Rules**:
- Calculate delivery rates, success rates
- Include message status counts
- Include total contacts count
- Handle empty campaigns (zero stats)

#### 3. Pydantic Schemas Required

**File**: `backend/app/schemas/campaign.py`

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.campaign import CampaignStatus

class CampaignBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    message_template: str = Field(..., min_length=1)
    daily_limit: int = Field(default=125, ge=1, le=1000)
    total_limit: Optional[int] = Field(None, ge=1)
    status: Optional[CampaignStatus] = CampaignStatus.DRAFT

class CampaignCreate(CampaignBase):
    message_template_b: Optional[str] = None  # For A/B testing
    ab_test_percentage: Optional[int] = Field(None, ge=0, le=100)

class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    message_template: Optional[str] = Field(None, min_length=1)
    daily_limit: Optional[int] = Field(None, ge=1, le=1000)
    total_limit: Optional[int] = Field(None, ge=1)
    status: Optional[CampaignStatus] = None

class CampaignResponse(CampaignBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CampaignListResponse(BaseModel):
    campaigns: List[CampaignResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

# Contact schemas
class ContactCreate(BaseModel):
    phone_number: str = Field(..., regex=r'^\+1\d{10}$')
    name: str = Field(..., min_length=1, max_length=100)

class CampaignContactsAdd(BaseModel):
    contacts: List[ContactCreate]

class ContactAddResponse(BaseModel):
    added: int
    duplicates: int
    total_contacts: int

class ContactImportResponse(BaseModel):
    imported: int
    errors: int
    total_contacts: int
    error_details: List[str] = []

class ContactResponse(BaseModel):
    id: UUID
    phone_number: str
    name: str
    opted_out: bool
    
    class Config:
        from_attributes = True

class CampaignContactsResponse(BaseModel):
    contacts: List[ContactResponse]
    total: int
    page: int
    per_page: int

# Campaign execution schemas
class CampaignSendResponse(BaseModel):
    task_id: str
    message: str

class CampaignStatsResponse(BaseModel):
    total_contacts: int
    messages_sent: int
    messages_delivered: int
    messages_failed: int
    messages_pending: int
    delivery_rate: float  # delivered / sent
    success_rate: float   # (sent + delivered) / total
```

#### 4. Service Layer Implementation

**File**: `backend/app/services/campaign_service.py`

```python
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone
from fastapi import UploadFile

from app.models import Campaign, Contact, Message, User
from app.models.campaign import CampaignStatus
from app.schemas.campaign import CampaignCreate, CampaignUpdate
from app.tasks import send_campaign_messages

class CampaignService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_campaigns(
        self,
        user_id: UUID,
        page: int = 1,
        per_page: int = 10,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """List campaigns with pagination and filtering."""
        # Build query with user filter
        query = select(Campaign).where(Campaign.user_id == user_id)
        
        # Add status filter if provided
        if status_filter:
            query = query.where(Campaign.status == status_filter)
        
        # Add ordering
        query = query.order_by(Campaign.created_at.desc())
        
        # Count total
        count_query = select(func.count(Campaign.id)).where(Campaign.user_id == user_id)
        if status_filter:
            count_query = count_query.where(Campaign.status == status_filter)
        
        total = await self.db.scalar(count_query) or 0
        total_pages = (total + per_page - 1) // per_page
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        campaigns = await self.db.scalars(query)
        
        return {
            "campaigns": list(campaigns),
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }

    async def get_campaign(self, campaign_id: UUID, user_id: UUID) -> Optional[Campaign]:
        """Get single campaign by ID for user."""
        query = select(Campaign).where(
            and_(Campaign.id == campaign_id, Campaign.user_id == user_id)
        )
        return await self.db.scalar(query)

    async def create_campaign(self, campaign_data: CampaignCreate, user_id: UUID) -> Campaign:
        """Create new campaign."""
        campaign = Campaign(
            name=campaign_data.name,
            message_template=campaign_data.message_template,
            daily_limit=campaign_data.daily_limit,
            total_limit=campaign_data.total_limit,
            status=CampaignStatus.DRAFT,
            user_id=user_id
        )
        
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)
        
        return campaign

    async def update_campaign(
        self,
        campaign_id: UUID,
        campaign_data: CampaignUpdate,
        user_id: UUID
    ) -> Optional[Campaign]:
        """Update existing campaign."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            return None
        
        # Check restrictions for active campaigns
        if campaign.status == CampaignStatus.ACTIVE and campaign_data.message_template:
            raise ValueError("Cannot modify message template of active campaign")
        
        # Update fields
        for field, value in campaign_data.dict(exclude_unset=True).items():
            setattr(campaign, field, value)
        
        campaign.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(campaign)
        
        return campaign

    async def delete_campaign(self, campaign_id: UUID, user_id: UUID) -> bool:
        """Delete campaign if allowed."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            return False
        
        # Cannot delete active campaigns
        if campaign.status == CampaignStatus.ACTIVE:
            raise ValueError("Cannot delete active campaign")
        
        await self.db.delete(campaign)
        await self.db.commit()
        
        return True

    async def add_contacts_to_campaign(
        self,
        campaign_id: UUID,
        contacts_data: List[Dict[str, str]],
        user_id: UUID
    ) -> Dict[str, int]:
        """Add contacts to campaign with duplicate prevention."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        added = 0
        duplicates = 0
        
        for contact_data in contacts_data:
            # Check if contact exists
            existing = await self.db.scalar(
                select(Contact).where(
                    and_(
                        Contact.phone_number == contact_data["phone_number"],
                        Contact.user_id == user_id
                    )
                )
            )
            
            if existing:
                duplicates += 1
            else:
                contact = Contact(
                    phone_number=contact_data["phone_number"],
                    name=contact_data["name"],
                    user_id=user_id
                )
                self.db.add(contact)
                added += 1
        
        await self.db.commit()
        
        # Get total contact count
        total_contacts = await self.db.scalar(
            select(func.count(Contact.id)).where(Contact.user_id == user_id)
        ) or 0
        
        return {
            "added": added,
            "duplicates": duplicates,
            "total_contacts": total_contacts
        }

    async def import_contacts_from_csv(
        self,
        campaign_id: UUID,
        file: UploadFile,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Import contacts from CSV file."""
        # Implementation for CSV parsing and bulk import
        # Must handle 5000 rows in <5 seconds
        pass  # To be implemented

    async def send_campaign(self, campaign_id: UUID, user_id: UUID) -> Dict[str, str]:
        """Trigger campaign sending."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        if campaign.status != CampaignStatus.ACTIVE:
            raise ValueError("Only active campaigns can be sent")
        
        # Check business hours (9am-6pm ET)
        now = datetime.now()
        hour = now.hour
        
        if hour < 9 or hour >= 18:
            # Queue for next business day
            task = send_campaign_messages.delay(campaign_id, user_id, schedule_next_day=True)
            return {
                "task_id": str(task.id),
                "message": "Campaign queued for next business day"
            }
        else:
            # Send immediately
            task = send_campaign_messages.delay(campaign_id, user_id)
            return {
                "task_id": str(task.id),
                "message": "Campaign sending initiated"
            }

    async def get_campaign_stats(self, campaign_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Get campaign statistics."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        # Get message statistics
        stats_query = select(
            func.count(Message.id).label("total_messages"),
            func.count().filter(Message.status == "sent").label("sent"),
            func.count().filter(Message.status == "delivered").label("delivered"),
            func.count().filter(Message.status == "failed").label("failed"),
            func.count().filter(Message.status == "pending").label("pending")
        ).where(Message.campaign_id == campaign_id)
        
        result = await self.db.execute(stats_query)
        stats = result.first()
        
        # Get total contacts count
        total_contacts = await self.db.scalar(
            select(func.count(Contact.id)).where(Contact.user_id == user_id)
        ) or 0
        
        # Calculate rates
        sent_count = stats.sent or 0
        delivered_count = stats.delivered or 0
        total_attempts = stats.total_messages or 0
        
        delivery_rate = delivered_count / sent_count if sent_count > 0 else 0.0
        success_rate = (sent_count + delivered_count) / total_attempts if total_attempts > 0 else 0.0
        
        return {
            "total_contacts": total_contacts,
            "messages_sent": sent_count,
            "messages_delivered": delivered_count,
            "messages_failed": stats.failed or 0,
            "messages_pending": stats.pending or 0,
            "delivery_rate": round(delivery_rate, 2),
            "success_rate": round(success_rate, 2)
        }
```

#### 5. Authentication & Authorization

**File**: `backend/app/core/auth.py`
**Function**: `get_current_user` dependency
**Requirements**:
- JWT token validation
- Return User object for authenticated requests
- Raise 401 for invalid/missing tokens

All endpoints MUST use `current_user: User = Depends(get_current_user)` dependency.

#### 6. Celery Tasks

**File**: `backend/app/tasks/campaign_tasks.py`

```python
from celery import Celery
from typing import Dict, Any
from uuid import UUID

@celery.task(bind=True)
def send_campaign_messages(self, campaign_id: UUID, user_id: UUID, schedule_next_day: bool = False):
    """Background task to send campaign messages."""
    # Implementation for async message sending
    # Respect daily limits, business hours, opt-outs
    pass  # To be implemented by campaign specialist
```

#### 7. Performance Requirements

- **API Response Time**: <200ms for list endpoints (tested)
- **CSV Import**: <5 seconds for 5000 rows (tested)
- **Pagination**: Default 10 items, max 100 per page
- **Database Queries**: Proper indexing on user_id, status, created_at

### Frontend Implementation NOT REQUIRED
This handoff covers ONLY the backend API implementation. Frontend will be handled separately.

## 🎯 DEFINITION OF DONE

Implementation is complete when:
- [ ] All 37 test cases pass (GREEN)
- [ ] No additional functionality beyond what tests require
- [ ] Coverage >95% for new code
- [ ] Performance tests pass (<200ms, <5s CSV)
- [ ] Proper error handling for all edge cases
- [ ] Authentication working for all endpoints

## 🏃 HOW TO START

1. **Read this handoff document completely**
2. **Create the API router file**: `backend/app/api/campaigns.py`
3. **Create schemas**: `backend/app/schemas/campaign.py`
4. **Create service layer**: `backend/app/services/campaign_service.py`
5. **Register router**: Add to `backend/app/main.py` or router registry
6. **Run tests after each endpoint**: `docker-compose exec backend pytest tests/integration/test_campaigns_api.py::TestCampaignsListAPI::test_list_campaigns_empty -xvs`
7. **Continue until all 37 tests pass**

## 🧪 TEST COMMANDS

```bash
# Run all campaign API tests
docker-compose exec backend pytest tests/integration/test_campaigns_api.py -xvs

# Run specific test class
docker-compose exec backend pytest tests/integration/test_campaigns_api.py::TestCampaignsListAPI -xvs

# Run with coverage
docker-compose exec backend pytest tests/integration/test_campaigns_api.py --cov=app --cov-report=term-missing

# Run performance tests only
docker-compose exec backend pytest tests/integration/test_campaigns_api.py::TestCampaignPerformance -xvs
```

## ⚠️ CRITICAL RULES

1. **DO NOT** add features not required by tests
2. **DO NOT** modify tests to pass - fix implementation instead
3. **DO NOT** skip authentication - all endpoints require it
4. **DO NOT** ignore performance requirements - they are tested
5. **DO NOT** implement A/B testing unless tests require it
6. **DO NOT** implement frontend - API only

## 📊 EXPECTED COVERAGE

After implementation:
- Campaign service layer: 100% coverage
- API endpoints: >95% coverage
- Error handling: All paths tested
- Business rules: Completely covered

## 🔄 NEXT STEPS

After all tests pass:
1. Run full test suite to ensure no regressions
2. Run coverage report to verify >95%
3. Update todo-manager with completion status
4. Hand back to main for review and integration

## 📋 IMPLEMENTATION CHECKLIST

### Core Endpoints
- [ ] GET /api/v1/campaigns (list with pagination)
- [ ] GET /api/v1/campaigns/{id} (single campaign)
- [ ] POST /api/v1/campaigns (create)
- [ ] PUT /api/v1/campaigns/{id} (update)
- [ ] DELETE /api/v1/campaigns/{id} (delete)

### Contact Management
- [ ] POST /api/v1/campaigns/{id}/contacts (add contacts)
- [ ] GET /api/v1/campaigns/{id}/contacts (list contacts)
- [ ] POST /api/v1/campaigns/{id}/contacts/import (CSV import)

### Campaign Execution
- [ ] POST /api/v1/campaigns/{id}/send (trigger sending)
- [ ] GET /api/v1/campaigns/{id}/stats (statistics)

### Supporting Components
- [ ] Pydantic schemas (CampaignCreate, CampaignUpdate, etc.)
- [ ] Service layer (CampaignService)
- [ ] Authentication integration
- [ ] Error handling middleware
- [ ] Celery task stubs

### Business Rules Implementation
- [ ] User isolation (only own campaigns)
- [ ] Status-based restrictions (no edit active, no delete active)
- [ ] Daily limits enforcement
- [ ] Business hours checking (9am-6pm ET)
- [ ] Contact deduplication
- [ ] Opt-out exclusion
- [ ] Performance requirements

Remember: **Tests define the contract. Implement exactly what they expect, nothing more, nothing less.**