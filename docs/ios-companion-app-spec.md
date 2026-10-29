# iOS Companion App Specification Document

**Version:** v1.0 · **Date:** 2026-10-26 · **Author:** Mobile Engineer (Fullstack Forge)
**Status:** Draft — Step 1 of KB-109
**Coordination:** Handoff window 2026-10-28 to 2026-10-30. Proposed meeting slot: **Thu 2026-10-29 10:00–11:00 UTC** (alternates: 10-28 14:00 UTC, 10-30 09:00 UTC). Awaiting Frontend Lead (agent-4747aa22) confirmation. See KB-414 coordination report for details.

---

**KB-414 Coordination Report Reference:** [Coordination Report](/tmp/coordination-report-kb-414.md) · Generated: 2026-10-27 · Architecture document task: KB-589 (delegated to Mobile Language Engineer) · Handoff meeting scheduled: Thu 2026-10-29 10:00–11:00 UTC
**Mission:** M-MVNG6264-0016-ZQWD (Firm Beachhead)
**Slice:** SL-MVNIC5SH-001E-P9IG
**Milestone:** MS-MVNIBVS4-001D-YFX8
**Feature:** F-MVNICDHF-001G-FI8Z

---

## 1. Executive Summary

The iOS Companion App enables accountants and field staff to perform on-site client visits with full offline capabilities. The app provides secure client data access, encrypted offline storage, push notifications for critical updates, and full compliance with Malaysia's PDPA 2024 and SST requirements. Built with Swift/SwiftUI using modern async/await concurrency, actors for thread safety, and protocol-oriented programming for testability.

---

## 2. Functional Requirements

### 2.1 Offline Client Browsing
- **Client List View**: Display cached client list with search/filter capabilities
- **Client Detail View**: Show client profile, contact info, tax details, and recent transactions
- **Offline-First Architecture**: All reads from local encrypted store; sync when online
- **Conflict Resolution**: Last-write-wins with server timestamp; user prompted for manual resolution on conflicts
- **Cache Expiry**: Configurable TTL (default 7 days) with background refresh when online

### 2.2 Encrypted Offline Store (AES-256 at Rest)
- **Encryption**: AES-256-GCM for all persisted data
- **Key Management**: Keys stored in iOS Keychain (kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly)
- **Data Scope**: Client records, transaction history, tax calculations, SST rates, user preferences
- **Key Rotation**: Automatic rotation every 90 days; re-encryption on app launch
- **Secure Deletion**: Crypto-shredding on logout/account removal

### 2.3 Push Notifications (APNs)
- **Notification Types**:
  - SST filing deadline reminders (T-7, T-3, T-1 days)
  - e-Invois submission status updates
  - Client data sync completion/failure
  - Compliance regulation changes
  - Firm-wide announcements
- **Payload**: Encrypted JSON with notification type, entity ID, and deep link
- **Handling**: Background fetch to pre-load data before user opens app
- **Token Management**: APNs token stored in Keychain; refreshed on app launch
- **Proxy Support**: Token proxying through backend for multi-tenant routing

### 2.4 Token Proxying & Secure Authentication
- **Auth Flow**: OAuth 2.0 + PKCE with backend-for-frontend (BFF) pattern
- **Token Storage**: Access/refresh tokens in Keychain (never in UserDefaults)
- **Token Proxy**: All API requests routed through BFF; tokens never leave device
- **Auto-Refresh**: Silent refresh 5 min before expiry using background task
- **Biometric Gate**: Face ID/Touch ID required for token access after app background > 15 min

### 2.5 PDPA 2024 Data Residency Compliance
- **Data Region**: All data stored/processed in AWS ap-southeast-1 (Singapore)
- **Data Minimization**: Only sync client data relevant to current visit
- **Consent Tracking**: Explicit consent flags per client for data processing
- **Right to Erasure**: Local delete + server delete request via API
- **Data Portability**: Export client data as JSON/CSV on demand
- **Audit Log**: Local immutable log of all data access/modification events

### 2.6 SST Tax Validation (LHDN e-Invois Integration)
- **SST Rates**: Cached locally with versioned schema (standard 6%, reduced 0%, exempt)
- **Validation Engine**: Local SST calculation matching LHDN rules
- **e-Invois Prep**: Generate UBL 2.1 compliant invoice XML for review
- **TIN Validation**: Local format check + server-side verification when online
- **Document Types**: Support 01 (standard), 02 (credit), 03 (debit), 04 (refund), 11-14 (self-billed)
- **Consolidated B2C**: Batch generation for high-volume retail clients

### 2.7 Accessibility (Dynamic Type & VoiceOver)
- **Dynamic Type**: All text scales with system setting (11pt–52pt range)
- **VoiceOver**: Full navigation support with meaningful labels, hints, and traits
- **Labels**: `accessibilityLabel`, `accessibilityHint`, `accessibilityValue` on all interactive elements
- **Traits**: Buttons, headers, links, adjustable values, search fields properly tagged
- **Rotor Support**: Custom rotor for client filtering, transaction types, date ranges
- **Color Contrast**: WCAG AA minimum (4.5:1) for all text; 3:1 for large text
- **Reduce Motion**: Respect `prefersReducedMotion` for animations
- **Dark Mode**: Full support with semantic colors

---

## 3. Non-Functional Requirements

### 3.1 Performance
- **Cold Launch**: < 2 seconds to interactive on iPhone 13+
- **Offline Search**: < 200ms for 10,000 client records
- **Sync Throughput**: 500 records/second on WiFi; 100 records/second on cellular
- **Memory Footprint**: < 150 MB baseline; < 300 MB during sync
- **Battery Impact**: < 3% per hour during active use; background sync < 1% per day

### 3.2 Security
- **Certificate Pinning**: SHA-256 pinning for API and APNs endpoints
- **Network Security**: TLS 1.3 only; ATS enforced; no cleartext traffic
- **Jailbreak Detection**: Runtime check; warn user; restrict sensitive operations
- **Screen Capture Prevention**: `UITextField` secure text entry; disable screenshots on sensitive screens
- **App Transport Security**: Custom exceptions only for local development (disabled in prod)

### 3.3 Reliability
- **Offline Duration**: Support 30 days fully offline
- **Sync Resilience**: Exponential backoff (1s, 2s, 4s, 8s, max 5m); max 3 retries
- **Crash-Free Sessions**: Target 99.9%
- **Data Integrity**: SQLite WAL mode + checksums; verify on app launch

### 3.4 Compatibility
- **iOS Version**: Minimum iOS 17.0; target latest stable
- **Devices**: iPhone (portrait/landscape), iPad (split view, multitasking)
- **Languages**: English (primary), Bahasa Malaysia, Simplified Chinese
- **RTL Support**: Ready for future Arabic/Hebrew expansion

---

## 4. Architecture Overview

### 4.1 High-Level Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation (SwiftUI)                  │
│  Views • ViewModels • Coordinators • Accessibility          │
├─────────────────────────────────────────────────────────────┤
│                        Domain (Actors)                       │
│  ClientActor • SyncActor • NotificationActor • CryptoActor  │
├─────────────────────────────────────────────────────────────┤
│                         Data (Protocols)                     │
│  ClientRepository • NotificationRepository • KeychainStore  │
├─────────────────────────────────────────────────────────────┤
│                      Infrastructure                          │
│  CoreData/SQLite • URLSession/APNs • CryptoKit • Keychain   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Core Modules

| Module | Responsibility | Key Technologies |
|--------|---------------|------------------|
| `AppCore` | App entry, DI container, environment | SwiftUI `@main`, `EnvironmentObject` |
| `Domain` | Business logic, actors, use cases | `actor`, `async/await`, protocols |
| `Data` | Repository implementations, persistence | CoreData, CryptoKit, Keychain |
| `Networking` | API client, interceptors, retry logic | URLSession, async/await, protocols |
| `Notifications` | APNs registration, handling, proxy | UserNotifications, BackgroundTasks |
| `Security` | Encryption, key management, biometrics | CryptoKit, LocalAuthentication, Keychain |
| `Compliance` | PDPA, SST, e-Invois logic | Custom validation engines |
| `Accessibility` | Dynamic Type, VoiceOver utilities | SwiftUI accessibility modifiers |
| `DesignSystem` | Colors, typography, components | SwiftUI, semantic colors |

### 4.3 Concurrency Model

- **MainActor**: All UI state and ViewModels
- **Domain Actors**: One actor per aggregate root (Client, Sync, Notification, Crypto)
- **Background Actors**: Dedicated actors for networking, persistence, background tasks
- **Structured Concurrency**: `TaskGroup` for parallel sync operations; `withTaskCancellationHandler` for cancellable work

### 4.4 Data Flow (Offline-First)

```
User Action → ViewModel → Domain Actor → Repository → Local Store (CoreData + Crypto)
                                                    ↓
                                          Background Sync Actor
                                                    ↓
                                          Network Layer → API/BFF
                                                    ↓
                                          Repository → Local Store (merge)
                                                    ↓
                                          ViewModel ← Publisher/AsyncSequence
                                                    ↓
                                                    UI Update
```

---

## 5. Data Models

### 5.1 Client (Local)

```swift
struct Client: Identifiable, Codable, Hashable {
    let id: UUID                    // Local UUID, synced with server
    let serverId: String            // Server-side identifier
    let name: String
    let tradingName: String?
    let taxId: String               // TIN (encrypted at rest)
    let sstRegistrationNumber: String?
    let address: Address
    let contacts: [Contact]
    let pdpaConsent: PDPAConsent
    let lastSyncedAt: Date
    let version: Int                // Optimistic locking
    let isDirty: Bool               // Pending local changes
}

struct Address: Codable, Hashable {
    let line1: String
    let line2: String?
    let city: String
    let state: String
    let postcode: String
    let country: String             // Default "MY"
}

struct Contact: Identifiable, Codable, Hashable {
    let id: UUID
    let name: String
    let email: String
    let phone: String
    let role: ContactRole
}

enum ContactRole: String, Codable {
    case primary, billing, technical, compliance
}

struct PDPAConsent: Codable, Hashable {
    let processing: Bool
    let marketing: Bool
    let analytics: Bool
    let consentedAt: Date
    let version: String             // Privacy policy version
}
```

### 5.2 Transaction (Local)

```swift
struct Transaction: Identifiable, Codable, Hashable {
    let id: UUID
    let serverId: String?
    let clientId: UUID
    let date: Date
    let type: TransactionType
    let amount: Decimal             // Stored as string for precision
    let currency: String            // Default "MYR"
    let sstRate: SSTRate
    let sstAmount: Decimal
    let description: String
    let reference: String?
    let status: TransactionStatus
    let eInvoisDocumentType: EInvoisDocumentType?
    let eInvoisStatus: EInvoisStatus?
    let version: Int
    let isDirty: Bool
}

enum TransactionType: String, Codable {
    case sale, purchase, expense, income, adjustment
}

enum TransactionStatus: String, Codable {
    case draft, pending, posted, cancelled
}

enum SSTRate: String, Codable {
    case standard = "0.06"
    case zero = "0.00"
    case exempt = "exempt"
    case notApplicable = "na"
    
    var decimalValue: Decimal? {
        switch self {
        case .standard: return Decimal(string: "0.06")
        case .zero: return Decimal(string: "0.00")
        default: return nil
        }
    }
}

enum EInvoisDocumentType: String, Codable {
    case standard = "01"
    case creditNote = "02"
    case debitNote = "03"
    case refund = "04"
    case selfBilledStandard = "11"
    case selfBilledCredit = "12"
    case selfBilledDebit = "13"
    case selfBilledRefund = "14"
}

enum EInvoisStatus: String, Codable {
    case notSubmitted, submitted, valid, invalid, cancelled
}
```

### 5.3 Sync State

```swift
struct SyncState: Codable {
    let lastFullSync: Date?
    let lastIncrementalSync: Date?
    let pendingUploadCount: Int
    let pendingDownloadCount: Int
    let lastError: SyncError?
    let isSyncing: Bool
}

struct SyncError: Codable, Error {
    let code: String
    let message: String
    let timestamp: Date
    let isRetryable: Bool
}
```

---

## 6. API Contracts

### 6.1 Client Sync Endpoints

| Operation | Endpoint | Method | Auth |
|-----------|----------|--------|------|
| Full Sync | `/api/v1/mobile/clients/sync/full` | POST | Bearer |
| Incremental Sync | `/api/v1/mobile/clients/sync/incremental` | POST | Bearer |
| Upload Changes | `/api/v1/mobile/clients/changes` | POST | Bearer |
| Resolve Conflict | `/api/v1/mobile/clients/conflicts/{id}/resolve` | POST | Bearer |

### 6.2 Request/Response Schemas

**Full Sync Request**
```json
{
  "lastSyncTimestamp": "2026-10-20T10:30:00Z",
  "clientVersion": 1,
  "includeTransactions": true,
  "transactionSince": "2026-10-01T00:00:00Z"
}
```

**Full Sync Response**
```json
{
  "clients": [...],
  "transactions": [...],
  "sstRates": {...},
  "serverTimestamp": "2026-10-26T10:30:00Z",
  "version": 2,
  "hasMore": false
}
```

### 6.3 Push Notification Payload

```json
{
  "aps": {
    "alert": {
      "title": "SST Filing Due",
      "body": "Client ABC Sdn Bhd - SST-02 due in 3 days"
    },
    "badge": 1,
    "sound": "default",
    "content-available": 1,
    "mutable-content": 1
  },
  "type": "sst_deadline",
  "entityId": "client-uuid",
  "entityType": "client",
  "deepLink": "myapp://client/uuid?tab=compliance",
  "priority": "high",
  "encryptionKeyId": "key-v3"
}
```

---

## 7. UI/UX Specification

### 7.1 Screen Map

```
Tab Bar (5 tabs)
├── Clients (Home)
│   ├── Client List (search, filter, sort)
│   ├── Client Detail
│   │   ├── Profile
│   │   ├── Transactions
│   │   ├── Compliance (SST, e-Invois)
│   │   └── Documents
│   └── Add Client (offline create)
├── Visits
│   ├── Upcoming Visits
│   ├── Visit Detail (check-in, notes, photos)
│   └── Visit History
├── Compliance
│   ├── SST Dashboard
│   ├── e-Invois Status
│   ├── Deadlines Calendar
│   └── Audit Log
├── Sync
│   ├── Sync Status
│   ├── Pending Changes
│   ├── Conflict Resolution
│   └── Settings
└── Profile
    ├── Account
    ├── Security (Face ID, PIN)
    ├── Notifications
    ├── Data & Privacy (PDPA)
    └── About
```

### 7.2 Key User Flows

#### Flow 1: Offline Client Visit
1. User opens app → sees cached client list
2. Taps client → views detail (all local data)
3. Adds transaction offline → marked `isDirty = true`
4. Completes visit → taps "Sync Now" or waits for background
5. Conflicts (if any) → presented for manual resolution

#### Flow 2: Push Notification → Deep Link
1. APNs notification received
2. Background fetch pre-loads client data
3. User taps notification → app opens to Client Detail → Compliance tab
4. Data already loaded → instant interaction

#### Flow 3: SST Validation
1. User creates invoice in app
2. Local SST engine validates rates, calculates tax
3. Generates UBL 2.1 XML preview
4. User reviews → taps "Submit to LHDN"
5. Background sync → BFF submits via Intermediary API
6. Push notification on completion/failure

---

## 8. Security & Compliance Details

### 8.1 Encryption Specification

| Data | Algorithm | Key Source | IV/Nonce |
|------|-----------|------------|----------|
| CoreData Store | AES-256-GCM | Keychain (per-device) | Random 12-byte per record |
| Keychain Items | Hardware-backed | Secure Enclave (if available) | N/A |
| Network Traffic | TLS 1.3 | Server cert (pinned) | N/A |
| Push Payload | AES-256-GCM | Keychain (rotated) | Random 12-byte |

### 8.2 Keychain Access Groups

```
com.fullstackforge.accounting.ios
├── com.fullstackforge.accounting.ios.tokens      // OAuth tokens
├── com.fullstackforge.accounting.ios.encryption  // Data encryption keys
├── com.fullstackforge.accounting.ios.biometric   // Biometric-protected items
└── com.fullstackforge.accounting.ios.apns        // APNs device token
```

### 8.3 PDPA Compliance Checklist

- [ ] Data Processing Agreement (DPA) with AWS for ap-southeast-1
- [ ] Consent collection UI at first client sync
- [ ] Consent withdrawal → immediate local purge + server request
- [ ] Data access request → export all client data as JSON
- [ ] Breach notification: 72-hour local log export for DPO
- [ ] Data Protection Impact Assessment (DPIA) completed
- [ ] Records of Processing Activities (ROPA) maintained

### 8.4 SST Compliance Checklist

- [ ] SST rates sourced from LHDN official publication
- [ ] Rate versioning with effective dates
- [ ] Local calculation matches LHDN test cases
- [ ] e-Invois XML validates against LHDN XSD schemas
- [ ] TIN format validation (new 12-digit format + legacy)
- [ ] Consolidated B2C invoice generation per LHDN guidelines

---

## 9. Testing Strategy

### 9.1 Unit Tests (Target: 80% coverage)
- Domain actors (ClientActor, SyncActor, CryptoActor)
- Repository implementations
- SST calculation engine
- PDPA consent logic
- Encryption/decryption round-trips

### 9.2 Integration Tests
- CoreData + CryptoKit persistence
- Keychain read/write/rotate
- APNs registration/token handling
- Background task scheduling
- Network retry/backoff logic

### 9.3 UI Tests (XCUITest)
- Critical paths: client browse → detail → add transaction → sync
- Accessibility: VoiceOver navigation, Dynamic Type scaling
- Offline/online transitions
- Biometric authentication flow

### 9.4 Compliance Tests
- AES-256-GCM encryption verification (known-answer tests)
- PDPA consent/withdrawal flows
- SST calculation against LHDN reference data
- e-Invois XML schema validation
- Keychain accessibility attributes

### 9.5 Performance Tests
- Launch time measurement (XCTMetric)
- Scroll performance (10k clients)
- Sync throughput (simulated network conditions)
- Memory profiling (Instruments)
- Battery impact (Energy Log)

---

## 10. Deployment & Operations

### 10.1 Build Configuration

| Config | Bundle ID | Provisioning | Destination |
|--------|-----------|--------------|-------------|
| Debug | `com.fullstackforge.accounting.ios.debug` | Development | TestFlight Internal |
| Staging | `com.fullstackforge.accounting.ios.staging` | Ad Hoc | TestFlight External |
| Release | `com.fullstackforge.accounting.ios` | App Store | App Store Connect |

### 10.2 CI/CD Pipeline
1. **PR Checks**: SwiftLint, SwiftFormat, unit tests, build
2. **Staging**: Deploy to TestFlight; run UI tests on device farm
3. **Release**: Promote to App Store Connect; phased rollout (10% → 50% → 100%)

### 10.3 Monitoring
- **Crash Reporting**: Firebase Crashlytics (ap-southeast-1)
- **Analytics**: Custom events (no PII); consent-gated
- **Performance**: MetricKit + custom spans
- **APNs Delivery**: Track delivery/ack rates per campaign

---

## 11. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| iOS version breaks CoreData migration | Medium | High | Lightweight migrations only; test on beta seeds |
| APNs token rotation fails silently | Low | Medium | Token validation on every app launch; fallback to re-register |
| Keychain access fails after iOS update | Low | High | Graceful degradation: re-auth flow; user guidance |
| PDPA regulation changes | Medium | High | Config-driven consent fields; remote config for policy version |
| SST rate change by LHDN | Medium | High | Remote config for rates; forced sync on app launch |
| Large client base (>50k) sync performance | Medium | Medium | Pagination, background batches, delta sync |

---

## 12. Open Questions

1. **Multi-device sync**: Should offline data sync across user's iPhone + iPad via iCloud? (Current: No, device-local only)
2. **Shared device support**: Multiple accountants sharing one iPad? (Current: Single user per device)
3. **Offline document capture**: Camera/photo for receipts? (Current: Out of scope for v1)
4. **Background sync frequency**: 15 min / 1 hr / manual only? (Current: 15 min when on WiFi + power)
5. **Firm vs SME mode**: Different UI/feature set per user role? (Current: Unified; feature flags)

---

## 13. Acceptance Criteria (Step 1 Complete)

- [ ] Specification document created at `docs/ios-companion-app-spec.md`
- [ ] All functional requirements (2.1–2.7) documented with measurable criteria
- [ ] Non-functional requirements (3.1–3.4) include specific targets
- [ ] Architecture overview (4.1–4.4) defines layers, modules, concurrency, data flow
- [ ] Data models (5.1–5.3) are Swift-ready with Codable/Identifiable
- [ ] API contracts (6.1–6.3) match backend team expectations
- [ ] UI/UX specification (7.1–7.2) covers all screens and key flows
- [ ] Security & compliance (8.1–8.4) addresses encryption, Keychain, PDPA, SST
- [ ] Testing strategy (9.1–9.5) defines coverage targets and test types
- [ ] Deployment & operations (10.1–10.3) covers build configs, CI/CD, monitoring
- [ ] Risks (11) and open questions (12) documented