export default function FieldReviewSummary({
  totalFields,
  missingCount,
  modifiedCount,
  reviewCount,
  hasReviewMetadata,
  activeFilter,
  onFilterChange,
}) {
  const filters = [
    { key: "all", label: "All Fields" },
    { key: "missing", label: `Missing (${missingCount})`, disabled: missingCount === 0 },
    { key: "modified", label: `Modified (${modifiedCount})`, disabled: modifiedCount === 0 },
  ];

  if (hasReviewMetadata) {
    filters.push({ key: "review", label: `Needs Review (${reviewCount})`, disabled: reviewCount === 0 });
  }

  return (
    <div className="rounded-none border border-ink/15 bg-white px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-ink-soft">
          {totalFields} field{totalFields === 1 ? "" : "s"} · {missingCount} missing · {modifiedCount} modified
          {hasReviewMetadata ? ` · ${reviewCount} need review` : ""}
        </p>
        <div className="flex flex-wrap gap-2">
          {filters.map((filter) => {
            const active = activeFilter === filter.key;
            return (
              <button
                key={filter.key}
                type="button"
                disabled={filter.disabled}
                onClick={() => onFilterChange(filter.key)}
                className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wide border transition-colors focus:outline-none focus:ring-2 focus:ring-folder-dark disabled:opacity-40 ${
                  active
                    ? "bg-ink text-paper border-ink"
                    : "border-ink/20 text-ink-soft hover:border-ink/40"
                }`}
              >
                {filter.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
