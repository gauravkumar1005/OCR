import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Loader2,
  FileWarning,
  Table2,
  ChevronLeft,
  Plus,
  X,
  ScanLine,
} from "lucide-react";
import {
  getClaim,
  updateEntities,
  deleteEntity,
  updateTables,
  updateClaimStatus,
  retryClaim,
} from "../api/client.js";
import PageContainer from "../components/PageContainer.jsx";
import DocumentNavigator from "../components/DocumentNavigator.jsx";
import ReviewStatusSummary from "../components/ReviewStatusSummary.jsx";
import FieldReviewSummary from "../components/FieldReviewSummary.jsx";
import EditableEntityField from "../components/EditableEntityField.jsx";
import ReviewActionBar from "../components/ReviewActionBar.jsx";
import ReviewToast from "../components/ReviewToast.jsx";
import { ConfirmationDialog, FormDialog } from "../components/ReviewDialogs.jsx";
import StatusBadge from "../components/StatusBadge.jsx";

function titleCase(s) {
  return (s || "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function isMissingValue(value) {
  return value === null || value === undefined || String(value).trim() === "";
}

function isStructuredField(value) {
  return Boolean(
    value &&
      typeof value === "object" &&
      !Array.isArray(value) &&
      ("value" in value || "text" in value || "extracted_value" in value || "confidence" in value || "source_page" in value || "page" in value)
  );
}

function normalizeFieldRecord(raw) {
  if (!isStructuredField(raw)) {
    return { displayValue: raw, confidence: null, sourcePage: null, sourceLabel: null, reviewNote: null };
  }
  return {
    displayValue: raw.value ?? raw.text ?? raw.extracted_value ?? raw.field_value ?? "",
    confidence: raw.confidence ?? raw.confidence_score ?? raw.score ?? null,
    sourcePage: raw.source_page ?? raw.page ?? raw.page_number ?? null,
    sourceLabel: raw.source_file_name ?? raw.source ?? raw.source_label ?? null,
    reviewNote: raw.review_note ?? raw.note ?? raw.warning ?? null,
  };
}

function formatPages(doc) {
  const pages = Array.isArray(doc?.pages_processed) ? [...new Set(doc.pages_processed)].sort((a, b) => a - b) : [];
  if (pages.length === 1) return `Page ${pages[0]}`;
  if (pages.length > 1) {
    const contiguous = pages.every((page, index) => index === 0 || page === pages[index - 1] + 1);
    return contiguous ? `Pages ${pages[0]}-${pages[pages.length - 1]}` : `Pages ${pages.join(", ")}`;
  }
  if (doc?.processed_page_count || doc?.total_page_count) {
    return `Pages ${doc.processed_page_count ?? 0}/${doc.total_page_count ?? "?"}`;
  }
  return "Page not available";
}

function isUnknownDocumentType(docType) {
  const normalized = (docType || "").toLowerCase();
  return !normalized || normalized === "unknown" || normalized === "claim_pdf";
}

function humanizeDocumentType(docType) {
  return isUnknownDocumentType(docType) ? "Unknown document type" : titleCase(docType);
}

function getDocumentTarget(doc) {
  const params = {};
  if (doc?.source_file_name) params.source_file_name = doc.source_file_name;
  if (doc?.sequence !== null && doc?.sequence !== undefined) params.sequence = doc.sequence;
  return params;
}

function getEntries(doc, edited) {
  return { ...(doc?.all_extracted_entities || {}), ...(edited || {}) };
}

function getStats(doc, edited) {
  const entries = getEntries(doc, edited);
  const verification = doc?.entity_verification || {};
  const remarks = doc?.entity_remarks || {};
  let missingCount = 0;
  let reviewCount = 0;
  let hasReviewMetadata = false;

  Object.entries(entries).forEach(([fieldKey, rawValue]) => {
    const rec = normalizeFieldRecord(rawValue);
    if (isMissingValue(rec.displayValue)) missingCount += 1;
    const confidencePct = typeof rec.confidence === "number"
      ? (rec.confidence > 1 ? rec.confidence : rec.confidence * 100)
      : null;
    const needsReview = verification[fieldKey] === false || Boolean(String(remarks[fieldKey] || "").trim()) || (confidencePct !== null && confidencePct < 75);
    if (verification[fieldKey] !== undefined || String(remarks[fieldKey] || "").trim() || confidencePct !== null) hasReviewMetadata = true;
    if (needsReview) reviewCount += 1;
  });

  return { totalFields: Object.keys(entries).length, missingCount, reviewCount, hasReviewMetadata };
}

function getDocLabel(doc, index, counts) {
  const base = humanizeDocumentType(doc?.document_type);
  const key = doc?.document_type || "unknown";
  const dupCount = counts[key] || 0;
  if (isUnknownDocumentType(doc?.document_type)) return dupCount > 1 ? `${base} ${doc?.sequence || index + 1}` : base;
  return dupCount > 1 || doc?.sequence ? `${base} ${doc?.sequence || index + 1}` : base;
}

function countDirty(fields) {
  return Object.keys(fields || {}).length;
}

function statusText(value) {
  return value ? String(value).replace(/_/g, " ") : "not available";
}

export default function DocumentDataPage() {
  const { claimId } = useParams();
  const navigate = useNavigate();
  const [claim, setClaim] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeDocId, setActiveDocId] = useState(null);
  const [editedEntities, setEditedEntities] = useState({});
  const [editedTables, setEditedTables] = useState({});
  const [fieldFilter, setFieldFilter] = useState("all");
  const [fieldMenuOpen, setFieldMenuOpen] = useState(null);
  const [saveState, setSaveState] = useState({ kind: "clean" });
  const [statusSaving, setStatusSaving] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [dialog, setDialog] = useState(null);
  const [toast, setToast] = useState(null);
  const toastTimerRef = useRef(null);
  const saveTimerRef = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getClaim(claimId);
      const nextClaim = res.data;
      setClaim(nextClaim);
      const firstDoc = nextClaim?.documents?.[0]?.id || null;
      setActiveDocId((prev) => (nextClaim?.documents?.some((doc) => doc.id === prev) ? prev : firstDoc));
    } catch (err) {
      setError(err?.response?.status === 404 ? "No claim found with that ID." : err?.message || "Could not reach the backend.");
    } finally {
      setLoading(false);
    }
  }, [claimId]);

  useEffect(() => { load(); }, [load]);

  const activeDoc = useMemo(
    () => claim?.documents?.find((doc) => doc.id === activeDocId) || null,
    [claim, activeDocId]
  );

  const activeEditedFields = editedEntities[activeDocId] || {};
  const activeTables = editedTables[activeDocId];
  const currentFieldsDirty = countDirty(activeEditedFields);
  const currentTablesDirty = activeTables !== undefined;
  const currentDocDirty = currentFieldsDirty > 0 || currentTablesDirty;
  const statusLocked = currentDocDirty || statusSaving || retrying;
  const claimDocuments = useMemo(() => claim?.documents || [], [claim]);

  useEffect(() => {
    if (!currentDocDirty) return undefined;
    const handler = (e) => { e.preventDefault(); e.returnValue = ""; };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [currentDocDirty]);

  useEffect(() => {
    if (!toast) return undefined;
    window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 4500);
    return () => window.clearTimeout(toastTimerRef.current);
  }, [toast]);

  useEffect(() => {
    if (saveState.kind !== "saved") return undefined;
    window.clearTimeout(saveTimerRef.current);
    saveTimerRef.current = window.setTimeout(() => setSaveState({ kind: "clean" }), 2200);
    return () => window.clearTimeout(saveTimerRef.current);
  }, [saveState.kind]);

  const documentsWithStats = useMemo(() => {
    const typeCounts = claimDocuments.reduce((acc, doc) => {
      const key = doc.document_type || "unknown";
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});

    return claimDocuments.map((doc, index) => {
      const edited = editedEntities[doc.id] || {};
      const stats = getStats(doc, edited);
      return {
        ...doc,
        label: getDocLabel(doc, index, typeCounts),
        pageLabel: formatPages(doc),
        ocrStatusText: statusText(doc.ocr_status),
        reviewStatusText: doc.review_status === "pending" ? "review pending" : statusText(doc.review_status),
        fieldCount: Object.keys(getEntries(doc, edited)).length,
        missingCount: stats.missingCount,
        reviewCount: stats.reviewCount,
        hasReviewMetadata: stats.hasReviewMetadata,
      };
    });
  }, [claimDocuments, editedEntities]);

  useEffect(() => { setFieldFilter("all"); }, [activeDocId]);

  const activeDocSummary = useMemo(() => {
    if (!activeDoc) return null;
    const edited = editedEntities[activeDoc.id] || {};
    const mergedEntries = getEntries(activeDoc, edited);
    return {
      mergedEntries,
      stats: getStats(activeDoc, edited),
      tablesForActive: activeTables !== undefined ? activeTables : activeDoc.all_extracted_tables || [],
      tablesDirty: activeTables !== undefined,
      fieldsForActive: edited,
    };
  }, [activeDoc, editedEntities, activeTables]);

  const fieldEntries = useMemo(() => {
    if (!activeDocSummary) return [];
    const verification = activeDoc?.entity_verification || {};
    const remarks = activeDoc?.entity_remarks || {};
    return Object.entries(activeDocSummary.mergedEntries).map(([fieldKey, rawValue]) => {
      const rec = normalizeFieldRecord(rawValue);
      const dirty = activeDocSummary.fieldsForActive[fieldKey] !== undefined;
      const missing = isMissingValue(rec.displayValue);
      const confidencePct = typeof rec.confidence === "number" ? (rec.confidence > 1 ? rec.confidence : rec.confidence * 100) : null;
      const reviewRequired = verification[fieldKey] === false || Boolean(String(remarks[fieldKey] || "").trim()) || (confidencePct !== null && confidencePct < 75);
      return {
        fieldKey,
        label: titleCase(fieldKey),
        value: rec.displayValue,
        confidence: rec.confidence,
        sourcePage: rec.sourcePage,
        sourceLabel: rec.sourceLabel,
        reviewNote: remarks[fieldKey] || rec.reviewNote,
        dirty,
        missing,
        reviewRequired,
      };
    });
  }, [activeDoc, activeDocSummary]);

  const filteredFieldEntries = useMemo(() => {
    return fieldEntries.filter((field) => {
      if (fieldFilter === "missing") return field.missing;
      if (fieldFilter === "modified") return field.dirty;
      if (fieldFilter === "review") return field.reviewRequired;
      return true;
    });
  }, [fieldEntries, fieldFilter]);


  const openToast = (tone, title, message, actionLabel, onAction) => {
    setToast({ tone, title, message, actionLabel, onAction });
  };

  const setFieldValue = (docId, fieldKey, value) => {
    setEditedEntities((prev) => ({
      ...prev,
      [docId]: { ...(prev[docId] || {}), [fieldKey]: value },
    }));
    setSaveState({ kind: "dirty" });
  };

  const updateClaimDoc = (docId, updater) => {
    setClaim((prev) => ({
      ...prev,
      documents: prev.documents.map((doc) => (doc.id === docId ? updater(doc) : doc)),
    }));
  };

  const getActiveTarget = () => (activeDoc ? getDocumentTarget(activeDoc) : {});

  const saveCurrentDocumentChanges = async () => {
    if (!activeDoc || !currentDocDirty) return;
    const docId = activeDoc.id;
    const target = getActiveTarget();
    const fieldChanges = editedEntities[docId] || {};
    const tableChanges = editedTables[docId];
    let savedSomething = false;

    setSaveState({ kind: "saving" });
    setFieldMenuOpen(null);
    try {
      if (Object.keys(fieldChanges).length > 0) {
        await updateEntities(claimId, activeDoc.document_type, fieldChanges, target);
        updateClaimDoc(docId, (doc) => ({
          ...doc,
          all_extracted_entities: { ...(doc.all_extracted_entities || {}), ...fieldChanges },
          review_status: "in_review",
        }));
        setEditedEntities((prev) => {
          const next = { ...prev };
          delete next[docId];
          return next;
        });
        savedSomething = true;
      }

      if (tableChanges !== undefined) {
        await updateTables(claimId, activeDoc.document_type, tableChanges, target);
        updateClaimDoc(docId, (doc) => ({
          ...doc,
          all_extracted_tables: tableChanges,
          review_status: "in_review",
        }));
        setEditedTables((prev) => {
          const next = { ...prev };
          delete next[docId];
          return next;
        });
        savedSomething = true;
      }

      if (savedSomething) {
        setSaveState({ kind: "saved" });
        openToast("success", "Changes saved", `${activeDoc.label || titleCase(activeDoc.document_type)} saved successfully.`);
      } else {
        setSaveState({ kind: "clean" });
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      let message = err?.message || "Could not save changes.";
      if (Array.isArray(detail)) message = detail.map((d) => d.msg).filter(Boolean).join("; ") || message;
      if (typeof detail === "string") message = detail;
      setSaveState({ kind: "error", message });
      openToast("error", "Save failed", message, "Retry", saveCurrentDocumentChanges);
    }
  };

  const discardCurrentChanges = () => {
    if (!activeDoc) return;
    setEditedEntities((prev) => {
      const next = { ...prev };
      delete next[activeDoc.id];
      return next;
    });
    setEditedTables((prev) => {
      const next = { ...prev };
      delete next[activeDoc.id];
      return next;
    });
    setSaveState({ kind: "clean" });
    setFieldMenuOpen(null);
    setDialog(null);
  };
  const switchDocument = (nextDocId) => {
    if (nextDocId === activeDocId) return;
    if (currentDocDirty) {
      setDialog({
        kind: "confirm",
        title: "Unsaved changes",
        description: "Save or discard the current document changes before switching.",
        actions: [
          { label: "Cancel", tone: "neutral", onClick: () => setDialog(null) },
          {
            label: "Discard & switch",
            tone: "danger",
            onClick: () => {
              discardCurrentChanges();
              setActiveDocId(nextDocId);
            },
          },
          {
            label: "Save & switch",
            tone: "primary",
            onClick: async () => {
              await saveCurrentDocumentChanges();
              setDialog(null);
              setActiveDocId(nextDocId);
            },
          },
        ],
      });
      return;
    }
    setActiveDocId(nextDocId);
    setFieldFilter("all");
    setSaveState({ kind: "clean" });
  };

  const openFieldDialog = () => {
    if (!activeDoc) return;
    setDialog({
      kind: "form",
      title: "Add field",
      description: "Add a field to the current document without changing backend keys.",
      fields: [
        { name: "key", label: "Field name", placeholder: "e.g. discount_amount" },
        { name: "value", label: "Value", placeholder: "Enter the field value" },
      ],
      confirmLabel: "Add field",
      onSubmit: ({ key, value }) => {
        const normalizedKey = String(key || "").trim().toLowerCase().replace(/\s+/g, "_");
        if (!normalizedKey) {
          openToast("error", "Field name required", "Please enter a field name before adding it.");
          return;
        }
        const currentEntries = getEntries(activeDoc, activeEditedFields);
        if (normalizedKey in currentEntries) {
          openToast("error", "Duplicate field", "A field with that name already exists on this document.");
          return;
        }
        setFieldValue(activeDoc.id, normalizedKey, value);
        setDialog(null);
      },
      onCancel: () => setDialog(null),
    });
  };

  const openTableDialog = () => {
    if (!activeDoc) return;
    setDialog({
      kind: "form",
      title: "Add table",
      description: "Create a new editable table for the current document.",
      fields: [
        { name: "name", label: "Table name", placeholder: "New Table", defaultValue: "New Table" },
        { name: "headers", label: "Column names", placeholder: "item, quantity, amount", multiline: true, rows: 3 },
      ],
      confirmLabel: "Add table",
      onSubmit: ({ name, headers }) => {
        const tableName = String(name || "").trim();
        const headerList = String(headers || "")
          .split(",")
          .map((h) => h.trim().toLowerCase().replace(/\s+/g, "_"))
          .filter(Boolean);
        if (!tableName || headerList.length === 0) {
          openToast("error", "Table details required", "Provide a table name and at least one column.");
          return;
        }
        const currentTables = activeTables !== undefined ? activeTables : activeDoc.all_extracted_tables || [];
        setEditedTables((prev) => ({ ...prev, [activeDoc.id]: [...currentTables, { table_name: tableName, headers: headerList, rows: [] }] }));
        setSaveState({ kind: "dirty" });
        setDialog(null);
      },
      onCancel: () => setDialog(null),
    });
  };

  const openColumnDialog = (tableIndex) => {
    if (!activeDoc) return;
    setDialog({
      kind: "form",
      title: "Add column",
      description: "Add a column to the selected table.",
      fields: [{ name: "column", label: "Column name", placeholder: "New column" }],
      confirmLabel: "Add column",
      onSubmit: ({ column }) => {
        const key = String(column || "").trim().toLowerCase().replace(/\s+/g, "_");
        if (!key) {
          openToast("error", "Column name required", "Please enter a column name.");
          return;
        }
        const currentTables = activeTables !== undefined ? activeTables : activeDoc.all_extracted_tables || [];
        const nextTables = currentTables.map((table, index) => {
          if (index !== tableIndex) return table;
          const headers = table.headers ? [...table.headers] : [];
          if (!headers.includes(key)) headers.push(key);
          const rows = (table.rows || []).map((row) => ({ ...row, [key]: row[key] ?? "" }));
          return { ...table, headers, rows };
        });
        setEditedTables((prev) => ({ ...prev, [activeDoc.id]: nextTables }));
        setSaveState({ kind: "dirty" });
        setDialog(null);
      },
      onCancel: () => setDialog(null),
    });
  };

  const confirmDeleteField = (fieldKey) => {
    if (!activeDoc) return;
    setDialog({
      kind: "confirm",
      title: "Delete field",
      description: `Delete ${titleCase(fieldKey)} from this document? This cannot be undone.`,
      actions: [
        { label: "Cancel", tone: "neutral", onClick: () => setDialog(null) },
        {
          label: "Delete field",
          tone: "danger",
          onClick: async () => {
            const currentEntries = activeDoc.all_extracted_entities || {};
            if (!(fieldKey in currentEntries)) {
              setEditedEntities((prev) => {
                const next = { ...(prev[activeDoc.id] || {}) };
                delete next[fieldKey];
                return { ...prev, [activeDoc.id]: next };
              });
              setDialog(null);
              openToast("success", "Field removed", `${titleCase(fieldKey)} was removed from the current draft.`);
              return;
            }
            try {
              await deleteEntity(claimId, activeDoc.document_type, fieldKey, getActiveTarget());
              updateClaimDoc(activeDoc.id, (doc) => {
                const nextEntities = { ...(doc.all_extracted_entities || {}) };
                delete nextEntities[fieldKey];
                const nextVerification = { ...(doc.entity_verification || {}) };
                delete nextVerification[fieldKey];
                const nextRemarks = { ...(doc.entity_remarks || {}) };
                delete nextRemarks[fieldKey];
                return { ...doc, all_extracted_entities: nextEntities, entity_verification: nextVerification, entity_remarks: nextRemarks, review_status: "in_review" };
              });
              setEditedEntities((prev) => {
                const next = { ...(prev[activeDoc.id] || {}) };
                delete next[fieldKey];
                return { ...prev, [activeDoc.id]: next };
              });
              setDialog(null);
              openToast("success", "Field deleted", `${titleCase(fieldKey)} was deleted.`);
            } catch (err) {
              setDialog(null);
              openToast("error", "Delete failed", err?.message || "Could not delete field.");
            }
          },
        },
      ],
    });
  };

  const confirmDeleteTable = (tableIndex) => {
    if (!activeDoc) return;
    setDialog({
      kind: "confirm",
      title: "Delete table",
      description: `Delete table ${tableIndex + 1}? This cannot be undone.`,
      actions: [
        { label: "Cancel", tone: "neutral", onClick: () => setDialog(null) },
        {
          label: "Delete table",
          tone: "danger",
          onClick: () => {
            const currentTables = activeTables !== undefined ? activeTables : activeDoc.all_extracted_tables || [];
            const nextTables = currentTables.filter((_, index) => index !== tableIndex);
            setEditedTables((prev) => ({ ...prev, [activeDoc.id]: nextTables }));
            setSaveState({ kind: "dirty" });
            setDialog(null);
          },
        },
      ],
    });
  };

  const confirmDeleteRow = (tableIndex, rowIndex) => {
    if (!activeDoc) return;
    setDialog({
      kind: "confirm",
      title: "Delete row",
      description: `Delete row ${rowIndex + 1} from table ${tableIndex + 1}?`,
      actions: [
        { label: "Cancel", tone: "neutral", onClick: () => setDialog(null) },
        {
          label: "Delete row",
          tone: "danger",
          onClick: () => {
            const currentTables = activeTables !== undefined ? activeTables : activeDoc.all_extracted_tables || [];
            const nextTables = currentTables.map((table, index) => {
              if (index !== tableIndex) return table;
              return { ...table, rows: (table.rows || []).filter((_, idx) => idx !== rowIndex) };
            });
            setEditedTables((prev) => ({ ...prev, [activeDoc.id]: nextTables }));
            setSaveState({ kind: "dirty" });
            setDialog(null);
          },
        },
      ],
    });
  };

  const confirmDeleteColumn = (tableIndex, header) => {
    if (!activeDoc) return;
    setDialog({
      kind: "confirm",
      title: "Delete column",
      description: `Delete ${titleCase(header)} from table ${tableIndex + 1}?`,
      actions: [
        { label: "Cancel", tone: "neutral", onClick: () => setDialog(null) },
        {
          label: "Delete column",
          tone: "danger",
          onClick: () => {
            const currentTables = activeTables !== undefined ? activeTables : activeDoc.all_extracted_tables || [];
            const nextTables = currentTables.map((table, index) => {
              if (index !== tableIndex) return table;
              return {
                ...table,
                headers: (table.headers || []).filter((h) => h !== header),
                rows: (table.rows || []).map((row) => {
                  const nextRow = { ...row };
                  delete nextRow[header];
                  return nextRow;
                }),
              };
            });
            setEditedTables((prev) => ({ ...prev, [activeDoc.id]: nextTables }));
            setSaveState({ kind: "dirty" });
            setDialog(null);
          },
        },
      ],
    });
  };

  const updateClaimStatusSafe = (nextStatus) => {
    if (!claim || statusLocked) return;
    setDialog({
      kind: "confirm",
      title: "Update claim status",
      description: `Change claim status to ${titleCase(nextStatus)}?`,
      actions: [
        { label: "Cancel", tone: "neutral", onClick: () => setDialog(null) },
        {
          label: `Set ${titleCase(nextStatus)}`,
          tone: "primary",
          onClick: async () => {
            setStatusSaving(true);
            try {
              await updateClaimStatus(claimId, nextStatus);
              setClaim((prev) => ({ ...prev, status: nextStatus }));
              setDialog(null);
              openToast("success", "Status updated", `Claim status changed to ${titleCase(nextStatus)}.`);
            } catch (err) {
              openToast("error", "Status update failed", err?.message || "Could not update claim status.");
            } finally {
              setStatusSaving(false);
            }
          },
        },
      ],
    });
  };

  const runRetry = async () => {
    if (!claim || retrying || currentDocDirty) return;
    setRetrying(true);
    try {
      await retryClaim(claimId);
      await load();
      openToast("success", "Retry started", "The claim was sent back into processing.");
    } catch (err) {
      openToast("error", "Retry failed", err?.message || "Could not retry this claim.");
    } finally {
      setRetrying(false);
    }
  };


  const currentDocStats = activeDocSummary?.stats || { totalFields: 0, missingCount: 0, reviewCount: 0, hasReviewMetadata: false };
  const selectedDocItem = documentsWithStats.find((item) => item.id === activeDocId);

  if (loading) {
    return (
      <PageContainer variant="full" className="flex items-center gap-2 text-ink-soft text-sm">
        <Loader2 size={16} className="animate-spin" />
        Opening case file…
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer variant="full">
        <div className="flex items-center gap-2 bg-stamp-red-soft border border-stamp-red/30 text-stamp-red px-4 py-3 text-sm">
          <FileWarning size={16} />
          {error}
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer variant="full">
      <button
        type="button"
        onClick={() => navigate("/claims")}
        className="mb-5 flex items-center gap-1 text-xs font-mono text-ink-soft hover:text-ink focus:outline-none focus:ring-2 focus:ring-folder-dark md:mb-6"
      >
        <ChevronLeft size={13} /> case register
      </button>

      <header className="mb-5 flex flex-wrap items-start justify-between gap-4 border-b border-ink/10 pb-5 md:mb-6">
        <div className="min-w-0">
          <p className="mb-2 font-mono text-[11px] uppercase tracking-[0.2em] text-folder-dark">
            Step 04 · Document review workspace
          </p>
          <h1 className="truncate font-display text-3xl leading-tight text-ink md:text-4xl">
            {claim?.file_no || "Untitled claim"}
          </h1>
          <p className="mt-2 text-xs font-mono text-ink-soft">{claim?.claim_id}</p>
        </div>
        <div className="shrink-0 text-right text-xs font-mono text-ink-soft">
          <p>{claimDocuments.length} document{claimDocuments.length === 1 ? "" : "s"}</p>
          <p>{selectedDocItem ? selectedDocItem.label : "No document selected"}</p>
        </div>
      </header>

      {toast && (
        <div className="mb-4">
          <ReviewToast
            tone={toast.tone}
            title={toast.title}
            message={toast.message}
            actionLabel={toast.actionLabel}
            onAction={toast.onAction}
            onClose={() => setToast(null)}
          />
        </div>
      )}

      <div className="space-y-4">
        <ReviewStatusSummary
          claimStatus={claim?.status}
          ocrStatus={activeDoc?.ocr_status}
          mappingStatus={activeDoc?.mapping_status}
          reviewStatus={activeDoc?.review_status}
        />

        <ReviewActionBar
          dirtyCount={currentFieldsDirty}
          tablesDirty={currentTablesDirty}
          saving={saveState.kind === "saving"}
          tablesSaving={false}
          saveDisabled={!currentDocDirty || saveState.kind === "saving"}
          claimStatus={claim?.status}
          onSave={saveCurrentDocumentChanges}
          onRequestStatus={updateClaimStatusSafe}
          onRetry={runRetry}
          retrying={retrying}
          canRetry={claim?.status === "failed" || claim?.status === "uploaded"}
          statusLocked={statusLocked}
        />
      </div>

      <div className="mt-6 lg:flex lg:items-start lg:gap-8">
        {claimDocuments.length > 0 && (
          <DocumentNavigator
            items={documentsWithStats}
            activeId={activeDocId}
            onSelect={switchDocument}
          />
        )}

        <div className="min-w-0 flex-1 space-y-6">
          {activeDoc ? (
            <>
              <div className="rounded-none border border-ink/15 bg-white px-4 py-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h2 className="truncate font-display text-2xl text-ink">
                      {humanizeDocumentType(activeDoc.document_type)}
                    </h2>
                    <p className="mt-1 text-xs font-mono text-ink-soft truncate">
                      {activeDoc.source_file_name || "Source file unavailable"} · {formatPages(activeDoc)}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge status={activeDoc.review_status} />
                    <StatusBadge status={activeDoc.ocr_status} />
                    <StatusBadge status={activeDoc.mapping_status} />
                  </div>
                </div>
              </div>

              <FieldReviewSummary
                totalFields={currentDocStats.totalFields}
                missingCount={currentDocStats.missingCount}
                modifiedCount={currentFieldsDirty}
                reviewCount={currentDocStats.reviewCount}
                hasReviewMetadata={currentDocStats.hasReviewMetadata}
                activeFilter={fieldFilter}
                onFilterChange={setFieldFilter}
              />

              <div className="rounded-none border border-ink/15 bg-white p-5 md:p-6">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <p className="text-xs font-mono uppercase tracking-wide text-ink-soft">Extracted fields</p>
                  <button
                    type="button"
                    onClick={openFieldDialog}
                    className="inline-flex items-center gap-1.5 border border-ink/20 px-3 py-1.5 text-xs font-medium transition-colors hover:bg-paper-dim focus:outline-none focus:ring-2 focus:ring-folder-dark"
                  >
                    <Plus size={13} /> Add field
                  </button>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
                  {filteredFieldEntries.map((field) => (
                    <EditableEntityField
                      key={field.fieldKey}
                      fieldKey={field.fieldKey}
                      label={field.label}
                      value={field.value}
                      metadata={{ confidence: field.confidence, sourcePage: field.sourcePage, sourceLabel: field.sourceLabel, reviewNote: field.reviewNote }}
                      dirty={field.dirty}
                      missing={field.missing}
                      reviewRequired={field.reviewRequired}
                      menuOpen={fieldMenuOpen === field.fieldKey}
                      onToggleMenu={() => setFieldMenuOpen((prev) => (prev === field.fieldKey ? null : field.fieldKey))}
                      onChange={(nextValue) => setFieldValue(activeDoc.id, field.fieldKey, nextValue)}
                      onClear={() => { setFieldMenuOpen(null); setFieldValue(activeDoc.id, field.fieldKey, ""); }}
                      onDelete={() => { setFieldMenuOpen(null); confirmDeleteField(field.fieldKey); }}
                      disabled={statusSaving || retrying}
                    />
                  ))}
                  {filteredFieldEntries.length === 0 && (
                    <div className="rounded-none border border-dashed border-ink/20 px-4 py-8 text-center text-sm text-ink-soft md:col-span-2 xl:col-span-3 2xl:col-span-4">
                      No fields match this filter.
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs font-mono uppercase tracking-wide text-ink-soft flex items-center gap-1.5">
                    <Table2 size={13} /> Extracted tables ({activeDocSummary?.tablesForActive?.length || 0})
                  </p>
                  <button
                    type="button"
                    onClick={openTableDialog}
                    className="inline-flex items-center gap-1.5 border border-ink/20 px-3 py-1.5 text-xs font-medium transition-colors hover:bg-paper-dim focus:outline-none focus:ring-2 focus:ring-folder-dark"
                  >
                    <Plus size={13} /> Add table
                  </button>
                </div>

                {(activeDocSummary?.tablesForActive || []).length === 0 ? (
                  <div className="rounded-none border border-dashed border-ink/20 bg-white px-5 py-6 text-sm text-ink-soft">
                    No tables extracted for this document. Use Add table to create one manually.
                  </div>
                ) : (
                  <div className="space-y-6">
                    {(activeDocSummary?.tablesForActive || []).map((tbl, tableIndex) => {
                      const headers = tbl.headers || (tbl.rows?.[0] ? Object.keys(tbl.rows[0]) : []);
                      return (
                        <div key={`${tbl.table_name || "table"}-${tableIndex}`} className="rounded-none border border-ink/15 bg-white">
                          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-ink/10 bg-paper-dim/60 px-4 py-3">
                            <p className="truncate text-sm font-medium text-ink">
                              {tbl.table_name || tbl.table_name_or_purpose || `Table ${tableIndex + 1}`}
                            </p>
                            <div className="flex flex-wrap items-center gap-2">
                              <button
                                type="button"
                                onClick={() => openColumnDialog(tableIndex)}
                                className="inline-flex items-center gap-1 text-[11px] font-mono uppercase tracking-wide text-ink-soft hover:text-ink focus:outline-none focus:ring-2 focus:ring-folder-dark"
                              >
                                <Plus size={12} /> column
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  const currentTables = activeTables !== undefined ? activeTables : activeDoc.all_extracted_tables || [];
                                  const nextTables = currentTables.map((table, index) => {
                                    if (index !== tableIndex) return table;
                                    const blankRow = {};
                                    (table.headers || []).forEach((header) => { blankRow[header] = ""; });
                                    return { ...table, rows: [...(table.rows || []), blankRow] };
                                  });
                                  setEditedTables((prev) => ({ ...prev, [activeDoc.id]: nextTables }));
                                  setSaveState({ kind: "dirty" });
                                }}
                                className="inline-flex items-center gap-1 text-[11px] font-mono uppercase tracking-wide text-ink-soft hover:text-ink focus:outline-none focus:ring-2 focus:ring-folder-dark"
                              >
                                <Plus size={12} /> row
                              </button>
                              <button
                                type="button"
                                onClick={() => confirmDeleteTable(tableIndex)}
                                className="inline-flex items-center gap-1 text-[11px] font-mono uppercase tracking-wide text-ink-soft hover:text-stamp-red focus:outline-none focus:ring-2 focus:ring-folder-dark"
                                aria-label={`Delete table ${tableIndex + 1}`}
                              >
                                <X size={12} /> delete
                              </button>
                            </div>
                          </div>
                          <div className="overflow-x-auto scroll-thin">
                            <table className="w-full min-w-[620px] text-xs">
                              <thead>
                                <tr className="bg-paper-dim">
                                  {headers.map((header) => (
                                    <th key={header} className="whitespace-nowrap px-3 py-2 text-left font-mono uppercase tracking-wide text-ink-soft">
                                      <span className="inline-flex items-center gap-1.5">
                                        {titleCase(header)}
                                        <button
                                          type="button"
                                          onClick={() => confirmDeleteColumn(tableIndex, header)}
                                          className="rounded-none text-ink-soft/40 hover:text-stamp-red focus:outline-none focus:ring-2 focus:ring-folder-dark"
                                          aria-label={`Delete column ${titleCase(header)}`}
                                        >
                                          <X size={11} />
                                        </button>
                                      </span>
                                    </th>
                                  ))}
                                  <th className="w-8" />
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-ink/10">
                                {(tbl.rows || []).map((row, rowIndex) => (
                                  <tr key={rowIndex} className="even:bg-paper/40">
                                    {headers.map((header) => (
                                      <td key={header} className="px-1.5 py-1.5 align-top text-ink">
                                        <input
                                          value={row[header] ?? ""}
                                          onChange={(e) => {
                                            const currentTables = activeTables !== undefined ? activeTables : activeDoc.all_extracted_tables || [];
                                            const nextTables = currentTables.map((table, index) => {
                                              if (index !== tableIndex) return table;
                                              const nextRows = (table.rows || []).map((existingRow, existingIndex) => existingIndex === rowIndex ? { ...existingRow, [header]: e.target.value } : { ...existingRow });
                                              return { ...table, rows: nextRows };
                                            });
                                            setEditedTables((prev) => ({ ...prev, [activeDoc.id]: nextTables }));
                                            setSaveState({ kind: "dirty" });
                                          }}
                                          className="w-full min-w-[92px] border border-transparent bg-transparent px-1.5 py-1 text-xs focus:border-folder-dark focus:outline-none focus:ring-1 focus:ring-folder-dark"
                                        />
                                      </td>
                                    ))}
                                    <td className="px-1.5 py-1.5 align-top">
                                      <button
                                        type="button"
                                        onClick={() => confirmDeleteRow(tableIndex, rowIndex)}
                                        className="rounded-none text-ink-soft/40 hover:text-stamp-red focus:outline-none focus:ring-2 focus:ring-folder-dark"
                                        aria-label={`Delete row ${rowIndex + 1}`}
                                      >
                                        <X size={12} />
                                      </button>
                                    </td>
                                  </tr>
                                ))}
                                {(tbl.rows || []).length === 0 && (
                                  <tr>
                                    <td colSpan={headers.length + 1} className="px-3 py-3 italic text-ink-soft">
                                      No rows yet. Use the row action above to add one.
                                    </td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center border border-dashed border-ink/20 bg-white px-6 py-16 text-center text-ink-soft">
              <ScanLine size={28} className="mb-3 text-folder-dark" />
              <p className="text-sm">Select a document to review its extracted fields.</p>
            </div>
          )}
        </div>
      </div>

      {dialog?.kind === "confirm" && (
        <ConfirmationDialog open title={dialog.title} description={dialog.description} actions={dialog.actions} onCancel={() => setDialog(null)} />
      )}

      {dialog?.kind === "form" && (
        <FormDialog
          open
          title={dialog.title}
          description={dialog.description}
          fields={dialog.fields}
          confirmLabel={dialog.confirmLabel}
          onSubmit={dialog.onSubmit}
          onCancel={() => setDialog(null)}
        />
      )}
    </PageContainer>
  );
}











