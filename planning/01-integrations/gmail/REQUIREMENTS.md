# Gmail Integration Requirements - Multi-Channel Communication Hub

## Vision
Transform Gmail from a cluttered inbox into a smart, surgical tool that surfaces only what matters, while seamlessly connecting email threads to customer records and enabling automated email workflows.

## Current Gmail Usage

### System of Record For:
1. **Customer Interactions**
   - Quote discussions
   - Photo submissions
   - Formal communications
   - Contract/agreement exchanges

2. **Vendor Management**
   - Material orders
   - Supplier communications
   - Delivery scheduling
   - Invoice management

3. **Professional Services**
   - Accountant communications
   - Legal correspondence
   - Insurance renewals
   - Compliance documentation

4. **Future: Email Marketing Responses**
   - Campaign replies (via SmartLead)
   - Newsletter feedback
   - Customer inquiries from marketing

## Critical Pain Points

### 1. Poor Email Categorization
**Problem**: Gmail's default categorization insufficient
- Important emails buried in noise
- Distractions overwhelming important items
- Manual sorting takes too much time

**Solution Needed**: Smart filtering that understands business context

### 2. Disconnected from Customer Records
**Problem**: Email threads exist in isolation
- Photos sent via email not accessible in OpenPhone workflow
- No link between email conversations and CRM records
- Manual copying between systems

**Solution Needed**: Unified conversation view across channels

### 3. Multi-Channel Conversation Chaos
**Problem**: Conversations jump between email/text/phone
- Customer starts in email, you move them to text
- Hard to track full conversation history
- High cognitive load maintaining context

**Solution Needed**: Single threaded view regardless of channel

## Smart Email Prioritization System

### Intelligent Filtering
```python
class EmailPrioritizer:
    def analyze_email(self, email):
        priority_score = 0
        
        # Critical business emails
        if "quote approved" in email.subject.lower():
            priority_score = 100  # URGENT
        
        if email.from_address in customer_database:
            priority_score += 50  # Customer email
            
        if email.from_address in vendor_database:
            if contains_renewal_keywords(email):
                priority_score = 90  # Insurance renewal, etc.
            else:
                priority_score += 30
                
        if is_quickbooks_email(email):
            priority_score += 40
            
        # Noise reduction
        if is_marketing_email(email):
            priority_score -= 50
        if is_automated_notification(email):
            priority_score -= 30
            
        return {
            "priority": priority_score,
            "category": determine_category(email),
            "action_required": detect_action_items(email)
        }
```

### Priority Categories
1. **🔴 URGENT** (Score 90-100)
   - Quote approvals
   - Customer replies to quotes
   - Insurance/compliance deadlines
   - Payment issues

2. **🟡 IMPORTANT** (Score 50-89)
   - Customer emails (non-urgent)
   - Vendor quotes/proposals
   - Professional services updates

3. **🟢 REVIEW** (Score 20-49)
   - Routine vendor communications
   - Informational updates
   - Non-critical notifications

4. **⚫ ARCHIVE** (Score <20)
   - Marketing emails
   - Automated reports
   - Newsletters

## QuickBooks Email Monitoring

### Critical Emails to Catch
```python
QUICKBOOKS_TRIGGERS = {
    "quote_approved": {
        "subject_patterns": ["quote.*approved", "accepted.*quote"],
        "action": "send_immediate_follow_up_text",
        "alert": "push_notification"
    },
    "customer_reply_to_quote": {
        "subject_patterns": ["re:.*quote", "question.*quote"],
        "action": "flag_for_response",
        "alert": "dashboard_banner"
    },
    "payment_received": {
        "subject_patterns": ["payment.*received", "invoice.*paid"],
        "action": "update_invoice_status",
        "alert": None  # No alert needed
    }
}
```

### Automated Actions
1. **Quote Approved** → Send text within 5 minutes
2. **Customer Reply** → Create task for response
3. **Payment Received** → Update customer record
4. **Invoice Overdue** → Create collection task

## Unified Conversation View

### Multi-Channel Threading
```
Customer: John Smith
├── OpenPhone (Primary)
│   ├── SMS: "Can you look at my foundation?"
│   ├── Call: 5 min discussion
│   └── SMS: "Thanks for coming out"
├── Gmail
│   ├── Email: "Here are the photos"
│   │   └── Attachments: [crack1.jpg, crack2.jpg]
│   └── Email: "Re: Quote #1234"
└── QuickBooks
    ├── Quote: $5,000 sent
    └── Invoice: Paid
```

### Media Extraction
- Automatically extract photos from emails
- Link to customer record
- Make available in appointment creation
- Store in unified media library

## Automated Email Workflows

### Near-Term Automations
1. **Quote Follow-ups**
   - 3 days after quote sent
   - 7 days if no response
   - 14 days final follow-up

2. **Appointment Reminders**
   - 24 hours before (email)
   - 2 hours before (text)

3. **Thank You Emails**
   - 1 day after job completion
   - Include review request link

4. **Seasonal Maintenance**
   - Quarterly newsletter
   - Spring basement check reminder
   - Fall waterproofing special

### Email Template System
```python
class EmailTemplate:
    def __init__(self, template_type, customer):
        self.type = template_type
        self.customer = customer
        
    def generate(self):
        # Use Gemini with your voice training
        context = {
            "customer_name": self.customer.name,
            "job_history": self.customer.jobs,
            "last_interaction": self.customer.last_contact
        }
        
        return gemini.generate_email(
            template=self.type,
            context=context,
            voice_model="your_voice_v1"
        )
```

## Vendor Management Features

### Critical Vendor Emails
```python
VENDOR_ALERTS = {
    "insurance_renewal": {
        "keywords": ["renewal", "expiration", "coverage"],
        "advance_notice": 30,  # days
        "create_task": True,
        "recurring": True
    },
    "material_delivery": {
        "keywords": ["delivery", "shipment", "arrival"],
        "advance_notice": 1,
        "create_task": False,
        "alert": "dashboard"
    },
    "compliance_requirement": {
        "keywords": ["required", "mandatory", "deadline"],
        "advance_notice": 14,
        "create_task": True,
        "alert": "urgent"
    }
}
```

### Vendor Email Organization
- Auto-categorize by vendor
- Track order status
- Monitor delivery schedules
- Alert for action items

## Implementation Strategy

### Phase 1: Email Monitoring & Alerts
1. Connect Gmail API
2. Set up QuickBooks email detection
3. Implement priority scoring
4. Create dashboard alerts

### Phase 2: Customer Integration
1. Link emails to customer records
2. Extract and store media
3. Unified conversation view
4. Cross-channel threading

### Phase 3: Automation
1. Quote follow-up sequences
2. Appointment reminders
3. Thank you emails
4. Gemini voice integration

### Phase 4: Advanced Features
1. Vendor management system
2. Newsletter automation
3. SmartLead integration
4. Full email campaign support

## Technical Architecture

### Gmail API Integration
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GmailIntegration:
    def __init__(self, credentials):
        self.service = build('gmail', 'v1', credentials=credentials)
    
    def watch_inbox(self):
        # Set up push notifications for new emails
        request = {
            'labelIds': ['INBOX'],
            'topicName': 'projects/attackacrack/topics/gmail-webhook'
        }
        self.service.users().watch(userId='me', body=request).execute()
    
    def process_new_email(self, message_id):
        message = self.service.users().messages().get(
            userId='me', 
            id=message_id
        ).execute()
        
        # Extract key information
        email_data = self.parse_email(message)
        
        # Determine priority and actions
        priority = self.prioritize_email(email_data)
        
        # Link to customer if possible
        customer = self.match_customer(email_data['from'])
        
        # Store in database
        self.store_email(email_data, customer, priority)
        
        # Trigger any automated actions
        self.trigger_actions(email_data, priority)
```

### Database Schema
```sql
-- Email storage
CREATE TABLE emails (
    id UUID PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE,
    thread_id VARCHAR(255),
    from_address VARCHAR(255),
    to_address VARCHAR(255),
    subject TEXT,
    body TEXT,
    received_at TIMESTAMP,
    priority_score INT,
    category VARCHAR(50),
    customer_id UUID REFERENCES customers(id),
    vendor_id UUID REFERENCES vendors(id),
    processed BOOLEAN DEFAULT FALSE
);

-- Email attachments
CREATE TABLE email_attachments (
    id UUID PRIMARY KEY,
    email_id UUID REFERENCES emails(id),
    filename VARCHAR(255),
    content_type VARCHAR(100),
    storage_url TEXT,
    extracted_to_media BOOLEAN DEFAULT FALSE
);

-- Email actions
CREATE TABLE email_actions (
    id UUID PRIMARY KEY,
    email_id UUID REFERENCES emails(id),
    action_type VARCHAR(50),
    scheduled_at TIMESTAMP,
    completed_at TIMESTAMP,
    result TEXT
);
```

## Success Metrics

### Immediate Goals
- Zero missed quote approvals
- All customer photos accessible in CRM
- 90% reduction in inbox clutter
- Vendor deadlines never missed

### Long-term Goals
- 50% of emails handled automatically
- Unified conversation view across all channels
- Automated follow-up sequences running
- Complete vendor management system

## Privacy & Security

### Data Handling
- OAuth 2.0 for Gmail access
- Encrypted credential storage
- Email content encrypted at rest
- Audit log for all email actions

### Permissions Required
- `gmail.readonly` - Read emails
- `gmail.send` - Send automated emails
- `gmail.modify` - Mark as read/archived
- `gmail.labels` - Organize with labels

---

*Gmail integration will transform email from a source of stress to a powerful, automated business tool.*