# Activity Feed UI/UX Design

## Core Requirements

### Display Hierarchy
1. **Most recent activity first** (reverse chronological)
2. **Show last message preview** for each conversation
3. **Clear type indicators** (text, call, voicemail, etc.)
4. **Contact name prominently** displayed (phone if no name)

## Filter System

### Essential Filters
- **Hide campaign messages** (DEFAULT ON) - Critical for usability
- **Unread** - Messages not yet viewed
- **Unresponded** - Customer messages without our reply
- **Has media** - Conversations with photos/videos
- **Calls only** - Filter to just phone calls
- **Today/Yesterday/This Week** - Time-based filters

### Filter Persistence
- Remember user's filter preferences
- Quick toggle for campaign messages
- Filter combinations (unread AND has media)

## Activity Item Design

### Conversation Preview
```
┌────────────────────────────────────────────────────┐
│ 👤 John Smith                           2 min ago  │
│ (617) 555-0123                         [Unread]    │
│                                                     │
│ 💬 "I have a crack in my basement wall that..."    │
│                                                     │
│ 📷 2 photos  📍 123 Main St, Quincy                │
│                                                     │
│ [Quick Reply] [Schedule] [Create Quote]            │
└────────────────────────────────────────────────────┘
```

### Call/Voicemail Preview
```
┌────────────────────────────────────────────────────┐
│ 👤 Mary Johnson                         15 min ago │
│ (781) 555-0456                                     │
│                                                     │
│ 📞 Missed call (2 attempts)                        │
│ 🔊 Voicemail (0:47)                                │
│                                                     │
│ ▶️ [────────────────] 0:00 / 0:47                  │
│                                                     │
│ [Call Back] [View Transcript]                      │
└────────────────────────────────────────────────────┘
```

### Campaign Response Preview
```
┌────────────────────────────────────────────────────┐
│ 👤 New Contact                          1 hour ago │
│ (508) 555-0789                                     │
│                                                     │
│ 💬 "Yes I'm interested in a quote"                 │
│ 🏷️ Campaign: Spring Foundation Check               │
│                                                     │
│ [View Conversation] [Add to Contacts]              │
└────────────────────────────────────────────────────┘
```

## Conversation Detail View

### Message Thread Display
```
┌────────────────────────────────────────────────────┐
│ < Back    John Smith (617) 555-0123      [⚙️]      │
├────────────────────────────────────────────────────┤
│                                                     │
│ Yesterday 3:42 PM                                  │
│ ┌─────────────────────────────────────┐           │
│ │ Hi, I saw your truck in my          │ Them      │
│ │ neighborhood. Do you fix basement    │           │
│ │ cracks?                              │           │
│ └─────────────────────────────────────┘           │
│                                                     │
│ ┌─────────────────────────────────────┐           │
│ │ Yes we do! I'm Matt from Attack A   │ You       │
│ │ Crack. Can you send photos?         │           │
│ └─────────────────────────────────────┘           │
│                                                     │
│ Today 9:15 AM                                      │
│ ┌─────────────────────────────────────┐           │
│ │ Here are the photos:                │ Them      │
│ │ [📷 Click to view]                  │           │
│ │ [📷 Click to view]                  │           │
│ └─────────────────────────────────────┘           │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ [Type a message...]                         │   │
│ │                                              │   │
│ │ [📎] [📷] [Send]                             │   │
│ └─────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────┘
```

### Inline Media Display
- **Images**: Thumbnail inline, click for full size
- **Audio**: Embedded player with play button
- **Voicemail transcripts**: Show below audio player

## Real-Time Updates

### WebSocket Integration
```javascript
// SvelteKit store for real-time updates
import { writable } from 'svelte/store';

export const activityFeed = writable([]);

// WebSocket connection
const ws = new WebSocket('wss://api.attackacrack.com/activity');

ws.onmessage = (event) => {
    const newActivity = JSON.parse(event.data);
    
    // Add to top of feed
    activityFeed.update(items => [newActivity, ...items]);
    
    // Show notification badge
    if (newActivity.unread) {
        updateUnreadCount();
    }
};
```

## Quick Actions

### Per Conversation Actions
- **Quick Reply** - Opens message composer
- **Schedule** - Creates Google Calendar appointment
- **Create Quote** - Starts quote with conversation context
- **Add Note** - Internal note (not sent)
- **Assign** - Future: assign to team member

### Bulk Actions
- Mark multiple as read
- Archive old conversations
- Export conversation list

## Mobile Considerations

### Responsive Design
- Stack elements vertically on mobile
- Larger touch targets
- Swipe gestures for quick actions
- Pull to refresh

### Mobile-Specific Features
- Click-to-call from phone numbers
- Share photos to other apps
- Voice-to-text for replies

## Performance Optimization

### Pagination Strategy
- Load 50 conversations initially
- Infinite scroll with 25 more at a time
- Virtual scrolling for huge lists

### Caching
- Cache recent conversations locally
- Optimistic UI updates
- Background sync for changes

## Implementation Priority

### MVP (Week 1)
- Basic activity list with filters
- Conversation detail view
- Hide campaign messages filter
- Inline media display

### Week 2
- WebSocket real-time updates
- Audio player for voicemails
- Quick actions
- Search functionality

### Future
- AI-suggested replies
- Sentiment analysis indicators
- Conversation summaries
- Advanced filtering

---

*The activity feed is the primary interface - must be fast, clear, and filterable to handle 125+ daily campaign messages without overwhelming actual customer conversations.*