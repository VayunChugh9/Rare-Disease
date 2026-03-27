# UI Redesign — Antechamber Health Frontend

**Date:** 2026-03-27
**Scope:** Frontend-only redesign. No backend, API, extraction, or LLM pipeline changes.
**Branch:** `ui-redesign`

## Design System

### Colors
- Background: soft gradient `#FFF8F0` (warm cream) → `#F5F0FF` (pale lavender)
- Cards: frosted glass — `rgba(255,255,255,0.85)`, `backdrop-filter: blur(12px)`, 1px `rgba(255,255,255,0.4)` border, `shadow-sm`, `rounded-2xl`
- Primary accent: `#0D9488` (teal-600)
- Text primary: `#0F172A` (slate-900), text muted: `#64748B` (slate-500)
- Section headers: 11px uppercase `tracking-wide` muted gray

### Triage Colors
| Level | Color | Hex |
|-------|-------|-----|
| Urgent | Red | `#DC2626` |
| Semi-urgent | Orange | `#EA580C` |
| Routine | Teal | `#0D9488` |
| Needs clarification | Gold | `#CA8A04` |
| Inappropriate | Gray | `#6B7280` |

### Indicators
- Abnormal values: red text or red left-border accent
- Modified/edited fields: blue left-border (`#2563EB`)

### Typography
- Font: Inter (already loaded)
- Body: 14px
- Section labels: 11px uppercase `tracking-wide`
- Patient name: 24px `font-semibold`
- Score values: bold display weight

## Technology Stack
- **shadcn/ui** components as base (Card, Button, Badge, Dialog, DropdownMenu, Sheet, Tooltip)
- **Tailwind CSS** for all styling
- **Framer Motion** for animations (stagger, slide, fade)
- **React Router** for new landing page route
- Existing API client unchanged

## Pages

### Page 1: Triage Dashboard (`/review/:id`)

#### Navigation Bar
- Fixed top, frosted glass, full-width
- Left: "Antechamber Health" teal logo text
- Center-left: "Queue" and "Upload" nav pills
- Right: "AI-assisted referral triage" muted text + user avatar circle

#### Patient Header Card (sticky)
- Left 70%: patient name (24px), demographic pills (age, sex, DOB, MRN), referral routing, date
- Right 30%: large triage badge (full color fill, white text, confidence bar), Generate PDF + Finalize Review buttons, status with pulsing dot
- All data from `extracted_data` and `triage`

#### Alert Strip (conditional)
- Only renders if `red_flags.length > 0` or `missing_info.length > 0`
- Red section for red flags, amber section for missing info
- No placeholder if both empty

#### Action Chips (conditional)
- Horizontal row of teal-outlined pills from `triage.action_items`
- Hidden if no action items

#### Main Layout: AI Summary Panel + Clinical Data

**Left Panel — AI Summary (collapsible, 35%)**
- Slides in/out, 300ms ease-out
- Grab handle on right edge with chevron
- Content: "AI-GENERATED SUMMARY" header, referral reason callout, summary narrative, triage reasoning, one-line summary
- Collapsed: 40px strip with rotated text
- Keyboard shortcut: "S" toggles
- State in React useState

**Right Content Area (65% / 100%)**

Section 1 — Vitals + Medications:
- Vitals card (55%): 2x3 grid from `clinical_data.recent_vitals`, trend indicators, abnormal highlight
- Medications card (45%): list from `clinical_data.medications.active`

Section 2 — Conditions + Labs:
- Active conditions card (50%): from `clinical_data.problem_list.active`, teal border for specialty-matching
- Recent labs card (50%): from `clinical_data.recent_labs`, table with flag indicators

Section 3 — Screening Scores (full width):
- Horizontal tiles from `clinical_data.screenings`
- Clinically significant: PHQ-9>=10, GAD-7>=10, PHQ-2>=3, AUDIT-C>=4M/3F, DAST-10>=3, HARK>=1
- Red background for concerning, sort concerning first

Section 4 — Social + Allergies + Clinical Trials:
- Social history (40%): key-value rows, safety in red bold
- Allergies (25%): list or "No known allergies" green
- Clinical trials (35%): only if `clinical_trial_relevance.potentially_eligible`

Section 5 — Historical Context (collapsed):
- Toggle bar with count of resolved conditions + procedures

#### Inline Editing
- Every field editable on click (pencil on hover)
- Blue left-border on edited fields
- Silent POST to `/api/referrals/{id}/corrections`
- Triage badge dropdown for urgency override

#### PDF Generation
- "Generate PDF" → GET `/api/referrals/{id}/summary-pdf`
- Modal preview, or placeholder toast if endpoint not built

### Page 2: Landing Page (`/`)

#### Hero (full viewport)
- Animated gradient background (cream → teal → lavender, 30s CSS)
- Left 55%: teal pill badge, headline "Every referral, triaged in seconds.", subheadline, two CTAs, trust badges
- Right 45%: floating dashboard mockup in frosted glass browser frame, bobbing animation

#### How It Works
- Three frosted glass cards, teal gradient top borders
- Step number, title, description
- Stagger fade-up on scroll (intersection observer)

#### Feature Showcase
- Large dashboard screenshot in frosted glass frame
- Floating annotation callouts

#### Benefits — Three Alternating Rows
- Alternating image-left/text-right
- Scroll-triggered slide-in animations

#### CTA Section
- Large frosted glass card centered
- "Ready to transform your referral workflow?" + demo button

#### Footer
- Logo, copyright, About/Privacy/Terms/Contact links

## Animations
- Page load: cards stagger fade-up (50ms offset)
- Card hover: translateY(-2px), shadow increase, 200ms ease-out
- AI panel slide: 300ms ease-out
- Triage badge: subtle glow
- Confidence bar: smooth fill on load
- Screening mini-bars: animate fill 400ms
- Pulsing status dot
- Edit icons: fade-in on hover
- Action chips: smooth fill on hover 150ms
- Landing gradient: 30s CSS color cycle
- Dashboard mockup: 4s translateY bob
- Scroll reveals: intersection observer, trigger once

## Data Binding
All components render dynamically from canonical JSON. No hardcoded patient data. The Bryant Bins data is test verification only. Every field pulls from the API response shape defined in `frontend/src/types/referral.ts`.

## Empty States
- No red flags + no missing info → alert strip doesn't render
- No action items → action chips don't render
- No screenings → screening section doesn't render
- No active medications → muted "No active medications documented"
- No labs → muted "No recent labs available"
- No clinical trial eligibility → trial card doesn't render
