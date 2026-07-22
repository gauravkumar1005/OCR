import { useEffect, useState } from "react";
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
  RefreshCw,
} from "lucide-react";
import { getDashboardStats } from "../api/client.js";
import PageContainer from "../components/PageContainer.jsx";
import StatusBadge from "../components/StatusBadge.jsx";

const STAT_CARDS = [
  { key: "uploaded", label: "Uploaded", icon: FolderOpen },
  { key: "processing", label: "Processing", icon: ScanLine },
  { key: "completed", label: "Completed", icon: CheckCircle2 },
  { key: "failed", label: "Failed", icon: XCircle },
];

function formatDayLabel(dateStr) {
  const d = new Date(`${dateStr}T00:00:00`);
  return d.toLocaleDateString(undefined, { weekday: "short" });
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getDashboardStats();
      setStats(res.data);
    } catch (err) {
      setError(err?.message || "Could not reach the backend.");
    } finally {
      setLoading(false);
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

  return (
    <PageContainer variant="full">
      <header className="mb-5 md:mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-[11px] tracking-[0.2em] uppercase text-folder-dark mb-2">
            Overview
          </p>
          <h1 className="font-display text-3xl md:text-4xl text-ink leading-tight">
            Dashboard
          </h1>
          <p className="text-ink-soft mt-2 text-sm max-w-lg">
            A snapshot of every claim on file — status, volume, and what
            still needs attention.
          </p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-1.5 text-xs font-mono text-ink-soft hover:text-ink"
        >
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          refresh
        </button>
      </header>

      {loading && (
        <div className="flex items-center gap-2 text-ink-soft text-sm py-6 md:py-7">
          <Loader2 size={16} className="animate-spin" />
          Loading dashboard…
        </div>
      )}

      {error && !loading && (
        <div className="flex items-center gap-2 bg-stamp-red-soft border border-stamp-red/30 text-stamp-red px-4 py-3 text-sm">
          <FileWarning size={16} />
          {error}
        </div>
      )}

      {stats && !loading && !error && (
        <div className="space-y-8">
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 md:gap-4">
            <div className="border border-ink/15 bg-white p-4 min-w-0">
              <div className="flex items-center gap-2 text-ink-soft mb-2">
                <LayoutDashboard size={15} />
                <span className="text-[10px] font-mono uppercase tracking-wide">
                  Total claims
                </span>
              </div>
              <p className="font-display text-2xl text-ink">{totalClaims}</p>
            </div>
            {STAT_CARDS.map(({ key, label, icon: Icon }) => (
              <div key={key} className="border border-ink/15 bg-white p-4 min-w-0">
                <div className="flex items-center gap-2 text-ink-soft mb-2">
                  <Icon size={15} />
                  <span className="text-[10px] font-mono uppercase tracking-wide">
                    {label}
                  </span>
                </div>
                <p className="font-display text-2xl text-ink">
                  {statusCounts[key] ?? 0}
                </p>
              </div>
            ))}
          </div>

          <div className="grid lg:grid-cols-2 gap-5 md:gap-6">
            <div className="border border-ink/15 bg-white p-5">
              <p className="text-xs font-mono uppercase tracking-wide text-ink-soft mb-4">
                Claims — last 7 days
              </p>
              <div className="flex items-end gap-3 h-32">
                {trend.map((d) => (
                  <div
                    key={d.date}
                    className="flex-1 flex flex-col items-center gap-2"
                  >
                    <span className="text-[10px] font-mono text-ink-soft">
                      {d.count}
                    </span>
                    <div className="w-full bg-ink/5 flex items-end h-full">
                      <div
                        className="w-full bg-folder-dark transition-all duration-500"
                        style={{
                          height: `${Math.max(4, (d.count / maxTrend) * 100)}%`,
                        }}
                      />
                    </div>
                    <span className="text-[10px] font-mono text-ink-soft">
                      {formatDayLabel(d.date)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border border-ink/15 bg-white p-5">
              <div className="flex items-center gap-2 text-ink-soft mb-4">
                <FileStack size={15} />
                <p className="text-xs font-mono uppercase tracking-wide">
                  Documents by type ({totalDocuments} total)
                </p>
              </div>
              {Object.keys(documentsByType).length === 0 && (
                <p className="text-sm text-ink-soft italic">
                  No documents scanned yet.
                </p>
              )}
              <div className="space-y-2.5">
                {Object.entries(documentsByType)
                  .sort((a, b) => b[1] - a[1])
                  .map(([type, count]) => {
                    const pct = totalDocuments
                      ? Math.round((count / totalDocuments) * 100)
                      : 0;
                    return (
                      <div key={type}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-ink capitalize">
                            {type.replace(/_/g, " ")}
                          </span>
                          <span className="font-mono text-ink-soft">
                            {count}
                          </span>
                        </div>
                        <div className="h-1.5 bg-ink/10 overflow-hidden">
                          <div
                            className="h-full bg-verify-green"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>

          <div>
            <p className="text-xs font-mono uppercase tracking-wide text-ink-soft mb-3">
              Recent claims
            </p>
            {recentClaims.length === 0 ? (
              <div className="flex flex-col items-center text-center py-16 border border-dashed border-ink/20 text-ink-soft">
                <FolderOpen size={28} className="mb-3 text-folder-dark" />
                <p className="text-sm">No claims on file yet.</p>
              </div>
            ) : (
              <div className="border border-ink/15 bg-white divide-y divide-ink/10">
                {recentClaims.map((c) => (
                  <div
                    key={c.claim_id}
                    onClick={() => navigate(`/claims/${c.claim_id}`)}
                    className="grid grid-cols-2 md:grid-cols-[minmax(180px,1.25fr)_minmax(180px,1fr)_110px_140px_56px] gap-4 px-4 py-3.5 items-center text-sm cursor-pointer hover:bg-folder/10 transition-colors"
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
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </PageContainer>
  );
}
