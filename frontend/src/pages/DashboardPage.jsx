import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Loader2,
  FileWarning,
  FolderOpen,
  FileStack,
  CheckCircle2,
  ScanLine,
  XCircle,
  ArrowUpRight,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
  Receipt,
  ShieldCheck,
  ClipboardList,
  IdCard,
  Landmark,
  FileCheck2,
  HelpCircle,
  FileText,
} from "lucide-react";
import { getDashboardStats } from "../api/client.js";
import StatusBadge from "../components/StatusBadge.jsx";
import PageContainer from "../components/PageContainer.jsx";

// Full literal class strings on purpose (not template-interpolated) so the
// Tailwind scanner can pick them up statically.
const STAT_CARDS = [
  {
    key: "uploaded",
    label: "Uploaded",
    icon: FolderOpen,
    chip: "bg-ink/10 text-ink-soft",
    bar: "bg-ink-soft",
  },
  {
    key: "processing",
    label: "Processing",
    icon: ScanLine,
    chip: "bg-amber-soft text-amber",
    bar: "bg-amber",
  },
  {
    key: "completed",
    label: "Completed",
    icon: CheckCircle2,
    chip: "bg-verify-green-soft text-verify-green",
    bar: "bg-verify-green",
  },
  {
    key: "failed",
    label: "Failed",
    icon: XCircle,
    chip: "bg-stamp-red-soft text-stamp-red",
    bar: "bg-stamp-red",
  },
];

const DOC_TYPE_ICONS = [
  [["invoice", "bill"], Receipt],
  [["insurance"], ShieldCheck],
  [["discharge", "summary", "report", "prescription"], ClipboardList],
  [["id", "card", "aadhaar", "pan"], IdCard],
  [["bank", "statement"], Landmark],
  [["certificate"], FileCheck2],
  [["unknown"], HelpCircle],
];

function iconForDocType(type) {
  const t = (type || "").toLowerCase();
  for (const [keywords, Icon] of DOC_TYPE_ICONS) {
    if (keywords.some((k) => t.includes(k))) return Icon;
  }
  return FileText;
}

function formatDayLabel(dateStr) {
  const d = new Date(`${dateStr}T00:00:00`);
  return d.toLocaleDateString(undefined, { weekday: "short" });
}

function isToday(dateStr) {
  const today = new Date();
  const d = new Date(`${dateStr}T00:00:00`);
  return d.toDateString() === today.toDateString();
}

const CHART_HEIGHT = 120; // px - bar track height, kept as a fixed pixel
// value so nested percentage-height bars resolve reliably (a % height only
// works against a definite-height ancestor; a flex column with no explicit
// height gives every bar 0px, which made the chart render empty before).

function DashboardSkeleton() {
  return (
    <div className="animate-pulse space-y-8">
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 md:gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="border border-ink/10 bg-white p-4 h-24 min-w-0" />
        ))}
      </div>
      <div className="grid lg:grid-cols-2 gap-5 md:gap-6">
        <div className="border border-ink/10 bg-white h-64" />
        <div className="border border-ink/10 bg-white h-64" />
      </div>
      <div className="border border-ink/10 bg-white h-56" />
    </div>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const load = async (silent = false) => {
    if (silent) setRefreshing(true);
    else setLoading(true);
    setError("");
    try {
      const res = await getDashboardStats();
      setStats(res.data);
    } catch (err) {
      setError(err?.message || "Could not reach the backend.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const statusCounts = stats?.status_counts || {};
  const totalClaims = stats?.total_claims ?? 0;
  const totalDocuments = stats?.total_documents ?? 0;
  const documentsByType = stats?.documents_by_type || {};
  const trend = stats?.claims_last_7_days || [];
  const maxTrend = Math.max(1, ...trend.map((d) => d.count));
  const recentClaims = stats?.recent_claims || [];

  const completedCount = statusCounts.completed ?? 0;
  const failedCount = statusCounts.failed ?? 0;
  const completionRate = totalClaims
    ? Math.round((completedCount / totalClaims) * 100)
    : 0;

  const sortedDocTypes = useMemo(
    () => Object.entries(documentsByType).sort((a, b) => b[1] - a[1]),
    [documentsByType]
  );

  return (
    <PageContainer variant="full">
      <header className="mb-5 md:mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl md:text-4xl text-ink leading-tight">
            Dashboard
          </h1>
          {/* <p className="text-ink-soft mt-2 text-sm max-w-lg">
            {totalClaims > 0 ? (
              <>
                <span className="text-ink font-medium">{totalClaims}</span>{" "}
                claims on file,{" "}
                <span className="text-verify-green font-medium">
                  {completionRate}%
                </span>{" "}
                completed.
                {failedCount > 0 && (
                  <>
                    {" "}
                    <button
                      onClick={() => navigate("/claims")}
                      className="text-stamp-red font-medium underline decoration-stamp-red/40 underline-offset-2 hover:decoration-stamp-red"
                    >
                      {failedCount} need{failedCount === 1 ? "s" : ""} review.
                    </button>
                  </>
                )}
              </>
            ) : (
              "A snapshot of every claim on file — status, volume, and what still needs attention."
            )}
          </p> */}
        </div>
        <button
          onClick={() => load(true)}
          disabled={loading || refreshing}
          className="flex items-center gap-1.5 text-xs font-mono text-ink-soft hover:text-ink disabled:opacity-50 shrink-0"
        >
          <RefreshCw size={13} className={refreshing ? "animate-spin" : ""} />
          refresh
        </button>
      </header>

      {loading && <DashboardSkeleton />}

      {error && !loading && (
        <div className="flex items-center gap-2 bg-stamp-red-soft border border-stamp-red/30 text-stamp-red px-4 py-3 text-sm">
          <FileWarning size={16} />
          {error}
        </div>
      )}

      {stats && !loading && !error && (
        <div className="space-y-8">
          {/* Top stat cards */}
          <div>
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 md:gap-4">
              <div className="relative border border-ink/15 bg-white p-4 overflow-hidden min-w-0">
                <span className="absolute left-0 top-0 bottom-0 w-1 bg-ink" />
                <div className="flex items-center gap-2 mb-3">
                  <span className="flex items-center justify-center w-6 h-6 bg-ink/10 text-ink shrink-0">
                    <LayoutDashboard size={13} />
                  </span>
                  <span className="text-[10px] font-mono uppercase tracking-wide text-ink-soft truncate">
                    Total claims
                  </span>
                </div>
                <p className="font-display text-2xl text-ink">
                  {totalClaims}
                </p>
              </div>
              {STAT_CARDS.map(({ key, label, icon: Icon, chip, bar }) => {
                const count = statusCounts[key] ?? 0;
                const pct = totalClaims
                  ? Math.round((count / totalClaims) * 100)
                  : 0;
                return (
                  <div
                    key={key}
                    className="relative border border-ink/15 bg-white p-4 overflow-hidden min-w-0"
                  >
                    <span className={`absolute left-0 top-0 bottom-0 w-1 ${bar}`} />
                    <div className="flex items-center gap-2 mb-3">
                      <span
                        className={`flex items-center justify-center w-6 h-6 shrink-0 ${chip}`}
                      >
                        <Icon size={13} />
                      </span>
                      <span className="text-[10px] font-mono uppercase tracking-wide text-ink-soft truncate">
                        {label}
                      </span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <p className="font-display text-2xl text-ink">
                        {count}
                      </p>
                      {totalClaims > 0 && (
                        <span className="text-[10px] font-mono text-ink-soft">
                          {pct}%
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Segmented status distribution bar */}
            {totalClaims > 0 && (
              <div className="mt-3 border border-ink/15 bg-white px-4 py-3">
                <div className="flex h-2 w-full overflow-hidden bg-ink/5">
                  {STAT_CARDS.map(({ key, bar }) => {
                    const count = statusCounts[key] ?? 0;
                    const pct = (count / totalClaims) * 100;
                    if (pct <= 0) return null;
                    return (
                      <div
                        key={key}
                        className={`h-full ${bar} transition-all duration-500`}
                        style={{ width: `${pct}%` }}
                        title={`${key}: ${count}`}
                      />
                    );
                  })}
                </div>
                <div className="flex flex-wrap gap-x-5 gap-y-1.5 mt-2.5">
                  {STAT_CARDS.map(({ key, label, bar }) => (
                    <span
                      key={key}
                      className="flex items-center gap-1.5 text-[11px] font-mono text-ink-soft"
                    >
                      <span className={`w-1.5 h-1.5 ${bar}`} />
                      {label} · {statusCounts[key] ?? 0}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="grid lg:grid-cols-2 gap-5 md:gap-6">
            {/* 7-day trend */}
            <div className="border border-ink/15 bg-white p-5">
              <div className="flex items-center justify-between mb-5">
                <p className="text-xs font-mono uppercase tracking-wide text-ink-soft">
                  Claims — last 7 days
                </p>
                <p className="text-xs font-mono text-ink-soft">
                  {trend.reduce((sum, d) => sum + d.count, 0)} total
                </p>
              </div>
              {trend.every((d) => d.count === 0) ? (
                <div className="flex flex-col items-center justify-center text-center h-40 text-ink-soft">
                  <ScanLine size={22} className="mb-2 text-folder-dark" />
                  <p className="text-sm">No claims filed this week.</p>
                </div>
              ) : (
                <div className="flex items-end gap-3">
                  {trend.map((d) => {
                    const barPx = Math.max(
                      2,
                      Math.round((d.count / maxTrend) * CHART_HEIGHT)
                    );
                    const today = isToday(d.date);
                    return (
                      <div
                        key={d.date}
                        className="flex-1 flex flex-col items-center gap-2 group"
                        title={`${d.count} claim${d.count === 1 ? "" : "s"}`}
                      >
                        <span
                          className={`text-[10px] font-mono ${
                            today ? "text-ink" : "text-ink-soft"
                          }`}
                        >
                          {d.count}
                        </span>
                        <div
                          className="w-full flex items-end bg-ink/5"
                          style={{ height: `${CHART_HEIGHT}px` }}
                        >
                          <div
                            className={`w-full transition-all duration-500 ${
                              today ? "bg-stamp-red" : "bg-folder-dark"
                            } group-hover:opacity-80`}
                            style={{ height: `${barPx}px` }}
                          />
                        </div>
                        <span
                          className={`text-[10px] font-mono uppercase ${
                            today ? "text-ink" : "text-ink-soft"
                          }`}
                        >
                          {today ? "Today" : formatDayLabel(d.date)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Documents by type */}
            <div className="border border-ink/15 bg-white p-5">
              <div className="flex items-center gap-2 text-ink-soft mb-5">
                <FileStack size={15} />
                <p className="text-xs font-mono uppercase tracking-wide">
                  Documents by type
                </p>
                <span className="ml-auto text-xs font-mono text-ink-soft">
                  {totalDocuments} total
                </span>
              </div>
              {sortedDocTypes.length === 0 ? (
                <div className="flex flex-col items-center justify-center text-center h-32 text-ink-soft">
                  <FileStack size={22} className="mb-2 text-folder-dark" />
                  <p className="text-sm">No documents scanned yet.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {sortedDocTypes.map(([type, count], i) => {
                    const pct = totalDocuments
                      ? Math.round((count / totalDocuments) * 100)
                      : 0;
                    const Icon = iconForDocType(type);
                    return (
                      <div key={type} className="flex items-center gap-3">
                        <span className="font-mono text-[10px] text-ink-soft/60 w-4 shrink-0">
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        <Icon size={14} className="text-folder-dark shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-ink capitalize truncate">
                              {type.replace(/_/g, " ")}
                            </span>
                            <span className="font-mono text-ink-soft shrink-0 ml-2">
                              {count}
                            </span>
                          </div>
                          <div className="h-1.5 bg-ink/10 overflow-hidden">
                            <div
                              className="h-full bg-folder-dark transition-all duration-500"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Recent claims */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-mono uppercase tracking-wide text-ink-soft">
                Recent claims
              </p>
              {recentClaims.length > 0 && (
                <button
                  onClick={() => navigate("/claims")}
                  className="flex items-center gap-1 text-xs font-mono text-ink-soft hover:text-ink"
                >
                  view all
                  <ArrowRight size={12} />
                </button>
              )}
            </div>
            {recentClaims.length === 0 ? (
              <div className="flex flex-col items-center text-center py-16 border border-dashed border-ink/20 text-ink-soft">
                <FolderOpen size={28} className="mb-3 text-folder-dark" />
                <p className="text-sm">No claims on file yet.</p>
              </div>
            ) : (
              <div className="border border-ink/15 bg-white divide-y divide-ink/10">
                {recentClaims.map((c) => {
                  const failed = (c.status || "").toLowerCase() === "failed";
                  return (
                    <div
                      key={c.claim_id}
                      onClick={() => navigate(`/claims/${c.claim_id}`)}
                      className={`grid grid-cols-2 md:grid-cols-[minmax(180px,1.25fr)_minmax(180px,1fr)_110px_140px_56px] gap-4 px-4 py-3.5 items-center text-sm cursor-pointer hover:bg-folder/10 transition-colors ${
                        failed ? "border-l-2 border-l-stamp-red" : ""
                      }`}
                    >
                      <span className="font-mono text-xs text-ink truncate col-span-2 md:col-span-1">
                        {c.claim_id}
                      </span>
                      <span className="text-ink-soft truncate">
                        {c.claim_number || c.file_no || (
                          <em className="not-italic text-ink-soft/50">—</em>
                        )}
                      </span>
                      <span className="font-mono text-xs text-ink-soft whitespace-nowrap">
                        {c.document_count ?? "—"} docs
                      </span>
                      <span className="whitespace-nowrap">
                        <StatusBadge status={c.status} />
                      </span>
                      <ArrowUpRight
                        size={14}
                        className="text-ink-soft justify-self-end"
                      />
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {failedCount > 0 && (
            <div className="flex items-center gap-2 text-xs text-ink-soft font-mono">
              <AlertTriangle size={13} className="text-stamp-red" />
              {failedCount} claim{failedCount === 1 ? "" : "s"} failed
              processing — open the Case Register to retry.
            </div>
          )}
        </div>
      )}
    </PageContainer>
  );
}
