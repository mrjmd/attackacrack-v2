# QuickBooks Integration Requirements - Attack-a-Crack v2

## Vision
QuickBooks integration ensures every quote approval is captured instantly, invoices are ready before jobs begin, and financial data flows seamlessly between systems - turning "money waiting" into "money collected."

## Critical Business Value
**"Quote approvals are money waiting to be scheduled"** - This integration directly impacts revenue by surfacing approvals instantly and streamlining the quote-to-cash cycle.

## Core Integration Points

### 1. Quote Management

#### Quote Creation Flow
**From CRM → QuickBooks:**
```
1. Create quote in CRM with:
   - Customer info
   - Line items (crack repair, waterproofing, etc.)
   - Photos attached
   - Job notes
   
2. Push to QuickBooks:
   - Create/match customer
   - Add line items with descriptions
   - Set expiration (30 days default)
   - Include CRM reference ID
   
3. QuickBooks sends quote to customer
4. Track status in both systems
```

#### Quote Approval Detection 🚨 CRITICAL
**The Money Waiting Alert:**

**Current Problem:** Quote approvals arrive via email and get lost

**Solution:**
1. **Email Monitoring:**
   - Watch for QuickBooks approval emails
   - Parse customer and amount
   - Create TOP PRIORITY todo
   - Dashboard alert with 💰 icon
   - Push notification to phone

2. **API Polling (Backup):**
   - Check quote status every 15 minutes
   - Compare against last known state
   - Trigger alerts on status change

**Dashboard Display:**
```
💰 MONEY WAITING - QUOTES APPROVED (2)
⚠️ Johnson - $4,500 approved 2 days ago [SCHEDULE NOW]
⚠️ Martinez - $2,800 approved 4 hours ago [SCHEDULE NOW]

🚨 UNPAID JOBS (3)
⚠️ Smith - Completed 3 days ago - $3,200 [SEND INVOICE]
⚠️ Davis - Completed 2 days ago - $1,800 [CHECK PAYMENT]

📊 OPEN ESTIMATES (5) - $47,000 total
Oldest: Wilson - 8 days old [FOLLOW UP]
```

### 2. Customer Synchronization

#### Two-Way Sync Strategy
**CRM → QuickBooks:**
- New contacts from OpenPhone
- Updated phone numbers
- Address changes
- Email additions

**QuickBooks → CRM:**
- Payment history
- Credit status
- Total lifetime value
- Outstanding balances

#### Matching Logic
```python
def match_customer(crm_contact, qb_customers):
    # Priority order for matching:
    # 1. Phone number (normalized)
    # 2. Email address
    # 3. Name + partial address
    # 4. Create new if no match
```

### 3. Invoice Automation

#### Morning Invoice Generation (6 AM Daily)
**Automatic Process:**
```
1. Query Google Calendar for today's repair jobs
2. For each repair job:
   - Find associated quote in QuickBooks
   - Convert quote → invoice
   - Add job date and technician
   - Set payment terms (due on completion)
3. Update dashboard:
   "✅ 3 invoices ready for today's jobs"
4. Notify technician via SMS
```

**Benefits:**
- Invoices ready when tech arrives
- No forgotten billing
- Faster payment collection
- Consistent pricing from quote

#### Post-Job Invoice Handling
**Completion Flow:**
1. Job marked complete (Calendar + Invoice exists)
2. Send invoice to customer
3. Include payment link
4. Track payment status
5. Auto-follow-up if unpaid after 7 days

### 4. Product/Service Catalog

#### Service Items Setup
**Standard Services in QuickBooks:**
```
- CRACK-REPAIR: Foundation Crack Repair (per linear foot)
- WATERPROOF: Basement Waterproofing (per sq ft)
- BULKHEAD: Bulkhead Replacement (flat rate)
- RESURFACE: Concrete Resurfacing (per sq ft)
- ASSESSMENT: Property Evaluation (free)
- EMERGENCY: Emergency Call-Out Fee
```

**Dynamic Pricing:**
- Base rates in QuickBooks
- Multipliers for property value
- Discounts for repeat customers
- Seasonal adjustments

### 5. Financial Reporting

#### Dashboard Metrics
**Real-Time Financial Snapshot:**
```
📊 FINANCIAL OVERVIEW
Month-to-Date: $47,500 (↑ 15% vs last month)
Outstanding Invoices: $12,300 (5 invoices)
Pending Quotes: $31,000 (8 quotes)
Average Job Value: $2,850
Cash Collected Today: $4,200
```

#### Key Reports
- Revenue by service type
- Customer lifetime value
- Quote conversion rate
- Payment aging
- Seasonal trends

### 6. Payment Processing

#### Payment Methods
**Accept via QuickBooks:**
- Credit/debit cards
- ACH bank transfer
- Cash/check (manual entry)

**Payment Links:**
- Include in invoices
- Text payment link post-job
- One-click from customer phone

#### Payment Tracking
- Real-time status updates
- Auto-update CRM on payment
- Clear from "money waiting"
- Thank you message trigger

## API Technical Requirements

### QuickBooks Online API
**Scopes Required:**
- `com.intuit.quickbooks.accounting` - Full accounting access

**Key Endpoints:**
```
Customers:
- POST /v3/company/{companyId}/customer
- GET /v3/company/{companyId}/query?query=...

Estimates (Quotes):
- POST /v3/company/{companyId}/estimate
- GET /v3/company/{companyId}/estimate/{estimateId}

Invoices:
- POST /v3/company/{companyId}/invoice
- GET /v3/company/{companyId}/invoice/{invoiceId}

Payments:
- POST /v3/company/{companyId}/payment
- GET /v3/company/{companyId}/payment/{paymentId}
```

### Authentication
**OAuth 2.0 Flow:**
1. Initial authorization in settings
2. Refresh tokens stored securely
3. Auto-refresh before expiration
4. Alert if reauthorization needed

### Webhook Events
**Subscribe to:**
- Estimate.Update (quote approved/rejected)
- Invoice.Update (payment received)
- Customer.Create (new customer added)
- Payment.Create (payment received)

## Data Mapping

### Customer Fields
```
CRM Contact ←→ QuickBooks Customer
----------------------------------------
name          ←→ DisplayName
phone         ←→ PrimaryPhone.FreeFormNumber  
email         ←→ PrimaryEmailAddr.Address
address       ←→ BillAddr / ShipAddr
notes         ←→ Notes
created_date  ←→ MetaData.CreateTime
```

### Quote/Invoice Line Items
```
CRM Service  ←→ QuickBooks Line
----------------------------------------
service_type  ←→ Item (ItemRef to catalog)
description   ←→ Description
quantity      ←→ Qty
rate          ←→ UnitPrice
total         ←→ Amount
```

## Implementation Priorities

### MVP (Must Have)
1. Quote approval detection & alerts
2. Customer sync (basic matching)
3. Morning invoice generation
4. Quote creation from CRM
5. Payment status tracking

### Phase 2 (Should Have)
1. Two-way customer sync
2. Financial dashboard metrics
3. Payment link automation
4. Service catalog management
5. Webhook real-time updates

### Phase 3 (Could Have)
1. Advanced reporting
2. Multi-company support (future Connecticut branch)
3. Inventory tracking
4. Purchase orders
5. Payroll integration

## Success Metrics

### Efficiency Metrics
- Quote approval → Scheduled: <4 hours
- Invoice ready before job: 100%
- Payment collection time: <3 days
- Manual data entry eliminated: 95%

### Financial Metrics
- Quote conversion rate improvement: >10%
- Days sales outstanding reduction: >20%
- Revenue recognition accuracy: 100%

## Error Handling

### Common Issues & Solutions
1. **Customer Duplicate**
   - Detection: Phone/email match
   - Solution: Merge or link records
   
2. **Quote Approval Miss**
   - Detection: Daily reconciliation
   - Solution: Manual check + alert

3. **Sync Failure**
   - Detection: Health monitoring
   - Solution: Retry queue + alerts

4. **Invoice Mismatch**
   - Detection: Amount variance
   - Solution: Flag for review

## Questions for Next Session

1. **Payment Terms**: Net 30? Due on completion? Varies?
2. **Discounts**: Volume discounts? Seasonal promotions?
3. **Tax Handling**: How handle tax exemptions?
4. **Multi-Location**: Separate QuickBooks accounts for Connecticut?
5. **Historical Data**: Import past customers/invoices?
6. **Accounting Preferences**: Cash vs accrual basis?

---

*QuickBooks integration transforms financial operations from reactive to proactive, ensuring no money is left waiting and every job is properly invoiced.*