"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileUp, LayoutDashboard, ShieldCheck } from "lucide-react";

import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/upload", label: "Upload Document", icon: FileUp }
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen max-w-[1600px] flex-col md:flex-row">
        <aside className="border-b border-white/10 bg-slate-950/70 px-5 py-4 backdrop-blur-xl md:sticky md:top-0 md:h-screen md:w-72 md:border-b-0 md:border-r">
          <div className="flex h-full flex-col gap-8">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 text-slate-950 shadow-glow">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Insurance Intelligence</p>
                <p className="text-xs text-slate-400">Document processing workspace</p>
              </div>
            </div>

            <nav className="space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm font-medium transition",
                      active
                        ? "border-cyan-400/30 bg-cyan-400/10 text-cyan-100"
                        : "border-transparent text-slate-300 hover:border-white/10 hover:bg-white/5 hover:text-white"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            <div className="mt-auto rounded-3xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-400">Workflow</p>
              <div className="mt-3 space-y-2 text-sm text-slate-300">
                <p>1. Upload PDF</p>
                <p>2. OCR callback</p>
                <p>3. Mapper output</p>
                <p>4. Viewer-ready data</p>
              </div>
            </div>
          </div>
        </aside>

        <main className="flex-1">
          <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-5 py-6 md:px-8 md:py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
