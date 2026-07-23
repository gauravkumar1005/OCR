import StatusBadge from "./StatusBadge.jsx";

function StatusLine({ label, value, emptyLabel = "Not available" }) {
  return (
    <div className="rounded-none border border-ink/15 bg-white px-4 py-3">
      <p className="text-[10px] font-mono uppercase tracking-wide text-ink-soft">{label}</p>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        {value ? (
          <StatusBadge status={value} />
        ) : (
          <span className="text-sm text-ink-soft">{emptyLabel}</span>
        )}
      </div>
    </div>
  );
}

export default function ReviewStatusSummary({ claimStatus, ocrStatus, mappingStatus, reviewStatus }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
      <StatusLine label="Claim Status" value={claimStatus} />
      <StatusLine label="OCR Status" value={ocrStatus} />
      <StatusLine label="Mapping Status" value={mappingStatus} />
      <StatusLine label="Review Status" value={reviewStatus === "pending" ? "Review pending" : reviewStatus} />
    </div>
  );
}
