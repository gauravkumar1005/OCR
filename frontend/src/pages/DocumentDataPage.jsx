import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Loader2,
  FileWarning,
  Save,
  Table2,
  AlertTriangle,
  ChevronLeft,
  Check,
  CircleDot,
} from "lucide-react";
import { getClaim, updateEntities, updateClaimStatus } from "../api/client.js";
import StatusBadge from "../components/StatusBadge.jsx";

function titleCase(s) {
  return (s || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function DocumentDataPage() {
  const { claimId } = useParams();
  const navigate = useNavigate();
  const [claim, setClaim] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeType, setActiveType] = useState(null);
  const [edited, setEdited] = useState({}); // documentType -> {field: value}
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [statusSaving, setStatusSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getClaim(claimId);
      setClaim(res.data);
      const first = res.data?.documents?.[0]?.document_type;
      setActiveType((prev) => prev || first || null);
    } catch (err) {
      setError(
        err?.response?.status === 404
          ? "No claim found with that ID."
          : err?.message || "Could not reach the backend."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claimId]);

  const docs = claim?.documents || [];
  const activeDoc = useMemo(
    () => docs.find((d) => d.document_type === activeType),
    [docs, activeType]
  );

  const fieldsForActive = edited[activeType] || {};

  const setField = (docType, field, value) => {
    setSaved(false);
    setEdited((prev) => ({
      ...prev,
      [docType]: { ...(prev[docType] || {}), [field]: value },
    }));
  };

  const hasChanges = Object.keys(fieldsForActive).length > 0;

  const entities = activeDoc?.all_extracted_entities || {};
  const totalFields = Object.keys(entities).length;
  const missingCount = Object.values(entities).filter(
    (v) => !v || String(v).toLowerCase() === "not available"
  ).length;

  const saveEntities = async () => {
    if (!activeDoc || !hasChanges) return;
    setSaving(true);
    try {
      await updateEntities(claimId, activeDoc.document_type, fieldsForActive);
      setClaim((prev) => ({
        ...prev,
        documents: prev.documents.map((d) =>
          d.document_type === activeDoc.document_type
            ? {
                ...d,
                all_extracted_entities: {
                  ...d.all_extracted_entities,
                  ...fieldsForActive,
                },
              }
            : d
        ),
      }));
      setEdited((prev) => ({ ...prev, [activeDoc.document_type]: {} }));
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      let message = err?.message || "Could not save changes.";
      if (Array.isArray(detail)) {
        message = detail.map((d) => d.msg).filter(Boolean).join("; ") || message;
      } else if (typeof detail === "string") {
        message = detail;
      }
      alert(message);
    } finally {
      setSaving(false);
    }
  };

  const changeClaimStatus = async (status) => {
    setStatusSaving(true);
    try {
      await updateClaimStatus(claimId, status);
      setClaim((prev) => ({ ...prev, status }));
    } catch (err) {
      alert(err?.message || "Could not update claim status.");
    } finally {
      setStatusSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-5 md:px-10 py-16 flex items-center gap-2 text-ink-soft text-sm">
        <Loader2 size={16} className="animate-spin" />
        Opening case file…
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-5 md:px-10 py-16">
        <div className="flex items-center gap-2 bg-stamp-red-soft border border-stamp-red/30 text-stamp-red px-4 py-3 text-sm">
          <FileWarning size={16} />
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-5 md:px-10 py-8 md:py-12">
      <button
        onClick={() => navigate("/claims")}
        className="flex items-center gap-1 text-xs font-mono text-ink-soft hover:text-ink mb-6"
      >
        <ChevronLeft size={13} /> case register
      </button>

      <header className="mb-8 flex flex-wrap items-start justify-between gap-4 pb-6 border-b border-ink/10">
        <div className="min-w-0">
          <p className="font-mono text-[11px] tracking-[0.2em] uppercase text-folder-dark mb-2">
            Step 04 · Document-wise data
          </p>
          <h1 className="font-display text-3xl md:text-4xl text-ink leading-tight truncate">
            {claim?.file_no || "Untitled claim"}
          </h1>
          <p className="text-ink-soft mt-2 text-xs font-mono">
            {claim?.claim_id}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <StatusBadge status={claim?.status} />
          <select
            disabled={statusSaving}
            value=""
            onChange={(e) => e.target.value && changeClaimStatus(e.target.value)}
            className="text-xs font-mono border border-ink/20 bg-white px-2.5 py-2 focus:outline-none focus:ring-2 focus:ring-folder-dark cursor-pointer"
          >
            <option value="">Update status…</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="pending">Pending</option>
            <option value="completed">Completed</option>
          </select>
        </div>
      </header>

      {docs.length === 0 ? (
        <div className="flex flex-col items-center text-center py-16 border border-dashed border-ink/20 text-ink-soft">
          <p className="text-sm">
            No documents have been extracted for this claim yet.
          </p>
        </div>
      ) : (
        <div className="lg:flex lg:items-start lg:gap-8">
          {/* Folder tabs */}
          <div className="lg:w-60 shrink-0 mb-6 lg:mb-0 lg:sticky lg:top-8">
            <p className="text-[10px] font-mono uppercase tracking-wide text-ink-soft/70 mb-2 px-1 hidden lg:block">
              {docs.length} document{docs.length !== 1 ? "s" : ""}
            </p>
            <div className="flex lg:flex-col gap-1.5 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0 scroll-thin">
              {docs.map((d, i) => {
                const isActive = activeType === d.document_type;
                const isEdited =
                  edited[d.document_type] &&
                  Object.keys(edited[d.document_type]).length > 0;
                return (
                  <button
                    key={d.id || i}
                    onClick={() => setActiveType(d.document_type)}
                    className={`shrink-0 text-left px-3.5 py-2.5 whitespace-nowrap lg:whitespace-normal border-l-[3px] transition-colors ${
                      isActive
                        ? "bg-ink text-paper border-folder-dark"
                        : "bg-white/70 text-ink-soft hover:bg-folder/15 hover:text-ink border-transparent"
                    }`}
                  >
                    <span className="text-sm font-medium flex items-center gap-1.5">
                      {titleCase(d.document_type)}
                      {isEdited && (
                        <CircleDot
                          size={10}
                          className={isActive ? "text-folder" : "text-folder-dark"}
                        />
                      )}
                    </span>
                    <span className="text-[10px] font-mono opacity-70 block mt-0.5">
                      {(d.ocr_status || "?").toUpperCase()}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active document detail */}
          {activeDoc && (
            <div className="flex-1 min-w-0 space-y-6">
              <div className="sticky top-14 md:top-0 z-10 -mx-5 md:-mx-10 lg:mx-0 px-5 md:px-10 lg:px-0 py-3.5 bg-paper/95 backdrop-blur-sm flex flex-wrap items-center justify-between gap-3 border-b border-ink/15">
                <div className="min-w-0">
                  <h2 className="font-display text-xl text-ink truncate">
                    {titleCase(activeDoc.document_type)}
                  </h2>
                  <p className="text-xs text-ink-soft font-mono mt-0.5 truncate">
                    {activeDoc.source_file_name} · pages{" "}
                    {activeDoc.pages_processed?.join(", ") || "—"}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <StatusBadge status={activeDoc.review_status} />
                  <button
                    onClick={saveEntities}
                    disabled={!hasChanges || saving}
                    className="flex items-center gap-1.5 px-4 py-2 bg-ink text-paper text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-ink-soft transition-colors"
                  >
                    {saving ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : saved ? (
                      <Check size={14} />
                    ) : (
                      <Save size={14} />
                    )}
                    {saved ? "Saved" : hasChanges ? `Save ${Object.keys(fieldsForActive).length} change${Object.keys(fieldsForActive).length !== 1 ? "s" : ""}` : "Save changes"}
                  </button>
                </div>
              </div>

              {/* Warnings */}
              {(activeDoc.warnings?.ignored_handwritten_content?.length > 0 ||
                activeDoc.warnings?.unmapped_ambiguous_text_regions?.length >
                  0) && (
                <div className="flex items-start gap-2 bg-amber-soft border border-amber/30 text-amber px-4 py-3 text-xs">
                  <AlertTriangle size={15} className="shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    {activeDoc.warnings.ignored_handwritten_content?.length >
                      0 && (
                      <p>
                        {activeDoc.warnings.ignored_handwritten_content.length}{" "}
                        handwritten region(s) were ignored.
                      </p>
                    )}
                    {activeDoc.warnings.unmapped_ambiguous_text_regions
                      ?.length > 0 && (
                      <p>
                        {
                          activeDoc.warnings.unmapped_ambiguous_text_regions
                            .length
                        }{" "}
                        ambiguous region(s) could not be mapped.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Entities form */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-mono uppercase tracking-wide text-ink-soft">
                    Extracted fields ({totalFields})
                  </p>
                  {missingCount > 0 && (
                    <p className="text-xs font-mono text-stamp-red flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-stamp-red" />
                      {missingCount} missing
                    </p>
                  )}
                </div>
                <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-x-6 gap-y-5 bg-white border border-ink/15 p-5 md:p-6">
                  {Object.entries(entities).map(([field, value]) => {
                    const current =
                      fieldsForActive[field] !== undefined
                        ? fieldsForActive[field]
                        : value;
                    const isMissing =
                      !value || String(value).toLowerCase() === "not available";
                    const isDirty = fieldsForActive[field] !== undefined;
                    return (
                      <label key={field} className="block">
                        <span className="text-[11px] font-mono uppercase tracking-wide text-ink-soft/80 flex items-center gap-1.5 mb-1">
                          <span className="truncate">{titleCase(field)}</span>
                          {isDirty && (
                            <span className="shrink-0 w-1.5 h-1.5 rounded-full bg-folder-dark" title="edited" />
                          )}
                        </span>
                        <input
                          value={current ?? ""}
                          onChange={(e) =>
                            setField(activeDoc.document_type, field, e.target.value)
                          }
                          placeholder={isMissing ? "Not extracted — enter manually" : ""}
                          className={`w-full border px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-folder-dark placeholder:text-stamp-red/50 placeholder:text-xs ${
                            isDirty
                              ? "border-folder-dark bg-folder/10"
                              : isMissing
                              ? "border-stamp-red/30 border-l-2 bg-white"
                              : "border-ink/15 bg-white"
                          }`}
                        />
                      </label>
                    );
                  })}
                  {totalFields === 0 && (
                    <p className="text-sm text-ink-soft italic sm:col-span-2 xl:col-span-3">
                      No fields were extracted for this document.
                    </p>
                  )}
                </div>
              </div>

              {/* Tables */}
              {(activeDoc.all_extracted_tables || []).length > 0 && (
                <div>
                  <p className="text-xs font-mono uppercase tracking-wide text-ink-soft mb-3 flex items-center gap-1.5">
                    <Table2 size={13} />
                    Extracted tables ({activeDoc.all_extracted_tables.length})
                  </p>
                  <div className="space-y-6">
                    {activeDoc.all_extracted_tables.map((tbl, ti) => {
                      const headers =
                        tbl.headers ||
                        (tbl.rows?.[0] ? Object.keys(tbl.rows[0]) : []);
                      return (
                        <div
                          key={ti}
                          className="border border-ink/15 bg-white"
                        >
                          <p className="px-4 py-3 text-sm font-medium text-ink border-b border-ink/10 bg-paper-dim/60">
                            {tbl.table_name ||
                              tbl.table_name_or_purpose ||
                              `Table ${ti + 1}`}
                          </p>
                          <div className="overflow-x-auto scroll-thin">
                            <table className="w-full text-xs min-w-[560px]">
                              <thead>
                                <tr className="bg-paper-dim">
                                  {headers.map((h) => (
                                    <th
                                      key={h}
                                      className="text-left px-3 py-2 font-mono uppercase tracking-wide text-ink-soft whitespace-nowrap"
                                    >
                                      {titleCase(h)}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-ink/10">
                                {(tbl.rows || []).map((row, ri) => (
                                  <tr key={ri} className="even:bg-paper/40">
                                    {headers.map((h) => (
                                      <td
                                        key={h}
                                        className="px-3 py-2 text-ink align-top"
                                      >
                                        {String(row[h] ?? "")}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
