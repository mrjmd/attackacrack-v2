# Google Business Profile Integration Requirements - Attack-a-Crack v2

## Vision
Monitor and manage online reputation through automated review tracking, intelligent response suggestions, and correlation with completed jobs to maximize review acquisition and maintain high ratings.

## Core Functionality

### 1. Review Monitoring
**Real-time Review Detection:**
- Poll for new reviews every hour
- Instant notification for new reviews
- Track star rating trends
- Identify customers who've reviewed

**Review Data Captured:**
- Reviewer name (may be alias)
- Star rating (1-5)
- Review text
- Review date/time
- Owner response (if any)
- Review ID for tracking

### 2. Customer Correlation

**Matching Challenge:**
Google reviewer names often don't match CRM exactly:
- "Mike S." vs "Michael Smith"
- "Boston Homeowner" vs actual name
- Nicknames vs legal names

**Correlation Strategy:**
1. **Automatic Matching** (when possible):
   - Exact name match
   - Partial match + recent job
   - Phone number in review text

2. **Manual Curation Interface**:
   ```
   NEW REVIEW TO MATCH:
   Reviewer: "Mike S." ⭐⭐⭐⭐⭐
   Date: Nov 14, 2024
   Text: "Fixed our basement crack perfectly..."
   
   POSSIBLE MATCHES:
   [ ] Michael Smith - Job Nov 12 (Crack repair)
   [ ] Mike Sullivan - Job Nov 10 (Waterproofing)
   [ ] Create new contact
   [ ] Skip matching
   ```

3. **Smart Suggestions**:
   - Jobs completed 1-14 days before review
   - Text analysis for job type mentions
   - Geographic proximity if mentioned

### 3. Review Response Management

**Dashboard Alert:**
- Unresponded reviews highlighted
- Response time tracking
- Template suggestions based on rating

**Response Templates:**
5-Star: "Thank you {name}! We're thrilled you're happy with your {service}. Your basement is in good hands!"

4-Star: "Thanks for the feedback {name}! We appreciate your business and would love to know how we could have earned that 5th star."

1-3 Star: "Thank you for your feedback {name}. We'd like to make this right. Please call us at (508) 507-2252 to discuss."

### 4. Review Analytics

**Metrics Tracked:**
- Overall rating and trends
- Review velocity (reviews/week)
- Response rate and time
- Review-to-job conversion rate
- Source of reviewers (which follow-up converted)

**Correlation with Campaigns:**
- Which A/B message version led to review
- Optimal timing analysis
- Message sentiment correlation

## Integration with Automated Messaging

### Suppression Rules
Once review detected:
- Stop review request messages
- Update contact record
- Thank you message (optional)

### Performance Tracking
- Link review to triggering message
- Track which message versions drive reviews
- Identify optimal request timing

## Social Proof Features

### Website Widget Data
Export for website:
- Recent reviews carousel
- Average rating
- Total review count
- Response snippets

### Marketing Integration
- Auto-flag great reviews for social media
- Extract testimonial quotes
- Identify case study candidates

## Technical Implementation

### Google Business Profile API
**Scopes Required:**
- `https://www.googleapis.com/auth/business.manage`

**Endpoints Used:**
- `accounts/{account}/locations/{location}/reviews` - List reviews
- `accounts/{account}/locations/{location}/reviews/{review}/reply` - Post responses

**Rate Limits:**
- 10,000 requests per day
- Handle pagination for large review sets

### Database Schema
```sql
CREATE TABLE google_reviews (
    id UUID PRIMARY KEY,
    google_review_id VARCHAR(255) UNIQUE,
    reviewer_name VARCHAR(255),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    review_date TIMESTAMP,
    response_text TEXT,
    response_date TIMESTAMP,
    contact_id UUID REFERENCES contacts,
    job_id UUID REFERENCES jobs,
    matched_confidence ENUM('high', 'medium', 'low', 'manual'),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE review_alerts (
    id UUID PRIMARY KEY,
    review_id UUID REFERENCES google_reviews,
    alert_type ENUM('new_review', 'needs_response', 'negative'),
    acknowledged BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Dashboard Integration

### Owner Dashboard
**Reviews Section:**
- New reviews needing response (red badge)
- Rating trend chart (last 30 days)
- Response time average
- Quick response buttons

### Marketer Dashboard
**Reviews for Social:**
- 5-star reviews with photos
- Quotable reviews
- Before/after success stories
- One-click social media draft

## Success Metrics

### Response Metrics
- Response rate: >95%
- Response time: <24 hours
- Review velocity: >2/week

### Quality Metrics
- Average rating: >4.7
- Review conversion from requests: >30%
- Successful correlation rate: >80%

## Future Enhancements

### Phase 2
- Multi-location support (Connecticut branch)
- Competitor review monitoring
- Review invitation cards/QR codes
- Video testimonial requests

### Phase 3
- AI-powered response drafting
- Sentiment analysis alerts
- Review quality scoring
- SEO keyword optimization in responses

## Questions for Next Session

1. **Other Platforms**: Also monitor Yelp, Facebook, Angie's List?
2. **Incentives**: Ever offer incentives for reviews? Legal considerations?
3. **Negative Reviews**: Escalation process for 1-2 star reviews?
4. **Response Style**: Professional vs conversational tone preference?
5. **Review Goals**: Target number of reviews per month?

---

*Proper review management can significantly impact business growth through improved local SEO and social proof.*