# Navigation & Information Architecture

## Primary Navigation Structure

### Top-Level Navigation Bar
```
[Logo] Dashboard | Conversations | Contacts | Campaigns | Todos | [User Menu ▼]
```

### Mobile Bottom Navigation (MVP)
```
[Dashboard] [Messages] [Contacts] [Campaigns] [More ▼]
```

## Information Architecture

### 1. Dashboard (Home/Command Center)
**Purpose**: Morning start point, money-first priority view
```
/dashboard
├── Money Waiting (Tier 1)
│   ├── Approved quotes not scheduled
│   ├── Quotes to generate
│   └── Items needing scheduling
├── Daily Operations (Tier 2)
│   ├── Today's schedule
│   ├── Week view
│   └── Follow-up status
├── Growth Intelligence (Tier 3)
│   ├── Activity feed (texts/calls)
│   ├── Campaign performance
│   └── Weather/Google Ads
└── Task Management (Tier 4)
    └── Smart todo list
```

### 2. Conversations
**Purpose**: All communication streams unified
```
/conversations
├── All Conversations (default)
│   ├── Recent (last 48 hours)
│   ├── Unread
│   ├── Starred/Priority
│   └── Archived
├── Individual Conversation View
│   ├── Message thread
│   ├── Contact info sidebar
│   ├── Property info
│   ├── Related job(s)
│   └── Quick actions (Quote, Schedule, Invoice)
└── Filters
    ├── By channel (SMS, Email, Call)
    ├── By status (New lead, Active job, Follow-up)
    └── By contact type (Customer, Vendor, Referral)
```

### 3. Contacts & Properties
**Purpose**: Dual-lens database (people OR places)
```
/contacts
├── Contacts List
│   ├── Search/Filter bar
│   ├── Contact cards
│   └── Bulk actions
├── Contact Detail
│   ├── Info & communications
│   ├── Properties (owned/managed)
│   ├── Jobs history
│   └── Referrals given
└── Import
    └── CSV upload

/properties
├── Properties List
│   ├── Map view option
│   ├── List view (default)
│   └── Filters (area, value, age)
├── Property Detail
│   ├── PropertyRadar data
│   ├── Associated contacts
│   ├── Job history
│   └── Photos/documents
└── Bulk Import
    └── PropertyRadar CSV
```

### 4. Campaigns
**Purpose**: Outreach and nurture automation
```
/campaigns
├── Active Campaigns
│   ├── Progress bars
│   ├── A/B results
│   └── Quick pause/resume
├── Lists
│   ├── Import lists (PropertyRadar batches)
│   ├── Smart lists (from searches)
│   └── List details/members
├── Create Campaign
│   ├── Select list
│   ├── Choose/create template
│   ├── Set schedule
│   └── Review & launch
└── Analytics
    ├── Response rates
    ├── Opt-outs
    └── ROI tracking
```

### 5. Todos
**Purpose**: Unified task management
```
/todos
├── Today
│   ├── Auto-generated (from system)
│   ├── Manual entries
│   └── Carried over
├── This Week
├── Completed
└── Categories
    ├── Follow-ups
    ├── Quotes
    ├── Scheduling
    └── Administrative
```

### 6. User Menu (Top Right Dropdown)
```
User Name ▼
├── Settings
│   ├── Account
│   ├── Integrations
│   ├── Notifications
│   └── Business Info
├── Financial (Future)
│   ├── Revenue reports
│   ├── Invoice tracking
│   └── QuickBooks sync
├── Marketing (Future)
│   ├── Social media
│   ├── Google Business
│   └── Review management
├── Help
└── Sign Out
```

## Mobile-First Considerations

### Critical Mobile Actions
Must work perfectly on phone:
- Read and reply to conversations
- Create and send quotes
- Check and update schedule
- View contact/property info
- Complete todos

### Desktop-Enhanced Features
Better on larger screen:
- Campaign creation/management
- Bulk imports
- Analytics/reporting
- Multi-column layouts
- Complex filtering

## Navigation Principles

### 1. Multiple Entry Points
Users can reach the same data different ways:
- Job → via Dashboard, Contact, Property, or Conversations
- Property → via Contact, Map, Campaign List, or Search
- Quote → via Dashboard, Conversation, Contact, or Job

### 2. Contextual Actions
Actions appear where needed:
- "Create Quote" in conversation view
- "Send Message" in contact view
- "View Property" in job details
- "Schedule" from approved quote

### 3. Breadcrumb Navigation
Always show path for deep navigation:
```
Contacts > John Smith > 123 Main St > Job #1234
```

### 4. Quick Search (Global)
Unified search bar that searches:
- Contacts (name, phone, email)
- Properties (address)
- Conversations (message content)
- Jobs (description, invoice #)

## State Management

### Persistent UI State
- Last selected filters
- Sort preferences
- View type (list/grid/map)
- Collapsed/expanded sections

### Cross-View Context
- Clicking contact in conversation → Opens in contact view
- Clicking property in job → Opens in property view
- Maintains back button context

## Future Navigation Expansions

### Phase 2 Additions
- Calendar (full schedule view)
- Quotes (dedicated section)
- Invoices (financial center)

### Phase 3 Additions
- Team (multi-user management)
- Reports (analytics dashboard)
- Automation (workflow builder)

### Phase 4 Additions
- Marketing Hub (social, email, reviews)
- Inventory (materials tracking)
- Subcontractors (partner portal)

## MVP Simplifications

### What's Hidden/Simplified in MVP
- Financial section → Just in dashboard widget
- Marketing → Just campaigns
- Settings → Minimal, just essentials
- Calendar → Use Google Calendar
- Multi-user → Not visible

### Progressive Disclosure
Start simple, reveal complexity as needed:
1. MVP: Core navigation only
2. Phase 2: Add financial/calendar
3. Phase 3: Add team/automation
4. Phase 4: Full feature set

---

*This IA prioritizes the daily workflow: Check dashboard → Handle conversations → Manage contacts/jobs → Run campaigns → Complete todos. Everything else is secondary.*