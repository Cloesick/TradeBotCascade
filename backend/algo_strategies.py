"""
Advanced Algorithmic Trading Strategies
Based on "Algorithmic Short Selling with Python" by Laurent Bernut
"""

import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import Tuple, Dict, List


class RegimeDetector:
    """
    Detect market regimes using multiple methodologies:
    1. Floor/Ceiling methodology
    2. Range breakout (Turtle Trader)
    3. Moving average crossover
    """
    
    @staticmethod
    def regime_breakout(df: pd.DataFrame, high_col: str, low_col: str, window: int) -> pd.Series:
        """
        Range breakout regime: 1 for bull, -1 for bear
        """
        hl = np.where(
            df[high_col] == df[high_col].rolling(window).max(), 1,
            np.where(df[low_col] == df[low_col].rolling(window).min(), -1, np.nan)
        )
        return pd.Series(index=df.index, data=hl).fillna(method='ffill')
    
    @staticmethod
    def turtle_trader(df: pd.DataFrame, high_col: str, low_col: str, slow: int, fast: int) -> pd.Series:
        """
        Asymmetrical range breakout (Turtle Trader strategy)
        Enter on longer duration (slow), exit on faster duration (fast)
        """
        slow_regime = RegimeDetector.regime_breakout(df, high_col, low_col, slow)
        fast_regime = RegimeDetector.regime_breakout(df, high_col, low_col, fast)
        
        turtle = np.where(
            slow_regime == 1, np.where(fast_regime == 1, 1, 0),
            np.where(slow_regime == -1, np.where(fast_regime == -1, -1, 0), 0)
        )
        return pd.Series(index=df.index, data=turtle)
    
    @staticmethod
    def regime_sma(df: pd.DataFrame, close_col: str, st: int, lt: int) -> pd.Series:
        """
        Simple Moving Average crossover regime
        Bull +1: SMA_st >= SMA_lt, Bear -1: SMA_st <= SMA_lt
        """
        sma_lt = df[close_col].rolling(lt).mean()
        sma_st = df[close_col].rolling(st).mean()
        return np.sign(sma_st - sma_lt)
    
    @staticmethod
    def regime_ema(df: pd.DataFrame, close_col: str, st: int, lt: int) -> pd.Series:
        """
        Exponential Moving Average crossover regime
        Bull +1: EMA_st >= EMA_lt, Bear -1: EMA_st <= EMA_lt
        """
        ema_st = df[close_col].ewm(span=st, min_periods=st).mean()
        ema_lt = df[close_col].ewm(span=lt, min_periods=lt).mean()
        return np.sign(ema_st - ema_lt)
    
    @staticmethod
    def average_true_range(df: pd.DataFrame, high_col: str, low_col: str, close_col: str, n: int) -> pd.Series:
        """
        Calculate Average True Range (ATR) for volatility measurement
        """
        atr = (
            df[high_col].combine(df[close_col].shift(), max) - 
            df[low_col].combine(df[close_col].shift(), min)
        ).rolling(window=n).mean()
        return atr


class ProbabilityCalculator:
    """
    Calculate probabilities for stock price movements
    """
    
    @staticmethod
    def calculate_movement_probability(df: pd.DataFrame, close_col: str, 
                                      lookback: int = 252, 
                                      target_move: float = 0.05) -> Dict[str, float]:
        """
        Calculate probability of price movements based on historical data
        
        Args:
            df: DataFrame with price data
            close_col: Column name for closing prices
            lookback: Number of periods to look back
            target_move: Target percentage move (e.g., 0.05 for 5%)
        
        Returns:
            Dictionary with probabilities
        """
        returns = df[close_col].pct_change()
        recent_returns = returns.tail(lookback)
        
        # Calculate probabilities
        prob_up = (recent_returns > 0).sum() / len(recent_returns)
        prob_down = (recent_returns < 0).sum() / len(recent_returns)
        prob_target_up = (recent_returns > target_move).sum() / len(recent_returns)
        prob_target_down = (recent_returns < -target_move).sum() / len(recent_returns)
        
        # Calculate volatility-based probabilities
        volatility = recent_returns.std()
        mean_return = recent_returns.mean()
        
        # Z-score for target move
        z_score_up = (target_move - mean_return) / volatility if volatility > 0 else 0
        z_score_down = (-target_move - mean_return) / volatility if volatility > 0 else 0
        
        # Sharpe-like ratio
        sharpe = mean_return / volatility if volatility > 0 else 0
        
        return {
            'prob_up': float(prob_up),
            'prob_down': float(prob_down),
            'prob_target_up': float(prob_target_up),
            'prob_target_down': float(prob_target_down),
            'volatility': float(volatility),
            'mean_return': float(mean_return),
            'sharpe_ratio': float(sharpe),
            'z_score_up': float(z_score_up),
            'z_score_down': float(z_score_down)
        }
    
    @staticmethod
    def monte_carlo_simulation(df: pd.DataFrame, close_col: str, 
                               days_ahead: int = 30, 
                               simulations: int = 1000) -> Dict[str, any]:
        """
        Monte Carlo simulation for future price movements
        """
        returns = df[close_col].pct_change().dropna()
        last_price = df[close_col].iloc[-1]
        
        # Calculate statistics
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Run simulations
        simulation_results = []
        for _ in range(simulations):
            daily_returns = np.random.normal(mean_return, std_return, days_ahead)
            price_series = last_price * (1 + daily_returns).cumprod()
            simulation_results.append(price_series[-1])
        
        simulation_results = np.array(simulation_results)
        
        return {
            'mean_price': float(np.mean(simulation_results)),
            'median_price': float(np.median(simulation_results)),
            'std_price': float(np.std(simulation_results)),
            'percentile_5': float(np.percentile(simulation_results, 5)),
            'percentile_25': float(np.percentile(simulation_results, 25)),
            'percentile_75': float(np.percentile(simulation_results, 75)),
            'percentile_95': float(np.percentile(simulation_results, 95)),
            'prob_profit': float((simulation_results > last_price).sum() / simulations),
            'prob_loss': float((simulation_results < last_price).sum() / simulations),
            'current_price': float(last_price)
        }


class SegmentGauge:
    """
    Calculate segment gauges for different market conditions
    """
    
    @staticmethod
    def calculate_trend_strength(df: pd.DataFrame, close_col: str, periods: List[int] = [20, 50, 200]) -> Dict[str, float]:
        """
        Calculate trend strength across multiple timeframes
        """
        current_price = df[close_col].iloc[-1]
        results = {}
        
        for period in periods:
            if len(df) >= period:
                sma = df[close_col].rolling(period).mean().iloc[-1]
                distance = (current_price - sma) / sma
                results[f'sma_{period}_distance'] = float(distance)
                results[f'above_sma_{period}'] = float(current_price > sma)
        
        # Overall trend score (-1 to 1)
        distances = [v for k, v in results.items() if 'distance' in k]
        trend_score = np.mean(distances) if distances else 0
        results['trend_score'] = float(trend_score)
        results['trend_direction'] = 'bullish' if trend_score > 0 else 'bearish' if trend_score < 0 else 'neutral'
        
        return results
    
    @staticmethod
    def calculate_momentum_gauge(df: pd.DataFrame, close_col: str) -> Dict[str, float]:
        """
        Calculate momentum indicators
        """
        # Rate of Change (ROC) for different periods
        roc_5 = (df[close_col].iloc[-1] / df[close_col].iloc[-6] - 1) if len(df) >= 6 else 0
        roc_10 = (df[close_col].iloc[-1] / df[close_col].iloc[-11] - 1) if len(df) >= 11 else 0
        roc_20 = (df[close_col].iloc[-1] / df[close_col].iloc[-21] - 1) if len(df) >= 21 else 0
        
        # Momentum score
        momentum_score = (roc_5 * 0.5 + roc_10 * 0.3 + roc_20 * 0.2)
        
        return {
            'roc_5d': float(roc_5),
            'roc_10d': float(roc_10),
            'roc_20d': float(roc_20),
            'momentum_score': float(momentum_score),
            'momentum_direction': 'strong_up' if momentum_score > 0.05 else 'up' if momentum_score > 0 else 'down' if momentum_score > -0.05 else 'strong_down'
        }
    
    @staticmethod
    def calculate_volatility_gauge(df: pd.DataFrame, close_col: str, high_col: str, low_col: str) -> Dict[str, float]:
        """
        Calculate volatility metrics
        """
        returns = df[close_col].pct_change()
        
        # Historical volatility (annualized)
        hist_vol_20 = returns.tail(20).std() * np.sqrt(252) if len(returns) >= 20 else 0
        hist_vol_60 = returns.tail(60).std() * np.sqrt(252) if len(returns) >= 60 else 0
        
        # ATR-based volatility
        atr_14 = RegimeDetector.average_true_range(df, high_col, low_col, close_col, 14).iloc[-1] if len(df) >= 14 else 0
        atr_pct = (atr_14 / df[close_col].iloc[-1]) if df[close_col].iloc[-1] > 0 else 0
        
        # Volatility regime
        vol_ratio = hist_vol_20 / hist_vol_60 if hist_vol_60 > 0 else 1
        
        return {
            'hist_vol_20d': float(hist_vol_20),
            'hist_vol_60d': float(hist_vol_60),
            'atr_14': float(atr_14),
            'atr_percent': float(atr_pct),
            'volatility_ratio': float(vol_ratio),
            'volatility_regime': 'expanding' if vol_ratio > 1.2 else 'contracting' if vol_ratio < 0.8 else 'stable'
        }


class ShortSellingSignals:
    """
    Generate short-selling signals based on algorithmic analysis
    """
    
    @staticmethod
    def generate_short_signal(df: pd.DataFrame, close_col: str, high_col: str, low_col: str) -> Dict[str, any]:
        """
        Generate comprehensive short-selling signal
        """
        # Regime detection
        regime_sma = RegimeDetector.regime_sma(df, close_col, 50, 200).iloc[-1]
        regime_turtle = RegimeDetector.turtle_trader(df, high_col, low_col, 50, 20).iloc[-1]
        
        # Probability analysis
        prob_calc = ProbabilityCalculator.calculate_movement_probability(df, close_col)
        
        # Segment gauges
        trend_gauge = SegmentGauge.calculate_trend_strength(df, close_col)
        momentum_gauge = SegmentGauge.calculate_momentum_gauge(df, close_col)
        volatility_gauge = SegmentGauge.calculate_volatility_gauge(df, close_col, high_col, low_col)
        
        # Short signal score (-10 to 0, more negative = stronger short signal)
        short_score = 0
        
        # Regime signals
        if regime_sma < 0:
            short_score -= 2
        if regime_turtle < 0:
            short_score -= 2
        
        # Trend signals
        if trend_gauge['trend_score'] < -0.05:
            short_score -= 2
        
        # Momentum signals
        if momentum_gauge['momentum_score'] < -0.03:
            short_score -= 2
        
        # Probability signals
        if prob_calc['prob_down'] > 0.55:
            short_score -= 1
        if prob_calc['sharpe_ratio'] < -0.5:
            short_score -= 1
        
        # Determine signal
        if short_score <= -6:
            signal = 'STRONG SHORT'
        elif short_score <= -3:
            signal = 'SHORT'
        elif short_score >= -1:
            signal = 'NO SHORT'
        else:
            signal = 'WEAK SHORT'
        
        return {
            'signal': signal,
            'score': int(short_score),
            'regime_sma': int(regime_sma),
            'regime_turtle': int(regime_turtle),
            'trend_direction': trend_gauge['trend_direction'],
            'momentum_direction': momentum_gauge['momentum_direction'],
            'volatility_regime': volatility_gauge['volatility_regime'],
            'probability_down': prob_calc['prob_down'],
            'sharpe_ratio': prob_calc['sharpe_ratio'],
            'confidence': 'high' if abs(short_score) >= 6 else 'medium' if abs(short_score) >= 3 else 'low'
        }
