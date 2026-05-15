"""
WorldMonitor 7-Signal Macro Radar Trading Strategy

Based on WorldMonitor.app's macro radar that synthesizes 7 independent signals
into a composite BUY or CASH verdict for risk-on vs risk-off positioning.

The 7 signals typically include:
1. Central Bank Policy (interest rates, QE/QT)
2. Credit Spreads (corporate bond spreads)
3. Volatility Index (VIX)
4. Currency Strength (USD index)
5. Commodity Prices (oil, gold)
6. Yield Curve (10Y-2Y spread)
7. Market Breadth (advance/decline ratio)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from enum import Enum


class MacroSignal(str, Enum):
    """Macro signal types"""
    BUY = "BUY"          # Risk-on
    CASH = "CASH"        # Risk-off
    NEUTRAL = "NEUTRAL"  # Mixed signals


class SignalStrength(str, Enum):
    """Signal strength levels"""
    STRONG_BUY = "STRONG_BUY"      # 6-7 bullish signals
    BUY = "BUY"                     # 4-5 bullish signals
    NEUTRAL = "NEUTRAL"             # 3-4 mixed signals
    CASH = "CASH"                   # 4-5 bearish signals
    STRONG_CASH = "STRONG_CASH"    # 6-7 bearish signals


class WorldMonitorStrategy:
    """
    Trading strategy based on WorldMonitor's 7-signal macro radar
    
    This strategy doesn't pick individual stocks, but determines whether
    the macro environment favors risk-on (BUY) or risk-off (CASH) positioning.
    """
    
    def __init__(self):
        self.signal_weights = {
            'central_bank': 1.5,    # Highest weight - rates drive everything
            'credit_spreads': 1.2,  # Credit markets lead equity
            'volatility': 1.0,      # VIX as fear gauge
            'currency': 1.0,        # USD strength
            'commodities': 0.8,     # Oil and gold
            'yield_curve': 1.2,     # Recession indicator
            'market_breadth': 1.0   # Internal market health
        }
        
        self.signal_history = []
        self.position_size_multiplier = {
            SignalStrength.STRONG_BUY: 1.0,
            SignalStrength.BUY: 0.7,
            SignalStrength.NEUTRAL: 0.3,
            SignalStrength.CASH: 0.0,
            SignalStrength.STRONG_CASH: 0.0
        }
    
    def analyze_central_bank_policy(self, df: pd.DataFrame) -> Dict:
        """
        Signal 1: Central Bank Policy
        
        Bullish: Rate cuts, QE, dovish stance
        Bearish: Rate hikes, QT, hawkish stance
        """
        # Proxy: Use interest rate changes via bond yields
        if 'Close' not in df.columns or len(df) < 60:
            return {'signal': 0, 'confidence': 0.5, 'reason': 'Insufficient data'}
        
        # Calculate rate of change in yields (inverse relationship with stocks)
        recent_change = df['Close'].pct_change(20).iloc[-1]
        
        if recent_change < -0.02:  # Yields falling = bullish
            signal = 1
            reason = "Falling yields suggest dovish policy"
        elif recent_change > 0.02:  # Yields rising = bearish
            signal = -1
            reason = "Rising yields suggest hawkish policy"
        else:
            signal = 0
            reason = "Stable yields, neutral policy"
        
        return {
            'signal': signal,
            'confidence': min(abs(recent_change) * 50, 1.0),
            'reason': reason,
            'value': recent_change
        }
    
    def analyze_credit_spreads(self, df: pd.DataFrame) -> Dict:
        """
        Signal 2: Credit Spreads
        
        Bullish: Tightening spreads (low risk premium)
        Bearish: Widening spreads (high risk premium)
        """
        # Proxy: Use volatility as credit stress indicator
        if len(df) < 20:
            return {'signal': 0, 'confidence': 0.5, 'reason': 'Insufficient data'}
        
        # Calculate rolling volatility
        returns = df['Close'].pct_change()
        recent_vol = returns.rolling(20).std().iloc[-1]
        avg_vol = returns.rolling(60).std().mean()
        
        if recent_vol < avg_vol * 0.8:  # Low volatility = tight spreads
            signal = 1
            reason = "Low volatility suggests tight credit spreads"
        elif recent_vol > avg_vol * 1.2:  # High volatility = wide spreads
            signal = -1
            reason = "High volatility suggests wide credit spreads"
        else:
            signal = 0
            reason = "Normal volatility, neutral spreads"
        
        return {
            'signal': signal,
            'confidence': min(abs(recent_vol - avg_vol) / avg_vol, 1.0),
            'reason': reason,
            'value': recent_vol / avg_vol
        }
    
    def analyze_volatility_index(self, df: pd.DataFrame) -> Dict:
        """
        Signal 3: Volatility Index (VIX proxy)
        
        Bullish: VIX < 15 (complacency)
        Bearish: VIX > 25 (fear)
        """
        if len(df) < 20:
            return {'signal': 0, 'confidence': 0.5, 'reason': 'Insufficient data'}
        
        # Calculate realized volatility as VIX proxy
        returns = df['Close'].pct_change()
        realized_vol = returns.rolling(20).std().iloc[-1] * np.sqrt(252) * 100
        
        if realized_vol < 15:
            signal = 1
            reason = f"Low volatility ({realized_vol:.1f}) - risk-on environment"
        elif realized_vol > 25:
            signal = -1
            reason = f"High volatility ({realized_vol:.1f}) - risk-off environment"
        else:
            signal = 0
            reason = f"Moderate volatility ({realized_vol:.1f}) - neutral"
        
        return {
            'signal': signal,
            'confidence': 0.8,
            'reason': reason,
            'value': realized_vol
        }
    
    def analyze_currency_strength(self, df: pd.DataFrame) -> Dict:
        """
        Signal 4: Currency Strength (USD)
        
        Bullish: Weak USD (good for risk assets)
        Bearish: Strong USD (flight to safety)
        """
        if len(df) < 60:
            return {'signal': 0, 'confidence': 0.5, 'reason': 'Insufficient data'}
        
        # Proxy: Use momentum - strong trends often correlate with USD moves
        sma_20 = df['Close'].rolling(20).mean().iloc[-1]
        sma_60 = df['Close'].rolling(60).mean().iloc[-1]
        
        momentum = (sma_20 - sma_60) / sma_60
        
        if momentum > 0.02:  # Strong uptrend = weak USD (bullish)
            signal = 1
            reason = "Strong momentum suggests weak USD"
        elif momentum < -0.02:  # Strong downtrend = strong USD (bearish)
            signal = -1
            reason = "Weak momentum suggests strong USD"
        else:
            signal = 0
            reason = "Neutral momentum, neutral USD"
        
        return {
            'signal': signal,
            'confidence': min(abs(momentum) * 50, 1.0),
            'reason': reason,
            'value': momentum
        }
    
    def analyze_commodities(self, df: pd.DataFrame) -> Dict:
        """
        Signal 5: Commodity Prices (Oil, Gold)
        
        Bullish: Rising oil (growth), stable gold
        Bearish: Falling oil (recession), rising gold (fear)
        """
        if len(df) < 30:
            return {'signal': 0, 'confidence': 0.5, 'reason': 'Insufficient data'}
        
        # Proxy: Use price momentum as commodity proxy
        price_change_30d = df['Close'].pct_change(30).iloc[-1]
        
        if price_change_30d > 0.05:  # Rising prices = growth
            signal = 1
            reason = "Rising prices suggest commodity strength"
        elif price_change_30d < -0.05:  # Falling prices = weakness
            signal = -1
            reason = "Falling prices suggest commodity weakness"
        else:
            signal = 0
            reason = "Stable prices, neutral commodities"
        
        return {
            'signal': signal,
            'confidence': min(abs(price_change_30d) * 10, 1.0),
            'reason': reason,
            'value': price_change_30d
        }
    
    def analyze_yield_curve(self, df: pd.DataFrame) -> Dict:
        """
        Signal 6: Yield Curve (10Y-2Y spread)
        
        Bullish: Steep curve (growth expectations)
        Bearish: Inverted curve (recession warning)
        """
        if len(df) < 60:
            return {'signal': 0, 'confidence': 0.5, 'reason': 'Insufficient data'}
        
        # Proxy: Use trend slope as yield curve proxy
        # Steepening trend = steepening curve
        x = np.arange(len(df.tail(60)))
        y = df['Close'].tail(60).values
        slope = np.polyfit(x, y, 1)[0]
        
        normalized_slope = slope / df['Close'].iloc[-1] * 100
        
        if normalized_slope > 0.1:  # Uptrend = steep curve
            signal = 1
            reason = "Uptrend suggests steepening yield curve"
        elif normalized_slope < -0.1:  # Downtrend = flat/inverted curve
            signal = -1
            reason = "Downtrend suggests flattening yield curve"
        else:
            signal = 0
            reason = "Neutral trend, neutral yield curve"
        
        return {
            'signal': signal,
            'confidence': 0.7,
            'reason': reason,
            'value': normalized_slope
        }
    
    def analyze_market_breadth(self, df: pd.DataFrame) -> Dict:
        """
        Signal 7: Market Breadth
        
        Bullish: Broad participation (many stocks rising)
        Bearish: Narrow leadership (few stocks rising)
        """
        if len(df) < 50:
            return {'signal': 0, 'confidence': 0.5, 'reason': 'Insufficient data'}
        
        # Proxy: Use price vs moving averages as breadth indicator
        sma_50 = df['Close'].rolling(50).mean().iloc[-1]
        sma_200 = df['Close'].rolling(200).mean().iloc[-1] if len(df) >= 200 else sma_50
        current_price = df['Close'].iloc[-1]
        
        above_50 = current_price > sma_50
        above_200 = current_price > sma_200
        
        if above_50 and above_200:
            signal = 1
            reason = "Price above both SMAs - broad strength"
        elif not above_50 and not above_200:
            signal = -1
            reason = "Price below both SMAs - broad weakness"
        else:
            signal = 0
            reason = "Mixed signals - neutral breadth"
        
        return {
            'signal': signal,
            'confidence': 0.8,
            'reason': reason,
            'value': (current_price - sma_50) / sma_50
        }
    
    def calculate_composite_signal(self, df: pd.DataFrame) -> Dict:
        """
        Calculate composite macro signal from all 7 indicators
        
        Returns BUY, CASH, or NEUTRAL with confidence and breakdown
        """
        # Analyze all 7 signals
        signals = {
            'central_bank': self.analyze_central_bank_policy(df),
            'credit_spreads': self.analyze_credit_spreads(df),
            'volatility': self.analyze_volatility_index(df),
            'currency': self.analyze_currency_strength(df),
            'commodities': self.analyze_commodities(df),
            'yield_curve': self.analyze_yield_curve(df),
            'market_breadth': self.analyze_market_breadth(df)
        }
        
        # Calculate weighted score
        total_score = 0
        total_weight = 0
        bullish_count = 0
        bearish_count = 0
        
        for name, result in signals.items():
            weight = self.signal_weights[name]
            signal_value = result['signal']
            confidence = result['confidence']
            
            weighted_signal = signal_value * weight * confidence
            total_score += weighted_signal
            total_weight += weight * confidence
            
            if signal_value > 0:
                bullish_count += 1
            elif signal_value < 0:
                bearish_count += 1
        
        # Normalize score
        normalized_score = total_score / total_weight if total_weight > 0 else 0
        
        # Determine signal strength
        if bullish_count >= 6:
            strength = SignalStrength.STRONG_BUY
        elif bullish_count >= 4:
            strength = SignalStrength.BUY
        elif bearish_count >= 6:
            strength = SignalStrength.STRONG_CASH
        elif bearish_count >= 4:
            strength = SignalStrength.CASH
        else:
            strength = SignalStrength.NEUTRAL
        
        # Determine macro signal
        if normalized_score > 0.3:
            macro_signal = MacroSignal.BUY
        elif normalized_score < -0.3:
            macro_signal = MacroSignal.CASH
        else:
            macro_signal = MacroSignal.NEUTRAL
        
        return {
            'macro_signal': macro_signal.value,
            'signal_strength': strength.value,
            'composite_score': normalized_score,
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'neutral_signals': 7 - bullish_count - bearish_count,
            'position_size_multiplier': self.position_size_multiplier[strength],
            'signals_breakdown': signals,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def generate_trading_decision(self, df: pd.DataFrame, current_position: float = 0) -> Dict:
        """
        Generate trading decision based on macro signals
        
        Args:
            df: Price dataframe
            current_position: Current position size (0 = no position, 1 = full position)
        
        Returns:
            Trading decision with action, size, and reasoning
        """
        composite = self.calculate_composite_signal(df)
        
        macro_signal = composite['macro_signal']
        strength = composite['signal_strength']
        target_size = composite['position_size_multiplier']
        
        # Determine action
        if target_size > current_position + 0.1:
            action = "BUY"
            size_change = target_size - current_position
            reason = f"Macro environment is {macro_signal} ({strength}). Increase exposure."
        elif target_size < current_position - 0.1:
            action = "SELL"
            size_change = current_position - target_size
            reason = f"Macro environment is {macro_signal} ({strength}). Reduce exposure."
        else:
            action = "HOLD"
            size_change = 0
            reason = f"Macro environment is {macro_signal} ({strength}). Maintain current position."
        
        return {
            'action': action,
            'current_position': current_position,
            'target_position': target_size,
            'size_change': size_change,
            'macro_signal': macro_signal,
            'signal_strength': strength,
            'composite_score': composite['composite_score'],
            'reason': reason,
            'signals_summary': {
                'bullish': composite['bullish_signals'],
                'bearish': composite['bearish_signals'],
                'neutral': composite['neutral_signals']
            },
            'detailed_signals': composite['signals_breakdown'],
            'timestamp': composite['timestamp']
        }
    
    def backtest_strategy(self, df: pd.DataFrame, initial_capital: float = 100000) -> Dict:
        """
        Backtest the WorldMonitor strategy
        
        Returns performance metrics
        """
        if len(df) < 200:
            return {'error': 'Insufficient data for backtesting'}
        
        capital = initial_capital
        position = 0
        position_size = 0
        trades = []
        equity_curve = []
        
        for i in range(200, len(df)):
            current_df = df.iloc[:i]
            current_price = df.iloc[i]['Close']
            
            # Get trading decision
            decision = self.generate_trading_decision(current_df, position_size)
            
            # Execute trade
            if decision['action'] == 'BUY' and decision['size_change'] > 0:
                # Buy more
                buy_amount = capital * decision['size_change']
                shares_to_buy = buy_amount / current_price
                position += shares_to_buy
                capital -= buy_amount
                position_size = decision['target_position']
                
                trades.append({
                    'date': df.index[i],
                    'action': 'BUY',
                    'price': current_price,
                    'shares': shares_to_buy,
                    'amount': buy_amount,
                    'signal': decision['macro_signal']
                })
            
            elif decision['action'] == 'SELL' and decision['size_change'] > 0:
                # Sell some
                shares_to_sell = position * decision['size_change']
                sell_amount = shares_to_sell * current_price
                position -= shares_to_sell
                capital += sell_amount
                position_size = decision['target_position']
                
                trades.append({
                    'date': df.index[i],
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares_to_sell,
                    'amount': sell_amount,
                    'signal': decision['macro_signal']
                })
            
            # Calculate equity
            total_equity = capital + (position * current_price)
            equity_curve.append({
                'date': df.index[i],
                'equity': total_equity,
                'position_size': position_size
            })
        
        # Calculate metrics
        final_equity = equity_curve[-1]['equity']
        total_return = (final_equity - initial_capital) / initial_capital * 100
        
        equity_series = pd.Series([e['equity'] for e in equity_curve])
        returns = equity_series.pct_change().dropna()
        
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        max_drawdown = ((equity_series.cummax() - equity_series) / equity_series.cummax()).max() * 100
        
        return {
            'initial_capital': initial_capital,
            'final_equity': final_equity,
            'total_return_pct': total_return,
            'total_trades': len(trades),
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown,
            'trades': trades,
            'equity_curve': equity_curve
        }
