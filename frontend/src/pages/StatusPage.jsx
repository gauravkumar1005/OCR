import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ScanLine,
  Search,
  RefreshCw,
  CheckCircle2,
  Loader2,
  FileWarning,
  ArrowRight,
} from "lucide-react";
import { getClaim, getClaimProgress, retryClaim } from "../api/client.js";
import PageContainer from "../components/PageContainer.jsx";
import StatusBadge from "../components/StatusBadge.jsx";

const TERMINAL = ["completed", "failed", "error"];

export default function StatusPage() {
  const { claimId: routeClaimId } = useParams();
  const navigate = useNavigate();
  const [claimIdInput, setClaimIdInput] = useState(routeClaimId || "");
  const [claim, setClaim] = useState(null);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(!!routeClaimId);
  const [error, setError] = useState("");
  const [retrying, setRetrying] = useState(false);
  const timerRef = useRef(null);

  const fetchClaim = async (id, silent = false) => {
    if (!id) return;
    if (!silent) setLoading(true);
    setError("");
    try {
      const res = await getClaim(id);
      setClaim(res.data);
    } catch (err) {
      setError(
        err?.response?.status === 404
          ? "No claim found with that ID."
          : err?.message || "Could not reach the backend."
      );
      setClaim(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchProgress = async (id) => {
    if (!id) return;
    try {
      const res = await getClaimProgress(id);
      setProgress(res.data);
    } catch {
      // Progress is a nice-to-have overlay - if it fails, the document
      // list below still shows real state, so fail silently here.
    }
  };

  useEffect(() => {
    if (!routeClaimId) return;
    fetchClaim(routeClaimId);
    fetchProgress(routeClaimId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeClaimId]);

  useEffect(() => {
    clearInterval(timerRef.current);
    if (claim && !TERMINAL.includes((claim.status || "").toLowerCase())) {
      timerRef.current = setInterval(() => {
        fetchClaim(routeClaimId, true);
        fetchProgress(routeClaimId);
      }, 3000);
    }
    return () => clearInterval(timerRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claim?.status, routeClaimId]);

  const goToClaim = (e) => {
    e.preventDefault();
    if (claimIdInput.trim()) navigate(`/status/${claimIdInput.trim()}`);
  };

  const handleRetry = async () => {
    if (!routeClaimId || retrying) return;
    setRetrying(true);
    setError("");
    try {
      await retryClaim(routeClaimId);
      // Pipeline continues from its last checkpoint on the engine side -
      // just refresh so the poller below picks up "processing" and starts
      // ticking again.
      await fetchClaim(routeClaimId);
      await fetchProgress(routeClaimId);
    } catch (err) {
      setError(
        err?.response?.data?.detail || err?.message || "Could not retry this claim."
      );
    } finally {
      setRetrying(false);
    }
  };

  const docs = claim?.documents || [];
  const completedDocs = docs.filter(
    (d) => (d.ocr_status || "").toLowerCase() === "completed"
  ).length;
  const totalDocs = claim?.document_count ?? docs.length;
  const pct = totalDocs ? Math.round((completedDocs / totalDocs) * 100) : 0;

  return (
    <PageContainer variant="wide">
      <header className="mb-5 md:mb-6">
        <p className="font-mono text-[11px] tracking-[0.2em] uppercase text-folder-dark mb-2">
          Intake — Step 02
        </p>
        <h1 className="font-display text-3xl md:text-4xl text-ink leading-tight">
          Watch the scan run
        </h1>
        <p className="text-ink-soft mt-2 text-sm max-w-lg">
          Track OCR and mapping progress for a claim, document by document.
        </p>
      </header>

      <form onSubmit={goToClaim} className="flex gap-2 mb-6 md:mb-7">
        <div className="relative flex-1 min-w-0">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-soft"
          />
          <input
            value={claimIdInput}
            onChange={(e) => setClaimIdInput(e.target.value)}
            placeholder="Paste a claim ID…"
            className="w-full border border-ink/20 bg-white pl-9 pr-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-folder-dark"
          />
        </div>
        <button
          type="submit"
          className="px-5 py-2.5 bg-ink text-paper text-sm font-medium hover:bg-ink-soft transition-colors"
        >
          Track
        </button>
      </form>

      {loading && (
        <div className="flex items-center gap-2 text-ink-soft text-sm py-4">
          <Loader2 size={16} className="animate-spin" />
          Fetching claim…
        </div>
      )}

      {error && !loading && (
        <div className="flex items-center gap-2 bg-stamp-red-soft border border-stamp-red/30 text-stamp-red px-4 py-3 text-sm">
          <FileWarning size={16} />
          {error}
        </div>
      )}

      {claim && !loading && (
        <div className="space-y-8">
          <div className="border border-ink/15 bg-white p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-mono text-ink-soft">
                  {claim.claim_id}
                </p>
                <p className="font-display text-xl text-ink mt-0.5">
                  {claim.file_no || "Untitled claim"}
                </p>
              </div>
              <StatusBadge status={claim.status} />
            </div>

            {progress &&
              !TERMINAL.includes((claim.status || "").toLowerCase()) && (
                <div className="mt-4 flex items-center gap-2 text-xs font-mono text-ink-soft bg-folder/40 border border-ink/10 px-3 py-2">
                  <Loader2 size={13} className="animate-spin shrink-0" />
                  <span className="truncate">
                    {progress.stage_label || progress.stage || "Working…"}
                  </span>
                  {typeof progress.percent === "number" && (
                    <span className="ml-auto shrink-0">
                      {progress.percent}%
                    </span>
                  )}
                </div>
              )}

            <div className="mt-5">
              <div className="flex justify-between text-xs font-mono text-ink-soft mb-1.5">
                <span>
                  {completedDocs} / {totalDocs} documents scanned
                </span>
                <span>{pct}%</span>
              </div>
              <div className="h-2 bg-ink/10 overflow-hidden relative">
                <div
                  className="h-full bg-folder-dark transition-all duration-500"
                  style={{ width: `${pct}%` }}
                />
                {pct < 100 && (
                  <div className="absolute inset-0 w-1/3 bg-white/40 animate-scan" />
                )}
              </div>
            </div>

            {claim.status?.toLowerCase() === "completed" && (
              <button
                onClick={() => navigate(`/claims/${claim.claim_id}`)}
                className="mt-5 flex items-center gap-1.5 text-sm font-medium text-ink hover:text-folder-dark transition-colors"
              >
                Review extracted documents <ArrowRight size={14} />
              </button>
            )}

            {claim.status?.toLowerCase() === "failed" && (
              <div className="mt-5">
                <button
                  onClick={handleRetry}
                  disabled={retrying}
                  className="flex items-center gap-1.5 px-4 py-2 bg-ink text-paper text-sm font-medium hover:bg-ink-soft transition-colors disabled:opacity-50"
                >
                  <RefreshCw size={14} className={retrying ? "animate-spin" : ""} />
                  {retrying ? "Resuming…" : "Retry from where it stopped"}
                </button>
                <p className="text-xs text-ink-soft mt-2">
                  Continues from the last completed page/step instead of
                  re-scanning the whole document.
                </p>
              </div>
            )}
          </div>

          <div>
            <p className="text-xs font-mono uppercase tracking-wide text-ink-soft mb-3">
              Documents ({docs.length})
            </p>
            <div className="space-y-2">
              {docs.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center gap-3 border border-ink/10 bg-white/70 px-4 py-3"
                >
                  {(doc.ocr_status || "").toLowerCase() === "completed" ? (
                    <CheckCircle2 size={17} className="text-verify-green shrink-0" />
                  ) : (
                    <Loader2 size={17} className="text-amber animate-spin shrink-0" />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-ink font-medium truncate">
                      {doc.document_type?.replace(/_/g, " ") || "unknown"}
                    </p>
                    <p className="text-xs text-ink-soft font-mono">
                      pages {doc.pages_processed?.join(", ") || "—"}
                    </p>
                  </div>
                  <StatusBadge status={doc.ocr_status} />
                  <StatusBadge status={doc.mapping_status} />
                </div>
              ))}
              {docs.length === 0 && (
                <p className="text-sm text-ink-soft italic">
                  No documents split out yet — check back shortly.
                </p>
              )}
            </div>
          </div>

          <button
            onClick={() => fetchClaim(routeClaimId)}
            className="flex items-center gap-1.5 text-xs font-mono text-ink-soft hover:text-ink"
          >
            <RefreshCw size={13} /> refresh now
          </button>
        </div>
      )}

      {!claim && !loading && !error && (
        <div className="flex flex-col items-center text-center py-16 border border-dashed border-ink/20 text-ink-soft">
          <ScanLine size={28} className="mb-3 text-folder-dark" />
          <p className="text-sm">
            Enter a claim ID above to watch its processing status.
          </p>
        </div>
      )}
    </PageContainer>
  );
}

