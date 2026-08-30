import { useEffect, type Dispatch, type SetStateAction } from "react";
import { CheckCircle2, AlertCircle, Info, X } from "../icons";
import { cn } from "./cn";

// H.4.6: single owned Toast abstraction. Stable project-level surface.
// Error-only in practice (per Empty/Loading/Error States) but built
// generically with severity variants so the call site decides.
export type ToastSeverity = "info" | "success" | "error";

export interface ToastItem {
  id: string;
  severity: ToastSeverity;
  message: string;
  durationMs?: number;
}

interface ToastViewportProps {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}

export function ToastViewport({ toasts, onDismiss }: ToastViewportProps) {
  return (
    <div
      role="region"
      aria-label="Notifications"
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm"
    >
      {toasts.map((t) => (
        <ToastCard key={t.id} item={t} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

function ToastCard({
  item,
  onDismiss,
}: {
  item: ToastItem;
  onDismiss: (id: string) => void;
}) {
  useEffect(() => {
    const ms = item.durationMs ?? 5000;
    const timer = setTimeout(() => onDismiss(item.id), ms);
    return () => clearTimeout(timer);
  }, [item.id, item.durationMs, onDismiss]);

  const Icon =
    item.severity === "success"
      ? CheckCircle2
      : item.severity === "error"
        ? AlertCircle
        : Info;

  const iconColor =
    item.severity === "error"
      ? "var(--risk-critical)"
      : item.severity === "success"
        ? "var(--status-safe)"
        : "var(--accent-cyan)";

  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-3",
        "p-3 pr-2",
        "bg-[var(--bg-elevated)]",
        "border border-[var(--border-strong)]",
        "rounded-[var(--radius-card)]",
      )}
    >
      <Icon style={{ color: iconColor }} className="mt-0.5 flex-shrink-0" aria-hidden />
      <p className="flex-1 text-[0.8125rem] text-[var(--text-primary)]">
        {item.message}
      </p>
      <button
        onClick={() => onDismiss(item.id)}
        aria-label="Dismiss"
        className="p-0.5 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)]"
      >
        <X aria-hidden />
      </button>
    </div>
  );
}

// Lightweight bridge: chrome mounts ToastViewport, features call
// pushToast from anywhere via the module-level dispatcher.
let _push: ((t: Omit<ToastItem, "id">) => void) | null = null;
let _idCounter = 0;

export function useToastBridge(
  setExternalToasts: Dispatch<SetStateAction<ToastItem[]>>,
) {
  useEffect(() => {
    _push = (t) => {
      _idCounter += 1;
      const id = `toast-${_idCounter}`;
      setExternalToasts((curr) => [...curr, { ...t, id }]);
    };
    return () => {
      _push = null;
    };
  }, [setExternalToasts]);
}

export function pushToast(t: Omit<ToastItem, "id">): void {
  if (_push) {
    _push(t);
  } else if (typeof console !== "undefined") {
    console.warn("toast: bridge not mounted, message dropped:", t.message);
  }
}

// Silence unused-import warning if a file imports only the type.
// (no-op)
