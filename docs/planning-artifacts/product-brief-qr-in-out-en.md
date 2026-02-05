---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments: []
date: 2026-02-05
author: Jake
version: 1.1
updated: 2026-02-05
changelog: "Added guest-specific timezone and allowed hours settings"
language: English
---

# Product Brief: QR In/Out

## 1. Product Vision

QR In/Out is a QR code-based checkpoint access management system. It enables organizations to deploy automatically refreshing or static QR codes at designated locations, allowing visitors to scan these codes to record their check-in and check-out activities at various checkpoints.

### Core Value Propositions

- **Effortless Access Management**: Check-in/check-out with a simple QR code scan
- **Enhanced Security**: Anti-forgery protection through dynamic QR code rotation
- **Flexibility**: Choice between static or dynamic QR modes per checkpoint
- **Privacy-First**: Current version uses local storage to ensure data privacy

### Future Vision

- Launch as a public web application accessible to all users
- Expand to native mobile applications (iOS/Android)
- Potential cloud-based version with API integration

---

## 2. Target Users

### Primary Users

#### 2.1 Checkpoint Administrators
- **Role**: Create, configure, and monitor checkpoints
- **Needs**:
  - Manage checkpoint-level access permissions
  - Authorize and manage visitors
  - Query and analyze access logs
  - Configure security settings (passwords, allowed hours)

#### 2.2 Hosts (QR Code Display Operators)
- **Role**: Operate devices that display QR codes at checkpoints
- **Needs**:
  - Display real-time QR codes
  - Block access outside allowed hours
  - Screen security with password protection

#### 2.3 Guests/Visitors
- **Role**: Visit checkpoints and scan QR codes
- **Needs**:
  - Simple check-in/check-out process
  - View personal visit history
  - Immediate success/failure feedback

---

## 3. Success Metrics

### Launch Criteria
- **Completeness**: All core features implemented (Admin/Host/Guest pages)
- **Stability**: Local storage functionality works reliably
- **Usability**: Intuitive UI/UX requiring no user manual

### Key Performance Indicators (KPIs)
- QR code scan success rate > 95%
- Dynamic QR code refreshes accurately every 30 minutes
- 100% accuracy in blocking access outside allowed hours
- 0% local data loss rate

---

## 4. Project Scope

### 4.1 Admin Page

#### Checkpoint Management
- **Create/Edit**:
  - Checkpoint name
  - Location information
  - Timezone settings
  - Allowed hours for check-in/check-out
  - Authorized visitor whitelist
  - QR mode (static or dynamic)
  - Per-checkpoint admin password

#### Visitor Management
- Register/modify visitor information
  - Name
  - Additional details
  - List of authorized checkpoints
  - **Timezone Setting**: Guest's current location timezone
  - **Allowed Hours Setting**: Per-guest check-in/check-out time windows (optional)

#### Monitoring and Reporting
- **Per-Checkpoint View**: All activity logs for a specific checkpoint
- **Per-Visitor View**: All activity logs for a specific visitor
- **Data Persistence**: Continuous local storage of all records

### 4.2 Host Page

#### QR Code Display
- Select one checkpoint from those created in the admin page
- Generate and display QR code according to checkpoint settings

#### Time-Based Control
- **Within Allowed Hours**: Display QR code
- **Outside Allowed Hours**: Hide QR code + display restriction message

#### Dynamic QR Management
- Automatic refresh every 30 minutes
- Countdown timer to next refresh

#### Security
- Require admin password to exit the screen

### 4.3 Guest Page

#### Visitor Information Entry
- Interface for entering personal information
- Validation against admin-registered visitor records

#### QR Code Scanning
- Camera access and QR code recognition
- Real-time success/failure feedback

#### Visit History Management
- View personal check-in/check-out records
- Continuous local storage

---

## 5. Key Features

### 5.1 QR Code System

#### Static QR Code
- **Characteristics**: Unchanging QR code
- **Use Cases**: Printable, permanent checkpoint installations
- **Benefits**: Can be used without electronic devices

#### Dynamic QR Code
- **Characteristics**: Auto-refreshes every 30 minutes
- **Use Cases**: Security-critical checkpoints
- **Benefits**: Prevents forgery and reuse
- **Constraints**: Not printable, requires electronic device
- **Validation**: Scanning expired QR code prompts refresh message

### 5.2 Time-Based Access Control

#### Dual Time Control System
The system validates both **checkpoint allowed hours** and **guest allowed hours**.

- **Checkpoint Allowed Hours**: Time windows when the checkpoint is active
- **Guest Allowed Hours** (optional): Time windows when a specific guest can access checkpoints
- **Timezone Support**: Time calculations based on each guest's timezone
- **Access Blocking**: Both conditions must be satisfied for successful QR code scan
- **Clear Status Indication**: Display reason for allowed/restricted access

#### Time Validation Logic
```
Access Granted = (Within Checkpoint Hours) AND (Within Guest Hours OR Guest Hours Not Set)
```

### 5.3 Permission Management
- Per-checkpoint authorized visitor whitelist
- Pre-registration of visitor information required
- Block unregistered visitor access

### 5.4 Local Data Storage
- All activity logs stored locally
- Offline operation capability
- Data privacy guaranteed

---

## 6. User Journeys

### 6.1 Administrator Journey

```
1. Access admin page
2. Create checkpoint
   - Set name, location, hours
   - Choose QR mode (static/dynamic)
   - Set admin password
3. Register visitors
   - Enter visitor information
   - Assign authorized checkpoints
   - Set timezone
   - Configure allowed hours (optional)
4. Monitor activity
   - View logs by checkpoint or visitor
```

### 6.2 Host Journey

```
1. Access host page
2. Select checkpoint
3. Enter admin password
4. Display QR code
   - Verify allowed hours
   - Show countdown for dynamic QR
5. Screen lock (password protected)
```

### 6.3 Visitor Journey

```
1. Access guest page
2. Enter personal information
3. Validate information match
4. Scan QR code
5. Receive success/failure feedback
6. View visit history
```

---

## 7. Technical Considerations

### 7.1 Technology Stack (Proposed)
- **Frontend**: Web-based (React, Vue, or Svelte)
- **QR Generation**: QR code generation library (e.g., qrcode.js, node-qrcode)
- **QR Scanning**: Web Camera API (getUserMedia)
- **Local Storage**: LocalStorage, IndexedDB, or SQLite
- **Future Expansion**: Native apps (React Native or Flutter)

### 7.2 Security Requirements
- Admin password encryption
- Dynamic QR code expiration validation
- Visitor information matching
- Allowed hours server/client synchronization
- Protection against QR code replay attacks

### 7.3 Data Model (High-Level)

#### Checkpoint Entity
```typescript
{
  id: string
  name: string
  location: string
  allowed_hours: {
    start_time: string  // HH:MM format
    end_time: string    // HH:MM format
  }
  qr_mode: 'static' | 'dynamic'
  admin_password: string (hashed)
  allowed_guests: string[]  // guest IDs
}
```

#### Guest Entity
```typescript
{
  id: string
  name: string
  additional_info: Record<string, any>
  allowed_checkpoints: string[]  // checkpoint IDs
  timezone: string  // IANA timezone (e.g., "Asia/Seoul", "America/New_York")
  allowed_hours?: {  // Optional: per-guest time restrictions
    start_time: string  // HH:MM format
    end_time: string    // HH:MM format
  }
}
```

#### Activity Log Entity
```typescript
{
  id: string
  timestamp: Date
  checkpoint_id: string
  guest_id: string
  action: 'check_in' | 'check_out'
  qr_code_used: string
  status: 'success' | 'failure'
  failure_reason?: string
}
```

---

## 8. Non-Functional Requirements

### 8.1 Performance
- QR code generation: < 100ms
- QR code scanning: < 500ms
- Page load time: < 2 seconds
- Dynamic QR refresh: Exactly 30-minute intervals

### 8.2 Accessibility
- WCAG 2.1 Level AA compliance
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support

### 8.3 Browser Compatibility
- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

### 8.4 Localization
- Support for multiple languages (i18n ready)
- Timezone handling
- Date/time formatting per locale

---

## 9. Out of Scope (Version 1.0)

The following features are explicitly excluded from the initial release:

- ❌ Cloud-based data storage and synchronization
- ❌ Multi-tenancy architecture
- ❌ Advanced analytics and reporting dashboards
- ❌ Native mobile applications (iOS/Android)
- ❌ Real-time push notifications
- ❌ External system integrations (REST API, webhooks)
- ❌ Biometric authentication
- ❌ Geolocation-based check-in validation
- ❌ Bulk import/export of visitor data
- ❌ Email/SMS notifications

---

## 10. Risk Assessment

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Browser compatibility issues | High | Extensive cross-browser testing |
| QR code scanning reliability | High | Use proven libraries, implement fallback |
| Local storage limitations | Medium | Implement data cleanup strategies |
| Time synchronization issues | High | Use server time, validate on both sides |

### Product Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| User adoption | Medium | Focus on intuitive UX, provide documentation |
| Security vulnerabilities | High | Security audit, follow OWASP guidelines |
| Data loss concerns | High | Implement backup/export functionality |
| Scalability limitations | Low | Plan for cloud migration in future versions |

---

## 11. Dependencies and Assumptions

### Dependencies
- Modern web browser with camera access
- JavaScript enabled
- LocalStorage/IndexedDB support
- Stable device time synchronization

### Assumptions
- Users have basic smartphone/computer literacy
- Devices have functional cameras for QR scanning
- Internet connection available for initial app load
- Users will manage their own data backups

---

## 12. Success Criteria for Public Release

### Functional Completeness
- ✅ All three pages (Admin/Host/Guest) fully functional
- ✅ Both QR modes (static/dynamic) working correctly
- ✅ Time-based access control functioning accurately
- ✅ Local data persistence stable

### Quality Assurance
- ✅ Comprehensive test coverage (unit + integration)
- ✅ Security audit completed
- ✅ Cross-browser testing passed
- ✅ Performance benchmarks met

### Documentation
- ✅ User guide (Admin/Host/Guest)
- ✅ API documentation (for future integrations)
- ✅ Deployment guide
- ✅ Troubleshooting guide

### Community Readiness
- ✅ Open-source license selected (MIT/Apache)
- ✅ GitHub repository with proper README
- ✅ Contributing guidelines (CONTRIBUTING.md)
- ✅ Code of conduct (CODE_OF_CONDUCT.md)
- ✅ Issue templates and PR templates

---

## 13. Roadmap (Post-V1)

### Phase 2: Enhanced Features
- Cloud-based data synchronization (optional)
- Basic REST API for external integrations
- Export functionality (CSV, JSON)
- Email notifications

### Phase 3: Mobile Native Apps
- iOS app (Swift/React Native)
- Android app (Kotlin/React Native)
- Offline-first architecture
- Background QR refresh

### Phase 4: Enterprise Features
- Multi-tenancy support
- Advanced analytics dashboard
- Role-based access control (RBAC)
- Audit logging
- SSO integration

---

## 14. Next Steps

1. ✅ **Product Brief Completed** (Current document)
2. 🔜 **PRD (Product Requirements Document)**
   - Detailed functional specifications
   - UI/UX specifications with wireframes
   - Technical architecture design
   - API specifications (for future use)
   - Test plan and test cases
3. 🔜 **UX Design**
   - Wireframes for all pages
   - User flow diagrams
   - Visual design mockups
4. 🔜 **Technical Design Document**
   - System architecture
   - Database schema (local storage structure)
   - QR code generation/validation algorithms
   - Security implementation details
5. 🔜 **Implementation Planning**
   - Technology stack finalization
   - Development sprint planning
   - Resource allocation

---

## Document Metadata

- **Author**: Jake
- **Date**: 2026-02-05
- **Version**: 1.1
- **Last Updated**: 2026-02-05
- **Changelog**: Added guest-specific timezone and allowed hours settings
- **Language**: English
- **Document Type**: Product Brief
- **Next Document**: Product Requirements Document (PRD)
- **Status**: Approved for PRD Development

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| Checkpoint | A physical or logical location where access control is enforced |
| Static QR | A QR code that never changes, can be printed |
| Dynamic QR | A QR code that refreshes every 30 minutes for security |
| Host | The device/person operating the QR code display |
| Guest | A visitor who scans QR codes to check in/out |
| Admin | The person who configures checkpoints and manages visitors |
| Allowed Hours | Time windows when a checkpoint is active |
| Activity Log | Record of all check-in/check-out events |

---

## Appendix B: References

- [OWASP Top 10 Security Guidelines](https://owasp.org/www-project-top-ten/)
- [WCAG 2.1 Accessibility Standards](https://www.w3.org/WAI/WCAG21/quickref/)
- [QR Code Specification (ISO/IEC 18004)](https://www.iso.org/standard/62021.html)
- [Web Camera API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)

---

**End of Product Brief**
