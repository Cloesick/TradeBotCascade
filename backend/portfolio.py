"""
Portfolio Management System
Multi-stock position tracking, risk allocation, and optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class Position:
    """Individual stock position"""
    symbol: str
    shares: float
    entry_price: float
    entry_date: str
    current_price: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    @property
    def market_value(self) -> float:
        return self.shares * self.current_price
    
    @property
    def cost_basis(self) -> float:
        return self.shares * self.entry_price
    
    @property
    def unrealized_pnl(self) -> float:
        return self.market_value - self.cost_basis
    
    @property
    def unrealized_pnl_pct(self) -> float:
        return (self.current_price / self.entry_price - 1) * 100 if self.entry_price > 0 else 0
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'market_value': self.market_value,
            'cost_basis': self.cost_basis,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_pct': self.unrealized_pnl_pct
        }


class PortfolioManager:
    """
    Comprehensive portfolio management system
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Dict] = []
        
    def add_position(self, symbol: str, shares: float, price: float, 
                    stop_loss: Optional[float] = None, 
                    take_profit: Optional[float] = None) -> Dict:
        """Add or update a position"""
        
        cost = shares * price
        
        if cost > self.cash:
            return {
                'success': False,
                'message': f'Insufficient funds. Need ${cost:.2f}, have ${self.cash:.2f}'
            }
        
        if symbol in self.positions:
            # Update existing position (average up/down)
            existing = self.positions[symbol]
            total_shares = existing.shares + shares
            total_cost = existing.cost_basis + cost
            avg_price = total_cost / total_shares
            
            existing.shares = total_shares
            existing.entry_price = avg_price
        else:
            # Create new position
            self.positions[symbol] = Position(
                symbol=symbol,
                shares=shares,
                entry_price=price,
                entry_date=datetime.now().isoformat(),
                current_price=price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
        
        self.cash -= cost
        
        return {
            'success': True,
            'message': f'Added {shares} shares of {symbol} at ${price:.2f}',
            'position': self.positions[symbol].to_dict()
        }
    
    def close_position(self, symbol: str, price: float, shares: Optional[float] = None) -> Dict:
        """Close a position (full or partial)"""
        
        if symbol not in self.positions:
            return {
                'success': False,
                'message': f'No position found for {symbol}'
            }
        
        position = self.positions[symbol]
        shares_to_close = shares if shares else position.shares
        
        if shares_to_close > position.shares:
            return {
                'success': False,
                'message': f'Cannot close {shares_to_close} shares, only {position.shares} available'
            }
        
        # Calculate P&L
        proceeds = shares_to_close * price
        cost = shares_to_close * position.entry_price
        pnl = proceeds - cost
        pnl_pct = (price / position.entry_price - 1) * 100
        
        # Record closed position
        self.closed_positions.append({
            'symbol': symbol,
            'shares': shares_to_close,
            'entry_price': position.entry_price,
            'exit_price': price,
            'entry_date': position.entry_date,
            'exit_date': datetime.now().isoformat(),
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
        
        self.cash += proceeds
        
        # Update or remove position
        if shares_to_close >= position.shares:
            del self.positions[symbol]
        else:
            position.shares -= shares_to_close
        
        return {
            'success': True,
            'message': f'Closed {shares_to_close} shares of {symbol} at ${price:.2f}',
            'pnl': pnl,
            'pnl_pct': pnl_pct
        }
    
    def update_prices(self, prices: Dict[str, float]):
        """Update current prices for all positions"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio metrics"""
        
        total_market_value = sum(pos.market_value for pos in self.positions.values())
        total_cost_basis = sum(pos.cost_basis for pos in self.positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        
        total_equity = self.cash + total_market_value
        total_return = (total_equity / self.initial_capital - 1) * 100
        
        # Realized P&L from closed positions
        total_realized_pnl = sum(pos['pnl'] for pos in self.closed_positions)
        
        # Position allocation
        allocations = {}
        for symbol, pos in self.positions.items():
            allocations[symbol] = {
                'value': pos.market_value,
                'weight_pct': (pos.market_value / total_equity * 100) if total_equity > 0 else 0,
                'unrealized_pnl': pos.unrealized_pnl,
                'unrealized_pnl_pct': pos.unrealized_pnl_pct
            }
        
        return {
            'total_equity': total_equity,
            'cash': self.cash,
            'invested': total_market_value,
            'cash_pct': (self.cash / total_equity * 100) if total_equity > 0 else 0,
            'invested_pct': (total_market_value / total_equity * 100) if total_equity > 0 else 0,
            'total_return_pct': total_return,
            'unrealized_pnl': total_unrealized_pnl,
            'realized_pnl': total_realized_pnl,
            'total_pnl': total_unrealized_pnl + total_realized_pnl,
            'num_positions': len(self.positions),
            'num_closed_trades': len(self.closed_positions),
            'allocations': allocations
        }
    
    def get_risk_metrics(self, volatilities: Dict[str, float]) -> Dict:
        """Calculate portfolio risk metrics"""
        
        total_equity = self.cash + sum(pos.market_value for pos in self.positions.values())
        
        if total_equity == 0:
            return {
                'portfolio_volatility': 0,
                'value_at_risk_95': 0,
                'value_at_risk_99': 0,
                'position_risks': {}
            }
        
        # Position-level risk
        position_risks = {}
        weighted_volatility = 0
        
        for symbol, pos in self.positions.items():
            vol = volatilities.get(symbol, 0)
            weight = pos.market_value / total_equity
            position_var = pos.market_value * vol * 1.65  # 95% confidence
            
            position_risks[symbol] = {
                'volatility': vol,
                'weight': weight,
                'value_at_risk_95': position_var,
                'risk_contribution': weight * vol
            }
            
            weighted_volatility += weight * vol
        
        # Portfolio VaR (simplified, assumes no correlation)
        portfolio_var_95 = total_equity * weighted_volatility * 1.65
        portfolio_var_99 = total_equity * weighted_volatility * 2.33
        
        return {
            'portfolio_volatility': weighted_volatility,
            'value_at_risk_95': portfolio_var_95,
            'value_at_risk_99': portfolio_var_99,
            'position_risks': position_risks
        }
    
    def optimize_allocation(self, target_symbols: List[str], 
                           expected_returns: Dict[str, float],
                           volatilities: Dict[str, float],
                           risk_tolerance: str = 'moderate') -> Dict:
        """
        Optimize portfolio allocation using risk-adjusted returns
        
        Args:
            target_symbols: List of symbols to include
            expected_returns: Expected annual returns for each symbol
            volatilities: Annual volatilities for each symbol
            risk_tolerance: 'conservative', 'moderate', 'aggressive'
        """
        
        # Risk tolerance multipliers
        risk_multipliers = {
            'conservative': 0.5,
            'moderate': 1.0,
            'aggressive': 1.5
        }
        
        multiplier = risk_multipliers.get(risk_tolerance, 1.0)
        
        # Calculate Sharpe ratios
        sharpe_ratios = {}
        for symbol in target_symbols:
            ret = expected_returns.get(symbol, 0)
            vol = volatilities.get(symbol, 0.01)
            sharpe = (ret / vol) if vol > 0 else 0
            sharpe_ratios[symbol] = max(sharpe, 0)  # No negative Sharpe
        
        # Normalize to get weights
        total_sharpe = sum(sharpe_ratios.values())
        
        if total_sharpe == 0:
            # Equal weight if no positive Sharpe ratios
            weights = {symbol: 1.0 / len(target_symbols) for symbol in target_symbols}
        else:
            weights = {symbol: sharpe / total_sharpe for symbol, sharpe in sharpe_ratios.items()}
        
        # Adjust for risk tolerance
        total_equity = self.cash + sum(pos.market_value for pos in self.positions.values())
        investable = total_equity * (0.7 + 0.2 * multiplier)  # 70-90% invested
        
        recommendations = {}
        for symbol, weight in weights.items():
            target_value = investable * weight
            recommendations[symbol] = {
                'weight': weight,
                'target_value': target_value,
                'sharpe_ratio': sharpe_ratios[symbol],
                'expected_return': expected_returns.get(symbol, 0),
                'volatility': volatilities.get(symbol, 0)
            }
        
        return {
            'risk_tolerance': risk_tolerance,
            'total_investable': investable,
            'cash_reserve': total_equity - investable,
            'recommendations': recommendations
        }
    
    def rebalance_recommendations(self, target_weights: Dict[str, float]) -> List[Dict]:
        """
        Generate rebalancing trades to reach target weights
        """
        total_equity = self.cash + sum(pos.market_value for pos in self.positions.values())
        
        recommendations = []
        
        for symbol, target_weight in target_weights.items():
            target_value = total_equity * target_weight
            
            if symbol in self.positions:
                current_value = self.positions[symbol].market_value
                current_price = self.positions[symbol].current_price
            else:
                current_value = 0
                current_price = 0
            
            difference = target_value - current_value
            
            if abs(difference) > total_equity * 0.01:  # Only if > 1% of portfolio
                if difference > 0:
                    action = 'BUY'
                    shares = difference / current_price if current_price > 0 else 0
                else:
                    action = 'SELL'
                    shares = abs(difference) / current_price if current_price > 0 else 0
                
                recommendations.append({
                    'symbol': symbol,
                    'action': action,
                    'shares': shares,
                    'value': abs(difference),
                    'current_weight': (current_value / total_equity) if total_equity > 0 else 0,
                    'target_weight': target_weight
                })
        
        return recommendations
