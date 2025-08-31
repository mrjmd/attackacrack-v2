# PropertyRadar Integration Requirements

## Current State Discovery (August 2025)

### Business Context
- **Current Subscription**: Highest tier at $599/month with API access
- **Monthly Allowances**: 
  - 50,000 property exports
  - 2,500 email exports  
  - 2,500 mobile phone exports
- **Strategic Goal**: Build comprehensive property database before canceling expensive subscription

### Two-Tier Usage Strategy

#### Tier 1: Database Building (Future-Proofing)
- **Volume**: Up to 50,000 properties/month
- **Purpose**: Build 6-figure property database of likely customers
- **Contact Info**: Not included (would cost extra)
- **Timeline**: Ongoing until sufficient database built
- **Current Status**: Not yet implemented in v1

#### Tier 2: Active Campaigns (Immediate Need)
- **Volume**: ~2,500 contacts/month with phone/email
- **Purpose**: Immediate text and email campaigns
- **Priority**: Text campaigns first, email secondary
- **Validation**: Requires phone number verification (NumVerify)
- **Current Status**: BROKEN in v1 - this is the primary pain point

## Pain Points with Current Workflow

### Critical Issues
1. **v1 Import Broken**: Can't import PropertyRadar data for campaigns
2. **Phone Data Quality**: Wrong numbers, landlines marked as mobile
3. **Email Data Quality**: Bounces and invalid addresses
4. **Manual Lookups**: Currently manually checking Google Maps and Zillow

### Frustrations
- Paying $599/month but can't use the data effectively
- No automated campaign system despite having the data
- Manual verification of every address

## Data Quality Issues

### Phone Numbers
- PropertyRadar mobile numbers sometimes incorrect
- Landlines misidentified as mobile
- Wrong number complaints from recipients
- Need third-party validation (NumVerify selected)

### Email Addresses
- Quality concerns but less critical than phone
- Some bounces observed
- Secondary priority to phone campaigns

## Integration Requirements

### Must Have (MVP)
1. **Bulk Import**: Handle PropertyRadar CSV format
2. **Phone Validation**: NumVerify integration for all phone numbers
3. **Deduplication**: Prevent duplicate properties across imports
4. **Campaign Creation**: Auto-create campaigns from validated contacts
5. **Data Persistence**: Store all property data for future use

### Should Have (v2)
1. **API Integration**: Direct PropertyRadar API instead of CSV
2. **Address Detection**: Parse addresses from text messages
3. **Property Enrichment**: Auto-lookup when address detected
4. **Google Maps**: Distance/directions from business
5. **Batch Processing**: Handle 50k property imports

### Could Have (Future)
1. **Predictive Scoring**: Identify most likely customers
2. **Neighborhood Campaigns**: Target areas near existing customers
3. **Seasonal Targeting**: Campaign based on property characteristics
4. **Export Tracking**: Monitor PropertyRadar usage limits

## Current Manual Process

### Monthly Campaign Export
1. Log into PropertyRadar
2. Apply saved filters for likely customers
3. Export ~2,500 properties with contact info
4. Download CSV file
5. Attempt import to v1 (currently broken)
6. Manual review of failed imports
7. No campaigns actually sent

### Address Lookup Process (Per Customer)
1. Customer texts address (usually with town name)
2. Google Maps: Check distance from business
3. Zillow/Redfin: Check year built and property value
4. Mental context building about property
5. Respond to customer with this context

## Data Fields Used

### From test-large.csv (Campaign Exports)
- Property address components
- Owner name
- Phone numbers (multiple types)
- Email addresses
- Year built
- Property value estimates
- Lot size
- Building square footage
- [Need complete field list from CSV analysis]

### Additional Desired Data
- Concrete basements indicator
- Swimming pools indicator
- Other service-relevant characteristics
- More accurate phone/email data

## Success Criteria

### Immediate (Month 1)
- [ ] Successfully import 2,500 contacts from PropertyRadar
- [ ] Validate all phone numbers through NumVerify
- [ ] Launch first automated text campaign
- [ ] Zero duplicate properties in database

### Short-term (Month 3)
- [ ] 10,000+ validated contacts in database
- [ ] 5+ automated campaigns completed
- [ ] 90% phone validation accuracy
- [ ] Address detection working in conversations

### Long-term (Month 6)
- [ ] 100,000+ properties in database
- [ ] Cancel PropertyRadar subscription
- [ ] Fully automated campaign pipeline
- [ ] Real-time property enrichment in conversations

## Open Questions

### Business Model
1. What service does Attack-a-Crack provide?
2. What makes a property a "likely customer"?
3. Why are basements/pools relevant indicators?

### Technical Implementation
1. How to handle validation conflicts (PR says mobile, NumVerify says landline)?
2. Batch validation vs on-demand validation strategy?
3. How to match properties across different exports?

### Campaign Strategy
1. Optimal texts per day limits?
2. Best time windows for sending?
3. How to handle responses and opt-outs?

---

*Last Updated: August 2025*
*Status: In Discovery*