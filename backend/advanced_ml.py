"""
Advanced Machine Learning Techniques
Based on "Advances in Financial Machine Learning" by Marcos López de Prado
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import KFold
from sklearn.ensemble import RandomForestClassifier
import warnings
warnings.filterwarnings('ignore')


class TripleBarrierLabeling:
    """
    Triple-Barrier Method for labeling financial data
    From López de Prado's "Advances in Financial Machine Learning"
    """
    
    @staticmethod
    def get_daily_volatility(close: pd.Series, span: int = 100) -> pd.Series:
        """
        Calculate daily volatility using exponential moving average
        """
        returns = close.pct_change()
        return returns.ewm(span=span).std()
    
    @staticmethod
    def apply_triple_barrier(
        close: pd.Series,
        events: pd.DatetimeIndex,
        pt_sl: List[float],
        molecule: Optional[pd.DatetimeIndex] = None,
        min_ret: float = 0.0,
        num_days: int = 10,
        t1: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """
        Apply triple-barrier labeling method
        
        Args:
            close: Close prices
            events: Event timestamps
            pt_sl: [profit_taking_multiple, stop_loss_multiple]
            molecule: Subset of events to process
            min_ret: Minimum return to trigger
            num_days: Maximum holding period
            t1: Optional vertical barrier timestamps
        
        Returns:
            DataFrame with labels and barrier info
        """
        # Get volatility
        target_vol = TripleBarrierLabeling.get_daily_volatility(close)
        
        # Vertical barrier (time-based)
        if t1 is None:
            t1 = pd.Series(
                close.index.searchsorted(events + pd.Timedelta(days=num_days)),
                index=events
            )
        
        # Horizontal barriers (profit-taking and stop-loss)
        if molecule is None:
            molecule = events
        
        out = pd.DataFrame(index=molecule)
        
        for loc, t0 in molecule.items():
            df0 = close[t0:t1[t0]]
            
            if df0.empty:
                continue
            
            # Calculate barriers
            vol = target_vol.loc[t0]
            pt = pt_sl[0] * vol  # Profit taking
            sl = -pt_sl[1] * vol  # Stop loss
            
            # Get returns
            ret = (df0 / close[t0] - 1)
            
            # Find first barrier touch
            out.loc[loc, 'pt'] = ret[ret > pt].index.min() if (ret > pt).any() else pd.NaT
            out.loc[loc, 'sl'] = ret[ret < sl].index.min() if (ret < sl).any() else pd.NaT
            out.loc[loc, 't1'] = t1[t0]
        
        return out
    
    @staticmethod
    def get_labels(
        close: pd.Series,
        events: pd.DatetimeIndex,
        pt_sl: List[float] = [1, 1],
        min_ret: float = 0.0,
        num_days: int = 10
    ) -> pd.Series:
        """
        Generate labels using triple-barrier method
        
        Returns:
            Series with labels: 1 (long), -1 (short), 0 (no position)
        """
        barriers = TripleBarrierLabeling.apply_triple_barrier(
            close, events, pt_sl, min_ret=min_ret, num_days=num_days
        )
        
        labels = pd.Series(index=events, dtype=float)
        
        for idx in barriers.index:
            pt = barriers.loc[idx, 'pt']
            sl = barriers.loc[idx, 'sl']
            t1 = barriers.loc[idx, 't1']
            
            # Determine which barrier was hit first
            if pd.notna(pt) and pd.notna(sl):
                if pt < sl:
                    labels[idx] = 1  # Profit target hit first
                else:
                    labels[idx] = -1  # Stop loss hit first
            elif pd.notna(pt):
                labels[idx] = 1
            elif pd.notna(sl):
                labels[idx] = -1
            else:
                # Vertical barrier hit, check return
                ret = close[t1] / close[idx] - 1
                labels[idx] = np.sign(ret)
        
        return labels


class PurgedKFold:
    """
    Purged K-Fold Cross-Validation
    Prevents data leakage in time-series data
    From López de Prado's "Advances in Financial Machine Learning"
    """
    
    def __init__(self, n_splits: int = 5, pct_embargo: float = 0.01):
        """
        Args:
            n_splits: Number of folds
            pct_embargo: Percentage of data to embargo after each test set
        """
        self.n_splits = n_splits
        self.pct_embargo = pct_embargo
    
    def split(self, X: pd.DataFrame, y: pd.Series = None, groups: pd.Series = None):
        """
        Generate purged train/test splits
        
        Args:
            X: Features
            y: Labels
            groups: Optional group labels (e.g., event end times)
        
        Yields:
            train_indices, test_indices
        """
        if groups is None:
            groups = pd.Series(index=X.index, data=X.index)
        
        # Get unique groups
        unique_groups = groups.unique()
        n_groups = len(unique_groups)
        
        # Calculate embargo size
        embargo_size = int(n_groups * self.pct_embargo)
        
        # Generate splits
        test_size = n_groups // self.n_splits
        
        for i in range(self.n_splits):
            # Test set
            test_start = i * test_size
            test_end = test_start + test_size if i < self.n_splits - 1 else n_groups
            test_groups = unique_groups[test_start:test_end]
            
            # Embargo: remove data after test set
            embargo_start = test_end
            embargo_end = min(embargo_start + embargo_size, n_groups)
            embargo_groups = unique_groups[embargo_start:embargo_end]
            
            # Train set: all data except test and embargo
            train_groups = np.concatenate([
                unique_groups[:test_start],
                unique_groups[embargo_end:]
            ])
            
            # Get indices
            test_indices = X.index[groups.isin(test_groups)]
            train_indices = X.index[groups.isin(train_groups)]
            
            yield train_indices, test_indices


class FeatureImportance:
    """
    Feature Importance Analysis
    Using Mean Decrease Impurity (MDI) and Mean Decrease Accuracy (MDA)
    """
    
    @staticmethod
    def get_mdi_importance(
        model: RandomForestClassifier,
        feature_names: List[str]
    ) -> pd.DataFrame:
        """
        Mean Decrease Impurity (MDI) feature importance
        """
        importance = pd.DataFrame({
            'feature': feature_names,
            'importance': model.feature_importances_
        })
        importance = importance.sort_values('importance', ascending=False)
        importance['cumulative'] = importance['importance'].cumsum()
        
        return importance
    
    @staticmethod
    def get_mda_importance(
        model: RandomForestClassifier,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        n_iterations: int = 5
    ) -> pd.DataFrame:
        """
        Mean Decrease Accuracy (MDA) feature importance
        Measures impact of shuffling each feature
        """
        # Baseline score
        baseline_score = model.score(X_test, y_test)
        
        importance_scores = {}
        
        for col in X_test.columns:
            scores = []
            
            for _ in range(n_iterations):
                # Shuffle feature
                X_shuffled = X_test.copy()
                X_shuffled[col] = np.random.permutation(X_shuffled[col].values)
                
                # Calculate score
                score = model.score(X_shuffled, y_test)
                scores.append(baseline_score - score)
            
            importance_scores[col] = np.mean(scores)
        
        importance = pd.DataFrame({
            'feature': list(importance_scores.keys()),
            'importance': list(importance_scores.values())
        })
        importance = importance.sort_values('importance', ascending=False)
        importance['cumulative'] = importance['importance'].cumsum()
        
        return importance


class FractionalDifferentiation:
    """
    Fractional Differentiation for achieving stationarity
    While preserving memory
    """
    
    @staticmethod
    def get_weights(d: float, size: int) -> np.ndarray:
        """
        Calculate weights for fractional differentiation
        
        Args:
            d: Differentiation order (0 < d < 1)
            size: Number of weights
        """
        w = [1.0]
        for k in range(1, size):
            w.append(-w[-1] * (d - k + 1) / k)
        return np.array(w)
    
    @staticmethod
    def frac_diff(series: pd.Series, d: float, threshold: float = 0.01) -> pd.Series:
        """
        Apply fractional differentiation
        
        Args:
            series: Time series to differentiate
            d: Differentiation order
            threshold: Weight threshold for truncation
        """
        # Get weights
        weights = FractionalDifferentiation.get_weights(d, len(series))
        
        # Truncate small weights
        weights = weights[np.abs(weights) > threshold]
        
        # Apply convolution
        result = pd.Series(index=series.index, dtype=float)
        
        for i in range(len(weights), len(series)):
            result.iloc[i] = np.dot(weights, series.iloc[i-len(weights):i][::-1])
        
        return result.dropna()
    
    @staticmethod
    def find_min_d(series: pd.Series, max_d: float = 1.0, step: float = 0.01) -> float:
        """
        Find minimum d for stationarity using ADF test
        """
        from statsmodels.tsa.stattools import adfuller
        
        for d in np.arange(0, max_d + step, step):
            diff_series = FractionalDifferentiation.frac_diff(series, d)
            
            if len(diff_series) < 50:
                continue
            
            # ADF test
            adf_result = adfuller(diff_series.dropna(), maxlag=1, regression='c', autolag=None)
            
            if adf_result[1] < 0.05:  # p-value < 0.05 means stationary
                return d
        
        return max_d


class MetaLabeling:
    """
    Meta-Labeling: Use ML to size bets
    Primary model predicts direction, meta-model predicts size
    """
    
    @staticmethod
    def create_meta_labels(
        primary_predictions: pd.Series,
        actual_returns: pd.Series,
        threshold: float = 0.0
    ) -> pd.Series:
        """
        Create meta-labels for bet sizing
        
        Args:
            primary_predictions: Primary model predictions (1/-1)
            actual_returns: Actual returns
            threshold: Minimum return threshold
        
        Returns:
            Meta-labels: 1 if bet should be taken, 0 otherwise
        """
        meta_labels = pd.Series(index=primary_predictions.index, dtype=int)
        
        for idx in primary_predictions.index:
            pred = primary_predictions[idx]
            ret = actual_returns[idx]
            
            # Label as 1 if prediction was correct and profitable
            if (pred > 0 and ret > threshold) or (pred < 0 and ret < -threshold):
                meta_labels[idx] = 1
            else:
                meta_labels[idx] = 0
        
        return meta_labels
    
    @staticmethod
    def apply_meta_model(
        primary_predictions: pd.Series,
        meta_predictions: pd.Series,
        base_size: float = 1.0
    ) -> pd.Series:
        """
        Apply meta-model to size bets
        
        Args:
            primary_predictions: Direction predictions
            meta_predictions: Confidence predictions (0-1)
            base_size: Base position size
        
        Returns:
            Sized positions
        """
        positions = pd.Series(index=primary_predictions.index, dtype=float)
        
        for idx in primary_predictions.index:
            direction = primary_predictions[idx]
            confidence = meta_predictions[idx]
            
            # Size position based on confidence
            positions[idx] = direction * confidence * base_size
        
        return positions


class BetSizing:
    """
    Advanced bet sizing techniques
    """
    
    @staticmethod
    def kelly_criterion(
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Calculate Kelly Criterion for optimal bet size
        
        Args:
            win_rate: Probability of winning (0-1)
            avg_win: Average win amount
            avg_loss: Average loss amount (positive)
        
        Returns:
            Optimal fraction of capital to bet
        """
        if avg_loss == 0:
            return 0
        
        b = avg_win / avg_loss  # Win/loss ratio
        p = win_rate
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Apply safety factor (use half Kelly)
        return max(0, kelly * 0.5)
    
    @staticmethod
    def dynamic_position_sizing(
        signal_strength: float,
        volatility: float,
        max_risk: float = 0.02,
        base_size: float = 1.0
    ) -> float:
        """
        Dynamic position sizing based on signal strength and volatility
        
        Args:
            signal_strength: Signal strength (0-1)
            volatility: Current volatility
            max_risk: Maximum risk per trade
            base_size: Base position size
        
        Returns:
            Position size
        """
        # Adjust for volatility (inverse relationship)
        vol_adjustment = 1.0 / (1.0 + volatility)
        
        # Combine signal strength and volatility
        size = base_size * signal_strength * vol_adjustment
        
        # Cap at max risk
        size = min(size, max_risk)
        
        return size
