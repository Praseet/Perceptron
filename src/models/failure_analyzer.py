"""
Failure Analyzer for Closed-Loop Feedback System
Analyzes model misses to identify evasion patterns.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any


class FailureAnalyzer:
    """Analyzes false negatives to identify evasion patterns."""
    
    def analyze_misses(self, df: pd.DataFrame, predictions: np.ndarray, threshold: float) -> Dict[str, Any]:
        """Analyze false negatives (missed fraud cases)."""
        is_fraud = df['is_fraud'] == 1
        is_missed = (is_fraud) & (predictions < threshold)
        missed_df = df[is_missed].copy()
        
        if missed_df.empty:
            return {'status': 'no_misses', 'n_misses': 0}
        
        # Analyze by fraud type
        fraud_type_analysis = {}
        for fraud_type, group in missed_df.groupby('fraud_type'):
            if fraud_type == 'normal':
                continue
            fraud_type_analysis[fraud_type] = {
                'n_misses': len(group),
                'avg_score': float(predictions[is_missed][missed_df['fraud_type'] == fraud_type].mean()),
                'median_amount': float(group['amount'].median()) if 'amount' in group else 0
            }
        
        # Identify evasion patterns
        evasion_patterns = self._identify_evasion_patterns(missed_df)
        
        return {
            'status': 'analyzed',
            'n_misses': len(missed_df),
            'fraud_type_breakdown': fraud_type_analysis,
            'evasion_patterns': evasion_patterns
        }
    
    def _identify_evasion_patterns(self, missed_df: pd.DataFrame) -> List[Dict]:
        """Identify what features help fraud evade detection."""
        patterns = []
        
        if 'amount' in missed_df.columns:
            low_amount = missed_df[missed_df['amount'] < 100]
            if len(low_amount) > len(missed_df) * 0.3:
                patterns.append({'type': 'low_amount_evasion', 'pct': len(low_amount) / len(missed_df)})
        
        if 'hour_of_day' in missed_df.columns:
            normal_hours = missed_df[(missed_df['hour_of_day'] >= 9) & (missed_df['hour_of_day'] <= 18)]
            if len(normal_hours) > len(missed_df) * 0.6:
                patterns.append({'type': 'normal_hours_evasion', 'pct': len(normal_hours) / len(missed_df)})
        
        return patterns
    
    def generate_adversarial_profile(self, failure_report: Dict) -> Dict[str, Any]:
        """Generate attack profile for adversarial training."""
        if failure_report['status'] == 'no_misses':
            return {}
        
        profile = {
            'target_fraud_types': list(failure_report.get('fraud_type_breakdown', {}).keys())[:3],
            'evasion_techniques': [p['type'] for p in failure_report.get('evasion_patterns', [])]
        }
        return profile


if __name__ == "__main__":
    print("Failure Analyzer loaded successfully")
