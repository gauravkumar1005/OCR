import { useEffect, useMemo, useRef, useState } from "react";
import { X } from "lucide-react";

function DialogShell({ open, title, description, children, actions, onClose, wide = false }) {
  const panelRef = useRef(null);
  const previousFocusRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    previousFocusRef.current = document.activeElement;
    const id = window.requestAnimationFrame(() => {
      panelRef.current?.focus();
    });
    const onKeyDown = (e) => {
      if (e.key === "Escape") onClose?.();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.cancelAnimationFrame(id);
      window.removeEventListener("keydown", onKeyDown);
      const prev = previousFocusRef.current;
      if (prev && typeof prev.focus === "function") {
        window.requestAnimationFrame(() => prev.focus());
      }
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4 py-6">
      <button
        type="button"
        aria-label="Close dialog backdrop"
        className="absolute inset-0 bg-ink/35"
        onClick={onClose}
      />
      <div
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="review-dialog-title"
        aria-describedby={description ? "review-dialog-description" : undefined}
        className={`relative w-full ${wide ? "max-w-2xl" : "max-w-lg"} border border-ink/15 bg-paper shadow-xl outline-none`}
      >
        <div className="flex items-start justify-between gap-4 border-b border-ink/10 px-5 py-4">
          <div className="min-w-0">
            <h2 id="review-dialog-title" className="font-display text-xl text-ink">
              {title}
            </h2>
            {description && (
              <p id="review-dialog-description" className="mt-1 text-sm text-ink-soft">
                {description}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1.5 text-ink-soft transition-colors hover:bg-ink/5 hover:text-ink focus:outline-none focus:ring-2 focus:ring-folder-dark"
            aria-label="Close dialog"
          >
            <X size={16} />
          </button>
        </div>
        <div className="px-5 py-4">{children}</div>
        <div className="flex flex-wrap justify-end gap-2 border-t border-ink/10 px-5 py-4 bg-paper-dim/40">
          {actions?.map((action) => (
            <button
              key={action.label}
              type="button"
              onClick={action.onClick}
              disabled={action.disabled}
              className={`px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-folder-dark disabled:opacity-50 disabled:cursor-not-allowed ${
                action.tone === "danger"
                  ? "bg-stamp-red text-paper hover:bg-stamp-red/90"
                  : action.tone === "primary"
                  ? "bg-ink text-paper hover:bg-ink-soft"
                  : "border border-ink/20 text-ink hover:bg-white"
              }`}
              autoFocus={action.autoFocus}
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export function ConfirmationDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  tone = "danger",
  onConfirm,
  onCancel,
  busy = false,
  actions,
}) {
  const resolvedActions = actions || [
    { label: cancelLabel, tone: "neutral", onClick: onCancel },
    { label: confirmLabel, tone, onClick: onConfirm, disabled: busy, autoFocus: true },
  ];

  return (
    <DialogShell open={open} title={title} description={description} actions={resolvedActions} onClose={onCancel} />
  );
}

export function FormDialog({
  open,
  title,
  description,
  fields,
  confirmLabel = "Save",
  cancelLabel = "Cancel",
  onSubmit,
  onCancel,
  busy = false,
}) {
  const initialValues = useMemo(() => {
    const values = {};
    for (const field of fields || []) values[field.name] = field.defaultValue ?? "";
    return values;
  }, [fields]);
  const [values, setValues] = useState(initialValues);

  useEffect(() => {
    if (open) setValues(initialValues);
  }, [open, initialValues]);

  const submit = () => onSubmit?.(values);

  return (
    <DialogShell
      open={open}
      title={title}
      description={description}
      wide
      onClose={onCancel}
      actions={[
        { label: cancelLabel, tone: "neutral", onClick: onCancel },
        { label: confirmLabel, tone: "primary", onClick: submit, disabled: busy, autoFocus: true },
      ]}
    >
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        {fields?.map((field) => (
          <label key={field.name} className="block">
            <span className="mb-1 block text-xs font-mono uppercase tracking-wide text-ink-soft">
              {field.label}
            </span>
            {field.multiline ? (
              <textarea
                value={values[field.name]}
                onChange={(e) => setValues((prev) => ({ ...prev, [field.name]: e.target.value }))}
                rows={field.rows || 4}
                placeholder={field.placeholder}
                className="w-full border border-ink/20 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-folder-dark"
              />
            ) : (
              <input
                type={field.type || "text"}
                value={values[field.name]}
                onChange={(e) => setValues((prev) => ({ ...prev, [field.name]: e.target.value }))}
                placeholder={field.placeholder}
                className="w-full border border-ink/20 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-folder-dark"
              />
            )}
          </label>
        ))}
      </form>
    </DialogShell>
  );
}
