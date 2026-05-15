# 🌍 WorldMonitor 7-Signal Macro Strategy Guide

## Overview

This strategy is based on **WorldMonitor.app's 7-signal macro radar** that synthesizes multiple macro indicators into a composite BUY or CASH verdict for risk-on vs risk-off positioning.

**Source:** [WorldMonitor Finance Dashboard](https://finance.worldmonitor.app/)

---

## 📊 The 7 Macro Signals

### **1. Central Bank Policy** (Weight: 1.5x)
**What it measures:** Interest rates, QE/QT, monetary policy stance

**Bullish Signals:**
- Rate cuts
- Quantitative Easing (QE)
- Dovish Fed/ECB statements
- Falling bond yields

**Bearish Signals:**
- Rate hikes
- Quantitative Tightening (QT)
- Hawkish central bank stance
- Rising bond yields

**Why it matters:** "Interest rates drive everything" - Central bank policy is the most important macro factor.

---

### **2. Credit Spreads** (Weight: 1.2x)
**What it measures:** Corporate bond spreads, credit risk premium

**Bullish Signals:**
- Tightening spreads (low risk premium)
- Easy credit conditions
- Low default rates

**Bearish Signals:**
- Widening spreads (high risk premium)
- Credit stress
- Rising default expectations

**Why it matters:** Credit markets lead equity markets. When credit spreads widen, stocks usually follow.

---

### **3. Volatility Index (VIX)** (Weight: 1.0x)
**What it measures:** Market fear gauge

**Bullish Signals:**
- VIX < 15 (complacency)
- Low realized volatility
- Calm markets

**Bearish Signals:**
- VIX > 25 (fear)
- High realized volatility
- Panic selling

**Why it matters:** Low volatility = risk-on environment. High volatility = risk-off.

---

### **4. Currency Strength (USD)** (Weight: 1.0x)
**What it measures:** US Dollar strength

**Bullish Signals:**
- Weak USD
- Risk currencies strengthening
- Carry trades working

**Bearish Signals:**
- Strong USD (flight to safety)
- Risk currencies weakening
- Carry trades unwinding

**Why it matters:** Weak USD = good for risk assets. Strong USD = flight to safety.

---

### **5. Commodity Prices** (Weight: 0.8x)
**What it measures:** Oil, gold, industrial metals

**Bullish Signals:**
- Rising oil prices (growth)
- Stable/falling gold (no fear)
- Strong industrial metals

**Bearish Signals:**
- Falling oil prices (recession)
- Rising gold (fear)
- Weak industrial metals

**Why it matters:** Commodities reflect global growth expectations.

---

### **6. Yield Curve** (Weight: 1.2x)
**What it measures:** 10Y-2Y Treasury spread

**Bullish Signals:**
- Steep curve (growth expectations)
- Positive spread
- Steepening trend

**Bearish Signals:**
- Inverted curve (recession warning)
- Negative spread
- Flattening trend

**Why it matters:** Inverted yield curve has predicted every recession since 1950.

---

### **7. Market Breadth** (Weight: 1.0x)
**What it measures:** Advance/decline ratio, participation

**Bullish Signals:**
- Broad participation
- Many stocks rising
- Strong internals

**Bearish Signals:**
- Narrow leadership
- Few stocks rising
- Weak internals

**Why it matters:** Healthy bull markets have broad participation. Weak breadth = warning sign.

---

## 🎯 Signal Strength Levels

| Strength | Bullish Signals | Position Size | Meaning |
|----------|----------------|---------------|---------|
| **STRONG_BUY** | 6-7 | 100% | All systems go - full risk-on |
| **BUY** | 4-5 | 70% | Favorable environment - moderate risk-on |
| **NEUTRAL** | 3-4 | 30% | Mixed signals - cautious positioning |
| **CASH** | 4-5 bearish | 0% | Unfavorable environment - risk-off |
| **STRONG_CASH** | 6-7 bearish | 0% | Danger zone - full risk-off |

---

## 🚀 API Endpoints

### **1. Get Macro Signal**
```bash
GET /worldmonitor/macro-signal/{symbol}
Authorization: Bearer <token>
```

**Returns:**
- Composite macro signal (BUY/CASH/NEUTRAL)
- Signal strength (STRONG_BUY to STRONG_CASH)
- Breakdown of all 7 signals
- Position size recommendation

**Example Response:**
```json
{
  "status": "success",
  "symbol": "SPY",
  "macro_signal": "BUY",
  "signal_strength": "BUY",
  "composite_score": 0.45,
  "signals_summary": {
    "bullish": 5,
    "bearish": 1,
    "neutral": 1
  },
  "position_recommendation": {
    "size_multiplier": 0.7,
    "description": "Recommended position size: 70% of capital"
  },
  "signals_breakdown": {
    "central_bank": {
      "signal": 1,
      "confidence": 0.8,
      "reason": "Falling yields suggest dovish policy"
    },
    "credit_spreads": {
      "signal": 1,
      "confidence": 0.7,
      "reason": "Low volatility suggests tight credit spreads"
    },
    ...
  }
}
```

---

### **2. Get Trading Decision**
```bash
GET /worldmonitor/trading-decision/{symbol}?current_position=0.5
Authorization: Bearer <token>
```

**Parameters:**
- `current_position`: Current position size (0-1, where 1 = 100% invested)

**Returns:**
- Action: BUY, SELL, or HOLD
- Target position size
- Size change required
- Detailed reasoning

**Example Response:**
```json
{
  "status": "success",
  "symbol": "SPY",
  "action": "BUY",
  "current_position": 0.5,
  "target_position": 0.7,
  "size_change": 0.2,
  "macro_signal": "BUY",
  "signal_strength": "BUY",
  "composite_score": 0.45,
  "reason": "Macro environment is BUY (BUY). Increase exposure.",
  "signals_summary": {
    "bullish": 5,
    "bearish": 1,
    "neutral": 1
  }
}
```

---

### **3. Backtest Strategy**
```bash
GET /worldmonitor/backtest/{symbol}?initial_capital=100000
Authorization: Bearer <token>
```

**Returns:**
- Performance metrics
- Trade history
- Equity curve

**Example Response:**
```json
{
  "status": "success",
  "symbol": "SPY",
  "strategy": "WorldMonitor 7-Signal Macro Radar",
  "initial_capital": 100000,
  "final_equity": 145230.50,
  "total_return_pct": 45.23,
  "total_trades": 28,
  "sharpe_ratio": 1.85,
  "max_drawdown_pct": -12.5,
  "trades": [...],
  "equity_curve": [...]
}
```

---

## 💡 How to Use the Strategy

### **Philosophy**
This strategy **doesn't pick stocks** - it determines **whether the macro environment favors risk-on or risk-off positioning**.

Think of it as the **weather forecast for markets**:
- You still pick where to go (which stocks)
- But you know whether to bring an umbrella (position sizing)

---

### **Use Case 1: Position Sizing**
```python
# Get macro signal
signal = get_macro_signal("SPY")

if signal["macro_signal"] == "BUY":
    position_size = signal["position_recommendation"]["size_multiplier"]
    # Invest 70-100% of capital
elif signal["macro_signal"] == "CASH":
    position_size = 0
    # Stay in cash or defensive assets
else:
    position_size = 0.3
    # Maintain small position
```

---

### **Use Case 2: Dynamic Allocation**
```python
# Current position: 50% invested
current_position = 0.5

# Get trading decision
decision = get_trading_decision("SPY", current_position)

if decision["action"] == "BUY":
    # Increase position by size_change
    buy_amount = capital * decision["size_change"]
elif decision["action"] == "SELL":
    # Reduce position by size_change
    sell_amount = capital * decision["size_change"]
else:
    # HOLD - do nothing
    pass
```

---

### **Use Case 3: Regime Detection**
```python
# Check macro environment before making trades
signal = get_macro_signal("SPY")

if signal["signal_strength"] in ["STRONG_BUY", "BUY"]:
    # Risk-on: Buy growth stocks, tech, small caps
    strategy = "aggressive"
elif signal["signal_strength"] in ["CASH", "STRONG_CASH"]:
    # Risk-off: Buy defensive stocks, utilities, bonds
    strategy = "defensive"
else:
    # Neutral: Balanced portfolio
    strategy = "balanced"
```

---

## 📈 Strategy Performance Characteristics

### **Strengths:**
✅ **Macro-aware**: Adjusts to changing market conditions  
✅ **Risk management**: Reduces exposure in dangerous environments  
✅ **Diversified signals**: 7 independent indicators reduce false signals  
✅ **Dynamic sizing**: Position size adapts to signal strength  
✅ **Trend following**: Captures major market moves  

### **Weaknesses:**
⚠️ **Whipsaws**: Can get caught in choppy markets  
⚠️ **Lagging**: Signals may lag major turning points  
⚠️ **No stock selection**: Doesn't tell you which stocks to buy  
⚠️ **Proxy limitations**: Uses price data as proxy for macro indicators  

---

## 🎓 Best Practices

### **1. Combine with Stock Selection**
```
WorldMonitor Strategy → Position sizing
Your stock analysis → Which stocks to buy
```

### **2. Use for Portfolio Allocation**
```
STRONG_BUY → 100% stocks
BUY → 70% stocks, 30% cash
NEUTRAL → 50% stocks, 50% cash/bonds
CASH → 30% stocks, 70% cash/bonds
STRONG_CASH → 100% cash/bonds
```

### **3. Rebalance Regularly**
- Check signals weekly or monthly
- Adjust position sizes gradually
- Don't overtrade on every signal change

### **4. Respect the Signals**
- When 6-7 signals agree, pay attention
- Don't fight the macro environment
- "The trend is your friend"

---

## 🔬 Technical Implementation

### **Signal Calculation:**
1. Analyze each of 7 indicators
2. Assign signal: +1 (bullish), 0 (neutral), -1 (bearish)
3. Apply confidence weight (0-1)
4. Apply indicator weight (0.8-1.5x)
5. Calculate weighted composite score
6. Determine signal strength based on count

### **Position Sizing:**
```
STRONG_BUY: 100% of capital
BUY: 70% of capital
NEUTRAL: 30% of capital
CASH: 0% of capital
STRONG_CASH: 0% of capital
```

---

## 📚 Related Resources

- **WorldMonitor Finance**: https://finance.worldmonitor.app/
- **Blog Post**: [Real-Time Market Intelligence for Traders](https://www.worldmonitor.app/blog/posts/real-time-market-intelligence-for-traders-and-analysts/)
- **Documentation**: https://www.worldmonitor.app/docs/documentation

---

## 🎯 Quick Start

### **PowerShell Example:**
```powershell
# Login
$body = @{username='trader1'; password='SecurePass123!'} | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method Post -Body $body -ContentType 'application/json'
$token = $response.access_token

# Get macro signal
$headers = @{Authorization = "Bearer $token"}
Invoke-RestMethod -Uri "http://localhost:8000/worldmonitor/macro-signal/SPY" -Headers $headers | ConvertTo-Json -Depth 5

# Get trading decision
Invoke-RestMethod -Uri "http://localhost:8000/worldmonitor/trading-decision/SPY?current_position=0.5" -Headers $headers | ConvertTo-Json -Depth 5

# Backtest
Invoke-RestMethod -Uri "http://localhost:8000/worldmonitor/backtest/SPY" -Headers $headers | ConvertTo-Json -Depth 5
```

---

## 🎉 Summary

The WorldMonitor 7-Signal Macro Strategy provides:
- ✅ **Macro context** for trading decisions
- ✅ **Dynamic position sizing** based on environment
- ✅ **Risk management** through signal-based allocation
- ✅ **Systematic approach** to market timing

**Use it to answer:** "Should I be risk-on or risk-off right now?"

**Don't use it to answer:** "Which stock should I buy?"

---

**Version:** 1.0  
**Last Updated:** May 15, 2026  
**Status:** ✅ Production Ready  
**Based on:** WorldMonitor.app 7-Signal Macro Radar
