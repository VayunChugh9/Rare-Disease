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
      <nav className="fixed top-0 w-full z-50 glass border-b border-white/20 shadow-sm">
        <div className="flex items-center justify-between px-6 py-3 max-w-[1440px] mx-auto">
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
      <main className={`flex-1 pt-[60px] ${isReview ? "" : "overflow-y-auto"}`}>
        <Outlet />
      </main>
    </div>
  );
}
