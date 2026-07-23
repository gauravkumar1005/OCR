export default function ReviewToast({ tone = "success", title, message, actionLabel, onAction, onClose }) {
  const tones = {
    success: "border-verify-green/30 bg-verify-green-soft text-verify-green",
    error: "border-stamp-red/30 bg-stamp-red-soft text-stamp-red",
    neutral: "border-ink/15 bg-white text-ink",
  };

  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      aria-live="polite"
      className={`flex items-start justify-between gap-4 border px-4 py-3 text-sm shadow-sm ${tones[tone] || tones.neutral}`}
    >
      <div>
        {title && <p className="font-medium">{title}</p>}
        {message && <p className={title ? "mt-1 text-sm" : ""}>{message}</p>}
      </div>
      <div className="flex items-center gap-2">
        {actionLabel && onAction && (
          <button
            type="button"
            onClick={onAction}
            className="text-xs font-medium underline underline-offset-2"
          >
            {actionLabel}
          </button>
        )}
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="text-xs font-medium uppercase tracking-wide opacity-70 hover:opacity-100"
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
}
