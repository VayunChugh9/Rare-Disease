# UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the Antechamber Health frontend with frosted glass design system, collapsible AI summary panel, new landing page, and shadcn/ui components — while keeping all backend/API unchanged.

**Architecture:** Replace all existing React components with new ones built on shadcn/ui primitives + Tailwind. Add Framer Motion for animations. Add a new `/landing` route for the marketing page and move the referral queue to `/queue`. The review page at `/review/:id` gets a complete visual overhaul with a sliding AI summary panel layout.

**Tech Stack:** React 19, shadcn/ui (Card, Button, Badge, Dialog, DropdownMenu, Sheet, Tooltip), Tailwind CSS 4, Framer Motion, Lucide React icons, React Router DOM 7

---

## File Structure

```
frontend/src/
├── index.css                          — MODIFY: new theme tokens, glass utilities, animations
├── App.tsx                            — MODIFY: add landing route, restructure routes
├── lib/
│   └── utils.ts                       — CREATE: cn() utility for shadcn
├── components/
│   └── ui/                            — CREATE: shadcn primitives (card, button, badge, dialog, dropdown-menu, tooltip)
│   ├── layout/
│   │   └── AppShell.tsx               — REWRITE: frosted glass nav bar
│   ├── landing/
│   │   └── LandingPage.tsx            — CREATE: full marketing landing page
│   ├── queue/
│   │   └── ReferralQueue.tsx          — MODIFY: minor styling updates for new theme
│   ├── upload/
│   │   └── UploadPanel.tsx            — MODIFY: minor styling updates for new theme
│   ├── review/
│   │   ├── ReviewWorkspace.tsx        — REWRITE: new layout with sliding AI panel
│   │   ├── PatientHeader.tsx          — REWRITE: sticky frosted glass with triage badge
│   │   ├── AlertStrip.tsx             — CREATE: conditional red flags + missing info strip
│   │   ├── ActionChips.tsx            — CREATE: teal pill buttons from action_items
│   │   ├── AISummaryPanel.tsx         — CREATE: collapsible left panel with grab handle
│   │   ├── VitalsCard.tsx             — CREATE: 2x3 metric grid with trend indicators
│   │   ├── MedicationsCard.tsx        — CREATE: medication list card
│   │   ├── ConditionsCard.tsx         — CREATE: active conditions with specialty highlight
│   │   ├── LabsCard.tsx               — CREATE: lab results table with abnormal flags
│   │   ├── ScreeningScores.tsx        — CREATE: horizontal score tiles with mini bars
│   │   ├── SocialHistoryCard.tsx      — CREATE: key-value rows with safety alerts
│   │   ├── AllergiesCard.tsx          — CREATE: allergy list or NKDA state
│   │   ├── ClinicalTrialsCard.tsx     — CREATE: conditional trial eligibility card
│   │   ├── HistoricalContext.tsx       — CREATE: collapsed toggle for past history
│   │   ├── FindingsPanel.tsx          — DELETE (replaced by AlertStrip + ActionChips)
│   │   ├── ScreeningCard.tsx          — DELETE (replaced by ScreeningScores)
│   │   └── ClinicalSections.tsx       — DELETE (replaced by individual cards)
│   └── shared/
│       ├── EditableField.tsx          — MODIFY: add blue left-border on edited state
│       ├── StatusBadge.tsx            — REWRITE: new triage badge with glow + confidence bar
│       ├── LoadingSkeleton.tsx        — KEEP (works as-is)
│       └── EmptyState.tsx             — KEEP (works as-is)
```

---

### Task 1: Git Setup — Commit Current Work and Create Branch

**Files:** None (git operations only)

- [ ] **Step 1: Commit current work on chunks-1-3 branch**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage"
git add docs/superpowers/
git commit -m "docs: add UI redesign design spec and implementation plan"
```

- [ ] **Step 2: Create and switch to ui-redesign branch**

```bash
git checkout -b ui-redesign
```

---

### Task 2: Install Dependencies — shadcn/ui + Framer Motion

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/components.json`

- [ ] **Step 1: Install shadcn/ui dependencies and Framer Motion**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npm install framer-motion class-variance-authority clsx tailwind-merge @radix-ui/react-slot @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tooltip @radix-ui/react-popover
```

- [ ] **Step 2: Create the cn() utility**

Create `frontend/src/lib/utils.ts`:

```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 3: Verify build still works**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/lib/utils.ts
git commit -m "feat: install shadcn/ui dependencies and Framer Motion"
```

---

### Task 3: Create shadcn/ui Base Components

**Files:**
- Create: `frontend/src/components/ui/button.tsx`
- Create: `frontend/src/components/ui/card.tsx`
- Create: `frontend/src/components/ui/badge.tsx`
- Create: `frontend/src/components/ui/dialog.tsx`
- Create: `frontend/src/components/ui/dropdown-menu.tsx`
- Create: `frontend/src/components/ui/tooltip.tsx`

- [ ] **Step 1: Create Button component**

Create `frontend/src/components/ui/button.tsx`:

```tsx
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 cursor-pointer",
  {
    variants: {
      variant: {
        default: "bg-[#0D9488] text-white shadow-sm hover:bg-[#0f766e] active:scale-[0.98]",
        outline: "border border-[#0D9488] text-[#0D9488] hover:bg-[#0D9488]/5 active:scale-[0.98]",
        ghost: "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
        destructive: "bg-red-600 text-white shadow-sm hover:bg-red-700",
        link: "text-[#0D9488] underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-6 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
```

- [ ] **Step 2: Create Card component**

Create `frontend/src/components/ui/card.tsx`:

```tsx
import * as React from "react";
import { cn } from "@/lib/utils";

const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-2xl bg-white/85 backdrop-blur-[12px] border border-white/40 shadow-sm",
        className
      )}
      {...props}
    />
  )
);
Card.displayName = "Card";

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />
  )
);
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("text-[11px] font-semibold uppercase tracking-wide text-[#64748B]", className)} {...props} />
  )
);
CardTitle.displayName = "CardTitle";

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
  )
);
CardContent.displayName = "CardContent";

export { Card, CardHeader, CardTitle, CardContent };
```

- [ ] **Step 3: Create Badge component**

Create `frontend/src/components/ui/badge.tsx`:

```tsx
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide transition-colors",
  {
    variants: {
      variant: {
        default: "bg-slate-100 text-slate-700",
        urgent: "bg-[#DC2626] text-white shadow-[0_0_12px_rgba(220,38,38,0.3)]",
        semi_urgent: "bg-[#EA580C] text-white shadow-[0_0_12px_rgba(234,88,12,0.3)]",
        routine: "bg-[#0D9488] text-white shadow-[0_0_12px_rgba(13,148,136,0.3)]",
        needs_clarification: "bg-[#CA8A04] text-white shadow-[0_0_12px_rgba(202,138,4,0.3)]",
        inappropriate: "bg-[#6B7280] text-white shadow-[0_0_12px_rgba(107,114,128,0.3)]",
        outline: "border border-current bg-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
```

- [ ] **Step 4: Create Dialog component**

Create `frontend/src/components/ui/dialog.tsx`:

```tsx
import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

const Dialog = DialogPrimitive.Root;
const DialogTrigger = DialogPrimitive.Trigger;
const DialogPortal = DialogPrimitive.Portal;
const DialogClose = DialogPrimitive.Close;

const DialogOverlay = React.forwardRef<
  React.ComponentRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    )}
    {...props}
  />
));
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

const DialogContent = React.forwardRef<
  React.ComponentRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 w-full max-w-4xl translate-x-[-50%] translate-y-[-50%] rounded-2xl bg-white/95 backdrop-blur-xl border border-white/40 p-6 shadow-2xl duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
        className
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none">
        <X className="h-4 w-4" />
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
));
DialogContent.displayName = DialogPrimitive.Content.displayName;

const DialogTitle = React.forwardRef<
  React.ComponentRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn("text-lg font-semibold text-[#0F172A]", className)}
    {...props}
  />
));
DialogTitle.displayName = DialogPrimitive.Title.displayName;

export { Dialog, DialogTrigger, DialogContent, DialogClose, DialogTitle };
```

- [ ] **Step 5: Create DropdownMenu component**

Create `frontend/src/components/ui/dropdown-menu.tsx`:

```tsx
import * as React from "react";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { cn } from "@/lib/utils";

const DropdownMenu = DropdownMenuPrimitive.Root;
const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;

const DropdownMenuContent = React.forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        "z-50 min-w-[8rem] overflow-hidden rounded-xl bg-white/95 backdrop-blur-xl border border-white/40 p-1 shadow-lg",
        className
      )}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
));
DropdownMenuContent.displayName = DropdownMenuPrimitive.Content.displayName;

const DropdownMenuItem = React.forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex cursor-pointer select-none items-center rounded-lg px-3 py-2 text-sm outline-none transition-colors focus:bg-slate-100 data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      className
    )}
    {...props}
  />
));
DropdownMenuItem.displayName = DropdownMenuPrimitive.Item.displayName;

export { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem };
```

- [ ] **Step 6: Create Tooltip component**

Create `frontend/src/components/ui/tooltip.tsx`:

```tsx
import * as React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { cn } from "@/lib/utils";

const TooltipProvider = TooltipPrimitive.Provider;
const Tooltip = TooltipPrimitive.Root;
const TooltipTrigger = TooltipPrimitive.Trigger;

const TooltipContent = React.forwardRef<
  React.ComponentRef<typeof TooltipPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <TooltipPrimitive.Portal>
    <TooltipPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        "z-50 overflow-hidden rounded-lg bg-slate-900 px-3 py-1.5 text-xs text-white animate-in fade-in-0 zoom-in-95",
        className
      )}
      {...props}
    />
  </TooltipPrimitive.Portal>
));
TooltipContent.displayName = TooltipPrimitive.Content.displayName;

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider };
```

- [ ] **Step 7: Verify TypeScript compilation**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/ui/
git commit -m "feat: add shadcn/ui base components (Card, Button, Badge, Dialog, DropdownMenu, Tooltip)"
```

---

### Task 4: Update Theme and Global Styles

**Files:**
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Rewrite index.css with new design system tokens**

Replace the entire contents of `frontend/src/index.css` with:

```css
@import "tailwindcss";

@theme {
  --font-sans: "Inter", ui-sans-serif, system-ui, -apple-system, sans-serif;

  /* Primary palette */
  --color-accent: #0D9488;
  --color-accent-hover: #0f766e;
  --color-accent-light: #ccfbf1;

  /* Text */
  --color-text-primary: #0F172A;
  --color-text-muted: #64748B;

  /* Triage colors */
  --color-urgent: #DC2626;
  --color-semi-urgent: #EA580C;
  --color-routine: #0D9488;
  --color-needs-clarification: #CA8A04;
  --color-inappropriate: #6B7280;

  /* Indicators */
  --color-abnormal: #DC2626;
  --color-modified: #2563EB;
}

/* Global background gradient */
body {
  font-family: var(--font-sans);
  color: var(--color-text-primary);
  background: linear-gradient(135deg, #FFF8F0 0%, #F5F0FF 100%);
  background-attachment: fixed;
  min-height: 100vh;
}

/* Glass utility */
.glass {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.4);
}

/* Section label style */
.section-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #64748B;
}

/* Landing page gradient animation */
@keyframes gradientCycle {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.hero-gradient {
  background: linear-gradient(-45deg, #FFF8F0, #e0f5f3, #F5F0FF, #ffffff);
  background-size: 400% 400%;
  animation: gradientCycle 30s ease infinite;
}

/* Floating animation for dashboard mockup */
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-12px); }
}

.floating {
  animation: float 4s ease-in-out infinite;
}

/* Pulsing status dot */
@keyframes pulse-dot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.5; }
}

.pulse-dot {
  animation: pulse-dot 2s ease-in-out infinite;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
```

- [ ] **Step 2: Verify the app still renders**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat: update theme with frosted glass design system and gradient background"
```

---

### Task 5: Rewrite AppShell — Frosted Glass Navigation Bar

**Files:**
- Modify: `frontend/src/components/layout/AppShell.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Rewrite AppShell.tsx**

Replace the entire contents of `frontend/src/components/layout/AppShell.tsx` with:

```tsx
import { Outlet, NavLink, useLocation } from "react-router-dom";
import { LayoutList, Upload } from "lucide-react";

const NAV_ITEMS = [
  { to: "/queue", icon: LayoutList, label: "Queue" },
  { to: "/upload", icon: Upload, label: "Upload" },
];

export function AppShell() {
  const location = useLocation();
  const isReview = location.pathname.startsWith("/review/");

  return (
    <div className="flex min-h-screen flex-col">
      {/* Frosted glass nav bar */}
      <nav className="fixed top-0 w-full z-50 glass border-b border-white/20 shadow-sm">
        <div className="flex items-center justify-between px-6 py-3 max-w-[1440px] mx-auto">
          {/* Left: Logo + Nav */}
          <div className="flex items-center gap-8">
            <NavLink to="/" className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-[#0D9488]">
                Antechamber Health
              </span>
            </NavLink>

            {!isReview && (
              <div className="flex gap-1">
                {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    className={({ isActive }) =>
                      `flex items-center gap-1.5 rounded-lg px-4 py-1.5 text-[13px] font-medium transition-all duration-200 ${
                        isActive
                          ? "text-[#0D9488] font-bold border-b-2 border-[#0D9488]"
                          : "text-slate-600 hover:bg-[#0D9488]/5 hover:text-[#0D9488]"
                      }`
                    }
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {label}
                  </NavLink>
                ))}
              </div>
            )}
          </div>

          {/* Right: Tagline + Avatar */}
          <div className="flex items-center gap-4">
            <span className="text-[11px] font-medium uppercase tracking-wide text-[#64748B]">
              AI-assisted referral triage
            </span>
            <div className="h-8 w-8 rounded-full bg-[#0D9488]/10 border border-[#0D9488]/20 flex items-center justify-center">
              <span className="text-xs font-bold text-[#0D9488]">U</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main content — offset for fixed nav */}
      <main className={`flex-1 pt-[60px] ${isReview ? "" : "overflow-y-auto"}`}>
        <Outlet />
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Update App.tsx routes**

Replace the contents of `frontend/src/App.tsx` with:

```tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { ReferralQueue } from "./components/queue/ReferralQueue";
import { UploadPanel } from "./components/upload/UploadPanel";
import { ReviewWorkspace } from "./components/review/ReviewWorkspace";
import { LandingPage } from "./components/landing/LandingPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing page — outside AppShell (has its own nav) */}
        <Route path="/" element={<LandingPage />} />

        {/* App routes — inside AppShell */}
        <Route element={<AppShell />}>
          <Route path="queue" element={<ReferralQueue />} />
          <Route path="upload" element={<UploadPanel />} />
          <Route path="review/:id" element={<ReviewWorkspace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

- [ ] **Step 3: Create a placeholder LandingPage to prevent import errors**

Create `frontend/src/components/landing/LandingPage.tsx`:

```tsx
export function LandingPage() {
  return <div className="min-h-screen hero-gradient flex items-center justify-center">
    <p className="text-lg text-slate-500">Landing page placeholder</p>
  </div>;
}
```

- [ ] **Step 4: Update ReferralQueue navigation links**

In `frontend/src/components/queue/ReferralQueue.tsx`, the queue currently navigates to `/review/${id}`. Review the file and update any `navigate("/")` calls to `navigate("/queue")` if they exist for "back" navigation. Also update the upload button link if it uses `<NavLink to="/upload">`.

The queue is now at `/queue` instead of `/`. Verify the component's internal links still work.

- [ ] **Step 5: Verify build**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/layout/AppShell.tsx frontend/src/App.tsx frontend/src/components/landing/LandingPage.tsx frontend/src/components/queue/ReferralQueue.tsx
git commit -m "feat: frosted glass nav bar, restructure routes with landing page"
```

---

### Task 6: Rewrite PatientHeader — Sticky Frosted Glass with Triage Badge

**Files:**
- Rewrite: `frontend/src/components/review/PatientHeader.tsx`
- Rewrite: `frontend/src/components/shared/StatusBadge.tsx`

- [ ] **Step 1: Rewrite StatusBadge.tsx with new triage badge**

Replace the entire contents of `frontend/src/components/shared/StatusBadge.tsx` with:

```tsx
import type { ReferralStatus, TriageUrgency } from "../../types/referral";
import { Badge } from "../ui/badge";

const STATUS_STYLES: Record<ReferralStatus, string> = {
  processing: "bg-blue-100 text-blue-700",
  pending_review: "bg-amber-100 text-amber-700",
  reviewed: "bg-green-100 text-green-700",
  finalized: "bg-slate-100 text-slate-700",
  archived: "bg-gray-100 text-gray-500",
};

const STATUS_LABELS: Record<ReferralStatus, string> = {
  processing: "Processing",
  pending_review: "Ready for Review",
  reviewed: "Reviewed",
  finalized: "Finalized",
  archived: "Archived",
};

export function StatusBadge({ status }: { status: ReferralStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide ${STATUS_STYLES[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  );
}

const URGENCY_COLORS: Record<TriageUrgency, string> = {
  urgent: "#DC2626",
  semi_urgent: "#EA580C",
  routine: "#0D9488",
  needs_clarification: "#CA8A04",
  inappropriate: "#6B7280",
};

const URGENCY_LABELS: Record<TriageUrgency, string> = {
  urgent: "Urgent",
  semi_urgent: "Semi-Urgent",
  routine: "Routine",
  needs_clarification: "Needs Clarification",
  inappropriate: "Inappropriate",
};

export function TriageBadgeLarge({
  urgency,
  confidence,
}: {
  urgency: TriageUrgency;
  confidence: number;
}) {
  const color = URGENCY_COLORS[urgency];
  const label = URGENCY_LABELS[urgency];
  const pct = Math.round(confidence * 100);

  return (
    <div className="flex flex-col items-end">
      <div
        className="px-5 py-2 rounded-xl shadow-lg flex flex-col items-center"
        style={{
          backgroundColor: color,
          boxShadow: `0 0 20px ${color}40`,
        }}
      >
        <span className="text-white font-black text-sm uppercase tracking-tight">
          {label}
        </span>
        <div className="w-full h-1 bg-white/20 rounded-full mt-1.5 overflow-hidden">
          <div
            className="h-full bg-white rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      <span className="text-[10px] text-[#64748B] mt-1">{pct}% confidence</span>
    </div>
  );
}

export function TriageBadge({ urgency }: { urgency: TriageUrgency }) {
  return <Badge variant={urgency}>{URGENCY_LABELS[urgency]}</Badge>;
}
```

- [ ] **Step 2: Rewrite PatientHeader.tsx**

Replace the entire contents of `frontend/src/components/review/PatientHeader.tsx` with:

```tsx
import type { Patient, ReferralInfo, ReferringProvider, ReferralStatus, TriageUrgency } from "../../types/referral";
import { Button } from "../ui/button";
import { StatusBadge, TriageBadgeLarge } from "../shared/StatusBadge";
import { FileText, CheckCircle } from "lucide-react";

interface PatientHeaderProps {
  patient?: Patient;
  referral?: ReferralInfo;
  referringProvider?: ReferringProvider;
  status: ReferralStatus;
  urgency: TriageUrgency;
  confidence: number;
  createdAt: string | null;
  onGeneratePdf: () => void;
  onFinalize: () => void;
}

export function PatientHeader({
  patient,
  referral,
  referringProvider,
  status,
  urgency,
  confidence,
  createdAt,
  onGeneratePdf,
  onFinalize,
}: PatientHeaderProps) {
  const name = [patient?.first_name, patient?.last_name].filter(Boolean).join(" ") || "Unknown Patient";
  const ageSex = [patient?.age ? `${patient.age}` : null, patient?.sex?.[0]?.toUpperCase()].filter(Boolean).join("");

  return (
    <header className="glass sticky top-[60px] z-40 rounded-2xl p-6 mx-6 mt-4 mb-4 shadow-sm flex justify-between items-start">
      {/* Left 70% — Patient info */}
      <div className="w-[70%]">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-[24px] font-semibold text-[#0F172A]">{name}</h1>
          {ageSex && (
            <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-[11px] font-bold text-[#64748B]">
              {ageSex}
            </span>
          )}
          {patient?.date_of_birth && (
            <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-[11px] font-bold text-[#64748B]">
              DOB {patient.date_of_birth}
            </span>
          )}
          {patient?.mrn && (
            <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-[11px] font-bold text-[#64748B] uppercase">
              MRN {patient.mrn.slice(0, 8)}
            </span>
          )}
        </div>

        <div className="flex items-center gap-4 text-sm text-[#64748B]">
          {referral?.receiving_specialty && (
            <span className="flex items-center gap-1.5">
              <span className="section-label">To:</span> {referral.receiving_specialty}
            </span>
          )}
          {referringProvider?.name && (
            <>
              <span className="text-slate-300">|</span>
              <span className="flex items-center gap-1.5">
                <span className="section-label">From:</span> {referringProvider.name}
                {referringProvider.practice_name && `, ${referringProvider.practice_name}`}
              </span>
            </>
          )}
          {(referral?.date_of_referral || createdAt) && (
            <>
              <span className="text-slate-300">|</span>
              <span className="flex items-center gap-1.5">
                <span className="section-label">Date:</span> {referral?.date_of_referral || createdAt}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Right 30% — Triage + Actions */}
      <div className="w-[30%] flex flex-col items-end gap-3">
        <div className="flex items-center gap-4">
          {/* Status dot */}
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="pulse-dot absolute inline-flex h-full w-full rounded-full bg-[#0D9488] opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#0D9488]" />
            </span>
            <StatusBadge status={status} />
          </div>
          <TriageBadgeLarge urgency={urgency} confidence={confidence} />
        </div>

        <div className="flex gap-2">
          <Button size="sm" onClick={onGeneratePdf}>
            <FileText className="h-4 w-4" />
            Generate PDF
          </Button>
          <Button variant="outline" size="sm" onClick={onFinalize}>
            <CheckCircle className="h-4 w-4" />
            Finalize Review
          </Button>
        </div>
      </div>
    </header>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/review/PatientHeader.tsx frontend/src/components/shared/StatusBadge.tsx
git commit -m "feat: frosted glass PatientHeader with large triage badge and confidence bar"
```

---

### Task 7: Create AlertStrip and ActionChips Components

**Files:**
- Create: `frontend/src/components/review/AlertStrip.tsx`
- Create: `frontend/src/components/review/ActionChips.tsx`

- [ ] **Step 1: Create AlertStrip.tsx**

Create `frontend/src/components/review/AlertStrip.tsx`:

```tsx
import { AlertTriangle, Info } from "lucide-react";

interface AlertStripProps {
  redFlags: string[];
  missingInfo: string[];
}

export function AlertStrip({ redFlags, missingInfo }: AlertStripProps) {
  if (redFlags.length === 0 && missingInfo.length === 0) return null;

  return (
    <div className="grid grid-cols-2 gap-4 mx-6 mb-4">
      {redFlags.length > 0 && (
        <div className="bg-red-50/60 border border-red-200/40 p-3 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-[#DC2626]" />
            <span className="section-label text-[#DC2626]">Red Flags</span>
          </div>
          <ul className="space-y-1">
            {redFlags.map((flag, i) => (
              <li key={i} className="text-sm font-medium text-red-800">{flag}</li>
            ))}
          </ul>
        </div>
      )}
      {missingInfo.length > 0 && (
        <div className="bg-amber-50/60 border border-amber-200/40 p-3 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <Info className="h-4 w-4 text-[#CA8A04]" />
            <span className="section-label text-[#CA8A04]">Missing Information</span>
          </div>
          <ul className="space-y-1">
            {missingInfo.map((item, i) => (
              <li key={i} className="text-sm font-medium text-amber-800">{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create ActionChips.tsx**

Create `frontend/src/components/review/ActionChips.tsx`:

```tsx
interface ActionChipsProps {
  items: string[];
}

export function ActionChips({ items }: ActionChipsProps) {
  if (items.length === 0) return null;

  return (
    <div className="flex gap-3 mx-6 mb-6 flex-wrap">
      {items.map((item, i) => (
        <button
          key={i}
          className="px-4 py-1.5 rounded-full border border-[#0D9488]/30 text-[#0D9488] text-xs font-bold uppercase tracking-wider hover:bg-[#0D9488] hover:text-white transition-all duration-150"
        >
          {item}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/review/AlertStrip.tsx frontend/src/components/review/ActionChips.tsx
git commit -m "feat: conditional AlertStrip and ActionChips components"
```

---

### Task 8: Create AISummaryPanel — Collapsible Sliding Panel

**Files:**
- Create: `frontend/src/components/review/AISummaryPanel.tsx`

- [ ] **Step 1: Create AISummaryPanel.tsx**

Create `frontend/src/components/review/AISummaryPanel.tsx`:

```tsx
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Sparkles } from "lucide-react";

interface AISummaryPanelProps {
  summaryNarrative: string | null;
  triageReasoning: string | null;
  referralReason: string | null;
  oneLineSummary: string | null;
}

export function AISummaryPanel({
  summaryNarrative,
  triageReasoning,
  referralReason,
  oneLineSummary,
}: AISummaryPanelProps) {
  const [isOpen, setIsOpen] = useState(true);

  // Keyboard shortcut: "S" toggles panel
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (
        e.key === "s" &&
        !e.ctrlKey &&
        !e.metaKey &&
        !e.altKey &&
        !(e.target instanceof HTMLInputElement) &&
        !(e.target instanceof HTMLTextAreaElement)
      ) {
        setIsOpen((prev) => !prev);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="flex h-full">
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.aside
            key="panel"
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: "35%", opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            className="overflow-hidden shrink-0"
          >
            <div className="glass rounded-2xl p-6 m-2 mr-0 h-[calc(100%-16px)] overflow-y-auto">
              {/* Header */}
              <div className="flex items-center gap-2 mb-6">
                <Sparkles className="h-4 w-4 text-[#0D9488]" />
                <h2 className="section-label text-[#0F172A]">AI-Generated Summary</h2>
                <span className="ml-auto text-[10px] text-[#64748B] bg-slate-100 rounded px-1.5 py-0.5">
                  Review before finalizing
                </span>
              </div>

              {/* Referral reason callout */}
              {referralReason && (
                <div className="border border-[#0D9488]/20 bg-[#0D9488]/5 rounded-xl p-4 mb-6">
                  <span className="section-label text-[#0D9488] block mb-1">Referral Reason</span>
                  <p className="font-semibold text-[#0D9488]">{referralReason}</p>
                </div>
              )}

              {/* Summary narrative */}
              {summaryNarrative && (
                <div className="space-y-3 text-sm leading-relaxed text-[#64748B] mb-6">
                  {summaryNarrative.split("\n\n").map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
              )}

              {/* Triage reasoning */}
              {triageReasoning && (
                <div className="border-l-4 border-[#0D9488] pl-4 py-1 mb-6">
                  <span className="section-label text-[#0D9488] block mb-1">Triage Reasoning</span>
                  <p className="text-xs italic text-[#64748B]">{triageReasoning}</p>
                </div>
              )}

              {/* One-line summary */}
              {oneLineSummary && (
                <div className="pt-4 border-t border-[#0D9488]/10">
                  <p className="text-[11px] italic text-slate-400">{oneLineSummary}</p>
                </div>
              )}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Grab handle / toggle */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center justify-center w-6 shrink-0 hover:bg-slate-100 transition-colors cursor-pointer group"
        title={isOpen ? "Collapse AI Summary (S)" : "Expand AI Summary (S)"}
      >
        <div className="flex flex-col items-center gap-1">
          {isOpen ? (
            <ChevronLeft className="h-4 w-4 text-[#64748B] group-hover:text-[#0D9488]" />
          ) : (
            <ChevronRight className="h-4 w-4 text-[#64748B] group-hover:text-[#0D9488]" />
          )}
          {!isOpen && (
            <span
              className="text-[10px] font-bold uppercase tracking-widest text-[#64748B] group-hover:text-[#0D9488]"
              style={{ writingMode: "vertical-rl", textOrientation: "mixed" }}
            >
              AI Summary
            </span>
          )}
        </div>
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/review/AISummaryPanel.tsx
git commit -m "feat: collapsible AI Summary panel with slide animation and keyboard shortcut"
```

---

### Task 9: Create Clinical Data Cards — Vitals, Medications, Conditions, Labs

**Files:**
- Create: `frontend/src/components/review/VitalsCard.tsx`
- Create: `frontend/src/components/review/MedicationsCard.tsx`
- Create: `frontend/src/components/review/ConditionsCard.tsx`
- Create: `frontend/src/components/review/LabsCard.tsx`

- [ ] **Step 1: Create VitalsCard.tsx**

Create `frontend/src/components/review/VitalsCard.tsx`:

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { RecentVitals } from "../../types/referral";

interface VitalsCardProps {
  vitals?: RecentVitals;
}

function isAbnormal(key: string, value: string): boolean {
  const num = parseFloat(value);
  if (isNaN(num)) return false;
  if (key === "bmi" && num > 30) return true;
  if (key === "heart_rate" && num > 100) return true;
  if (key === "blood_pressure") {
    const parts = value.split("/");
    if (parts.length === 2) {
      const sys = parseFloat(parts[0]);
      const dia = parseFloat(parts[1]);
      return sys > 140 || dia > 90;
    }
  }
  return false;
}

interface VitalTileProps {
  label: string;
  value: string;
  unit?: string;
  abnormal?: boolean;
  trend?: string;
  priorValue?: string;
}

function VitalTile({ label, value, unit, abnormal, trend, priorValue }: VitalTileProps) {
  return (
    <div className={`p-3 rounded-xl ${abnormal ? "bg-red-50/60 border border-red-200/30" : "bg-slate-50/50"}`}>
      <span className={`section-label block mb-1 ${abnormal ? "text-[#DC2626]/70" : ""}`}>{label}</span>
      <div className="flex items-baseline gap-2">
        <span className={`text-xl font-bold ${abnormal ? "text-[#DC2626]" : "text-[#0F172A]"}`}>
          {value}
        </span>
        {unit && <span className="text-xs text-[#64748B]">{unit}</span>}
        {trend && (
          <span className={`text-xs font-bold ${abnormal ? "text-[#DC2626]" : "text-[#64748B]"}`}>
            {trend}
          </span>
        )}
      </div>
      {priorValue && (
        <span className="text-[10px] text-[#64748B]/60">Prev: {priorValue}</span>
      )}
    </div>
  );
}

export function VitalsCard({ vitals }: VitalsCardProps) {
  if (!vitals) return null;

  const tiles: VitalTileProps[] = [];

  if (vitals.weight) {
    const weightTrend = vitals.trends?.weight_3_visits;
    tiles.push({
      label: "Weight",
      value: vitals.weight,
      unit: vitals.weight.includes("kg") ? "" : "kg",
      abnormal: false,
      trend: weightTrend && weightTrend.length > 1
        ? `${parseFloat(vitals.weight) > parseFloat(weightTrend[weightTrend.length - 2]) ? "↑" : "↓"} ${Math.abs(parseFloat(vitals.weight) - parseFloat(weightTrend[weightTrend.length - 2])).toFixed(1)}`
        : undefined,
      priorValue: weightTrend && weightTrend.length > 1 ? `${weightTrend[weightTrend.length - 2]} kg` : undefined,
    });
  }

  if (vitals.bmi) {
    tiles.push({
      label: "BMI",
      value: vitals.bmi,
      abnormal: isAbnormal("bmi", vitals.bmi),
    });
  }

  if (vitals.heart_rate) {
    tiles.push({
      label: "Heart Rate",
      value: vitals.heart_rate,
      unit: "bpm",
      abnormal: isAbnormal("heart_rate", vitals.heart_rate),
    });
  }

  if (vitals.blood_pressure) {
    tiles.push({
      label: "Blood Pressure",
      value: vitals.blood_pressure,
      unit: "mmHg",
      abnormal: isAbnormal("blood_pressure", vitals.blood_pressure),
    });
  }

  if (vitals.respiratory_rate) {
    tiles.push({ label: "Resp. Rate", value: vitals.respiratory_rate, unit: "/min" });
  }

  if (vitals.height) {
    tiles.push({ label: "Height", value: vitals.height });
  }

  if (vitals.temperature) {
    tiles.push({ label: "Temperature", value: vitals.temperature });
  }

  if (vitals.pain_score) {
    tiles.push({ label: "Pain Score", value: `${vitals.pain_score}/10` });
  }

  if (vitals.oxygen_saturation) {
    tiles.push({ label: "SpO2", value: vitals.oxygen_saturation, unit: "%" });
  }

  if (tiles.length === 0) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle>Recent Vitals</CardTitle>
        {vitals.date && (
          <span className="text-[10px] uppercase font-bold text-[#64748B]">Updated {vitals.date}</span>
        )}
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          {tiles.map((tile, i) => (
            <VitalTile key={i} {...tile} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Create MedicationsCard.tsx**

Create `frontend/src/components/review/MedicationsCard.tsx`:

```tsx
import { Pill } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { Medications } from "../../types/referral";

interface MedicationsCardProps {
  medications?: Medications;
}

export function MedicationsCard({ medications }: MedicationsCardProps) {
  const active = medications?.active ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Medications</CardTitle>
      </CardHeader>
      <CardContent>
        {active.length > 0 ? (
          <div className="space-y-4">
            {active.map((med, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488] shrink-0">
                  <Pill className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-[#0F172A]">{med.name}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {med.dose && (
                      <span className="text-xs bg-slate-100 rounded px-1.5 py-0.5 text-[#64748B]">
                        {med.dose}
                      </span>
                    )}
                    {med.frequency && (
                      <span className="text-xs text-[#64748B]">{med.frequency}</span>
                    )}
                    {med.first_prescribed && (
                      <span className="text-xs text-[#64748B]">since {med.first_prescribed}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm italic text-[#64748B]">No active medications documented</p>
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 3: Create ConditionsCard.tsx**

Create `frontend/src/components/review/ConditionsCard.tsx`:

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { Condition } from "../../types/referral";

interface ConditionsCardProps {
  conditions: Condition[];
  receivingSpecialty?: string;
}

export function ConditionsCard({ conditions, receivingSpecialty }: ConditionsCardProps) {
  if (conditions.length === 0) return null;

  // Simple heuristic: highlight conditions that might match the referral specialty
  const specialtyLower = (receivingSpecialty ?? "").toLowerCase();

  function isSpecialtyRelevant(diagnosis: string): boolean {
    const diagLower = diagnosis.toLowerCase();
    // Check for keyword overlap between diagnosis and specialty
    const keywords: Record<string, string[]> = {
      endocrinology: ["diabetes", "prediabetes", "thyroid", "a1c", "insulin", "obesity", "metabolic"],
      cardiology: ["heart", "cardiac", "hypertension", "afib", "coronary", "cholesterol"],
      neurology: ["seizure", "migraine", "neuropathy", "stroke", "epilepsy"],
      psychiatry: ["depression", "anxiety", "bipolar", "schizophrenia", "ptsd"],
      rheumatology: ["arthritis", "lupus", "fibromyalgia", "autoimmune"],
    };
    const matchKeywords = keywords[specialtyLower] ?? [];
    return matchKeywords.some((kw) => diagLower.includes(kw));
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Conditions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {conditions.map((cond, i) => {
            const relevant = isSpecialtyRelevant(cond.diagnosis);
            return (
              <div
                key={i}
                className={`flex justify-between items-center text-sm p-2 rounded-lg hover:bg-slate-50 transition-colors ${
                  relevant ? "border-l-4 border-[#0D9488] pl-3" : ""
                }`}
              >
                <span className="font-medium text-[#0F172A]">{cond.diagnosis}</span>
                {cond.onset_date && (
                  <span className="section-label text-[#64748B]">Since {cond.onset_date}</span>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 4: Create LabsCard.tsx**

Create `frontend/src/components/review/LabsCard.tsx`:

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { LabPanel } from "../../types/referral";

interface LabsCardProps {
  labs?: LabPanel[];
}

export function LabsCard({ labs }: LabsCardProps) {
  if (!labs || labs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Labs</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm italic text-[#64748B]">No recent labs available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Labs</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {labs.map((panel, pi) => (
            <div key={pi}>
              <div className="flex justify-between items-center mb-3">
                {panel.panel_name && (
                  <span className="text-sm font-semibold text-[#0F172A]">{panel.panel_name}</span>
                )}
                {panel.date && (
                  <span className="text-[10px] uppercase font-bold text-[#64748B]">{panel.date}</span>
                )}
              </div>
              <div className="space-y-2">
                {panel.results.map((result, ri) => {
                  const isAbnormal = result.flag && result.flag.toLowerCase() !== "normal";
                  return (
                    <div
                      key={ri}
                      className={`flex justify-between items-center text-sm py-1.5 border-b border-slate-100 last:border-0 ${
                        isAbnormal ? "border-l-4 border-l-[#DC2626] pl-3" : ""
                      }`}
                    >
                      <span className="text-[#0F172A]">{result.test_name}</span>
                      <div className="flex items-center gap-2">
                        <span className={`font-medium ${isAbnormal ? "text-[#DC2626]" : "text-[#0F172A]"}`}>
                          {result.value}
                        </span>
                        {result.unit && (
                          <span className="text-xs text-[#64748B]">{result.unit}</span>
                        )}
                        {isAbnormal && (
                          <span className="text-[10px] font-bold text-[#DC2626] uppercase">{result.flag}</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 5: Verify build**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/review/VitalsCard.tsx frontend/src/components/review/MedicationsCard.tsx frontend/src/components/review/ConditionsCard.tsx frontend/src/components/review/LabsCard.tsx
git commit -m "feat: clinical data cards — Vitals, Medications, Conditions, Labs"
```

---

### Task 10: Create Screening Scores, Social History, Allergies, Clinical Trials, Historical Context

**Files:**
- Create: `frontend/src/components/review/ScreeningScores.tsx`
- Create: `frontend/src/components/review/SocialHistoryCard.tsx`
- Create: `frontend/src/components/review/AllergiesCard.tsx`
- Create: `frontend/src/components/review/ClinicalTrialsCard.tsx`
- Create: `frontend/src/components/review/HistoricalContext.tsx`

- [ ] **Step 1: Create ScreeningScores.tsx**

Create `frontend/src/components/review/ScreeningScores.tsx`:

```tsx
import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { Screening } from "../../types/referral";

interface ScreeningScoresProps {
  screenings?: Screening[];
}

const THRESHOLDS: Record<string, number> = {
  "PHQ-9": 10,
  "GAD-7": 10,
  "PHQ-2": 3,
  "AUDIT-C": 4, // Using male threshold as default
  "DAST-10": 3,
  "HARK": 1,
};

function isConcerning(instrument: string, score: number): boolean {
  const threshold = THRESHOLDS[instrument.toUpperCase()] ?? THRESHOLDS[instrument];
  if (threshold === undefined) return false;
  return score >= threshold;
}

function getMaxScore(instrument: string): number {
  const maxScores: Record<string, number> = {
    "PHQ-9": 27,
    "GAD-7": 21,
    "PHQ-2": 6,
    "AUDIT-C": 12,
    "DAST-10": 10,
    "HARK": 4,
    "CSSRS": 6,
  };
  return maxScores[instrument.toUpperCase()] ?? maxScores[instrument] ?? 30;
}

export function ScreeningScores({ screenings }: ScreeningScoresProps) {
  if (!screenings || screenings.length === 0) return null;

  // Sort: concerning scores first
  const sorted = [...screenings].sort((a, b) => {
    const aScore = parseFloat(a.score) || 0;
    const bScore = parseFloat(b.score) || 0;
    const aConcerning = isConcerning(a.instrument, aScore);
    const bConcerning = isConcerning(b.instrument, bScore);
    if (aConcerning && !bConcerning) return -1;
    if (!aConcerning && bConcerning) return 1;
    return 0;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Screening Scores</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-4 overflow-x-auto pb-2">
          {sorted.map((screening, i) => {
            const score = parseFloat(screening.score) || 0;
            const max = getMaxScore(screening.instrument);
            const concerning = isConcerning(screening.instrument, score);
            const pct = Math.min((score / max) * 100, 100);

            return (
              <div
                key={i}
                className={`min-w-[160px] flex-1 p-4 rounded-xl ${
                  concerning
                    ? "bg-red-50/60 border border-red-200/30"
                    : "bg-slate-50/50"
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="font-bold text-sm text-[#0F172A]">{screening.instrument}</h4>
                    {screening.date && (
                      <p className="text-[10px] text-[#64748B] uppercase">{screening.date}</p>
                    )}
                  </div>
                  <span className={`text-2xl font-black ${concerning ? "text-[#DC2626]" : "text-[#0F172A]"}`}>
                    {screening.score}
                  </span>
                </div>

                {/* Mini progress bar */}
                <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.4, delay: i * 0.1 }}
                    className={`h-full rounded-full ${concerning ? "bg-[#DC2626]" : "bg-[#0D9488]"}`}
                  />
                </div>

                {screening.interpretation && (
                  <p className={`text-[10px] mt-2 font-bold uppercase ${
                    concerning ? "text-[#DC2626]" : "text-[#64748B]"
                  }`}>
                    {screening.interpretation}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Create SocialHistoryCard.tsx**

Create `frontend/src/components/review/SocialHistoryCard.tsx`:

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { SocialHistory } from "../../types/referral";

interface SocialHistoryCardProps {
  socialHistory?: SocialHistory;
}

export function SocialHistoryCard({ socialHistory }: SocialHistoryCardProps) {
  if (!socialHistory) return null;

  const entries: { label: string; value: string; isSafety?: boolean }[] = [];

  if (socialHistory.smoking_status) entries.push({ label: "Smoking", value: socialHistory.smoking_status });
  if (socialHistory.alcohol_use) entries.push({ label: "Alcohol", value: socialHistory.alcohol_use });
  if (socialHistory.substance_use) entries.push({ label: "Substance Use", value: socialHistory.substance_use });
  if (socialHistory.employment) entries.push({ label: "Employment", value: socialHistory.employment });
  if (socialHistory.education) entries.push({ label: "Education", value: socialHistory.education });
  if (socialHistory.housing) entries.push({ label: "Housing", value: socialHistory.housing });
  if (socialHistory.other) entries.push({ label: "Other", value: socialHistory.other });
  if (socialHistory.safety_concerns) {
    entries.push({ label: "Safety", value: socialHistory.safety_concerns, isSafety: true });
  }

  if (entries.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Social History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {entries.map((entry, i) =>
            entry.isSafety ? (
              <div key={i} className="pt-3 border-t border-red-200/50">
                <div className="flex items-center gap-2 text-[#DC2626] mb-1">
                  <span className="section-label text-[#DC2626]">Safety Alert</span>
                </div>
                <p className="text-sm font-bold text-[#DC2626] uppercase tracking-tight">
                  {entry.value}
                </p>
              </div>
            ) : (
              <div key={i} className="flex justify-between text-sm">
                <span className="text-[#64748B]">{entry.label}</span>
                <span className="font-semibold text-[#0F172A]">{entry.value}</span>
              </div>
            )
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 3: Create AllergiesCard.tsx**

Create `frontend/src/components/review/AllergiesCard.tsx`:

```tsx
import { Check } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { Allergies } from "../../types/referral";

interface AllergiesCardProps {
  allergies?: Allergies;
}

export function AllergiesCard({ allergies }: AllergiesCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Allergies</CardTitle>
      </CardHeader>
      <CardContent>
        {allergies?.no_known_allergies ? (
          <div className="flex items-center gap-2 bg-[#0D9488]/10 text-[#0D9488] px-4 py-2 rounded-xl text-sm font-bold">
            <Check className="h-4 w-4" />
            No known allergies
          </div>
        ) : allergies?.known_allergies && allergies.known_allergies.length > 0 ? (
          <div className="space-y-2">
            {allergies.known_allergies.map((allergy, i) => (
              <div key={i} className="text-sm">
                <span className="font-semibold text-[#0F172A]">{allergy.substance}</span>
                {allergy.reaction && (
                  <span className="text-[#64748B] ml-2">— {allergy.reaction}</span>
                )}
                {allergy.severity && (
                  <span className="ml-2 text-[10px] font-bold uppercase text-[#DC2626]">
                    {allergy.severity}
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm italic text-[#64748B]">No allergy information available</p>
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 4: Create ClinicalTrialsCard.tsx**

Create `frontend/src/components/review/ClinicalTrialsCard.tsx`:

```tsx
import { FlaskConical, ExternalLink } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";

interface ClinicalTrialsCardProps {
  flagged: boolean;
  signals: unknown;
}

export function ClinicalTrialsCard({ flagged, signals }: ClinicalTrialsCardProps) {
  if (!flagged) return null;

  // signals can be an object with various shapes — render what we can
  const signalData = signals as Record<string, unknown> | null;
  const signalList = signalData
    ? Object.entries(signalData).filter(([, v]) => v != null)
    : [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Clinical Trial Signals</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="p-4 bg-[#0D9488]/5 border border-[#0D9488]/20 rounded-xl mb-4">
          <div className="flex items-center gap-2 text-[#0D9488] mb-1">
            <FlaskConical className="h-4 w-4" />
            <span className="text-[10px] font-bold uppercase">Potential Eligibility</span>
          </div>
          {signalList.length > 0 ? (
            <div className="space-y-1 mt-2">
              {signalList.map(([key, value], i) => (
                <p key={i} className="text-xs text-[#0F172A]">
                  <span className="font-semibold">{key}:</span> {String(value)}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-xs font-semibold text-[#0F172A]">Patient may qualify for clinical trials</p>
          )}
        </div>
        <a
          href="https://clinicaltrials.gov"
          target="_blank"
          rel="noopener noreferrer"
          className="text-[11px] text-[#0D9488] hover:underline font-bold uppercase tracking-wider flex items-center gap-1"
        >
          Search ClinicalTrials.gov
          <ExternalLink className="h-3 w-3" />
        </a>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 5: Create HistoricalContext.tsx**

Create `frontend/src/components/review/HistoricalContext.tsx`:

```tsx
import { useState } from "react";
import { ChevronDown, ChevronUp, History } from "lucide-react";
import type { SignificantHistory, Procedure } from "../../types/referral";

interface HistoricalContextProps {
  significantHistory?: SignificantHistory[];
  procedures?: Procedure[];
}

export function HistoricalContext({ significantHistory, procedures }: HistoricalContextProps) {
  const [isOpen, setIsOpen] = useState(false);

  const historyCount = significantHistory?.length ?? 0;
  const procedureCount = procedures?.length ?? 0;

  if (historyCount === 0 && procedureCount === 0) return null;

  return (
    <div className="glass rounded-xl overflow-hidden">
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-full flex justify-between items-center py-3 px-6 opacity-70 hover:opacity-100 transition-opacity cursor-pointer"
      >
        <div className="flex items-center gap-3">
          <History className="h-4 w-4 text-[#64748B]" />
          <span className="section-label">
            Historical Context — {historyCount} resolved conditions, {procedureCount} procedures
          </span>
        </div>
        {isOpen ? (
          <ChevronUp className="h-4 w-4 text-[#64748B]" />
        ) : (
          <ChevronDown className="h-4 w-4 text-[#64748B]" />
        )}
      </button>

      {isOpen && (
        <div className="px-6 pb-4 space-y-4 text-sm text-[#64748B]">
          {historyCount > 0 && (
            <div>
              <h4 className="section-label mb-2">Resolved Conditions</h4>
              <div className="space-y-1">
                {significantHistory!.map((item, i) => (
                  <div key={i} className="flex justify-between">
                    <span>{item.diagnosis}</span>
                    <span className="text-xs">
                      {item.onset_date && `${item.onset_date}`}
                      {item.resolution_date && ` — ${item.resolution_date}`}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {procedureCount > 0 && (
            <div>
              <h4 className="section-label mb-2">Procedures & Surgeries</h4>
              <div className="space-y-1">
                {procedures!.map((proc, i) => (
                  <div key={i} className="flex justify-between">
                    <span>{proc.description}</span>
                    {proc.date && <span className="text-xs">{proc.date}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 6: Verify build**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/review/ScreeningScores.tsx frontend/src/components/review/SocialHistoryCard.tsx frontend/src/components/review/AllergiesCard.tsx frontend/src/components/review/ClinicalTrialsCard.tsx frontend/src/components/review/HistoricalContext.tsx
git commit -m "feat: screening scores, social history, allergies, clinical trials, and historical context cards"
```

---

### Task 11: Rewrite ReviewWorkspace — Full New Layout

**Files:**
- Rewrite: `frontend/src/components/review/ReviewWorkspace.tsx`

- [ ] **Step 1: Rewrite ReviewWorkspace.tsx with new layout**

Replace the entire contents of `frontend/src/components/review/ReviewWorkspace.tsx` with:

```tsx
import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { getReferral, saveCorrection } from "../../api/client";
import type { ReferralDetail } from "../../types/referral";
import { ReviewSkeleton } from "../shared/LoadingSkeleton";
import { PatientHeader } from "./PatientHeader";
import { AlertStrip } from "./AlertStrip";
import { ActionChips } from "./ActionChips";
import { AISummaryPanel } from "./AISummaryPanel";
import { VitalsCard } from "./VitalsCard";
import { MedicationsCard } from "./MedicationsCard";
import { ConditionsCard } from "./ConditionsCard";
import { LabsCard } from "./LabsCard";
import { ScreeningScores } from "./ScreeningScores";
import { SocialHistoryCard } from "./SocialHistoryCard";
import { AllergiesCard } from "./AllergiesCard";
import { ClinicalTrialsCard } from "./ClinicalTrialsCard";
import { HistoricalContext } from "./HistoricalContext";

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.05, duration: 0.3, ease: [0.4, 0, 0.2, 1] },
  }),
};

export function ReviewWorkspace() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ReferralDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getReferral(id)
      .then((d) => {
        setData(d);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleCorrection = useCallback(
    async (fieldPath: string, oldValue: string, newValue: string) => {
      if (!id) return;
      try {
        await saveCorrection(id, {
          field_path: fieldPath,
          original_value: oldValue,
          corrected_value: newValue,
          correction_type: "value_change",
        });
      } catch (err) {
        console.error("Failed to save correction:", err);
      }
    },
    [id]
  );

  const handleGeneratePdf = useCallback(() => {
    // TODO: Wire to GET /api/referrals/{id}/summary-pdf when available
    alert("PDF generation not yet available. Endpoint: GET /api/referrals/{id}/summary-pdf");
  }, []);

  const handleFinalize = useCallback(() => {
    // TODO: Wire to status update endpoint
    alert("Finalize review functionality coming soon.");
  }, []);

  if (loading) {
    return (
      <div className="h-full pt-4">
        <ReviewSkeleton />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-sm text-red-600 mb-2">{error ?? "Referral not found"}</p>
          <button
            onClick={() => navigate("/queue")}
            className="text-sm text-[#0D9488] hover:underline"
          >
            Back to queue
          </button>
        </div>
      </div>
    );
  }

  const ed = data.extracted_data;
  const cd = ed.clinical_data;
  const triage = data.triage;

  let sectionIndex = 0;

  return (
    <div className="flex flex-col min-h-full">
      {/* Patient Header — sticky */}
      <PatientHeader
        patient={ed.patient}
        referral={ed.referral}
        referringProvider={ed.referring_provider}
        status={data.status}
        urgency={triage.urgency}
        confidence={triage.confidence}
        createdAt={data.created_at}
        onGeneratePdf={handleGeneratePdf}
        onFinalize={handleFinalize}
      />

      {/* Alert strip — conditional */}
      <AlertStrip redFlags={triage.red_flags} missingInfo={triage.missing_info} />

      {/* Action chips — conditional */}
      <ActionChips items={triage.action_items} />

      {/* Main layout: AI Panel + Clinical Data */}
      <div className="flex flex-1 mx-6 mb-6 overflow-hidden">
        <AISummaryPanel
          summaryNarrative={data.summary_narrative}
          triageReasoning={triage.reasoning}
          referralReason={ed.referral?.reason}
          oneLineSummary={data.one_line_summary}
        />

        {/* Right content area — scrollable */}
        <div className="flex-1 overflow-y-auto pl-4 space-y-6 pb-8">
          {/* Section 1: Vitals + Medications */}
          <motion.div
            className="flex gap-6"
            custom={sectionIndex++}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
          >
            <div className="w-[55%]">
              <VitalsCard vitals={cd?.recent_vitals} />
            </div>
            <div className="w-[45%]">
              <MedicationsCard medications={cd?.medications} />
            </div>
          </motion.div>

          {/* Section 2: Conditions + Labs */}
          <motion.div
            className="flex gap-6"
            custom={sectionIndex++}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
          >
            <div className="w-[50%]">
              <ConditionsCard
                conditions={cd?.problem_list?.active ?? []}
                receivingSpecialty={ed.referral?.receiving_specialty}
              />
            </div>
            <div className="w-[50%]">
              <LabsCard labs={cd?.recent_labs} />
            </div>
          </motion.div>

          {/* Section 3: Screening Scores */}
          <motion.div
            custom={sectionIndex++}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
          >
            <ScreeningScores screenings={cd?.screenings} />
          </motion.div>

          {/* Section 4: Social + Allergies + Trials */}
          <motion.div
            className="grid grid-cols-10 gap-6"
            custom={sectionIndex++}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
          >
            <div className="col-span-4">
              <SocialHistoryCard socialHistory={cd?.social_history} />
            </div>
            <div className="col-span-3">
              <AllergiesCard allergies={cd?.allergies} />
            </div>
            <div className="col-span-3">
              <ClinicalTrialsCard
                flagged={data.clinical_trial_flagged}
                signals={data.clinical_trial_signals}
              />
            </div>
          </motion.div>

          {/* Section 5: Historical Context */}
          <motion.div
            custom={sectionIndex++}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
          >
            <HistoricalContext
              significantHistory={cd?.problem_list?.significant_history}
              procedures={cd?.procedures_and_surgeries}
            />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/review/ReviewWorkspace.tsx
git commit -m "feat: rewrite ReviewWorkspace with sliding AI panel layout and staggered card animations"
```

---

### Task 12: Update EditableField with Blue Left Border

**Files:**
- Modify: `frontend/src/components/shared/EditableField.tsx`

- [ ] **Step 1: Read current EditableField.tsx and add blue left-border for edited state**

The EditableField component needs a visual indicator when a field has been modified. Add a `wasEdited` state that shows a blue left-border after a successful save. Find the root wrapper `<div>` or `<span>` of the component and add a conditional `border-l-4 border-[#2563EB] pl-2` class when the field has been edited.

Look at the current file, find where the "Saved" feedback is shown (the existing save confirmation), and ensure the blue border persists after saving (not just a momentary flash).

- [ ] **Step 2: Verify build and commit**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit && git add frontend/src/components/shared/EditableField.tsx && git commit -m "feat: blue left-border indicator on edited fields"
```

---

### Task 13: Update Queue and Upload Styling for New Theme

**Files:**
- Modify: `frontend/src/components/queue/ReferralQueue.tsx`
- Modify: `frontend/src/components/upload/UploadPanel.tsx`

- [ ] **Step 1: Update ReferralQueue for glass theme**

Read `frontend/src/components/queue/ReferralQueue.tsx`. Apply the new design system:
- Replace `bg-white` with the glass utility class where appropriate
- Replace `border-stone-*` with `border-white/40`
- Replace `bg-stone-50`, `bg-stone-100` hover states with the glass class equivalents
- Replace any `navigate("/")` back-navigation calls with `navigate("/queue")`
- Keep all functional logic exactly the same — only change CSS classes

- [ ] **Step 2: Update UploadPanel for glass theme**

Read `frontend/src/components/upload/UploadPanel.tsx`. Apply the same glass theme adjustments:
- Replace solid backgrounds with frosted glass
- Update border and hover state colors
- Keep all upload logic untouched

- [ ] **Step 3: Verify build and commit**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit && git add frontend/src/components/queue/ReferralQueue.tsx frontend/src/components/upload/UploadPanel.tsx && git commit -m "feat: apply frosted glass theme to Queue and Upload pages"
```

---

### Task 14: Build Landing Page

**Files:**
- Rewrite: `frontend/src/components/landing/LandingPage.tsx`

- [ ] **Step 1: Build the full landing page**

Replace the placeholder in `frontend/src/components/landing/LandingPage.tsx` with the full implementation:

```tsx
import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, useInView } from "framer-motion";
import { Shield, FileCheck, Sparkles, ArrowRight, CloudUpload, Brain, CheckCircle } from "lucide-react";
import { Button } from "../ui/button";

function FadeInSection({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay, ease: [0.4, 0, 0.2, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white text-[#0F172A]">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 glass border-b border-white/20 shadow-sm">
        <div className="flex justify-between items-center px-6 py-4 max-w-7xl mx-auto">
          <span className="text-xl font-bold tracking-tight text-[#0D9488]">
            Antechamber Health
          </span>
          <div className="hidden md:flex items-center gap-8">
            <a href="#how-it-works" className="text-sm font-medium text-[#64748B] hover:text-[#0D9488] transition-colors">How It Works</a>
            <a href="#features" className="text-sm font-medium text-[#64748B] hover:text-[#0D9488] transition-colors">Features</a>
            <a href="#benefits" className="text-sm font-medium text-[#64748B] hover:text-[#0D9488] transition-colors">Benefits</a>
          </div>
          <Button onClick={() => navigate("/queue")}>
            Request Demo
          </Button>
        </div>
      </nav>

      {/* Hero */}
      <header className="relative min-h-screen flex items-center pt-20 hero-gradient overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left */}
          <div className="lg:col-span-7 z-10">
            <div className="inline-flex items-center px-3 py-1 rounded-full bg-[#0D9488]/10 text-[#0D9488] text-[11px] uppercase tracking-wider font-semibold mb-6">
              <span className="mr-2 h-1.5 w-1.5 rounded-full bg-[#0D9488] pulse-dot" />
              AI-Powered Referral Triage
            </div>
            <h1 className="text-5xl lg:text-7xl font-bold text-[#0F172A] leading-[1.1] mb-6">
              Every referral, triaged in{" "}
              <span className="text-[#0D9488] italic">seconds.</span>
            </h1>
            <p className="text-lg lg:text-xl text-[#64748B] leading-relaxed mb-10 max-w-xl">
              Antechamber Health parses referral notes and connects to your Health Information Exchange.
              We give your team a complete patient picture, so you're prepared before the first appointment.
            </p>
            <div className="flex flex-wrap gap-4 mb-12">
              <Button size="lg" className="shadow-lg shadow-[#0D9488]/20" onClick={() => navigate("/queue")}>
                Request Demo
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="lg" onClick={() => {
                document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" });
              }}>
                See How It Works
              </Button>
            </div>
            <div className="flex items-center gap-6 text-[#64748B]/60 text-[11px] uppercase tracking-[0.1em] font-semibold">
              <span className="flex items-center gap-1.5"><Shield className="h-3 w-3" /> HIPAA Compliant</span>
              <span className="h-1 w-1 rounded-full bg-slate-300" />
              <span>BAA Available</span>
              <span className="h-1 w-1 rounded-full bg-slate-300" />
              <span>SOC 2 In Progress</span>
            </div>
          </div>

          {/* Right — floating mockup */}
          <div className="lg:col-span-5 relative">
            <div className="floating glass rounded-xl overflow-hidden shadow-2xl border border-white/40">
              <div className="bg-slate-50 px-4 py-2 flex items-center gap-2 border-b border-slate-200/50">
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-400/40" />
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-400/40" />
                  <div className="w-2.5 h-2.5 rounded-full bg-green-400/40" />
                </div>
                <div className="mx-auto bg-slate-100 px-4 py-1 rounded text-[10px] text-[#64748B]/50 font-mono">
                  app.antechamber.health/review
                </div>
              </div>
              <div className="bg-gradient-to-br from-[#FFF8F0] to-[#F5F0FF] p-6 min-h-[300px] flex items-center justify-center">
                <div className="space-y-3 w-full max-w-sm">
                  <div className="glass p-3 rounded-lg shadow-sm flex justify-between items-center">
                    <span className="font-bold text-sm">Patient Review</span>
                    <span className="px-2 py-0.5 bg-[#0D9488] text-white text-[10px] rounded-full font-bold">ROUTINE</span>
                  </div>
                  <div className="glass p-3 rounded-lg shadow-sm flex justify-between items-center">
                    <span className="font-bold text-sm">AI Summary</span>
                    <Sparkles className="h-4 w-4 text-[#0D9488]" />
                  </div>
                  <div className="glass p-3 rounded-lg shadow-sm flex justify-between items-center">
                    <span className="font-bold text-sm">Clinical Data</span>
                    <span className="text-xs text-[#64748B]">12 sections</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute -z-10 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[140%] h-[140%] bg-[#0D9488]/5 blur-[100px] rounded-full" />
          </div>
        </div>
      </header>

      {/* How It Works */}
      <section id="how-it-works" className="py-24 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Precision Workflow</h2>
            <div className="h-1 w-12 bg-[#0D9488] mx-auto rounded-full" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { icon: CloudUpload, step: "01", title: "Upload or receive", desc: "Securely ingest PDFs, faxes, or EMR exports. Our AI handles the mess so your team doesn't have to." },
              { icon: Brain, step: "02", title: "AI extracts & triages", desc: "Proprietary LLMs extract comorbidities, ICD-10 codes, and clinical urgency based on your specific protocols." },
              { icon: CheckCircle, step: "03", title: "Review and act", desc: "Approve the triage, schedule the patient, or request missing data with a single click. Efficiency redefined." },
            ].map((item, i) => (
              <FadeInSection key={i} delay={i * 0.15}>
                <div className="glass p-8 rounded-xl relative group hover:-translate-y-2 transition-transform duration-300">
                  <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#0D9488] to-transparent rounded-t-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                  <div className="w-12 h-12 rounded-lg bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488] mb-6">
                    <item.icon className="h-6 w-6" />
                  </div>
                  <div className="text-[11px] uppercase tracking-widest text-[#0D9488]/50 mb-2 font-semibold">Step {item.step}</div>
                  <h3 className="text-xl font-bold mb-3">{item.title}</h3>
                  <p className="text-[#64748B] text-sm leading-relaxed">{item.desc}</p>
                </div>
              </FadeInSection>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Showcase */}
      <section id="features" className="py-24 bg-slate-50/50 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="max-w-2xl mb-16">
            <h2 className="text-4xl font-bold mb-6">Built for the Clinical Workspace</h2>
            <p className="text-[#64748B] text-lg">Stop fighting your EMR. Start reviewing referrals in a workspace designed for speed and clarity.</p>
          </div>
          <FadeInSection>
            <div className="relative glass rounded-xl p-4 shadow-2xl border border-white/40">
              <div className="bg-gradient-to-br from-[#FFF8F0] to-[#F5F0FF] rounded-lg p-12 min-h-[400px] flex items-center justify-center">
                <div className="grid grid-cols-3 gap-6 w-full max-w-3xl">
                  <div className="glass p-4 rounded-lg shadow-sm col-span-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="h-4 w-4 text-[#0D9488]" />
                      <span className="text-[10px] font-bold uppercase text-[#0D9488]">AI Summary</span>
                    </div>
                    <div className="space-y-2">
                      <div className="h-2 bg-slate-200 rounded w-full" />
                      <div className="h-2 bg-slate-200 rounded w-3/4" />
                      <div className="h-2 bg-slate-200 rounded w-5/6" />
                    </div>
                  </div>
                  <div className="glass p-4 rounded-lg shadow-sm col-span-2">
                    <div className="flex items-center gap-2 mb-3">
                      <FileCheck className="h-4 w-4 text-[#64748B]" />
                      <span className="text-[10px] font-bold uppercase text-[#64748B]">Clinical Data</span>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-slate-50 p-2 rounded"><div className="h-2 bg-slate-200 rounded w-2/3" /></div>
                      <div className="bg-slate-50 p-2 rounded"><div className="h-2 bg-slate-200 rounded w-1/2" /></div>
                      <div className="bg-red-50 p-2 rounded border-l-2 border-red-300"><div className="h-2 bg-red-200 rounded w-3/4" /></div>
                      <div className="bg-slate-50 p-2 rounded"><div className="h-2 bg-slate-200 rounded w-4/5" /></div>
                    </div>
                  </div>
                </div>
              </div>
              {/* Floating annotations */}
              <div className="absolute top-[20%] right-[8%] glass px-4 py-3 rounded-lg shadow-xl border-l-4 border-[#0D9488]">
                <div className="flex items-center gap-3">
                  <Sparkles className="h-4 w-4 text-[#0D9488]" />
                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-[#0D9488] font-bold">AI Summary</p>
                    <p className="text-sm font-semibold">Instant clinical context</p>
                  </div>
                </div>
              </div>
              <div className="absolute bottom-[25%] left-[5%] glass px-4 py-3 rounded-lg shadow-xl border-l-4 border-[#DC2626]">
                <div className="flex items-center gap-3">
                  <Shield className="h-4 w-4 text-[#DC2626]" />
                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-[#DC2626] font-bold">Urgent Triage</p>
                    <p className="text-sm font-semibold">Flagged for immediate review</p>
                  </div>
                </div>
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Benefits */}
      <section id="benefits" className="py-24">
        <div className="max-w-7xl mx-auto px-6 space-y-32">
          {[
            {
              title: "Built for referral coordinators, not clinicians.",
              desc: "Most tools are built for the physician's eye. We built Antechamber for the operations team that keeps the clinic running. Large buttons, clear status indicators, and bulk actions.",
              tags: ["Bulk Intake", "Priority Sorter", "Fax Ingestion"],
              reverse: false,
            },
            {
              title: "Every format, one workflow.",
              desc: "Whether it's a blurry handwritten fax, a multi-page PDF export, or a direct HL7 message, Antechamber normalizes the data into a single, clean view for your intake team.",
              tags: ["PDF", "Fax", "HL7", "CDA"],
              reverse: true,
            },
            {
              title: "Your data becomes your advantage.",
              desc: "Every correction your team makes teaches the AI. Over time, your triage becomes perfectly aligned with your clinic's unique clinical guidelines and scheduling logic.",
              tags: ["Feedback Loop", "Adaptive Learning", "Custom Protocols"],
              reverse: false,
            },
          ].map((row, i) => (
            <FadeInSection key={i}>
              <div className={`grid grid-cols-1 lg:grid-cols-2 gap-16 items-center ${row.reverse ? "direction-rtl" : ""}`}>
                <div className={row.reverse ? "order-2 lg:order-2" : ""}>
                  <h3 className="text-3xl font-bold mb-6">{row.title}</h3>
                  <p className="text-[#64748B] leading-relaxed mb-8">{row.desc}</p>
                  <div className="flex flex-wrap gap-3">
                    {row.tags.map((tag) => (
                      <span key={tag} className="px-4 py-2 glass rounded-lg text-xs font-semibold text-[#0D9488]">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div className={`glass p-8 rounded-xl bg-gradient-to-br from-slate-50 to-white min-h-[250px] flex items-center justify-center ${row.reverse ? "order-1 lg:order-1" : ""}`}>
                  <div className="w-full max-w-sm space-y-3">
                    <div className="h-3 bg-[#0D9488]/10 rounded-full overflow-hidden">
                      <div className="h-full bg-[#0D9488] rounded-full" style={{ width: `${65 + i * 12}%` }} />
                    </div>
                    <p className="text-xs text-[#64748B] italic text-center">
                      {i === 0 && "85% faster triage processing"}
                      {i === 1 && "All formats, unified view"}
                      {i === 2 && "98% extraction accuracy"}
                    </p>
                  </div>
                </div>
              </div>
            </FadeInSection>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] h-[80%] bg-[#0D9488]/5 blur-[120px] rounded-full" />
        <div className="max-w-5xl mx-auto glass p-16 rounded-[2rem] text-center relative z-10">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to transform your referral workflow?
          </h2>
          <p className="text-[#64748B] text-lg max-w-2xl mx-auto mb-12">
            Join modern clinical teams reducing triage time by 85% and improving patient access.
          </p>
          <div className="flex flex-col sm:flex-row justify-center items-center gap-6">
            <Button size="lg" className="shadow-xl shadow-[#0D9488]/30 text-lg px-10 py-5 h-auto" onClick={() => navigate("/queue")}>
              Request Demo
            </Button>
            <Button variant="outline" size="lg" className="text-lg px-10 py-5 h-auto">
              Contact Sales
            </Button>
          </div>
          <p className="mt-6 text-sm text-[#64748B]">Free pilot for early partners</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-50/50 w-full py-12 px-6 border-t border-[#0D9488]/5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-7xl mx-auto">
          <div>
            <div className="text-lg font-bold text-[#0F172A] mb-4">Antechamber Health</div>
            <p className="text-xs tracking-wide uppercase text-[#64748B]/70 max-w-xs leading-loose">
              &copy; 2025 Antechamber Health. Precision Triage for Modern Clinicians.
            </p>
          </div>
          <div className="flex flex-wrap gap-x-12 gap-y-6 md:justify-end">
            {["About", "Privacy", "Terms", "Contact"].map((link) => (
              <a key={link} href="#" className="text-xs tracking-wide uppercase text-[#64748B]/70 hover:text-[#0D9488] transition-colors">
                {link}
              </a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/landing/LandingPage.tsx
git commit -m "feat: full marketing landing page with hero, how-it-works, features, benefits, CTA"
```

---

### Task 15: Clean Up Deleted Components

**Files:**
- Delete: `frontend/src/components/review/FindingsPanel.tsx`
- Delete: `frontend/src/components/review/ScreeningCard.tsx`
- Delete: `frontend/src/components/review/ClinicalSections.tsx`

- [ ] **Step 1: Delete old components**

These are no longer imported by the new ReviewWorkspace. Remove them:

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage"
rm frontend/src/components/review/FindingsPanel.tsx
rm frontend/src/components/review/ScreeningCard.tsx
rm frontend/src/components/review/ClinicalSections.tsx
```

- [ ] **Step 2: Verify no dangling imports**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit
```

Expected: No errors. If there are errors, fix any remaining imports.

- [ ] **Step 3: Commit**

```bash
git add -u frontend/src/components/review/
git commit -m "chore: remove replaced components (FindingsPanel, ScreeningCard, ClinicalSections)"
```

---

### Task 16: Verify Full Build and Test with Dev Server

- [ ] **Step 1: Full TypeScript check**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 2: Vite build**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 3: Start dev server and verify pages load**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage/frontend"
npm run dev
```

Then verify:
- `http://localhost:5173/` — Landing page renders with hero, gradient background, nav
- `http://localhost:5173/queue` — Queue page renders with glass theme
- `http://localhost:5173/upload` — Upload page renders with glass theme
- (If backend running) `http://localhost:5173/review/<id>` — Review page renders with frosted glass cards, AI panel

- [ ] **Step 4: Final commit**

```bash
cd "/Users/vayun/Desktop/Rare Disease/Referral Triage"
git add -A
git commit -m "feat: UI redesign complete — frosted glass dashboard, landing page, shadcn/ui components"
```
