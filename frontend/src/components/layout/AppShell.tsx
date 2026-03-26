import { Outlet, NavLink, useLocation } from "react-router-dom";
import { LayoutList, Upload, Activity } from "lucide-react";

const NAV_ITEMS = [
  { to: "/", icon: LayoutList, label: "Queue" },
  { to: "/upload", icon: Upload, label: "Upload" },
];

export function AppShell() {
  const location = useLocation();
  const isReview = location.pathname.startsWith("/review/");

  return (
    <div className="flex h-screen flex-col">
      {/* Top bar */}
      <header className="flex h-12 shrink-0 items-center justify-between border-b border-stone-200 bg-white px-5">
        <div className="flex items-center gap-6">
          <NavLink to="/" className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-teal-600" />
            <span className="text-sm font-semibold tracking-tight text-slate-800">
              RefTriage
            </span>
          </NavLink>

          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-stone-100 text-slate-800"
                      : "text-slate-500 hover:text-slate-700 hover:bg-stone-50"
                  }`
                }
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="text-xs text-slate-400">
          AI-assisted referral triage
        </div>
      </header>

      {/* Main content */}
      <main className={`flex-1 overflow-hidden ${isReview ? "" : "overflow-y-auto"}`}>
        <Outlet />
      </main>
    </div>
  );
}
