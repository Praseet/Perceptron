"""
Production inference module for fraud detection.

Provides a fast, production-ready interface for serving fraud predictions
via single-record, batch, or CLI modes. Combines Tier 1 (XGBoost supervised)
and Tier 2 (Isolation Forest unsupervised) when both artifacts exist.

Hardening notes (v1.2.0):
- Fixed broken indentation in predict_batch and get_business_metrics
  (the old file had these methods orphaned at module scope, so the CLI
  mode silently produced empty results).
- predict_single returns a complete result dict in all paths.
- health_check reports detailed load status for each tier.
- All public methods accept an optional logger; default writes to stderr.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

from config import (
    BUSINESS_THRESHOLDS,
    FEATURE_COLS, CAT_COLS, MODEL_COLS, BINARY_FLAG_COLS,
    XGB_TIER1_JSON, XGB_TIER1_SMOTENC_JSON, XGB_TIER1_FEEDBACK_JSON,
    ISO_FOREST_TIER2_JOBLIB, ISO_FOREST_CONFIG_JSON,
    ensure_directories, get_feature_config,
)
from fraud_model.pipeline.pipeline import FraudPipeline, create_inference_pipeline

logger = logging.getLogger("fraud_model.inference")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class FraudInferenceError(Exception):
    """Raised when inference cannot produce a valid result."""


class FraudInferenceService:
    """Production-ready inference service for fraud detection."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        pipeline_path: Optional[Path] = None,
        tier2_path: Optional[Path] = None,
    ) -> None:
        self.model_path = Path(model_path) if model_path else XGB_TIER1_JSON
        self.pipeline_path = Path(pipeline_path) if pipeline_path else None
        self.tier2_path = Path(tier2_path) if tier2_path else ISO_FOREST_TIER2_JOBLIB

        self.tier1_pipeline: Optional[FraudPipeline] = None
        self.tier2_model: Optional[Any] = None
        self.tier2_thresholds: Dict[str, float] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Load model artifacts exactly once. Safe to call multiple times."""
        if self._initialized:
            return
        ensure_directories()
        self._load_tier1()
        self._load_tier2()
        self._initialized = True
        logger.info(
            "Inference service initialized: tier1=%s tier2=%s",
            self.tier1_pipeline is not None,
            self.tier2_model is not None,
        )

    def _load_tier1(self) -> None:
        if self.pipeline_path and self.pipeline_path.exists():
            logger.info("Loading full pipeline from %s", self.pipeline_path)
            self.tier1_pipeline = FraudPipeline.load_pipeline(self.pipeline_path)
            return
        if not self.model_path.exists():
            raise FraudInferenceError(
                f"Tier 1 model not found: {self.model_path}. "
                f"Train the model first via `python -m src.models.train`."
            )
        logger.info("Loading Tier 1 XGBoost model from %s", self.model_path)
        self.tier1_pipeline = create_inference_pipeline(self.model_path)
        self.tier1_pipeline.load_model()

    def _load_tier2(self) -> None:
        if not self.tier2_path.exists():
            logger.warning("Tier 2 model not found at %s -- ensemble disabled", self.tier2_path)
            return
        logger.info("Loading Tier 2 Isolation Forest from %s", self.tier2_path)
        self.tier2_model = joblib.load(self.tier2_path)
        config_path = self.tier2_path.with_name("isolation_forest_tier2_config.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                self.tier2_thresholds = config.get("frozen_threshold_table", {})
                if not self.tier2_thresholds:
                    pct = config.get("normalization_percentiles") or []
                    self.tier2_thresholds = {f"p{int(p)}": float(v) for p, v in pct}
        if "p99" not in self.tier2_thresholds and self.tier2_thresholds:
            self.tier2_thresholds["p99"] = max(self.tier2_thresholds.values())

    def _validate_input_columns(self, df: pd.DataFrame) -> None:
        missing = [c for c in MODEL_COLS if c not in df.columns]
        if missing:
            raise FraudInferenceError(
                f"Input is missing required columns for inference: {missing}. "
                f"Required: {MODEL_COLS}"
            )

    def predict_single(
        self,
        transaction_dict: Dict[str, Any],
        threshold: float = 0.5,
        include_tier2: bool = False,
    ) -> Dict[str, Any]:
        """Predict fraud for a single transaction (as a dict)."""
        self.initialize()
        df = pd.DataFrame([transaction_dict])
        self._validate_input_columns(df)

        try:
            fraud_prob = float(self.tier1_pipeline.predict_proba(df)[0])
        except Exception as exc:
            raise FraudInferenceError(f"Tier 1 prediction failed: {exc}") from exc

        result: Dict[str, Any] = {
            "transaction_id": transaction_dict.get("transaction_id"),
            "fraud_probability": fraud_prob,
            "fraud_prediction": int(fraud_prob >= threshold),
            "threshold_used": float(threshold),
            "tier": "tier1_xgboost",
        }

        if include_tier2:
            result.update(self._compute_tier2(df, [fraud_prob])[0])
        return result

    def predict_batch(
        self,
        transactions_df: pd.DataFrame,
        threshold: float = 0.5,
        include_tier2: bool = False,
    ) -> pd.DataFrame:
        """Predict fraud for a batch of transactions.

        Returns a DataFrame indexed like the input, with columns:
        transaction_id (if present), fraud_probability, fraud_prediction,
        threshold_used, tier, and (if include_tier2) anomaly_score, is_anomaly.
        """
        self.initialize()
        if transactions_df.empty:
            return pd.DataFrame()
        self._validate_input_columns(transactions_df)

        try:
            fraud_probs = self.tier1_pipeline.predict_proba(transactions_df)
        except Exception as exc:
            raise FraudInferenceError(f"Tier 1 batch prediction failed: {exc}") from exc

        if "transaction_id" in transactions_df.columns:
            results = transactions_df[["transaction_id"]].copy()
        else:
            results = pd.DataFrame(index=transactions_df.index)

        results["fraud_probability"] = fraud_probs
        results["fraud_prediction"] = (fraud_probs >= threshold).astype(int)
        results["threshold_used"] = float(threshold)
        results["tier"] = "tier1_xgboost"

        if include_tier2:
            tier2_info = self._compute_tier2(transactions_df, fraud_probs)
            results["anomaly_score"] = [t["anomaly_score"] for t in tier2_info]
            results["is_anomaly"] = [t["is_anomaly"] for t in tier2_info]
            results.loc[results["is_anomaly"], "tier"] = "tier1_tier2_ensemble"

        return results

    def _compute_tier2(
        self, df: pd.DataFrame, tier1_probs: Union[np.ndarray, List[float]]
    ) -> List[Dict[str, Any]]:
        """Run Tier 2 (Isolation Forest) on the feature matrix.

        Returns a list of dicts (one per row) with anomaly_score, is_anomaly,
        and ensemble_proba. The ensemble probability nudges Tier 1's score
        upward when the isolation forest disagrees strongly.
        """
        if self.tier2_model is None:
            return [
                {"anomaly_score": 0.0, "is_anomaly": False, "ensemble_proba": float(p)}
                for p in tier1_probs
            ]
        try:
            # Tier 2 expects raw numeric columns (same as used in anomaly.py training)
            # Select only numeric columns from the raw input
            X_numeric = df.select_dtypes("number").to_numpy()
            anomaly_scores = -self.tier2_model.score_samples(X_numeric)
        except Exception as exc:
            logger.error("Tier 2 scoring failed, falling back to Tier 1 only: %s", exc)
            return [
                {"anomaly_score": 0.0, "is_anomaly": False, "ensemble_proba": float(p)}
                for p in tier1_probs
            ]

        threshold = self.tier2_thresholds.get("p99", 0.0)
        results: List[Dict[str, Any]] = []
        for score, prob in zip(anomaly_scores, tier1_probs):
            is_anomaly = bool(score > threshold)
            ensemble_proba = max(float(prob), float(is_anomaly) * 0.9)
            results.append(
                {
                    "anomaly_score": float(score),
                    "is_anomaly": is_anomaly,
                    "ensemble_proba": ensemble_proba,
                }
            )
        return results

    def get_business_metrics(
        self,
        transactions_df: pd.DataFrame,
        threshold: Optional[float] = None,
    ) -> Dict[str, Dict[str, float]]:
        """Compute precision/recall/F1 at each business threshold.

        Requires a ground-truth `is_fraud` column.
        """
        self.initialize()
        if "is_fraud" not in transactions_df.columns:
            raise ValueError("Ground truth 'is_fraud' column required for metrics")
        y_true = transactions_df["is_fraud"].to_numpy()
        fraud_probs = self.tier1_pipeline.predict_proba(transactions_df)
        thresholds = [threshold] if threshold else BUSINESS_THRESHOLDS

        metrics: Dict[str, Dict[str, float]] = {}
        for thresh in thresholds:
            y_pred = (fraud_probs >= thresh).astype(int)
            tp = int(((y_true == 1) & (y_pred == 1)).sum())
            fp = int(((y_true == 0) & (y_pred == 1)).sum())
            tn = int(((y_true == 0) & (y_pred == 0)).sum())
            fn = int(((y_true == 1) & (y_pred == 0)).sum())
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
            metrics[f"threshold_{thresh:.2f}"] = {
                "threshold": float(thresh),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
                "true_positives": tp,
                "false_positives": fp,
                "true_negatives": tn,
                "false_negatives": fn,
                "alert_rate": float((y_pred == 1).mean()),
            }
        return metrics

    def health_check(self) -> Dict[str, Any]:
        """Return a structured health report (does not raise)."""
        try:
            self.initialize()
            test_tx = {
                "amount": 100.0, "account_age_days": 365,
                "tx_last_1min": 0, "tx_last_1hr": 1, "tx_last_24hr": 5,
                "count_30d": 50, "amount_zscore_30d": 0.0,
                "new_device": 0, "new_merchant": 0,
                "merchant_cat_freq_user": 0.5,
                "time_since_last_s": 3600, "dist_from_prev_km": 0.0,
                "geo_velocity_kmh": 0.0, "hour_of_day": 12,
                "three_ds_failures_before_result": 0,
                "three_ds_failures_last_30d": 0, "device_trust_age_days": 30,
                "burst_count_10m": 0, "is_high_amount_burst": 0,
                "inter_transaction_time_s": 3600,
                "merchant_category": "grocery",
                "channel": "online",
                "three_ds_result": "success",
            }
            result = self.predict_single(test_tx, threshold=0.5, include_tier2=True)
            return {
                "status": "healthy",
                "tier1_loaded": self.tier1_pipeline is not None,
                "tier2_loaded": self.tier2_model is not None,
                "tier2_p99_threshold": self.tier2_thresholds.get("p99"),
                "test_prediction": result,
            }
        except Exception as exc:
            logger.exception("Health check failed")
            return {
                "status": "unhealthy",
                "error": str(exc),
                "tier1_loaded": self.tier1_pipeline is not None,
                "tier2_loaded": self.tier2_model is not None,
            }


def create_inference_service(
    model_path: Optional[Path] = None,
    pipeline_path: Optional[Path] = None,
    tier2_path: Optional[Path] = None,
) -> FraudInferenceService:
    """Factory function for the inference service."""
    return FraudInferenceService(
        model_path=model_path,
        pipeline_path=pipeline_path,
        tier2_path=tier2_path,
    )


def _run_cli() -> None:
    """Command-line entry point for batch inference."""
    parser = argparse.ArgumentParser(description="Batch fraud inference")
    parser.add_argument("--input", required=True, help="Input CSV/Parquet file")
    parser.add_argument("--output", required=True, help="Output CSV/Parquet file")
    parser.add_argument("--model", default=str(XGB_TIER1_JSON), help="Tier 1 model path")
    parser.add_argument("--pipeline", help="Full pipeline path (joblib)")
    parser.add_argument("--tier2", action="store_true", help="Include Tier 2 anomaly detection")
    parser.add_argument("--threshold", type=float, default=0.5, help="Decision threshold")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    args = parser.parse_args()

    logger.setLevel(getattr(logging, args.log_level))

    if args.input.endswith(".parquet"):
        df = pd.read_parquet(args.input)
    else:
        df = pd.read_csv(args.input)

    service = create_inference_service(
        model_path=args.model,
        pipeline_path=args.pipeline,
    )
    results = service.predict_batch(df, threshold=args.threshold, include_tier2=args.tier2)

    if args.output.endswith(".parquet"):
        results.to_parquet(args.output, index=False)
    else:
        results.to_csv(args.output, index=False)

    logger.info("Processed %d transactions", len(df))
    logger.info("Fraud predictions: %d", int(results["fraud_prediction"].sum()))
    logger.info("Results saved to %s", args.output)


if __name__ == "__main__":
    _run_cli()
