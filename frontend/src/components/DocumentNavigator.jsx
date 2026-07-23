export default function DocumentNavigator({ items, activeId, onSelect }) {
  return (
    <div className="lg:w-72 xl:w-80 shrink-0">
      <p className="text-[10px] font-mono uppercase tracking-wide text-ink-soft/70 mb-2 px-1 hidden lg:block">
        {items.length} document{items.length !== 1 ? "s" : ""}
      </p>
      <div className="flex lg:flex-col gap-1.5 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0 scroll-thin">
        {items.map((item) => {
          const active = item.id === activeId;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect(item.id)}
              aria-current={active ? "page" : undefined}
              className={`min-w-[190px] shrink-0 text-left rounded-none border-l-[3px] px-3.5 py-2.5 transition-colors focus:outline-none focus:ring-2 focus:ring-folder-dark lg:min-w-0 ${
                active
                  ? "bg-ink text-paper border-folder-dark"
                  : "bg-white/70 text-ink-soft hover:bg-folder/15 hover:text-ink border-transparent"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-medium leading-tight">{item.label}</p>
                  <p className={`mt-0.5 text-[10px] font-mono ${active ? "text-paper/70" : "text-ink-soft"}`}>
                    {item.pageLabel}
                  </p>
                </div>
                {item.reviewCount > 0 && (
                  <span className={`shrink-0 text-[10px] font-mono uppercase tracking-wide ${active ? "text-folder" : "text-stamp-red"}`}>
                    {item.reviewCount} review
                  </span>
                )}
              </div>
              <div className="mt-2 space-y-1 text-[10px] font-mono uppercase tracking-wide">
                <p className={active ? "text-paper/75" : "text-ink-soft"}>
                  {item.fieldCount} field{item.fieldCount === 1 ? "" : "s"}
                </p>
                {item.missingCount > 0 && (
                  <p className={active ? "text-paper/75" : "text-stamp-red"}>
                    {item.missingCount} missing
                  </p>
                )}
                <p className={active ? "text-paper/75" : "text-ink-soft"}>
                  OCR {item.ocrStatusText}
                </p>
                <p className={active ? "text-paper/75" : "text-ink-soft"}>
                  Review {item.reviewStatusText}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}




