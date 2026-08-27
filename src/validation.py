"""
Data validation module for fraud detection pipeline.

Provides schema validation for input data, feature matrices, and model outputs.
Used to ensure data quality and catch drift in production.
"""

from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Import centralized configuration
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    FEATURE_COLS, CAT_COLS, MODEL_COLS, BINARY_FLAG_COLS,
    STEERABLE_COLS
)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    severity: ValidationSeverity
    check_name: str
    message: str
    details: Optional[Dict[str, Any]] = None


class DataValidator:
    """Validates data at various stages of the fraud detection pipeline."""
    
    REQUIRED_RAW_COLUMNS = [
        "transaction_id", "timestamp", "user_id", "amount",
        "merchant_id", "merchant_category", "channel", "three_ds_result",
        "is_fraud"
    ]
    
    RAW_DTYPES = {
        "transaction_id": "object",
        "timestamp": "object",
        "user_id": "object",
        "amount": "float64",
        "merchant_id": "object",
        "merchant_category": "object",
        "channel": "object",
        "three_ds_result": "object",
        "is_fraud": "int64",
    }
    
    VALID_MERCHANT_CATEGORIES = [
        "grocery", "restaurant", "retail", "online", "travel",
        "entertainment", "utilities", "healthcare", "education", "other"
    ]
    
    VALID_CHANNELS = ["online", "pos", "atm", "mobile"]
    VALID_THREE_DS_RESULTS = ["success", "failure", "not_attempted", "attempted"]
    
    NUMERIC_BOUNDS = {
        "amount": (0.01, 100000.0),
        "account_age_days": (0, 10000),
        "tx_last_1min": (0, 100),
        "tx_last_1hr": (0, 1000),
        "tx_last_24hr": (0, 10000),
        "count_30d": (0, 10000),
        "hour_of_day": (0, 23),
    }
    
    def __init__(self, strict: bool = False):
        self.strict = strict
        self.results: List[ValidationResult] = []
        
    def validate_raw_data(self, df: pd.DataFrame) -> List[ValidationResult]:
        self.results = []
        self._check_required_columns(df, self.REQUIRED_RAW_COLUMNS, "raw_data_required_columns")
        self._check_dtypes(df, self.RAW_DTYPES, "raw_data_dtypes")
        self._check_nulls(df, self.REQUIRED_RAW_COLUMNS, "raw_data_nulls")
        if "merchant_category" in df.columns:
            self._check_categorical_values(df, "merchant_category", self.VALID_MERCHANT_CATEGORIES, "merchant_category_values")
        if "channel" in df.columns:
            self._check_categorical_values(df, "channel", self.VALID_CHANNELS, "channel_values")
        if "three_ds_result" in df.columns:
            self._check_categorical_values(df, "three_ds_result", self.VALID_THREE_DS_RESULTS, "three_ds_result_values")
        self._check_numeric_bounds(df, "raw_data_numeric_bounds")
        if "is_fraud" in df.columns:
            self._check_target_distribution(df, "raw_data_target_distribution")
        if "transaction_id" in df.columns:
            self._check_duplicate_ids(df, "raw_data_duplicate_ids")
        if "timestamp" in df.columns and "user_id" in df.columns:
            self._check_temporal_ordering(df, "raw_data_temporal_ordering")
        return self.results
    
    def validate_features(self, df: pd.DataFrame) -> List[ValidationResult]:
        self.results = []
        self._check_required_columns(df, FEATURE_COLS, "features_required_columns")
        self._check_nulls(df, FEATURE_COLS, "features_nulls")
        self._check_binary_flags(df, "features_binary_flags")
        self._check_feature_numeric_bounds(df, "features_numeric_bounds")
        self._check_outliers(df, "features_outliers")
        self._check_constant_columns(df, FEATURE_COLS, "features_constant_columns")
        return self.results
    
    def validate_model_input(self, df: pd.DataFrame) -> List[ValidationResult]:
        self.results = []
        self._check_required_columns(df, MODEL_COLS, "model_input_required_columns")
        self._check_nulls(df, MODEL_COLS, "model_input_nulls")
        self._check_inf_nan(df, "model_input_inf_nan")
        self._check_scaled_ranges(df, "model_input_scaled_ranges")
        return self.results
    
    def validate_predictions(self, y_true: np.ndarray, y_pred: np.ndarray, 
                           y_prob: np.ndarray) -> List[ValidationResult]:
        self.results = []
        if len(y_true) != len(y_pred) or len(y_true) != len(y_prob):
            self.results.append(ValidationResult(
                ValidationSeverity.ERROR,
                "predictions_shape_mismatch",
                f"Shape mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}, y_prob={len(y_prob)}"
            ))
            return self.results
        self._check_binary_predictions(y_pred, "predictions_binary_values")
        self._check_probability_range(y_prob, "predictions_probability_range")
        self._check_prediction_diversity(y_pred, "predictions_diversity")
        self._check_calibration(y_true, y_prob, "predictions_calibration")
        return self.results
    
    def _check_required_columns(self, df: pd.DataFrame, required: List[str], check_name: str):
        missing = [c for c in required if c not in df.columns]
        if missing:
            self.results.append(ValidationResult(
                ValidationSeverity.ERROR,
                check_name,
                f"Missing required columns: {missing}",
                {"missing_columns": missing, "available_columns": list(df.columns)}
            ))
    
    def _check_dtypes(self, df: pd.DataFrame, expected: Dict[str, str], check_name: str):
        mismatches = []
        for col, expected_dtype in expected.items():
            if col in df.columns:
                actual_dtype = str(df[col].dtype)
                if not self._dtype_matches(actual_dtype, expected_dtype):
                    mismatches.append({"column": col, "expected": expected_dtype, "actual": actual_dtype})
        if mismatches:
            self.results.append(ValidationResult(
                ValidationSeverity.WARNING,
                check_name,
                f"Dtype mismatches: {mismatches}",
                {"mismatches": mismatches}
            ))
    
    def _dtype_matches(self, actual: str, expected: str) -> bool:
        if expected == "float64":
            return actual in ("float64", "float32", "float")
        if expected == "int64":
            return actual in ("int64", "int32", "int")
        if expected == "object":
            return actual in ("object", "string", "str")
        return actual == expected
    
    def _check_nulls(self, df: pd.DataFrame, columns: List[str], check_name: str):
        null_cols = []
        for col in columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    null_cols.append({"column": col, "null_count": int(null_count), "null_pct": float(null_count / len(df))})
        if null_cols:
            severity = ValidationSeverity.ERROR if self.strict else ValidationSeverity.WARNING
            self.results.append(ValidationResult(
                severity,
                check_name,
                f"Null values found in {len(null_cols)} columns",
                {"null_columns": null_cols}
            ))
    
    def _check_categorical_values(self, df: pd.DataFrame, column: str, 
                                   valid_values: List[str], check_name: str):
        invalid = df[~df[column].isin(valid_values)][column].unique()
        if len(invalid) > 0:
            self.results.append(ValidationResult(
                ValidationSeverity.WARNING,
                check_name,
                f"Invalid values in {column}: {list(invalid)}",
                {"invalid_values": list(invalid), "valid_values": valid_values}
            ))
    
    def _check_numeric_bounds(self, df: pd.DataFrame, check_name: str):
        violations = []
        for col, (min_val, max_val) in self.NUMERIC_BOUNDS.items():
            if col in df.columns:
                below = (df[col] < min_val).sum()
                above = (df[col] > max_val).sum()
                if below > 0 or above > 0:
                    violations.append({
                        "column": col,
                        "below_min": int(below),
                        "above_max": int(above),
                        "min": min_val,
                        "max": max_val
                    })
        if violations:
            severity = ValidationSeverity.WARNING if not self.strict else ValidationSeverity.ERROR
            self.results.append(ValidationResult(
                severity,
                check_name,
                f"Numeric bounds violations in {len(violations)} columns",
                {"violations": violations}
            ))
    
    def _check_target_distribution(self, df: pd.DataFrame, check_name: str):
        target = df["is_fraud"]
        fraud_rate = target.mean()
        if fraud_rate == 0:
            self.results.append(ValidationResult(
                ValidationSeverity.ERROR,
                check_name,
                "No fraud cases in dataset (target is all zeros)"
            ))
        elif fraud_rate == 1:
            self.results.append(ValidationResult(
                ValidationSeverity.ERROR,
                check_name,
                "All cases are fraud (target is all ones)"
            ))
        elif fraud_rate < 0.001:
            self.results.append(ValidationResult(
                ValidationSeverity.WARNING,
                check_name,
                f"Very low fraud rate: {fraud_rate:.4f} (class imbalance)",
                {"fraud_rate": fraud_rate}
            ))
    
    def _check_duplicate_ids(self, df: pd.DataFrame, check_name: str):
        dup_count = df["transaction_id"].duplicated().sum()
        if dup_count > 0:
            self.results.append(ValidationResult(
                ValidationSeverity.WARNING,
                check_name,
                f"Found {dup_count} duplicate transaction_ids",
                {"duplicate_count": int(dup_count)}
            ))
    
    def _check_temporal_ordering(self, df: pd.DataFrame, check_name: str):
        try:
            df_sorted = df.sort_values(["user_id", "timestamp"])
            is_sorted = df.index.equals(df_sorted.index)
            if not is_sorted:
                self.results.append(ValidationResult(
                    ValidationSeverity.INFO,
                    check_name,
                    "Data not sorted by user_id and timestamp (will be sorted during feature engineering)"
                ))
        except Exception:
            pass
    
    def _check_binary_flags(self, df: pd.DataFrame, check_name: str):
        invalid_flags = []
        for col in BINARY_FLAG_COLS:
            if col in df.columns:
                unique_vals = df[col].dropna().unique()
                invalid = [v for v in unique_vals if v not in (0, 1, 0.0, 1.0)]
                if invalid:
                    invalid_flags.append({"column": col, "invalid_values": invalid})
        if invalid_flags:
            self.results.append(ValidationResult(
                ValidationSeverity.ERROR,
                check_name,
                f"Binary flag columns contain non-binary values: {invalid_flags}",
                {"invalid_flags": invalid_flags}
            ))
    
    def _check_feature_numeric_bounds(self, df: pd.DataFrame, check_name: str):
        feature_bounds = {
            "amount_zscore_30d": (-10, 10),
            "merchant_cat_freq_user": (0, 1),
            "time_since_last_s": (0, 31536000),
            "dist_from_prev_km": (0, 20000),
            "geo_velocity_kmh": (0, 1000),
            "inter_transaction_time_s": (0, 31536000),
        }
        violations = []
        for col, (min_val, max_val) in feature_bounds.items():
            if col in df.columns:
                below = (df[col] < min_val).sum()
                above = (df[col] > max_val).sum()
                if below > 0 or above > 0:
                    violations.append({
                        "column": col,
                        "below_min": int(below),
                        "above_max": int(above),
                        "min": min_val,
                        "max": max_val
                    })
        if violations:
            self.results.append(ValidationResult(
                ValidationSeverity.WARNING,
                check_name,
                f"Feature bounds violations in {len(violations)} columns",
                {"violations": violations}
            ))
    
    def _check_outliers(self, df: pd.DataFrame, check_name: str):
        outlier_cols = []
        for col in FEATURE_COLS:
            if col in df.columns and df[col].dtype in ("float64", "float32", "int64", "int32"):
                if col in BINARY_FLAG_COLS:
                    continue
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                if IQR > 0:
                    lower = Q1 - 3 * IQR
                    upper = Q3 + 3 * IQR
                    outliers = ((df[col] < lower) | (df[col] > upper)).sum()
                    if outliers > len(df) * 0.05:
                        outlier_cols.append({
                            "column": col,
                            "outlier_count": int(outliers),
                            "outlier_pct": float(outliers / len(df)),
                            "lower_bound": float(lower),
                            "upper_bound": float(upper)
                        })
        if outlier_cols:
            self.results.append(ValidationResult(
                ValidationSeverity.INFO,
                check_name,
                f"Potential outliers detected in {len(outlier_cols)} columns (using 3*IQR rule)",
                {"outlier_columns": outlier_cols}
            ))
    
    def _check_constant_columns(self, df: pd.DataFrame, columns: List[str], check_name: str):
        constant_cols = []
        for col in columns:
            if col in df.columns:
                n_unique = df[col].nunique()
                if n_unique <= 1:
                    constant_cols.append({"column": col, "unique_values": int(n_unique)})
        if constant_cols:
            self.results.append(ValidationResult(
                ValidationSeverity.WARNING,
                check_name,
                f"Constant or near-constant columns: {len(constant_cols)}",
                {"constant_columns": constant_cols}
            ))
    
    def _check_inf_nan(self, df: pd.DataFrame, check_name: str):
        inf_cols = []
        nan_cols = []
        for col in df.columns:
            if df[col].dtype in ("float64", "float32", "int64", "int32"):
                inf_count = np.isinf(df[col]).sum()
                nan_count = df[col].isnull().sum()
                if inf_count > 0:
                    inf_cols.append({"column": col, "inf_count": int(inf_count)})
                if nan_count > 0:
                    nan_cols.append({"column": col, "nan_count": int(nan_count)})
        if inf_cols or nan_cols:
            self.results.append(ValidationResult(
                ValidationSeverity.ERROR,
                check_name,
                f"Inf/NaN values found: {len(inf_cols)} inf, {len(nan_cols)} nan columns",
                {"inf_columns": inf_cols, "nan_columns": nan_cols}
            ))
    
    def _check_scaled_ranges(self, df: pd.DataFrame, check_name: str):
        extreme_cols = []
        for col in df.columns:
            if df[col].dtype in ("float64", "float32"):
                max_abs = df[col].abs().max()
                if max_abs > 10:
                    extreme_cols.append({"column": col, "max_abs_value": float(max_abs)})
        if extreme_cols:
            self.results.append(ValidationResult(
                ValidationSeverity.WARNING,
                check_name,
                f"Features with extreme values after scaling: {len(extreme_cols)}",
                {"extreme_columns": extreme_cols}
            ))
    
    def _check_binary_predictions(self, y_pred: np.ndarray, check_name: str):
        unique = np.unique(y_pred)
        invalid = [v for v in unique if v not in (0, 1)]
        if invalid:
            self.results.append(ValidationResult(
                ValidationSeverity.ERROR,
                check_name,
                f"Predictions contain non-binary values: {invalid}",
                {"invalid_values": list(invalid)}
            ))
    
    def _check_probability_range(self, y_prob: np.ndarray, check_name: str):
        if y_prob.min() < 0 or y_prob.max() > 1:
            self.results.append(ValidationResult(
                ValidationSeverity.ERROR,
                check_name,
                f"Probabilities out of [0, 1] range: min={y_prob.min()}, max={y_prob.max()}",
                {"min": float(y_prob.min()), "max": float(y_prob.max())}
            ))
    
    def _check_prediction_diversity(self, y_pred: np.ndarray, check_name: str):
        if len(np.unique(y_pred)) == 1:
            self.results.append(ValidationResult(
                ValidationSeverity.WARNING,
                check_name,
                f"All predictions are the same value: {y_pred[0]} (model may have collapsed)",
                {"predicted_class": int(y_pred[0])}
            ))
    
    def _check_calibration(self, y_true: np.ndarray, y_prob: np.ndarray, check_name: str):
        avg_pred = y_prob.mean()
        actual_rate = y_true.mean()
        diff = abs(avg_pred - actual_rate)
        if diff > 0.1:
            self.results.append(ValidationResult(
                ValidationSeverity.WARNING,
                check_name,
                f"Model may be miscalibrated: avg_pred={avg_pred:.4f}, actual_rate={actual_rate:.4f}, diff={diff:.4f}",
                {"avg_predicted": float(avg_pred), "actual_rate": float(actual_rate), "diff": float(diff)}
            ))
    
    def has_errors(self) -> bool:
        return any(r.severity == ValidationSeverity.ERROR for r in self.results)
    
    def has_warnings(self) -> bool:
        return any(r.severity == ValidationSeverity.WARNING for r in self.results)
    
    def summary(self) -> Dict[str, Any]:
        return {
            "total_checks": len(self.results),
            "errors": sum(1 for r in self.results if r.severity == ValidationSeverity.ERROR),
            "warnings": sum(1 for r in self.results if r.severity == ValidationSeverity.WARNING),
            "info": sum(1 for r in self.results if r.severity == ValidationSeverity.INFO),
            "passed": not self.has_errors(),
            "results": [
                {
                    "severity": r.severity.value,
                    "check": r.check_name,
                    "message": r.message,
                    "details": r.details
                }
                for r in self.results
            ]
        }
    
    def raise_if_errors(self):
        if self.has_errors():
            errors = [r for r in self.results if r.severity == ValidationSeverity.ERROR]
            raise ValueError(f"Validation failed with {len(errors)} errors: {[e.message for e in errors]}")


def validate_raw_data(df: pd.DataFrame, strict: bool = False) -> List[ValidationResult]:
    validator = DataValidator(strict=strict)
    return validator.validate_raw_data(df)


def validate_features(df: pd.DataFrame, strict: bool = False) -> List[ValidationResult]:
    validator = DataValidator(strict=strict)
    return validator.validate_features(df)


def validate_model_input(df: pd.DataFrame, strict: bool = False) -> List[ValidationResult]:
    validator = DataValidator(strict=strict)
    return validator.validate_model_input(df)


def validate_predictions(y_true: np.ndarray, y_pred: np.ndarray, 
                        y_prob: np.ndarray, strict: bool = False) -> List[ValidationResult]:
    validator = DataValidator(strict=strict)
    return validator.validate_predictions(y_true, y_pred, y_prob)