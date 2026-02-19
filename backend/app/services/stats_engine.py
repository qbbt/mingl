import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from scipy.stats import gumbel_r

class StatsEngine:
    """
    Mathematical Core of the Alignment Protocol.
    Implements Entropy-Weighting, Kalman Filtering, and Bayesian Bootstrapping.
    """
    
    def __init__(self, convergence_threshold: int = 20):
        self.convergence_threshold = convergence_threshold
        # Kalman Filter state: [filtered_value, estimation_error]
        self.kalman_state = [0.0, 1.0] 
        self.process_variance = 1e-5
        self.measurement_variance = 0.1

    def filter_user_score(self, raw_score: float) -> float:
        """1D Kalman Filter to reduce 'Human Noise' in user ratings."""
        # Prediction
        p = self.kalman_state[1] + self.process_variance
        
        # Update
        kalman_gain = p / (p + self.measurement_variance)
        self.kalman_state[0] = self.kalman_state[0] + kalman_gain * (raw_score - self.kalman_state[0])
        self.kalman_state[1] = (1 - kalman_gain) * p
        
        return float(self.kalman_state[0])

    def compute_alignment_objective(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Computes the entropy-weighted objective.
        Uses Bayesian Bootstrapping (flat weights) for N < convergence_threshold.
        """
        n = len(df)
        metrics = ['pearson_r', 'knowledge_gain', 'stability_score']
        
        if n == 0:
            return {"objective": 0.5, "weights": {m: 0.33 for m in metrics}, "phase": "Empty"}

        # Normalized inputs [0, 1]
        X_raw = df[metrics].copy()
        
        # Robust Normalization: If range is zero (sparse data), trust raw values or center them
        x_min = X_raw.min()
        x_max = X_raw.max()
        x_range = x_max - x_min
        
        # Apply normalization only where there is variance
        X = (X_raw - x_min) / (x_range + 1e-8)
        
        phase = "Cold Start"
        if n < 5:
            # Cold Start: Flat weights and trust raw values (don't zero out single data points)
            weights = np.array([1/3, 1/3, 1/3])
            X = X_raw # Use raw values [0,1] during cold start
        elif n < self.convergence_threshold:
            # Phase: Volatility-Adjusted weighting
            phase = "Volatility Phase"
            variances = X.var().values + 1e-8
            inv_variance = 1.0 / variances
            weights = inv_variance / inv_variance.sum()
        else:
            # Phase: Entropy weighting (Divergence-based)
            phase = "Entropy Phase"
            # Ensure X is normalized [0,1] for entropy
            p = X / (X.sum() + 1e-8)
            entropy = -np.sum(p * np.log(p + 1e-8), axis=0) / np.log(n)
            divergence = 1 - entropy
            weights = divergence / (divergence.sum() + 1e-8)

        # Map weights back to metric names
        weights_dict = {m: float(w) for m, w in zip(metrics, weights)}
        
        # Final Objective (weighted sum of most recent row)
        latest_values = X.iloc[-1].values
        objective = np.dot(latest_values, weights)
        
        # Ensure JSON compliance: No NaN or Inf
        obj_val = float(np.nan_to_num(objective, nan=0.5, posinf=1.0, neginf=0.0))
        
        return {
            "objective": obj_val,
            "weights": weights_dict,
            "n": n,
            "phase": phase
        }

    def compute_commit_risk(self, lines_changed: int, complexity_delta: float, history: List[float]) -> float:
        """
        Calculates risk of 'Architectural Drift' or breakage.
        Uses Gumbel SF if history is sufficient, otherwise Z-score.
        """
        disruption = lines_changed * abs(complexity_delta)
        
        if len(history) < 20:
            # Z-score fallback
            if not history: return 0.1
            avg = np.mean(history)
            std = np.std(history) + 1e-8
            z = (disruption - avg) / std
            return float(1 / (1 + np.exp(-z))) # Sigmoid of Z
        
        # Gumbel Extreme Value audit
        params = gumbel_r.fit(history)
        risk = gumbel_r.sf(disruption, *params)
        return float(risk)

# Singleton instance
stats_engine = StatsEngine()
