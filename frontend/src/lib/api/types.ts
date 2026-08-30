// Phase 4 - lib/api/types.ts
// Verbatim from Appendix E of afl_phases_0-11_FRONTEND_CLARIFICATIONS.md.
// Every interface matches the API contract (Appendix C) field-for-field.
//
// The AflApiClient interface lives here too (not in client.ts) to
// avoid a circular import: client.ts imports the httpClient and
// demoClient values to return from getApiClient(), and those files
// import the AflApiClient type from here. A value import in either
// direction would create a cycle that the bundler cannot resolve.

export type FraudType =
  | "account_takeover"
  | "ai_impersonation"
  | "auth_bypass"
  | "bustout_identity"
  | "card_testing"
  | "synthetic_identity"
  | "bnpl_abuse";

export type AttackCategory = "A" | "B" | "C" | "D" | "E";

// Per the unified taxonomy source (docs/ATTACK_TAXONOMY.md +
// src/identify/attacks.json), five statuses exist in the data:
// implemented, partial, conceptual, future, and novel. The
// original Phase 4 type only listed 3 - widened in Phase 6 to
// match the data, since "novel" is the project's named
// differentiator (Appendix A and FRONTEND_VISION) and "future"
// is a real status in the fixture that the type system was
// silently rejecting.
export type AttackStatus = "implemented" | "partial" | "conceptual" | "future" | "novel";

export interface Attack {
  id: string;
  name: string;
  category: AttackCategory;
  status: AttackStatus;
  feasibility: 1 | 2 | 3 | 4 | 5;
  fraud_type: FraudType | null;
  generator_profile_id: string | null;
  description: string;
}

// MODEL_COLS-shaped - Appendix B (23 fields total: 20 numeric + 3 categorical)
export interface TransactionRow {
  amount: number;
  account_age_days: number;
  tx_last_1min: number;
  tx_last_1hr: number;
  tx_last_24hr: number;
  count_30d: number;
  amount_zscore_30d: number;
  new_device: 0 | 1;
  new_merchant: 0 | 1;
  merchant_cat_freq_user: number;
  time_since_last_s: number;
  dist_from_prev_km: number;
  geo_velocity_kmh: number;
  hour_of_day: number;
  three_ds_failures_before_result: number;
  three_ds_failures_last_30d: number;
  device_trust_age_days: number;
  burst_count_10m: number;
  is_high_amount_burst: 0 | 1;
  inter_transaction_time_s: number;
  merchant_category: string;
  channel: string;
  three_ds_result: string;
}

// Extension per H.2.12: backend actually uses transaction_id; not id.
export interface TransactionRowWithId extends TransactionRow {
  transaction_id?: string;
}

export interface GenerateRequest {
  attack_id: string;
  // Per Phase 10 user-input fix: a user can type a username (string)
  // or a numeric user_id, or leave the field empty / "random" to
  // let the backend pick. The frontend stores the raw string the user
  // typed and forwards it as-is; the demo client coerces to a
  // sensible number when possible and otherwise passes the string
  // through to the live API.
  user_id: number | string;
  urgency: "low" | "medium" | "high" | null;
}

// Per H.2.13: user_medians is required for the Diff Against Normal panel
// in the Generate page. Added as an extension to the original contract.
export interface UserMedians {
  amount: number;
  channel: string;
  hour_of_day: number;
  device_trust_age_days: number;
}

export interface GenerateResult {
  run_id: string;
  conversation: { role: string; content: string }[];
  transaction: TransactionRowWithId;
  accepted: boolean;
  rejection_reason?: string;
  drop_stats: Record<string, number>;
  user_medians?: UserMedians;
}

export interface PredictRequest {
  transaction: TransactionRow;
}

export interface ShapFeature {
  feature: string;
  value: number;
  impact: "positive" | "negative";
}

export interface PredictResult {
  probability: number;
  threshold: number;
  label: "legit" | "fraud";
  shap: ShapFeature[];
}

export interface EvalPerClassRow {
  fraud_type: FraudType;
  count: number;
  precision: number;
  recall: number;
  pr_auc: number;
  fpr: number;
}

export interface PrCurveResponse {
  precision: number[];
  recall: number[];
  thresholds: number[];
  operating_point: { precision: number; recall: number; threshold: number };
}

// H.2.14: business metrics are produced by FraudInferenceService.
// Frontend reads them verbatim per Phase 8 DO-NOT #2.
export interface BusinessMetricRow {
  threshold: number;
  precision: number;
  recall: number;
  f1: number;
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  alert_rate: number;
}
export type BusinessMetricsResponse = BusinessMetricRow[];

// H.2.15: confusion heatmap data, per fraud type.
export interface ConfusionRow {
  fraud_type: FraudType;
  predicted_legit: number;
  predicted_fraud: number;
  total: number;
}
export type ConfusionResponse = ConfusionRow[];

export interface LoopHistoryEntry {
  run_id: string;
  started_at: string;
  duration_s: number;
  final_pr_auc: number;
  n_cycles: number;
  n_new_attacks: number;
  artifact_url?: string;
}

export interface LoopRunRequest {
  fraud_type: FraudType | "all";
  n_new_attacks: number;
  max_cycles: number;
}

// H.2.18: extended event types to guarantee baseline/final pair is
// always present. Old events remain valid.
export type LoopEvent =
  | {
      type: "run_start";
      run_id: string;
      started_at: string;
      baseline: {
        recall: number;
        pr_auc: number;
        fn: number;
        precision: number;
      };
    }
  | { type: "cycle_start"; cycle: number }
  | {
      type: "miss_added";
      cycle: number;
      fraud_type: FraudType;
      count: number;
    }
  | {
      type: "metric_update";
      cycle: number;
      metric: "recall" | "pr_auc" | "fn" | "precision";
      value: number;
    }
  | { type: "cycle_end"; cycle: number }
  | {
      type: "run_complete";
      run_id: string;
      final: {
        recall: number;
        pr_auc: number;
        fn: number;
        precision: number;
      };
      duration_s: number;
      n_cycles: number;
      n_new_attacks: number;
      artifact_url?: string;
    }
  | { type: "error"; message: string };

export interface SystemStatus {
  online: boolean;
  n_users: number;
  n_transactions: number;
  fraud_rate: number;
  pr_auc_test: number;
  last_retrain_at: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  model_loaded: boolean;
  data_loaded: boolean;
  n_users: number;
}

// Stream event type for POST /api/generate when it takes > 2s (H.2.17)
export type GenerateStreamEvent =
  | { type: "progress"; message: string }
  | { type: "result"; result: GenerateResult }
  | { type: "error"; message: string };

// The API client interface. Two implementations: httpClient (real
// fetch) and demoClient (fixtures). Both implement this exactly.
//
// `generate` accepts an optional `onProgress` callback. When the
// backend streams SSE progress events (H.2.17), the http client
// invokes this callback with each "progress" message. The demo
// client ignores the callback (it has nothing to stream). This
// keeps the streaming concern owned by the API client (it knows
// the transport) while letting the Generate page surface those
// messages in the UI.
export interface AflApiClient {
  getHealth(): Promise<HealthResponse>;
  getAttacks(): Promise<Attack[]>;
  getAttack(id: string): Promise<Attack>;
  generate(
    req: GenerateRequest,
    onProgress?: (msg: string) => void,
  ): Promise<GenerateResult>;
  predict(req: PredictRequest): Promise<PredictResult>;
  getEvalPerClass(): Promise<EvalPerClassRow[]>;
  getEvalPrCurve(): Promise<PrCurveResponse>;
  getEvalBusiness(): Promise<BusinessMetricsResponse>;
  getEvalConfusion(): Promise<ConfusionResponse>;
  getLoopHistory(): Promise<LoopHistoryEntry[]>;
  // runLoop does NOT return a Promise - it opens a stream and hands
  // back an unsubscribe function synchronously. See use-event-stream.ts.
  runLoop(
    req: LoopRunRequest,
    onEvent: (e: LoopEvent) => void,
  ): () => void;
  getSystemStatus(): Promise<SystemStatus>;
}
