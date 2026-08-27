"""
Production inference module for fraud detection.

This module provides a fast, production-ready interface for serving fraud predictions
via REST API, batch processing, or real-time streaming.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib

# Import centralized configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    FEATURE_COLS, CAT_COLS, MODEL_COLS, BINARY_FLAG_COLS,
    XGB_TIER1_JSON, XGB_TIER1_SMOTENC_JSON, ISO_FOREST_TIER2_JOBLIB,
    ISO_FOREST_CONFIG_JSON, BUSINESS_THRESHOLDS,
    ensure_directories, get_feature_config
)
class FraudInferenceService:
    """Production-ready inference service for fraud detection."""
    
    def __init__(self, model_path=None, pipeline_path=None, tier2_path=None):
        """
        Initialize inference service.
        
        Args:
            model_path: Path to XGBoost model (JSON format)
            pipeline_path: Path to saved full pipeline (joblib format)
            tier2_path: Path to Isolation Forest model (joblib format)
        """
        self.model_path = model_path or XGB_TIER1_JSON
        self.pipeline_path = pipeline_path
        self.tier2_path = tier2_path or ISO_FOREST_TIER2_JOBLIB
        
        self.tier1_pipeline = None
        self.tier2_model = None
        self.tier2_thresholds = None
        self._initialized = False
        
    def initialize(self):
        """Load models and prepare for inference."""
        if self._initialized:
            return
            
        # Load Tier 1 pipeline
        if self.pipeline_path and Path(self.pipeline_path).exists():
            self.tier1_pipeline = FraudPipeline.load_pipeline(self.pipeline_path)
        else:
            self.tier1_pipeline = create_inference_pipeline(self.model_path)
            self.tier1_pipeline.load_model()
            
        # Load Tier 2 (Isolation Forest) if available
        if Path(self.tier2_path).exists():
            self.tier2_model = joblib.load(self.tier2_path)
            config_path = Path(self.tier2_path).with_name("isolation_forest_config.json")
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                    self.tier2_thresholds = config.get("thresholds", {})
                    
        self._initialized = True
        
    def predict_single(self, transaction_dict, threshold=0.5, include_tier2=False):
        """
        Predict fraud for a single transaction.
        
        Args:
            transaction_dict: Dictionary with transaction features
            threshold: Decision threshold for Tier 1
            include_tier2: Whether to include Tier 2 anomaly score
            
        Returns:
            Dict with prediction results
        """
        self.initialize()
        
        # Convert to DataFrame
        df = pd.DataFrame([transaction_dict])
        
        # Tier 1 prediction
        fraud_prob = self.tier1_pipeline.predict_proba(df)[0]
        fraud_pred = int(fraud_prob >= threshold)
        
        result = {
            "transaction_id": transaction_dict.get("transaction_id", None),
            "fraud_probability": float(fraud_prob),
            "fraud_prediction": fraud_pred,
            "threshold_used": threshold,
            "tier": "tier1_xgboost"
        }
        
        # Tier 2 anomaly detection
        if include_tier2 and self.tier2_model is not None:
            # For Tier 2, we need the feature matrix
            X_transformed = self.tier1_pipeline.feature_pipeline.transform(df)
            anomaly_score = -self.tier2_model.score_samples(X_transformed)[0]
            is_anomaly = anomaly_score > self.tier2_thresholds.get("p99", 0)
            
            result.update({
                "anomaly_score": float(anomaly_score),
                "is_anomaly": bool(is_anomaly),
                "tier": "tier1_tier2_ensemble"
            })
            
        return result
    
    def predict_batch(self, transactions_df, threshold=0.5, include_tier2=False):
        """
        Predict fraud for a batch of transactions.
        
        Args:
            transactions_df: DataFrame with transaction features
            threshold: Decision threshold for Tier 1
            include_tier2: Whether to include Tier 2 anomaly score
            
        Returns:
            DataFrame with predictions
        """
        self.initialize()
def get_business_metrics(self, transactions_df, threshold=None):
        """
        Compute business-relevant metrics at multiple thresholds.
        
        Args:
            transactions_df: DataFrame with transactions and ground truth (is_fraud)
            threshold: Specific threshold to evaluate (optional)
            
        Returns:
            Dict with metrics at each threshold
        """
        self.initialize()
        
        if "is_fraud" not in transactions_df.columns:
            raise ValueError("Ground truth 'is_fraud' column required for metrics")
            
        y_true = transactions_df["is_fraud"].values
        fraud_probs = self.tier1_pipeline.predict_proba(transactions_df)
        
        thresholds = [threshold] if threshold else BUSINESS_THRESHOLDS
        metrics = {}
        
        for thresh in thresholds:
            y_pred = (fraud_probs >= thresh).astype(int)
            
            tp = ((y_true == 1) & (y_pred == 1)).sum()
            fp = ((y_true == 0) & (y_pred == 1)).sum()
            tn = ((y_true == 0) & (y_pred == 0)).sum()
            fn = ((y_true == 1) & (y_pred == 0)).sum()
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            metrics[f"threshold_{thresh:.2f}"] = {
                "threshold": thresh,
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
                "true_positives": int(tp),
                "false_positives": int(fp),
                "true_negatives": int(tn),
                "false_negatives": int(fn),
                "alert_rate": float((y_pred == 1).mean()),
            }
            
        return metrics
    
    def health_check(self):
        """Check if service is healthy and models are loaded."""
        try:
            self.initialize()
            # Quick test prediction
            test_tx = {
                "amount": 100.0,
                "account_age_days": 365,
                "tx_last_1min": 0,
                "tx_last_1hr": 1,
                "tx_last_24hr": 5,
                "count_30d": 10,
                "amount_zscore_30d": 0.5,
                "new_device": 0,
                "new_merchant": 0,
                "merchant_cat_freq_user": 0.1,
                "time_since_last_s": 3600,
                "dist_from_prev_km": 1.0,
                "geo_velocity_kmh": 1.0,
                "hour_of_day": 12,
                "three_ds_failures_before_result": 0,
                "three_ds_failures_last_30d": 0,
                "device_trust_age_days": 30,
                "burst_count_10m": 0,
                "is_high_amount_burst": 0,
                "inter_transaction_time_s": 3600,
                "merchant_category": "grocery",
                "channel": "online",
                "three_ds_result": "success",
            }
            result = self.predict_single(test_tx)
            return {
                "status": "healthy",
                "tier1_loaded": self.tier1_pipeline is not None,
                "tier2_loaded": self.tier2_model is not None,
                "test_prediction": result
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


def create_inference_service(model_path=None, pipeline_path=None, tier2_path=None):
    """Factory function to create inference service."""
    return FraudInferenceService(
        model_path=model_path,
        pipeline_path=pipeline_path,
        tier2_path=tier2_path
    )


# CLI for batch inference
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch fraud inference")
    parser.add_argument("--input", required=True, help="Input CSV/Parquet file")
    parser.add_argument("--output", required=True, help="Output CSV/Parquet file")
    parser.add_argument("--model", default=str(XGB_TIER1_JSON), help="Model path")
    parser.add_argument("--pipeline", help="Full pipeline path (joblib)")
    parser.add_argument("--tier2", action="store_true", help="Include Tier 2 anomaly detection")
    parser.add_argument("--threshold", type=float, default=0.5, help="Decision threshold")
    
    args = parser.parse_args()
    
    # Load data
    if args.input.endswith(".parquet"):
        df = pd.read_parquet(args.input)
    else:
        df = pd.read_csv(args.input)
        
    # Run inference
    service = create_inference_service(
        model_path=args.model,
        pipeline_path=args.pipeline,
    )
    
    results = service.predict_batch(df, threshold=args.threshold, include_tier2=args.tier2)
    
    # Save results
    if args.output.endswith(".parquet"):
        results.to_parquet(args.output, index=False)
    else:
        results.to_csv(args.output, index=False)
        
    print(f"Processed {len(df)} transactions")
    print(f"Fraud predictions: {results['fraud_prediction'].sum()}")
    print(f"Results saved to {args.output}")
        
        # Tier 1 predictions
        fraud_probs = self.tier1_pipeline.predict_proba(transactions_df)
        fraud_preds = (fraud_probs >= threshold).astype(int)
        
        results = transactions_df[["transaction_id"]].copy() if "transaction_id" in transactions_df.columns else pd.DataFrame(index=transactions_df.index)
        results["fraud_probability"] = fraud_probs
        results["fraud_prediction"] = fraud_preds
        results["threshold_used"] = threshold
        results["tier"] = "tier1_xgboost"
        
        # Tier 2 anomaly detection
        if include_tier2 and self.tier2_model is not None:
            X_transformed = self.tier1_pipeline.feature_pipeline.transform(transactions_df)
            anomaly_scores = -self.tier2_model.score_samples(X_transformed)
            is_anomaly = anomaly_scores > self.tier2_thresholds.get("p99", 0)
            
            results["anomaly_score"] = anomaly_scores
            results["is_anomaly"] = is_anomaly.astype(int)
            results["tier"] = "tier1_tier2_ensemble"
            
        return results
from fraud_model.pipeline.pipeline import FraudPipeline, create_inference_pipeline
﻿
