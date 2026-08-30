// Phase 8 - features/defend/transaction-builder-form.tsx
// The transaction builder form. Per the Phase 8 spec: react-hook-form
// + zod. 7 visible fields (amount, hour_of_day, channel, new_device,
// tx_last_1hr, device_trust_age_days, count_30d), plus a collapsed
// "Advanced fields" disclosure with the remaining 16 fields, plus a
// "Load a transaction I just generated" link visible only when
// useAppStore().lastGeneratedTransaction is set. Two variants:
// "full" (the /defend page) and "compact" (the Home mini).

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
// (Removed unused useAppStore import - was tracked here as a
// potential future need for the store's lastGeneratedTransaction,
// but the actual implementation uses useLastGeneratedTransaction
// from ./use-defend instead. Keeping the file clean for the
// Phase 9 build verification.)
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { FEATURE_COLS, CAT_COLS } from "../../lib/constants";
import { Input, Select, Button } from "../../design-system/primitives";
import {
  ChevronDown,
  ChevronUp,
  Loader2,
  Sparkles,
  AlertCircle,
  Wand2,
} from "../../design-system/icons";
import { useLastGeneratedTransaction } from "./use-defend";
import type { TransactionRowWithId } from "../../lib/api/types";

const CHANNELS = ["online", "pos", "atm", "mobile"] as const;

const DEFAULT_ADVANCED = {
  account_age_days: 365,
  tx_last_1min: 0,
  tx_last_24hr: 5,
  amount_zscore_30d: 0.0,
  new_merchant: 0 as const,
  merchant_cat_freq_user: 0.5,
  time_since_last_s: 3600,
  dist_from_prev_km: 0.0,
  geo_velocity_kmh: 0.0,
  three_ds_failures_before_result: 0,
  three_ds_failures_last_30d: 0,
  burst_count_10m: 0,
  is_high_amount_burst: 0 as const,
  inter_transaction_time_s: 3600,
  merchant_category: "grocery",
  three_ds_result: "passed_first_try",
} as const;

const DEFAULT_PRIMARY = {
  amount: 120,
  hour_of_day: 12,
  channel: "card_present",
  new_device: 0 as const,
  tx_last_1hr: 1,
  device_trust_age_days: 30,
  count_30d: 50,
} as const;

const primarySchema = z.object({
  amount: z.coerce.number().positive("Amount must be > 0"),
  hour_of_day: z.coerce.number().int().min(0).max(23, "0-23"),
  channel: z.string().min(1),
  new_device: z.coerce.number().int().min(0).max(1),
  tx_last_1hr: z.coerce.number().int().min(0),
  device_trust_age_days: z.coerce.number().int().min(0),
  count_30d: z.coerce.number().int().min(0),
});
type PrimaryForm = z.infer<typeof primarySchema>;

type Variant = "full" | "compact";

interface TransactionBuilderFormProps {
  onSubmit?: (tx: TransactionRowWithId) => void;
  variant?: Variant;
  showAdvanced?: boolean;
  defaultValues?: Partial<TransactionRowWithId>;
}

// Advanced state is typed as a writable superset of DEFAULT_ADVANCED
// (the literal-typed `typeof DEFAULT_ADVANCED` makes the useState
// setter require matching the literal types, which breaks when we
// spread `lastGenerated` over it - lastGenerated has wider numeric
// types). Defined at module scope so buildRow and AdvancedFields
// can share the same type.
type AdvancedState = {
  account_age_days: number;
  tx_last_1min: number;
  tx_last_24hr: number;
  amount_zscore_30d: number;
  new_merchant: 0 | 1;
  merchant_cat_freq_user: number;
  time_since_last_s: number;
  dist_from_prev_km: number;
  geo_velocity_kmh: number;
  three_ds_failures_before_result: number;
  three_ds_failures_last_30d: number;
  burst_count_10m: number;
  is_high_amount_burst: 0 | 1;
  inter_transaction_time_s: number;
  merchant_category: string;
  three_ds_result: string;
  [k: string]: unknown;
};

function buildRow(
  primary: PrimaryForm,
  advanced: AdvancedState = DEFAULT_ADVANCED as unknown as AdvancedState,
  transaction_id?: string,
): TransactionRowWithId {
  return {
    ...advanced,
    ...primary,
    new_device: primary.new_device as 0 | 1,
    new_merchant: advanced.new_merchant,
    is_high_amount_burst: advanced.is_high_amount_burst,
    merchant_category: advanced.merchant_category,
    three_ds_result: advanced.three_ds_result,
    ...(transaction_id ? { transaction_id } : {}),
  };
}

export function TransactionBuilderForm({
  onSubmit,
  variant = "full",
  showAdvanced,
  defaultValues,
}: TransactionBuilderFormProps) {
  const isCompact = variant === "compact";
  const showAdv = showAdvanced ?? !isCompact;
  const lastGenerated = useLastGeneratedTransaction();

  const initialPrimary: PrimaryForm = {
    amount: defaultValues?.amount ?? lastGenerated?.amount ?? DEFAULT_PRIMARY.amount,
    hour_of_day: defaultValues?.hour_of_day ?? lastGenerated?.hour_of_day ?? DEFAULT_PRIMARY.hour_of_day,
    channel: defaultValues?.channel ?? lastGenerated?.channel ?? DEFAULT_PRIMARY.channel,
    new_device: (defaultValues?.new_device ?? lastGenerated?.new_device ?? DEFAULT_PRIMARY.new_device) as 0 | 1,
    tx_last_1hr: defaultValues?.tx_last_1hr ?? lastGenerated?.tx_last_1hr ?? DEFAULT_PRIMARY.tx_last_1hr,
    device_trust_age_days: defaultValues?.device_trust_age_days ?? lastGenerated?.device_trust_age_days ?? DEFAULT_PRIMARY.device_trust_age_days,
    count_30d: defaultValues?.count_30d ?? lastGenerated?.count_30d ?? DEFAULT_PRIMARY.count_30d,
  };

  const form = useForm<PrimaryForm>({
    resolver: zodResolver(primarySchema),
    defaultValues: initialPrimary,
  });

  // Advanced state is typed as a writable superset of DEFAULT_ADVANCED
  // (the literal-typed `typeof DEFAULT_ADVANCED` would make this
  // useState's setter require matching the literal types, which
  // breaks when we spread `lastGenerated` over it - lastGenerated
  // has wider numeric types).
  const [advancedState, setAdvancedState] = useState<AdvancedState>(() => ({
    ...DEFAULT_ADVANCED,
    ...(lastGenerated ?? {}),
  }));

  const [formKey, setFormKey] = useState(0);
  useEffect(() => {
    if (defaultValues) {
      form.reset({
        amount: defaultValues.amount ?? DEFAULT_PRIMARY.amount,
        hour_of_day: defaultValues.hour_of_day ?? DEFAULT_PRIMARY.hour_of_day,
        channel: defaultValues.channel ?? DEFAULT_PRIMARY.channel,
        new_device: (defaultValues.new_device ?? DEFAULT_PRIMARY.new_device) as 0 | 1,
        tx_last_1hr: defaultValues.tx_last_1hr ?? DEFAULT_PRIMARY.tx_last_1hr,
        device_trust_age_days: defaultValues.device_trust_age_days ?? DEFAULT_PRIMARY.device_trust_age_days,
        count_30d: defaultValues.count_30d ?? DEFAULT_PRIMARY.count_30d,
      });
      setAdvancedState((cur) => ({ ...cur, ...defaultValues }));
      setFormKey((k) => k + 1);
      return;
    }
    // Cross-page handoff: when lastGenerated transitions from null
    // to a populated value (the Generate page set the store, then
    // the user navigated to /defend), re-init the form. This
    // covers the case where useForm was called before the store
    // was populated. We track the last-seen transaction id so we
    // only fire once per new generated transaction.
    if (lastGenerated?.transaction_id) {
      form.reset({
        amount: lastGenerated.amount,
        hour_of_day: lastGenerated.hour_of_day,
        channel: lastGenerated.channel,
        new_device: lastGenerated.new_device as 0 | 1,
        tx_last_1hr: lastGenerated.tx_last_1hr,
        device_trust_age_days: lastGenerated.device_trust_age_days,
        count_30d: lastGenerated.count_30d,
      });
      setAdvancedState((cur) => ({ ...cur, ...lastGenerated }));
      setFormKey((k) => k + 1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultValues, lastGenerated?.transaction_id]);

  function handleLoadGenerated() {
    if (!lastGenerated) return;
    form.reset({
      amount: lastGenerated.amount,
      hour_of_day: lastGenerated.hour_of_day,
      channel: lastGenerated.channel,
      new_device: lastGenerated.new_device as 0 | 1,
      tx_last_1hr: lastGenerated.tx_last_1hr,
      device_trust_age_days: lastGenerated.device_trust_age_days,
      count_30d: lastGenerated.count_30d,
    });
    setAdvancedState((cur) => ({ ...cur, ...lastGenerated }));
    setFormKey((k) => k + 1);
  }

  function handleSubmit(values: PrimaryForm) {
    const row = buildRow(values, advancedState, lastGenerated?.transaction_id);
    onSubmit?.(row);
  }

  return (
    <form
      key={formKey}
      onSubmit={form.handleSubmit(handleSubmit)}
      className="space-y-4"
      noValidate
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Field label="Amount" htmlFor="tx-amount" error={form.formState.errors.amount?.message}>
          <Input id="tx-amount" type="number" step="0.01" {...form.register("amount")} aria-label="Amount" />
        </Field>
        <Field label="Hour of day (0-23)" htmlFor="tx-hour" error={form.formState.errors.hour_of_day?.message}>
          <Input id="tx-hour" type="number" min={0} max={23} step={1} {...form.register("hour_of_day")} aria-label="Hour of day" />
        </Field>
        <Field label="Channel" htmlFor="tx-channel" error={form.formState.errors.channel?.message}>
          <Select id="tx-channel" {...form.register("channel")} aria-label="Channel">
            {CHANNELS.map((c) => <option key={c} value={c}>{c}</option>)}
          </Select>
        </Field>
        {!isCompact && (
          <>
            <Field label="New device (0/1)" htmlFor="tx-new-device" error={form.formState.errors.new_device?.message}>
              <Input id="tx-new-device" type="number" min={0} max={1} step={1} {...form.register("new_device")} aria-label="New device" />
            </Field>
            <Field label="tx last 1hr" htmlFor="tx-last-1hr" error={form.formState.errors.tx_last_1hr?.message}>
              <Input id="tx-last-1hr" type="number" min={0} step={1} {...form.register("tx_last_1hr")} aria-label="tx last 1hr" />
            </Field>
            <Field label="device trust age (days)" htmlFor="tx-device-trust" error={form.formState.errors.device_trust_age_days?.message}>
              <Input id="tx-device-trust" type="number" min={0} step={1} {...form.register("device_trust_age_days")} aria-label="device trust age (days)" />
            </Field>
            <Field label="count 30d" htmlFor="tx-count-30d" error={form.formState.errors.count_30d?.message}>
              <Input id="tx-count-30d" type="number" min={0} step={1} {...form.register("count_30d")} aria-label="count 30d" />
            </Field>
          </>
        )}
      </div>

      {showAdv && !isCompact && (
        <AdvancedFields values={advancedState} onChange={setAdvancedState} />
      )}

      <div className="flex flex-wrap items-center gap-2 pt-1">
        <Button type="submit" variant="primary" size={isCompact ? "sm" : "md"} disabled={form.formState.isSubmitting} aria-label="Predict">
          {form.formState.isSubmitting ? <Loader2 aria-hidden /> : <Sparkles aria-hidden />}
          {isCompact ? "Predict" : "Predict \u2192"}
        </Button>
        {!isCompact && lastGenerated && (
          <Button type="button" variant="secondary" size="md" onClick={handleLoadGenerated} aria-label="Load a transaction I just generated">
            <Wand2 aria-hidden />
            Load a transaction I just generated
          </Button>
        )}
        {!isCompact && lastGenerated && (
          <span className="text-[0.625rem] font-mono text-[var(--text-muted)]">
            pre-fill from {lastGenerated.transaction_id ?? "last generate"}
          </span>
        )}
      </div>
    </form>
  );
}

function Field({ label, htmlFor, error, children }: { label: string; htmlFor?: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
        {label}
      </label>
      {children}
      {error && (
        <p className="text-[0.6875rem] text-[var(--risk-critical)] flex items-center gap-1">
          <AlertCircle aria-hidden size="inline" />
          {error}
        </p>
      )}
    </div>
  );
}

function AdvancedFields({ values, onChange: _onChange }: { values: AdvancedState; onChange: (next: AdvancedState) => void }) {
  const [open, setOpen] = useState(false);
  const reduceMotion = useReducedMotion();
  return (
    <div className="rounded-[var(--radius-input)] border border-[var(--border-subtle)] bg-[var(--bg-base)] overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls="advanced-fields-panel"
        className="w-full flex items-center justify-between px-3 py-2 text-left text-[0.75rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors"
      >
        <span>Advanced fields (using dataset medians) - click to inspect</span>
        {open ? <ChevronUp aria-hidden size="inline" /> : <ChevronDown aria-hidden size="inline" />}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id="advanced-fields-panel"
            key="advanced-fields-panel"
            // Phase 9.5 step 5: Motion `layout` makes the 7-field
            // -> 23-field expansion feel intentional rather than an
            // abrupt height jump. Use case mapping: H.71 §F
            // ("Defend - apply Motion `layout` to the advanced-fields
            // disclosure so the 7-field -> 23-field expansion reads
            // as intentional rather than an abrupt jump"). Reduced
            // motion keeps the instant-open behavior (no transition
            // duration) so the disclosure still expands immediately
            // for users who request it.
            layout={!reduceMotion}
            initial={reduceMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={reduceMotion ? { opacity: 1 } : { opacity: 0 }}
            transition={
              reduceMotion
                ? { duration: 0 }
                : { duration: 0.18, ease: "easeOut" }
            }
            className="p-3 border-t border-[var(--border-subtle)] space-y-3"
          >
          <p className="text-[0.6875rem] text-[var(--text-muted)]">
            All {FEATURE_COLS.length + CAT_COLS.length} model fields, pre-filled with dataset medians. A judge can see the full payload the form sends to <code className="font-mono">/api/predict</code>.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[0.75rem]">
            {FEATURE_COLS.map((col) => {
              if (col in DEFAULT_PRIMARY) {
                const v = (values as unknown as Record<string, unknown>)[col] ??
                  (DEFAULT_PRIMARY as unknown as Record<string, unknown>)[col];
                return (
                  <div key={col} className="flex items-baseline justify-between gap-2">
                    <span className="text-[var(--text-muted)] font-mono">{col}</span>
                    <span className="text-[var(--text-primary)] font-mono tabular-nums">{typeof v === "number" ? v : String(v)}</span>
                  </div>
                );
              }
              const v = (values as unknown as Record<string, unknown>)[col];
              return (
                <div key={col} className="flex items-baseline justify-between gap-2">
                  <span className="text-[var(--text-muted)] font-mono">{col}</span>
                  <span className="text-[var(--text-primary)] font-mono tabular-nums">{typeof v === "number" ? v : String(v ?? "")}</span>
                </div>
              );
            })}
            {CAT_COLS.map((col) => {
              const v = (values as unknown as Record<string, unknown>)[col];
              return (
                <div key={col} className="flex items-baseline justify-between gap-2">
                  <span className="text-[var(--text-muted)] font-mono">{col}</span>
                  <span className="text-[var(--text-primary)] font-mono">{String(v ?? "")}</span>
                </div>
              );
            })}
          </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
