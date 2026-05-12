# Advanced Algorithmic Trading Features

## Overview

This trading bot now includes professional-grade algorithmic trading strategies based on **"Algorithmic Short Selling with Python"** by Laurent Bernut (Packt Publishing).

## 🎯 New Advanced Features

### 1. **Regime Detection System**
Multiple methodologies to identify market regimes (bull/bear/neutral):

#### Methodologies:
- **Floor/Ceiling Method**: Advanced swing detection with volatility-based thresholds
- **Range Breakout (Turtle Trader)**: Asymmetrical entry/exit strategy
- **Moving Average Crossover**: SMA and EMA-based regime identification
- **Consensus Regime**: Aggregates 8+ indicators for robust regime classification

#### Endpoint: `/regime/{symbol}`

**Example Response:**
```json
{
  "status": "success",
  "symbol": "AAPL",
  "regimes": {
    "sma_20_50": 1,
    "sma_50_200": 1,
    "ema_12_26": 1,
    "ema_50_200": 1,
    "turtle_50_20": 1,
    "breakout_50d": 1,
    "breakout_200d": 1,
    "breakout_252d": 1
  },
  "consensus": {
    "regime": "STRONG BULL",
    "score": 8,
    "total_indicators": 8,
    "bullish_count": 8,
    "bearish_count": 0,
    "neutral_count": 0
  },
  "interpretation": {
    "short_term": "Bullish",
    "medium_term": "Bullish",
    "long_term": "Bullish",
    "turtle_signal": "Long"
  }
}
```

**Regime Values:**
- `1` = Bullish
- `-1` = Bearish
- `0` = Neutral

**Consensus Classifications:**
- **STRONG BULL**: Score ≥ 60% of total indicators
- **BULL**: Score ≥ 30% of total indicators
- **NEUTRAL/MIXED**: Score between -30% and 30%
- **BEAR**: Score ≤ -30% of total indicators
- **STRONG BEAR**: Score ≤ -60% of total indicators

---

### 2. **Probability Calculator**
Statistical analysis of price movement probabilities using:
- Historical probability distributions
- Monte Carlo simulations (1000+ iterations)
- Volatility-adjusted probabilities
- Z-score calculations

#### Endpoint: `/probability/{symbol}?target_move=0.05&days_ahead=30`

**Parameters:**
- `target_move`: Target percentage move (default: 0.05 = 5%)
- `days_ahead`: Forecast horizon in days (default: 30)

**Example Response:**
```json
{
  "status": "success",
  "symbol": "AAPL",
  "target_move_percent": 5.0,
  "days_ahead": 30,
  "probability_analysis": {
    "prob_up": 0.52,
    "prob_down": 0.48,
    "prob_target_up": 0.23,
    "prob_target_down": 0.19,
    "volatility": 0.018,
    "mean_return": 0.0008,
    "sharpe_ratio": 0.044,
    "z_score_up": 2.72,
    "z_score_down": -2.83
  },
  "monte_carlo_simulation": {
    "mean_price": 175.50,
    "median_price": 174.80,
    "std_price": 12.30,
    "percentile_5": 155.20,
    "percentile_25": 167.40,
    "percentile_75": 182.60,
    "percentile_95": 198.30,
    "prob_profit": 0.54,
    "prob_loss": 0.46,
    "current_price": 173.00
  },
  "interpretation": {
    "upside_probability": "52.0%",
    "downside_probability": "48.0%",
    "target_upside_probability": "23.0%",
    "target_downside_probability": "19.0%",
    "expected_price_range": "$167.40 - $182.60",
    "profit_probability": "54.0%"
  }
}
```

**Key Metrics:**
- **prob_up/prob_down**: Historical probability of any upward/downward move
- **prob_target_up/prob_target_down**: Probability of reaching target move
- **volatility**: Annualized historical volatility
- **sharpe_ratio**: Risk-adjusted return metric
- **z_score**: Statistical distance from mean (in standard deviations)
- **percentile_X**: Price levels at various confidence intervals

---

### 3. **Segment Gauge Calculator**
Multi-dimensional market condition analysis:

#### Gauges:
1. **Trend Gauge**: Distance from multiple SMAs (20, 50, 200)
2. **Momentum Gauge**: Rate of Change (ROC) across timeframes
3. **Volatility Gauge**: Historical volatility and ATR analysis

**Included in**: `/advanced-analysis/{symbol}`

**Example Segment Gauges:**
```json
{
  "trend": {
    "sma_20_distance": 0.025,
    "sma_50_distance": 0.048,
    "sma_200_distance": 0.092,
    "above_sma_20": 1.0,
    "above_sma_50": 1.0,
    "above_sma_200": 1.0,
    "trend_score": 0.055,
    "trend_direction": "bullish"
  },
  "momentum": {
    "roc_5d": 0.032,
    "roc_10d": 0.058,
    "roc_20d": 0.095,
    "momentum_score": 0.051,
    "momentum_direction": "strong_up"
  },
  "volatility": {
    "hist_vol_20d": 0.22,
    "hist_vol_60d": 0.18,
    "atr_14": 3.45,
    "atr_percent": 0.020,
    "volatility_ratio": 1.22,
    "volatility_regime": "expanding"
  }
}
```

**Trend Directions:**
- `bullish`: Price above moving averages
- `bearish`: Price below moving averages
- `neutral`: Mixed signals

**Momentum Directions:**
- `strong_up`: ROC > 5%
- `up`: ROC > 0%
- `down`: ROC > -5%
- `strong_down`: ROC < -5%

**Volatility Regimes:**
- `expanding`: Vol ratio > 1.2 (increasing volatility)
- `contracting`: Vol ratio < 0.8 (decreasing volatility)
- `stable`: Vol ratio 0.8-1.2

---

### 4. **Short-Selling Signals**
Algorithmic short-selling recommendations based on:
- Regime detection (bearish regimes)
- Trend analysis (downtrends)
- Momentum indicators (negative momentum)
- Probability analysis (high downside probability)

#### Endpoint: `/advanced-analysis/{symbol}`

**Short Signal Scoring:**
```
Score Range: -10 to 0 (more negative = stronger short signal)

Components:
- Regime SMA < 0: -2 points
- Regime Turtle < 0: -2 points
- Trend score < -0.05: -2 points
- Momentum score < -0.03: -2 points
- Probability down > 0.55: -1 point
- Sharpe ratio < -0.5: -1 point
```

**Signal Classifications:**
- **STRONG SHORT**: Score ≤ -6 (High confidence short)
- **SHORT**: Score ≤ -3 (Medium confidence short)
- **WEAK SHORT**: Score -3 to -1 (Low confidence short)
- **NO SHORT**: Score ≥ -1 (Do not short)

**Example Short Signal:**
```json
{
  "signal": "SHORT",
  "score": -4,
  "regime_sma": -1,
  "regime_turtle": -1,
  "trend_direction": "bearish",
  "momentum_direction": "down",
  "volatility_regime": "expanding",
  "probability_down": 0.58,
  "sharpe_ratio": -0.35,
  "confidence": "medium"
}
```

---

### 5. **Comprehensive Advanced Analysis**
All-in-one endpoint combining all advanced features.

#### Endpoint: `/advanced-analysis/{symbol}`

**Full Response Structure:**
```json
{
  "status": "success",
  "symbol": "AAPL",
  "current_price": 173.50,
  "price_changes": {
    "1_day": -0.85,
    "5_day": 2.34,
    "20_day": 5.67
  },
  "regime_detection": {
    "sma_50_200": 1,
    "ema_50_200": 1,
    "turtle_trader": 1,
    "breakout_252d": 1,
    "interpretation": {
      "sma": "Bullish",
      "ema": "Bullish",
      "turtle": "Long",
      "breakout": "Bullish"
    }
  },
  "probability_analysis": {
    "5_percent_move": { ... },
    "10_percent_move": { ... },
    "monte_carlo_30_days": { ... }
  },
  "segment_gauges": {
    "trend": { ... },
    "momentum": { ... },
    "volatility": { ... }
  },
  "short_selling_signal": {
    "signal": "NO SHORT",
    "score": 0,
    "confidence": "low",
    ...
  },
  "trading_recommendation": {
    "action": "NO SHORT",
    "confidence": "low",
    "score": 0,
    "reasoning": "Regime: bullish, Momentum: up, Volatility: stable"
  }
}
```

---

## 📊 Algorithmic Strategies Implemented

### 1. **Turtle Trader Strategy**
- **Entry**: 50-day breakout (slow)
- **Exit**: 20-day breakout (fast)
- **Logic**: Asymmetrical risk management
- **Use**: Trend following with controlled exits

### 2. **Floor/Ceiling Methodology**
- **Detection**: Swing highs/lows using ATR-based thresholds
- **Regime Change**: Material break of floor or ceiling
- **Validation**: Distance test + retest/retracement confirmation
- **Use**: Robust regime identification

### 3. **Moving Average Regimes**
- **SMA Crossover**: 20/50, 50/200 periods
- **EMA Crossover**: 12/26, 50/200 periods
- **Signal**: Sign of (Fast MA - Slow MA)
- **Use**: Classic trend identification

### 4. **Monte Carlo Simulation**
- **Iterations**: 1000 simulations
- **Method**: Geometric Brownian Motion
- **Output**: Price distribution, percentiles, probabilities
- **Use**: Risk assessment and price forecasting

---

## 🔧 Technical Implementation

### Core Classes:

#### `RegimeDetector`
```python
# Detect market regimes
regime_sma = RegimeDetector.regime_sma(df, 'Close', 50, 200)
regime_turtle = RegimeDetector.turtle_trader(df, 'High', 'Low', 50, 20)
atr = RegimeDetector.average_true_range(df, 'High', 'Low', 'Close', 14)
```

#### `ProbabilityCalculator`
```python
# Calculate movement probabilities
prob = ProbabilityCalculator.calculate_movement_probability(
    df, 'Close', target_move=0.05
)
monte_carlo = ProbabilityCalculator.monte_carlo_simulation(
    df, 'Close', days_ahead=30
)
```

#### `SegmentGauge`
```python
# Calculate segment gauges
trend = SegmentGauge.calculate_trend_strength(df, 'Close')
momentum = SegmentGauge.calculate_momentum_gauge(df, 'Close')
volatility = SegmentGauge.calculate_volatility_gauge(df, 'Close', 'High', 'Low')
```

#### `ShortSellingSignals`
```python
# Generate short signals
signal = ShortSellingSignals.generate_short_signal(df, 'Close', 'High', 'Low')
```

---

## 📚 Usage Examples

### Python
```python
import requests

# Get comprehensive analysis
response = requests.get('http://localhost:8000/advanced-analysis/AAPL')
analysis = response.json()

print(f"Regime: {analysis['regime_detection']['interpretation']['sma']}")
print(f"Short Signal: {analysis['short_selling_signal']['signal']}")
print(f"Confidence: {analysis['short_selling_signal']['confidence']}")

# Get probability analysis
prob_response = requests.get(
    'http://localhost:8000/probability/AAPL?target_move=0.10&days_ahead=60'
)
prob = prob_response.json()

print(f"Upside Probability: {prob['interpretation']['upside_probability']}")
print(f"Expected Range: {prob['interpretation']['expected_price_range']}")

# Get regime analysis
regime_response = requests.get('http://localhost:8000/regime/AAPL')
regime = regime_response.json()

print(f"Consensus: {regime['consensus']['regime']}")
print(f"Score: {regime['consensus']['score']}/{regime['consensus']['total_indicators']}")
```

### cURL
```bash
# Advanced analysis
curl http://localhost:8000/advanced-analysis/TSLA

# Probability analysis (10% move, 60 days)
curl "http://localhost:8000/probability/TSLA?target_move=0.10&days_ahead=60"

# Regime analysis
curl http://localhost:8000/regime/NVDA
```

---

## ⚠️ Important Notes

### Rate Limiting
- Alpha Vantage free tier: **5 API calls per minute**
- Data is cached for **1 hour** per symbol
- Use cached data when possible to avoid rate limits

### Data Requirements
- Minimum **252 trading days** (1 year) for accurate analysis
- Some indicators require specific minimum periods:
  - SMA 200: 200 days
  - Turtle Trader: 50 days
  - ATR: 14 days

### Interpretation Guidelines
1. **Regime Analysis**: Use consensus of multiple indicators
2. **Probability**: Consider both historical and Monte Carlo results
3. **Short Signals**: Higher confidence = stronger signal
4. **Volatility**: Expanding volatility increases risk

---

## 🎓 Based on Academic Research

These algorithms are based on professional trading methodologies from:

**"Algorithmic Short Selling with Python"**
- Author: Laurent Bernut
- Publisher: Packt Publishing
- Topics: Regime definition, position sizing, risk management, long/short strategies

**Key Concepts Implemented:**
- ✅ Regime Definition (Chapter 5)
- ✅ Trading Edge Calculation (Chapter 6)
- ✅ Position Sizing (Chapter 8)
- ✅ Risk Management (Chapter 9)
- ✅ Long/Short Toolbox (Chapter 11)
- ✅ Signals and Execution (Chapter 12)

---

## 🚀 Next Steps

To use these advanced features:

1. **Wait 60 seconds** between API calls (rate limit)
2. **Start with regime analysis** to understand market conditions
3. **Check probability** for risk assessment
4. **Review segment gauges** for multi-dimensional view
5. **Consider short signals** only with high confidence

**Example Workflow:**
```bash
# 1. Check regime
curl http://localhost:8000/regime/AAPL

# 2. Wait 60 seconds...

# 3. Get full analysis
curl http://localhost:8000/advanced-analysis/AAPL

# 4. Wait 60 seconds...

# 5. Get probability forecast
curl "http://localhost:8000/probability/AAPL?target_move=0.05&days_ahead=30"
```

---

## 📈 Performance Metrics

The algorithms provide:
- **8 regime indicators** for robust classification
- **1000 Monte Carlo simulations** for price forecasting
- **3 segment gauges** (trend, momentum, volatility)
- **6-component scoring** for short signals
- **Multiple timeframes** (5d, 10d, 20d, 50d, 200d, 252d)

All calculations are performed in real-time with professional-grade accuracy! 🎯
