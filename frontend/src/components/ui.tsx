import { useId, useState, type ReactNode } from "react";
import { CONFIDENCE_STYLE } from "../theme";

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-3 p-6 text-sm text-slate-600">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-oi-blue" aria-hidden />
      {label}…
    </div>
  );
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-900">
      <p className="font-semibold">Something went wrong</p>
      <p className="mt-1">{message}</p>
      {onRetry && <button className="btn-secondary mt-3" onClick={onRetry}>Try again</button>}
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-600">
      <p className="font-semibold text-slate-800">{title}</p>
      {children && <div className="mt-1">{children}</div>}
    </div>
  );
}

export function ConfidenceBadge({ level }: { level: "High" | "Medium" | "Low" | undefined }) {
  if (!level) return <span className="text-xs text-slate-400">-</span>;
  const s = CONFIDENCE_STYLE[level];
  return (
    <span title={s.help} className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-semibold ${s.cls}`}>
      <span aria-hidden>{s.icon}</span>
      {level}
      <span className="sr-only">confidence. {s.help}</span>
    </span>
  );
}

/** Keyboard-accessible tooltip: hover or focus the (i) button. */
export function Tooltip({ text, label = "More information" }: { text: string; label?: string }) {
  const id = useId();
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-block align-middle">
      <button
        type="button"
        aria-label={label}
        aria-describedby={open ? id : undefined}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onKeyDown={(e) => e.key === "Escape" && setOpen(false)}
        className="ml-1 inline-flex h-5 w-5 items-center justify-center rounded-full border border-slate-400 text-[11px] font-bold text-slate-600 hover:bg-slate-100"
      >
        i
      </button>
      {open && (
        <span id={id} role="tooltip" className="absolute left-1/2 top-6 z-30 w-64 -translate-x-1/2 rounded-md bg-navy-900 p-2 text-xs font-normal leading-snug text-white shadow-lg">
          {text}
        </span>
      )}
    </span>
  );
}

export function Disclaimer() {
  return (
    <p className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900" role="note">
      <strong>Data note:</strong> material values are typical figures stored as ranges and are flagged "needs verification".
      Spot-check them against supplier datasheets before relying on a result.
    </p>
  );
}
