import { MoreVertical } from "lucide-react";

export default function EditableEntityField({
  label,
  value,
  metadata,
  dirty,
  missing,
  reviewRequired,
  menuOpen,
  onToggleMenu,
  onChange,
  onClear,
  onDelete,
  disabled,
}) {
  const confidence = metadata?.confidence;
  const confidenceLabel =
    typeof confidence === "number"
      ? confidence >= 0 && confidence <= 1
        ? Math.round(confidence * 100)
        : Math.round(confidence)
      : null;
  const sourcePage = metadata?.sourcePage;
  const sourceLabel = metadata?.sourceLabel;
  const reviewNote = metadata?.reviewNote;

  let confidenceTone = null;
  if (confidenceLabel !== null) {
    if (confidenceLabel >= 90) confidenceTone = "High confidence";
    else if (confidenceLabel >= 75) confidenceTone = "Review recommended";
    else confidenceTone = "Needs attention";
  }

  return (
    <div className={`relative rounded-none border p-4 ${dirty ? "border-folder-dark bg-folder/10" : missing ? "border-stamp-red/30 bg-white" : "border-ink/15 bg-white"}`}>
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-start gap-2">
            <label className="min-w-0 flex-1">
              <span className="block text-[11px] font-mono uppercase tracking-wide text-ink-soft/80">
                {label}
              </span>
            </label>
            <button
              type="button"
              onClick={onToggleMenu}
              aria-label={`Field actions for ${label}`}
              className="rounded-none p-1.5 text-ink-soft transition-colors hover:bg-ink/5 hover:text-ink focus:outline-none focus:ring-2 focus:ring-folder-dark"
            >
              <MoreVertical size={15} />
            </button>
          </div>

          <input
            value={value ?? ""}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            title={typeof value === "string" ? value : undefined}
            placeholder={missing ? "Not extracted — enter manually" : ""}
            className={`mt-2 w-full border px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-folder-dark disabled:cursor-not-allowed ${
              dirty
                ? "border-folder-dark bg-white"
                : missing
                ? "border-stamp-red/30 bg-white"
                : "border-ink/15 bg-white"
            }`}
          />

          <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] font-mono uppercase tracking-wide">
            {dirty && <span className="text-folder-dark">Modified</span>}
            {missing && <span className="text-stamp-red">Missing</span>}
            {reviewRequired && <span className="text-amber">Needs review</span>}
            {confidenceLabel !== null && (
              <span className="text-ink-soft">
                Confidence {confidenceLabel}%{confidenceTone ? ` · ${confidenceTone}` : ""}
              </span>
            )}
            {sourcePage != null && <span className="text-ink-soft">Page {sourcePage}</span>}
            {sourceLabel && <span className="text-ink-soft truncate">{sourceLabel}</span>}
            {reviewNote && <span className="text-stamp-red truncate">{reviewNote}</span>}
          </div>
        </div>
      </div>

      {menuOpen && (
        <div className="absolute right-3 top-11 z-20 w-44 border border-ink/15 bg-paper shadow-lg">
          <button
            type="button"
            onClick={onClear}
            disabled={disabled}
            className="block w-full px-3 py-2 text-left text-sm text-ink hover:bg-paper-dim focus:outline-none focus:bg-paper-dim disabled:opacity-50"
          >
            Clear value
          </button>
          <button
            type="button"
            onClick={onDelete}
            disabled={disabled}
            className="block w-full px-3 py-2 text-left text-sm text-stamp-red hover:bg-stamp-red-soft focus:outline-none focus:bg-stamp-red-soft disabled:opacity-50"
          >
            Delete field
          </button>
        </div>
      )}
    </div>
  );
}
