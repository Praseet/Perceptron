// Phase 8 - features/defend/defend-page.tsx
// The real Defend page. Replaces the Phase 5 placeholder.
//
// Layout (per spec):
//   1. Header strip with the real split-sizes copy.
//   2. The live predictor as the hero: TransactionBuilderForm
//      (left), ProbabilityGauge + ShapWaterfall (right).
//   3. Below, in order: PerFraudTypeTable (shared pattern),
//      ConfusionHeatmap, PrCurveChart, BusinessMetrics table.
//
// The Generate -> Defend cross-link is honored: when
// useAppStore().lastGeneratedTransaction is set, the form's
// "Load a transaction I just generated" button pre-fills the
// form. This is the end-to-end loop the spec wants verified.

import { useState } from "react";
import { Card, Skeleton } from "../../design-system/primitives";
import { EmptyState } from "../../design-system/patterns/empty-state";
import { PerFraudTypeTable } from "../../design-system/patterns/per-fraud-type-table";
import { TransactionBuilderForm } from "./transaction-builder-form";
import { ThresholdLine } from "./threshold-line";
import { ProbabilityGauge } from "./probability-gauge";
import { ShapWaterfall } from "./shap-waterfall";
import { ConfusionHeatmap } from "./confusion-heatmap";
import { PrCurveChart } from "./pr-curve-chart";
import { BusinessMetricsTable } from "./business-metrics-table";
import {
  usePredict,
  useEvalPerClass,
  useEvalBusiness,
  useEvalConfusion,
  useEvalPrCurve,
} from "./use-defend";
import { ShieldCheck, Inbox, TrendingUp } from "../../design-system/icons";
import type { TransactionRowWithId, PredictResult } from "../../lib/api/types";
import { formatPct } from "../../lib/format";

const HEADER_TITLE = "Defend";
const HEADER_SUBTITLE =
  "Built on a 1,064,963-transaction dataset, trained on 745,474 transactions, validated on 106,496, tested on 212,993.";
const HEADER_STEP = "Step 3 of 4";

export function DefendPage() {
  // The latest prediction result, plus the tx that produced it.
  // The form's "Load a transaction I just generated" pre-fills
  // the input via defaultValues (state lift from TransactionBuilderForm
  // through the parent).
  const [lastPrediction, setLastPrediction] = useState<{
    tx: TransactionRowWithId;
    prediction: PredictResult;
  } | null>(null);
  const [pendingTx, setPendingTx] = useState<TransactionRowWithId | null>(null);

  const predict = usePredict();
  const perClass = useEvalPerClass();
  const business = useEvalBusiness();
  const confusion = useEvalConfusion();
  const prCurve = useEvalPrCurve();

  function handleSubmit(tx: TransactionRowWithId) {
    setPendingTx(tx);
    predict.mutate(tx, {
      onSuccess: (prediction) => {
        setLastPrediction({ tx, prediction });
        setPendingTx(null);
      },
      onError: () => {
        setPendingTx(null);
      },
    });
  }

  const anyError =
    perClass.isError || business.isError || confusion.isError || predict.isError;
  const firstErrorMessage =
    (perClass.error as Error | null)?.message ??
    (business.error as Error | null)?.message ??
    (confusion.error as Error | null)?.message ??
    (predict.error as Error | null)?.message ??
    "Unknown error";

  return (
    <div className="space-y-6">
      <header>
        <p className="text-caption font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
          {HEADER_STEP}
        </p>
        <h1 className="text-section-title text-[var(--text-primary)] mt-1">
          {HEADER_TITLE}
        </h1>
        <p className="text-body text-[var(--text-secondary)] mt-2 max-w-2xl">
          {HEADER_SUBTITLE}
        </p>
      </header>

      <Card className="p-4 space-y-4">
        <div className="flex items-center gap-2">
          <ShieldCheck aria-hidden size="inline" style={{ color: "var(--loop-defend)" }} />
          <h2 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
            Live predictor
          </h2>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-6 items-start">
          <div>
            <TransactionBuilderForm onSubmit={handleSubmit} />
          </div>
          <div className="space-y-4">
            <ProbabilityGauge probability={lastPrediction?.prediction.probability ?? null} />
            <ShapWaterfall
              prediction={lastPrediction?.prediction ?? null}
              isLoading={predict.isPending || pendingTx != null}
              isError={predict.isError}
              errorMessage={predict.error?.message}
            />
          </div>
        </div>
        {lastPrediction && (
          <div className="space-y-1">
            <p className="text-[0.6875rem] font-mono text-[var(--text-muted)] tabular-nums">
              Verdict: <span className="text-[var(--text-primary)]">{lastPrediction.prediction.label}</span>
              {" "}- probability {formatPct(lastPrediction.prediction.probability, 2)}, threshold {lastPrediction.prediction.threshold.toFixed(2)}
            </p>
            {/* Phase 12 (§12.17.6): probability + threshold + decision as one
                glanceable number line; the dot animates to each new score. */}
            <ThresholdLine
              probability={lastPrediction.prediction.probability}
              threshold={lastPrediction.prediction.threshold}
            />
          </div>
        )}
      </Card>


      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <Card className="p-4 space-y-3">
          <h2 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
            Per-fraud-type PR-AUC
          </h2>
          <p className="text-[0.6875rem] font-mono text-[var(--text-muted)]">
            Same data source as the Home page's eval tile.
          </p>
          {perClass.isLoading ? (
            <Skeleton className="h-32 w-full" />
          ) : perClass.isError ? (
            <EmptyState
              icon={<Inbox size="empty" />}
              message="Could not load the per-class evaluation."
            />
          ) : perClass.data && perClass.data.length > 0 ? (
            <PerFraudTypeTable rows={perClass.data} />
          ) : (
            <EmptyState
              icon={<Inbox size="empty" />}
              message="No per-class evaluation data."
            />
          )}
        </Card>

        <Card className="p-4 space-y-3">
          <div className="flex items-center gap-2">
            <TrendingUp aria-hidden size="inline" style={{ color: "var(--accent-cyan)" }} />
            <h2 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
              Confusion heatmap
            </h2>
          </div>
          <p className="text-[0.6875rem] font-mono text-[var(--text-muted)]">
            Per-fraud-type. Cells colored by row-normalized count;
            numeric count printed in every cell.
          </p>
          <ConfusionHeatmap
            data={confusion.data}
            isLoading={confusion.isLoading}
            isError={confusion.isError}
            errorMessage={(confusion.error as Error | null)?.message}
          />
        </Card>
      </div>

      <Card className="p-4 space-y-3">
        <h2 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
          Precision-Recall curve
        </h2>
        <p className="text-[0.6875rem] font-mono text-[var(--text-muted)]">
          The dot is the real operating point. Move the fixture's
          threshold to see the dot move.
        </p>
        <PrCurveChart
          data={prCurve.data}
          isLoading={prCurve.isLoading}
          isError={prCurve.isError}
          errorMessage={(prCurve.error as Error | null)?.message}
        />
      </Card>

      <Card className="p-4 space-y-3">
        <h2 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
          Business-threshold tradeoff
        </h2>
        <p className="text-[0.6875rem] font-mono text-[var(--text-muted)]">
          Precision/recall/F1/TP/FP/FN/alert-rate at the four spec
          thresholds. No single threshold is highlighted; the
          choice is a business decision (per H.34).
        </p>
        <BusinessMetricsTable
          data={business.data}
          isLoading={business.isLoading}
          isError={business.isError}
          errorMessage={(business.error as Error | null)?.message}
        />
      </Card>

      {anyError && (
        <Card className="p-4">
          <EmptyState
            icon={<Inbox size="empty" />}
            message={`One or more eval panels failed to load: ${firstErrorMessage}`}
          />
        </Card>
      )}
    </div>
  );
}
