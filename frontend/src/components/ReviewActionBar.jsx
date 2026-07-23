export default function ReviewActionBar({
  dirtyCount,
  tablesDirty,
  saving,
  tablesSaving,
  saveDisabled,
  claimStatus,
  onSave,
  onRequestStatus,
  onRetry,
  retrying,
  canRetry,
  statusLocked,
}) {
  return (
    <div className="rounded-none border border-ink/15 bg-white px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-mono uppercase tracking-wide text-ink-soft">Review actions</p>
          <p className="mt-1 text-sm text-ink-soft">
            {saving || tablesSaving
              ? "Saving…"
              : dirtyCount > 0 || tablesDirty
              ? `${dirtyCount > 0 ? `${dirtyCount} unsaved field change${dirtyCount === 1 ? "" : "s"}` : "No unsaved field changes"}${tablesDirty ? " · table changes pending" : ""}`
              : "All changes saved"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onSave}
            disabled={saveDisabled}
            className="px-4 py-2 text-sm font-medium bg-ink text-paper transition-colors hover:bg-ink-soft focus:outline-none focus:ring-2 focus:ring-folder-dark disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving || tablesSaving ? "Saving…" : dirtyCount > 0 || tablesDirty ? "Save current changes" : "All changes saved"}
          </button>
          <button
            type="button"
            onClick={() => onRequestStatus("reviewed")}
            disabled={statusLocked}
            className="px-4 py-2 text-sm font-medium border border-ink/20 text-ink transition-colors hover:bg-paper-dim focus:outline-none focus:ring-2 focus:ring-folder-dark disabled:cursor-not-allowed disabled:opacity-50"
          >
            Mark reviewed
          </button>
          <button
            type="button"
            onClick={() => onRequestStatus("processing")}
            disabled={statusLocked}
            className="px-4 py-2 text-sm font-medium border border-ink/20 text-ink transition-colors hover:bg-paper-dim focus:outline-none focus:ring-2 focus:ring-folder-dark disabled:cursor-not-allowed disabled:opacity-50"
          >
            Send to processing
          </button>
          {canRetry && (
            <button
              type="button"
              onClick={onRetry}
              disabled={statusLocked || retrying}
              className="px-4 py-2 text-sm font-medium border border-stamp-red/30 text-stamp-red transition-colors hover:bg-stamp-red-soft focus:outline-none focus:ring-2 focus:ring-folder-dark disabled:cursor-not-allowed disabled:opacity-50"
            >
              {retrying ? "Retrying…" : "Retry processing"}
            </button>
          )}
        </div>
      </div>
      {statusLocked && (
        <p className="mt-2 text-xs text-ink-soft">
          Save or discard the current document changes before changing claim status.
        </p>
      )}
      <p className="mt-1 text-xs text-ink-soft">
        Current claim status: <span className="font-mono uppercase tracking-wide">{claimStatus || "Not available"}</span>
      </p>
    </div>
  );
}
