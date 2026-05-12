"""
Enhanced Backtesting Engine
Comprehensive strategy testing with performance metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime


class BacktestEngine:
    """
    Professional backtesting engine with performance analytics
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
    def run_strategy(self, df: pd.DataFrame, strategy_signals: pd.Series) -> Dict:
        """
        Run backtest with given strategy signals
        
        Args:
            df: DataFrame with OHLC data
            strategy_signals: Series with 1 (buy), -1 (sell), 0 (hold)
        
        Returns:
            Performance metrics dictionary
        """
        position = 0
        entry_price = 0
        equity = self.initial_capital
        
        for i in range(len(df)):
            date = df.index[i]
            close = df['Close'].iloc[i]
            signal = strategy_signals.iloc[i]
            
            # Entry logic
            if signal == 1 and position == 0:  # Buy signal
                shares = equity // close
                if shares > 0:
                    position = shares
                    entry_price = close
                    cost = shares * close
                    equity -= cost
                    
                    self.trades.append({
                        'date': date,
                        'type': 'BUY',
                        'price': close,
                        'shares': shares,
                        'value': cost
                    })
            
            # Exit logic
            elif signal == -1 and position > 0:  # Sell signal
                proceeds = position * close
                equity += proceeds
                
                pnl = (close - entry_price) * position
                pnl_pct = (close / entry_price - 1) * 100
                
                self.trades.append({
                    'date': date,
                    'type': 'SELL',
                    'price': close,
                    'shares': position,
                    'value': proceeds,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
                
                position = 0
                entry_price = 0
            
            # Calculate current equity
            current_equity = equity + (position * close if position > 0 else 0)
            self.equity_curve.append({
                'date': date,
                'equity': current_equity,
                'position': position,
                'price': close
            })
        
        # Calculate performance metrics
        metrics = self._calculate_metrics(df)
        
        return metrics
    
    def _calculate_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive performance metrics"""
        
        equity_df = pd.DataFrame(self.equity_curve)
        trades_df = pd.DataFrame(self.trades)
        
        # Basic metrics
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity / self.initial_capital - 1) * 100
        
        # Trade statistics
        sell_trades = trades_df[trades_df['type'] == 'SELL']
        num_trades = len(sell_trades)
        
        if num_trades > 0:
            winning_trades = sell_trades[sell_trades['pnl'] > 0]
            losing_trades = sell_trades[sell_trades['pnl'] < 0]
            
            win_rate = len(winning_trades) / num_trades * 100
            avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
            
            profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else float('inf')
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
        
        # Risk metrics
        equity_returns = equity_df['equity'].pct_change().dropna()
        
        # Sharpe Ratio (annualized)
        if len(equity_returns) > 0 and equity_returns.std() > 0:
            sharpe_ratio = (equity_returns.mean() / equity_returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # Maximum Drawdown
        equity_series = equity_df['equity']
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # Sortino Ratio (downside deviation)
        downside_returns = equity_returns[equity_returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino_ratio = (equity_returns.mean() / downside_returns.std()) * np.sqrt(252)
        else:
            sortino_ratio = 0
        
        # Calmar Ratio
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Win/Loss Ratio
        win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Average trade duration
        if num_trades > 0:
            buy_dates = trades_df[trades_df['type'] == 'BUY']['date']
            sell_dates = trades_df[trades_df['type'] == 'SELL']['date']
            
            if len(buy_dates) > 0 and len(sell_dates) > 0:
                durations = []
                for i in range(min(len(buy_dates), len(sell_dates))):
                    duration = (sell_dates.iloc[i] - buy_dates.iloc[i]).days
                    durations.append(duration)
                avg_trade_duration = np.mean(durations) if durations else 0
            else:
                avg_trade_duration = 0
        else:
            avg_trade_duration = 0
        
        return {
            'initial_capital': float(self.initial_capital),
            'final_equity': float(final_equity),
            'total_return_pct': float(total_return),
            'total_trades': int(num_trades),
            'winning_trades': int(len(winning_trades) if num_trades > 0 else 0),
            'losing_trades': int(len(losing_trades) if num_trades > 0 else 0),
            'win_rate_pct': float(win_rate),
            'profit_factor': float(profit_factor),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'win_loss_ratio': float(win_loss_ratio),
            'sharpe_ratio': float(sharpe_ratio),
            'sortino_ratio': float(sortino_ratio),
            'max_drawdown_pct': float(max_drawdown),
            'calmar_ratio': float(calmar_ratio),
            'avg_trade_duration_days': float(avg_trade_duration),
            'equity_curve': equity_df.to_dict('records'),
            'trades': trades_df.to_dict('records')
        }


class StrategyLibrary:
    """
    Collection of trading strategies for backtesting
    """
    
    @staticmethod
    def sma_crossover(df: pd.DataFrame, fast: int = 50, slow: int = 200) -> pd.Series:
        """
        Simple Moving Average Crossover Strategy
        Buy when fast SMA crosses above slow SMA
        Sell when fast SMA crosses below slow SMA
        """
        sma_fast = df['Close'].rolling(fast).mean()
        sma_slow = df['Close'].rolling(slow).mean()
        
        signals = pd.Series(0, index=df.index)
        signals[sma_fast > sma_slow] = 1
        signals[sma_fast < sma_slow] = -1
        
        # Generate actual trade signals (only on crossovers)
        trade_signals = signals.diff()
        trade_signals[trade_signals > 0] = 1  # Buy
        trade_signals[trade_signals < 0] = -1  # Sell
        trade_signals[trade_signals == 0] = 0  # Hold
        
        return trade_signals.fillna(0)
    
    @staticmethod
    def rsi_strategy(df: pd.DataFrame, period: int = 14, oversold: int = 30, overbought: int = 70) -> pd.Series:
        """
        RSI Mean Reversion Strategy
        Buy when RSI < oversold
        Sell when RSI > overbought
        """
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        signals = pd.Series(0, index=df.index)
        signals[rsi < oversold] = 1  # Buy
        signals[rsi > overbought] = -1  # Sell
        
        # Generate trade signals
        trade_signals = signals.diff()
        trade_signals[trade_signals > 0] = 1
        trade_signals[trade_signals < 0] = -1
        trade_signals[trade_signals == 0] = 0
        
        return trade_signals.fillna(0)
    
    @staticmethod
    def macd_strategy(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
        """
        MACD Strategy
        Buy when MACD crosses above signal line
        Sell when MACD crosses below signal line
        """
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        
        signals = pd.Series(0, index=df.index)
        signals[macd > macd_signal] = 1
        signals[macd < macd_signal] = -1
        
        # Generate trade signals
        trade_signals = signals.diff()
        trade_signals[trade_signals > 0] = 1
        trade_signals[trade_signals < 0] = -1
        trade_signals[trade_signals == 0] = 0
        
        return trade_signals.fillna(0)
    
    @staticmethod
    def bollinger_bands_strategy(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.Series:
        """
        Bollinger Bands Mean Reversion Strategy
        Buy when price touches lower band
        Sell when price touches upper band
        """
        sma = df['Close'].rolling(period).mean()
        std = df['Close'].rolling(period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        signals = pd.Series(0, index=df.index)
        signals[df['Close'] <= lower_band] = 1  # Buy
        signals[df['Close'] >= upper_band] = -1  # Sell
        
        # Generate trade signals
        trade_signals = signals.diff()
        trade_signals[trade_signals > 0] = 1
        trade_signals[trade_signals < 0] = -1
        trade_signals[trade_signals == 0] = 0
        
        return trade_signals.fillna(0)
    
    @staticmethod
    def turtle_trader_strategy(df: pd.DataFrame, entry_period: int = 50, exit_period: int = 20) -> pd.Series:
        """
        Turtle Trader Breakout Strategy
        Buy on 50-day high
        Sell on 20-day low
        """
        high_50 = df['High'].rolling(entry_period).max()
        low_20 = df['Low'].rolling(exit_period).min()
        
        signals = pd.Series(0, index=df.index)
        
        # Buy when price breaks above 50-day high
        buy_signal = df['High'] >= high_50.shift(1)
        # Sell when price breaks below 20-day low
        sell_signal = df['Low'] <= low_20.shift(1)
        
        signals[buy_signal] = 1
        signals[sell_signal] = -1
        
        return signals.fillna(0)
