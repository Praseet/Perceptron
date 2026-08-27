"""
Production-ready fraud detection pipeline combining transformers and model.

This module provides the FraudPipeline class that packages feature engineering
with the XGBoost model for consistent training and inference.
"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.pipeline import Pipeline

# Import centralized configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config import (
    FEATURE_COLS, CAT_COLS, MODEL_COLS, BINARY_FLAG_COLS,
    XGB_PARAMS, XGB_TIER1_JSON, XGB_TIER1_SMOTENC_JSON,
    XGB_TIER1_FEEDBACK_JSON, XGB_TIER1_CTGAN_JSON,
    ISO_FOREST_TIER2_JOBLIB, ISO_FOREST_CONFIG_JSON,
    ensure_directories, get_feature_config
)
from .transformers import (
    DateTimeFeatureExtractor,
    AmountFeatureExtractor,
    CustomerAggregator,
    MerchantAggregator,
    CategoricalEncoder,
    FeatureSelector,
    NumericScaler,
    FeaturePipeline
)


class FraudPipeline:
    """End-to-end fraud detection pipeline with feature engineering and model."""
    
    def __init__(self, model_path=None, training_columns=None):
        """
        Initialize the fraud pipeline.
        
        Args:
            model_path: Path to saved XGBoost model (optional, for inference)
            training_columns: List of expected feature columns after encoding (for inference)
        """
        self.model_path = model_path
        self.training_columns = training_columns
        self.model = None
        self.feature_pipeline = None
        self.is_fitted = False
        
    def build_feature_pipeline(self):
        """Build the feature engineering pipeline."""
        self.feature_pipeline = FeaturePipeline.create_pipeline(
            training_columns=self.training_columns
        )
        return self.feature_pipeline
    
    def fit(self, X, y, model_variant="tier1"):
        """
        Fit the full pipeline (feature engineering + model).
        
        Args:
            X: Training DataFrame with raw features
            y: Target labels
            model_variant: Which model variant to train ("tier1", "smotenc", "feedback", "ctgan")
        """
        ensure_directories()
        
        # Build and fit feature pipeline
        self.build_feature_pipeline()
        X_transformed = self.feature_pipeline.fit_transform(X, y)
        
        # Store training columns for inference
        self.training_columns = list(X_transformed.columns)
        
        # Configure model
        scale_pos_weight = (y == 0).sum() / max((y == 1).sum(), 1)
        model_params = XGB_PARAMS.copy()
        model_params["scale_pos_weight"] = float(scale_pos_weight)
        
        self.model = xgb.XGBClassifier(**model_params)
        self.model.fit(X_transformed, y)
        
        self.is_fitted = True
        
        # Save model
        model_paths = {
            "tier1": XGB_TIER1_JSON,
            "smotenc": XGB_TIER1_SMOTENC_JSON,
            "feedback": XGB_TIER1_FEEDBACK_JSON,
            "ctgan": XGB_TIER1_CTGAN_JSON,
        }
        self.model.save_model(model_paths.get(model_variant, XGB_TIER1_JSON))
        
        return self
    
    def predict_proba(self, X):
        """Predict fraud probabilities."""
        if not self.is_fitted and self.model_path:
            self.load_model()
            
        if not self.is_fitted:
            raise ValueError("Pipeline not fitted and no model_path provided")
            
        X_transformed = self.feature_pipeline.transform(X)
        return self.model.predict_proba(X_transformed)[:, 1]
    
    def predict(self, X, threshold=0.5):
        """Predict fraud labels."""
        probs = self.predict_proba(X)
        return (probs >= threshold).astype(int)
    
    def load_model(self, model_path=None):
        """Load a saved model and feature pipeline."""
        model_path = model_path or self.model_path
        if model_path is None:
            raise ValueError("No model_path provided")
            
        self.model = xgb.XGBClassifier()
        self.model.load_model(model_path)
        
        # Rebuild feature pipeline with stored training columns
        self.build_feature_pipeline()
        self.is_fitted = True
        return self
    
    def save_pipeline(self, path):
        """Save the entire pipeline (transformers + model) for inference."""
        ensure_directories()
        pipeline_data = {
            "model": self.model,
            "feature_pipeline": self.feature_pipeline,
            "training_columns": self.training_columns,
            "feature_config": get_feature_config(),
        }
        joblib.dump(pipeline_data, path)
    
    @classmethod
    def load_pipeline(cls, path):
        """Load a saved pipeline for inference."""
        pipeline_data = joblib.load(path)
        instance = cls()
        instance.model = pipeline_data["model"]
        instance.feature_pipeline = pipeline_data["feature_pipeline"]
        instance.training_columns = pipeline_data["training_columns"]
        instance.is_fitted = True
        return instance


def create_inference_pipeline(model_path=None):
    """Create a pipeline ready for production inference."""
    return FraudPipeline(model_path=model_path)
﻿
