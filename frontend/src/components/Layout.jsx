import { NavLink, useNavigate } from "react-router-dom";
import { useState } from "react";
import {
  LayoutDashboard,
  UploadCloud,
  ScanLine,
  FolderOpen,
  Stamp,
  Settings,
  LogOut,
  ChevronRight,
} from "lucide-react";
import SettingsModal from "./SettingsModal.jsx";
import { useAuth } from "../context/AuthContext.jsx";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/upload", label: "Upload", icon: UploadCloud, end: true },
  { to: "/status", label: "Processing", icon: ScanLine },
  { to: "/claims", label: "Case Register", icon: FolderOpen },
];

export default function Layout({ children }) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const initial = user?.email?.[0]?.toUpperCase() || "?";

  return (
    <div className="min-h-screen paper-texture flex">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-ink/10 bg-paper sticky top-0 h-screen overflow-y-auto scroll-thin">
        <div className="px-5 pt-7 pb-6 border-b border-ink/10">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-full bg-ink text-paper flex items-center justify-center rotate-[-6deg] shadow-sm">
              <Stamp size={18} strokeWidth={2} />
            </div>
            <div>
              <p className="font-display text-lg leading-tight text-ink">
                OCR
              </p>
              <p className="text-[10px] tracking-[0.18em] uppercase text-ink-soft font-mono">
                Review Desk
              </p>
            </div>
          </div>
        </div>

        <nav className="flex-1 pt-6 pb-4 flex flex-col gap-1 px-3">
          <p className="px-3 mb-2 text-[10px] font-mono uppercase tracking-[0.18em] text-ink-soft/50">
            Menu
          </p>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 pl-3 pr-2.5 py-2.5 tab-stub transition-all duration-200 ${
                  isActive
                    ? "bg-ink text-paper shadow-sm"
                    : "text-ink-soft hover:bg-folder/20 hover:text-ink hover:translate-x-0.5"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={`flex items-center justify-center w-7 h-7 shrink-0 transition-colors ${
                      isActive
                        ? "text-paper"
                        : "text-ink-soft/70 group-hover:text-folder-dark"
                    }`}
                  >
                    <item.icon size={17} strokeWidth={2} />
                  </span>
                  <span className="text-sm font-medium flex-1">
                    {item.label}
                  </span>
                  <ChevronRight
                    size={13}
                    className={`shrink-0 transition-opacity ${
                      isActive
                        ? "opacity-70"
                        : "opacity-0 group-hover:opacity-30"
                    }`}
                  />
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-ink/10 space-y-3">
          {user && (
            <div className="flex items-center gap-2.5 min-w-0 px-1">
              <div className="w-7 h-7 rounded-full bg-folder/30 text-ink-soft flex items-center justify-center text-[11px] font-mono font-semibold shrink-0">
                {initial}
              </div>
              <p
                className="text-xs text-ink-soft font-mono truncate"
                title={user.email}
              >
                {user.email}
              </p>
            </div>
          )}
          <div className="flex flex-col gap-0.5">
            <button
              onClick={() => setSettingsOpen(true)}
              className="flex items-center gap-2 text-xs text-ink-soft hover:text-ink hover:bg-ink/5 transition-colors font-mono px-2 py-1.5 -mx-2"
            >
              <Settings size={14} />
              API endpoint
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 text-xs text-ink-soft hover:text-stamp-red hover:bg-stamp-red-soft/60 transition-colors font-mono px-2 py-1.5 -mx-2"
            >
              <LogOut size={14} />
              Log out
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 inset-x-0 z-30 bg-ink text-paper flex items-center justify-between px-4 py-3 shadow-md">
        <div className="flex items-center gap-2">
          <Stamp size={18} />
          <span className="font-display text-base">Claim OCR</span>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setSettingsOpen(true)}>
            <Settings size={18} />
          </button>
          <button onClick={handleLogout}>
            <LogOut size={18} />
          </button>
        </div>
      </div>
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-30 bg-ink text-paper flex justify-around py-2 shadow-[0_-2px_10px_rgba(0,0,0,0.15)]">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `relative flex flex-col items-center gap-0.5 px-3 py-1 text-[10px] transition-colors ${
                isActive ? "text-folder" : "text-paper/60"
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute -top-2 w-1 h-1 rounded-full bg-folder" />
                )}
                <item.icon size={17} />
                {item.label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <main className="flex-1 min-w-0 pt-14 pb-16 md:pt-0 md:pb-0">
        {children}
      </main>

      {settingsOpen && <SettingsModal onClose={() => setSettingsOpen(false)} />}
    </div>
  );
}
