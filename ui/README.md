# Blostem ACTIVATE - UI Dashboard Suite

Professional HTML dashboard for Blostem's ACTIVATE partnership activation intelligence system.

## Overview

This folder contains 5 complete, production-ready HTML pages providing a comprehensive dashboard for managing partnership activation:

1. **index.html** - Landing page with feature overview and navigation
2. **activate-dashboard.html** - Main dashboard showing partnerships, stalls, risks, and system health
3. **manage-interventions.html** - Workflow for generating, reviewing, and tracking intervention emails
4. **contacts.html** - Partner contact database organized by persona (CTO, Business Contact, CFO, CEO)
5. **metrics.html** - Intervention effectiveness analysis with response rates and insights
6. **settings.html** - System configuration, webhook setup, and team management

## Design Specifications

### Visual Identity
- **Primary Color**: #2563eb (Blostem blue)
- **Background**: #f8fafc (light slate)
- **Typography**: System fonts (-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto)
- **Style**: Professional fintech aesthetic, clean and modern
- **No external dependencies**: All CSS is inline for easy deployment

### Key Features
✅ **Responsive Design** - Works on desktop, tablet, and mobile
✅ **Professional Styling** - Metric cards, progress bars, tables, forms
✅ **No Emojis** - Clean, professional appearance throughout
✅ **Consistent Navigation** - 5-page navigation bar present on all pages
✅ **Mockup Data** - Representative example data showing all features
✅ **Self-Contained** - No external CSS/JS files, can be deployed as-is

## Page Descriptions

### index.html (Landing/Home)
Entry point showcasing system capabilities and navigation to all features.

**Content:**
- Hero section with CTA to dashboard
- Feature cards explaining core capabilities (Detect Stalls, Generate Interventions, Contact Management, etc.)
- Statistics grid (47 active partners, 6 stalls, 12 interventions, 67% response rate)
- About section explaining ACTIVATE's role in GTM intelligence
- Links to developer documentation

### activate-dashboard.html (Main Dashboard)
Executive overview of partnership activation status and recent activity.

**Content:**
- Key metrics: Active Partners (47), Stalls Detected (6), Interventions Sent (12), API Health (99.8%)
- Stall patterns grid: Dead on Arrival (3), Stuck in Sandbox (2), Production Blocked (1)
- Recent stalls table: 6 partners with stall patterns and detection dates
- Political risks section: Active risks with confidence levels
- System status: Webhook health, database status, last sync time
- Action buttons: Generate Email, Mark Resolved for each stall

### manage-interventions.html (Intervention Workflow)
Create, review, and track intervention emails by stall pattern.

**Content:**
- Tab-based workflow:
  - **Generate New**: Partner selector → stall pattern display → target persona → contact selector → email preview → assign owner
  - **Pending Review**: Interventions awaiting approval (3 items)
  - **Sent & Tracked**: Delivered interventions with response tracking (2 items)
  - **Response History**: Historical outcomes over time
- Contact availability checking (shows if CTO/Business Contact known for partner)
- Team owner assignment (CSM, Account Manager, etc.)
- Email preview pane showing full generated content
- Outcome badges: Generated, Sent, Responded, Bounced, etc.

### contacts.html (Contact Management)
Build and maintain partner contact database by persona.

**Content:**
- Statistics: 47 partners, 156 total contacts, 63 CTOs, 45 business contacts
- Search and filter box
- Contact groups by partner (Razorpay: 3 contacts, Jupiter: 2, Upstox: 4)
- Contact items showing: Name, Email, Persona badge (color-coded), Added date
- Edit/Remove buttons for each contact
- Add Contact form:
  - Partner dropdown
  - Full name field
  - Email field
  - Persona selector (CTO, Business Contact, CFO, CEO, CEO)
  - Confidence level dropdown
  - Add button

### metrics.html (Effectiveness Analysis)
Analyze intervention performance and guide optimization.

**Content:**
- Key metrics: Total Sent (12), Response Rate (67%), Resolution Rate (58%), Avg Response Time (2.3 hrs)
- Pattern-specific effectiveness cards:
  - Dead on Arrival: 4 sent, 75% response, 50% resolution
  - Stuck in Sandbox: 5 sent, 80% response, 60% resolution
  - Production Blocked: 3 sent, 100% response, 67% resolution
- Progress bars and trend indicators
- Response time analysis by pattern (simple bar charts)
- Recent outcomes table: 6 interventions with dates and results
- Key insights box: 4 actionable insights from the data
- Recommendations section with 3 colored callout boxes:
  - Green: Best performing pattern insights
  - Orange: Improvement recommendations
  - Blue: Data quality issues

### settings.html (System Configuration)
Manage webhook endpoints, detection thresholds, and team access.

**Content:**
- Webhook Configuration:
  - Endpoint URL display
  - API key management (rotate, view logs)
  - Webhook status indicator
  - Event selection toggles (API Calls, Errors Only, Production Only)
- Stall Detection Parameters:
  - Dead on Arrival threshold (days)
  - Stuck in Sandbox threshold (days)
  - Production Blocked threshold (days)
  - Save/Reset buttons
- Intervention Settings:
  - Auto-generate toggle
  - Email template language selector
  - Notification preferences (Email, Slack, Daily Digest)
- Team & Access:
  - Current team members list with roles
  - Add team member form with role assignment
- System Information:
  - Version, database status, uptime, certification

## Integration with Backend API

These pages are **currently static mockups** demonstrating the UI/UX design. To connect them to the backend Blostem ACTIVATE API:

### Available Backend Endpoints

```
GET    /api/activate/patterns/all/summary
       → Returns stalls, risks, intervention metrics for dashboard

GET    /api/activate/patterns/{partner_id}
       → Returns detected stalls for specific partner

POST   /api/activate/patterns/{partner_id}/generate-intervention
       → Generates intervention email with contact info

GET    /api/activate/partners/{partner_id}/contacts
       → Returns contacts grouped by persona

POST   /api/activate/partners/{partner_id}/contacts
       → Add new contact for partner

POST   /api/activate/partners/{partner_id}/intervention-outcome
       → Record intervention outcome (responded, resolved, bounced, etc.)

GET    /api/activate/interventions/metrics
       → Returns effectiveness metrics by pattern

POST   /api/activate/patterns/{partner_id}/mark-intervention-sent
POST   /api/activate/patterns/{partner_id}/mark-resolved
GET    /api/activate/political-risks/{partner_id}
```

### Next Steps for Integration

1. **Choose a Frontend Framework** (optional):
   - Vanilla JavaScript with fetch API (simplest)
   - Vue.js (lightweight, progressive)
   - React (more complex but powerful)
   - Angular (enterprise)

2. **Add JavaScript Layer**:
   - Replace hardcoded mockup data with API calls
   - Add form submission handlers
   - Implement real-time updates

3. **Authentication**:
   - Add OAuth or JWT token handling
   - Store credentials in browser/environment

4. **Error Handling**:
   - Display API errors gracefully
   - Add loading states and spinners
   - Implement retry logic

## Deployment

### Quick View (Local Development)
```bash
# Simple file serving (Python 3.6+)
cd ui/
python -m http.server 8000

# Or with Python 2
python -m SimpleHTTPServer 8000

# Then visit http://localhost:8000/index.html
```

### Production Deployment

Option 1: Serve from FastAPI
```python
from fastapi.staticfiles import StaticFiles

app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")
```

Option 2: Static hosting (AWS S3, CloudFront, Netlify, Vercel)
- All files are self-contained (no build process needed)
- Just upload the `ui/` folder contents
- Point root domain to `index.html`

Option 3: Docker container
```dockerfile
FROM nginx:alpine
COPY ui/ /usr/share/nginx/html/
EXPOSE 80
```

## Design System

### Colors
- Primary Blue: `#2563eb` (Blostem brand)
- Slate Gray: `#64748b` (text/secondary)
- Dark Gray: `#0f172a` (headings)
- Light Background: `#f8fafc`
- White: `#ffffff` (cards, forms)
- Green: `#10b981` (success, positive trends)
- Red: `#ef4444` (errors, negative)
- Orange: `#f59e0b` (warnings)
- Blue accents: `#3b82f6`, `#dbeafe`

### Typography
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
```

### Component Examples

**Metric Card**
```html
<div class="metric-card">
  <div class="metric-label">Active Partners</div>
  <div class="metric-value">47</div>
  <div class="metric-change">+3 this week</div>
</div>
```

**Action Button**
```html
<button class="action-button">Generate Intervention</button>
<button class="action-button secondary">Cancel</button>
<button class="action-button danger">Delete</button>
```

**Outcome Badge**
```html
<span class="outcome-badge responded">Responded</span>
<span class="outcome-badge resolved">Resolved</span>
<span class="outcome-badge no-response">No Response</span>
<span class="outcome-badge bounced">Bounced</span>
```

## File Structure

```
ui/
├── index.html                    (Landing page)
├── activate-dashboard.html       (Main dashboard)
├── manage-interventions.html     (Intervention workflow)
├── contacts.html                 (Contact management)
├── metrics.html                  (Effectiveness analysis)
├── settings.html                 (System configuration)
└── README.md                     (This file)
```

## Browser Compatibility

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- Mobile browsers (iOS Safari 14+, Chrome Android)

## Notes for Developers

- All CSS is inline for simplicity - no external stylesheets
- HTML is semantic and accessible
- Responsive design uses CSS Grid and Flexbox
- No build process or dependencies required
- Easy to customize colors by search-replacing #2563eb
- Form elements use standard HTML inputs (easily hookable to JavaScript)
- Tab systems and accordions use CSS classes (ready for JavaScript event listeners)

## Related Documentation

For backend API specifications and implementation details, see:
- `BLOSTEM_API_INTEGRATION.md` - Complete webhook and API documentation
- `IMPROVEMENTS_SUMMARY.md` - Overview of all ACTIVATE improvements
- `intelligence/activation_patterns.py` - Stall detection logic
- `intelligence/activation_interventions.py` - Email generation logic
- `intelligence/contact_manager.py` - Contact management logic
- `main.py` - FastAPI application and endpoints

## Support

For issues or questions about the dashboard, refer to:
1. API endpoint documentation in BLOSTEM_API_INTEGRATION.md
2. Backend implementation in main.py
3. Test suite in test_blostem_api_integration.py
