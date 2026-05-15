# 🧠 WorldMonitor Algorithm - Complete Breakdown

## 📊 **Algorithm Flow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT: Stock Price Data                   │
│                    (OHLCV DataFrame)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              STEP 1: Analyze 7 Macro Signals                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Central Bank Policy (Weight: 1.5x)                      │
│     ├─ Calculate yield change (20-day)                      │
│     ├─ Falling yields → +1 (Bullish)                        │
│     ├─ Rising yields → -1 (Bearish)                         │
│     └─ Stable yields → 0 (Neutral)                          │
│                                                              │
│  2. Credit Spreads (Weight: 1.2x)                           │
│     ├─ Calculate volatility (20-day vs 60-day avg)          │
│     ├─ Low volatility → +1 (Tight spreads)                  │
│     ├─ High volatility → -1 (Wide spreads)                  │
│     └─ Normal volatility → 0 (Neutral)                      │
│                                                              │
│  3. Volatility Index (Weight: 1.0x)                         │
│     ├─ Calculate realized volatility (annualized)           │
│     ├─ Vol < 15 → +1 (Low fear)                             │
│     ├─ Vol > 25 → -1 (High fear)                            │
│     └─ Vol 15-25 → 0 (Moderate)                             │
│                                                              │
│  4. Currency Strength (Weight: 1.0x)                        │
│     ├─ Calculate momentum (SMA20 vs SMA60)                  │
│     ├─ Strong momentum → +1 (Weak USD)                      │
│     ├─ Weak momentum → -1 (Strong USD)                      │
│     └─ Neutral momentum → 0 (Neutral USD)                   │
│                                                              │
│  5. Commodity Prices (Weight: 0.8x)                         │
│     ├─ Calculate 30-day price change                        │
│     ├─ Rising > 5% → +1 (Growth)                            │
│     ├─ Falling > 5% → -1 (Weakness)                         │
│     └─ Stable → 0 (Neutral)                                 │
│                                                              │
│  6. Yield Curve (Weight: 1.2x)                              │
│     ├─ Calculate trend slope (60-day linear fit)            │
│     ├─ Uptrend → +1 (Steep curve)                           │
│     ├─ Downtrend → -1 (Flat/inverted)                       │
│     └─ Neutral → 0 (Stable)                                 │
│                                                              │
│  7. Market Breadth (Weight: 1.0x)                           │
│     ├─ Compare price to SMA50 and SMA200                    │
│     ├─ Above both → +1 (Broad strength)                     │
│     ├─ Below both → -1 (Broad weakness)                     │
│     └─ Mixed → 0 (Neutral)                                  │
│                                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         STEP 2: Calculate Weighted Composite Score          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  For each signal:                                           │
│    weighted_signal = signal × weight × confidence           │
│                                                              │
│  Total Score = Σ(weighted_signals) / Σ(weights)            │
│                                                              │
│  Example:                                                   │
│    Signal 1: +1 × 1.5 × 0.8 = +1.20                        │
│    Signal 2: +1 × 1.2 × 0.7 = +0.84                        │
│    Signal 3:  0 × 1.0 × 0.8 =  0.00                        │
│    Signal 4: +1 × 1.0 × 0.6 = +0.60                        │
│    Signal 5: -1 × 0.8 × 0.5 = -0.40                        │
│    Signal 6: +1 × 1.2 × 0.7 = +0.84                        │
│    Signal 7: +1 × 1.0 × 0.8 = +0.80                        │
│    ─────────────────────────────                            │
│    Total = +4.88 / 7.9 = +0.62                             │
│                                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           STEP 3: Determine Signal Strength                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Count bullish/bearish signals:                             │
│    Bullish: 5 signals                                       │
│    Bearish: 1 signal                                        │
│    Neutral: 1 signal                                        │
│                                                              │
│  Apply Rules:                                               │
│    ├─ 6-7 bullish → STRONG_BUY (100% position)             │
│    ├─ 4-5 bullish → BUY (70% position)          ← Selected │
│    ├─ 3-4 mixed   → NEUTRAL (30% position)                 │
│    ├─ 4-5 bearish → CASH (0% position)                     │
│    └─ 6-7 bearish → STRONG_CASH (0% position)              │
│                                                              │
│  Result: BUY (70% position size)                            │
│                                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          STEP 4: Determine Macro Signal                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Composite Score: +0.62                                     │
│                                                              │
│  Apply Thresholds:                                          │
│    ├─ Score > +0.3 → BUY (Risk-on)          ← Selected     │
│    ├─ Score -0.3 to +0.3 → NEUTRAL                         │
│    └─ Score < -0.3 → CASH (Risk-off)                       │
│                                                              │
│  Result: BUY (Risk-on environment)                          │
│                                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         STEP 5: Generate Trading Decision                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Current Position: 50% (0.5)                                │
│  Target Position:  70% (0.7)                                │
│                                                              │
│  Decision Logic:                                            │
│    IF target > current + 0.1:                               │
│       Action = BUY                                          │
│       Size = target - current = 0.2 (20%)                   │
│                                                              │
│    ELIF target < current - 0.1:                             │
│       Action = SELL                                         │
│       Size = current - target                               │
│                                                              │
│    ELSE:                                                    │
│       Action = HOLD                                         │
│       Size = 0                                              │
│                                                              │
│  Result: BUY 20% more (increase from 50% to 70%)           │
│                                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT: Trading Signal                    │
├─────────────────────────────────────────────────────────────┤
│  Action: BUY                                                │
│  Size Change: +20%                                          │
│  Macro Signal: BUY                                          │
│  Signal Strength: BUY                                       │
│  Composite Score: +0.62                                     │
│  Reason: "Macro environment is BUY. Increase exposure."     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔢 **Mathematical Formulas**

### **1. Central Bank Policy Signal**
```python
recent_change = (price[-1] - price[-20]) / price[-20]

if recent_change < -0.02:
    signal = +1  # Bullish
elif recent_change > 0.02:
    signal = -1  # Bearish
else:
    signal = 0   # Neutral

confidence = min(abs(recent_change) * 50, 1.0)
```

### **2. Credit Spreads Signal**
```python
recent_vol = std(returns[-20:])
avg_vol = mean(std(returns[-60:]))

if recent_vol < avg_vol * 0.8:
    signal = +1  # Tight spreads
elif recent_vol > avg_vol * 1.2:
    signal = -1  # Wide spreads
else:
    signal = 0   # Neutral

confidence = min(abs(recent_vol - avg_vol) / avg_vol, 1.0)
```

### **3. Volatility Index Signal**
```python
realized_vol = std(returns[-20:]) * sqrt(252) * 100

if realized_vol < 15:
    signal = +1  # Low fear
elif realized_vol > 25:
    signal = -1  # High fear
else:
    signal = 0   # Moderate

confidence = 0.8
```

### **4. Currency Strength Signal**
```python
sma_20 = mean(price[-20:])
sma_60 = mean(price[-60:])
momentum = (sma_20 - sma_60) / sma_60

if momentum > 0.02:
    signal = +1  # Weak USD (bullish)
elif momentum < -0.02:
    signal = -1  # Strong USD (bearish)
else:
    signal = 0   # Neutral

confidence = min(abs(momentum) * 50, 1.0)
```

### **5. Commodity Prices Signal**
```python
price_change_30d = (price[-1] - price[-30]) / price[-30]

if price_change_30d > 0.05:
    signal = +1  # Rising (growth)
elif price_change_30d < -0.05:
    signal = -1  # Falling (weakness)
else:
    signal = 0   # Stable

confidence = min(abs(price_change_30d) * 10, 1.0)
```

### **6. Yield Curve Signal**
```python
x = [0, 1, 2, ..., 59]
y = price[-60:]
slope = polyfit(x, y, degree=1)[0]
normalized_slope = slope / price[-1] * 100

if normalized_slope > 0.1:
    signal = +1  # Steep curve
elif normalized_slope < -0.1:
    signal = -1  # Flat/inverted
else:
    signal = 0   # Neutral

confidence = 0.7
```

### **7. Market Breadth Signal**
```python
sma_50 = mean(price[-50:])
sma_200 = mean(price[-200:])
current_price = price[-1]

above_50 = current_price > sma_50
above_200 = current_price > sma_200

if above_50 and above_200:
    signal = +1  # Broad strength
elif not above_50 and not above_200:
    signal = -1  # Broad weakness
else:
    signal = 0   # Mixed

confidence = 0.8
```

### **8. Composite Score Calculation**
```python
weights = {
    'central_bank': 1.5,
    'credit_spreads': 1.2,
    'volatility': 1.0,
    'currency': 1.0,
    'commodities': 0.8,
    'yield_curve': 1.2,
    'market_breadth': 1.0
}

total_score = 0
total_weight = 0

for signal_name, signal_data in signals.items():
    weight = weights[signal_name]
    signal_value = signal_data['signal']  # -1, 0, or +1
    confidence = signal_data['confidence']  # 0 to 1
    
    weighted_signal = signal_value * weight * confidence
    total_score += weighted_signal
    total_weight += weight * confidence

normalized_score = total_score / total_weight
```

### **9. Signal Strength Determination**
```python
bullish_count = sum(1 for s in signals if s['signal'] > 0)
bearish_count = sum(1 for s in signals if s['signal'] < 0)

if bullish_count >= 6:
    strength = "STRONG_BUY"
    position_size = 1.0  # 100%
elif bullish_count >= 4:
    strength = "BUY"
    position_size = 0.7  # 70%
elif bearish_count >= 6:
    strength = "STRONG_CASH"
    position_size = 0.0  # 0%
elif bearish_count >= 4:
    strength = "CASH"
    position_size = 0.0  # 0%
else:
    strength = "NEUTRAL"
    position_size = 0.3  # 30%
```

### **10. Macro Signal Determination**
```python
if normalized_score > 0.3:
    macro_signal = "BUY"      # Risk-on
elif normalized_score < -0.3:
    macro_signal = "CASH"     # Risk-off
else:
    macro_signal = "NEUTRAL"  # Mixed
```

### **11. Trading Decision**
```python
target_position = position_size  # From signal strength
current_position = 0.5  # Example: 50% invested

if target_position > current_position + 0.1:
    action = "BUY"
    size_change = target_position - current_position
elif target_position < current_position - 0.1:
    action = "SELL"
    size_change = current_position - target_position
else:
    action = "HOLD"
    size_change = 0
```

---

## 📈 **Example Calculation**

### **Input Data:**
- Stock: SPY (S&P 500 ETF)
- Current Price: $450
- 20-day price change: -1.5%
- Volatility (20-day): 12%
- SMA20: $448, SMA60: $440
- 30-day return: +3%

### **Step-by-Step:**

#### **Signal 1: Central Bank Policy**
```
recent_change = -0.015 (falling yields)
signal = +1 (bullish)
confidence = 0.75
weighted = +1 × 1.5 × 0.75 = +1.125
```

#### **Signal 2: Credit Spreads**
```
recent_vol = 0.12, avg_vol = 0.15
ratio = 0.12 / 0.15 = 0.8 (low vol)
signal = +1 (tight spreads)
confidence = 0.7
weighted = +1 × 1.2 × 0.7 = +0.84
```

#### **Signal 3: Volatility Index**
```
realized_vol = 12% (annualized)
signal = +1 (low fear)
confidence = 0.8
weighted = +1 × 1.0 × 0.8 = +0.8
```

#### **Signal 4: Currency Strength**
```
momentum = (448 - 440) / 440 = 0.018
signal = 0 (neutral, below 0.02 threshold)
confidence = 0.6
weighted = 0 × 1.0 × 0.6 = 0
```

#### **Signal 5: Commodity Prices**
```
price_change_30d = 0.03 (3%)
signal = 0 (neutral, below 5% threshold)
confidence = 0.5
weighted = 0 × 0.8 × 0.5 = 0
```

#### **Signal 6: Yield Curve**
```
slope = positive (uptrend)
normalized_slope = 0.15
signal = +1 (steep curve)
confidence = 0.7
weighted = +1 × 1.2 × 0.7 = +0.84
```

#### **Signal 7: Market Breadth**
```
price = $450
SMA50 = $445, SMA200 = $430
above both = True
signal = +1 (broad strength)
confidence = 0.8
weighted = +1 × 1.0 × 0.8 = +0.8
```

### **Composite Calculation:**
```
total_score = 1.125 + 0.84 + 0.8 + 0 + 0 + 0.84 + 0.8 = 4.405
total_weight = 1.125 + 1.008 + 0.8 + 0.6 + 0.4 + 0.84 + 0.8 = 5.573

normalized_score = 4.405 / 5.573 = 0.79
```

### **Signal Determination:**
```
Bullish signals: 5 (CB, Credit, Vol, Yield, Breadth)
Bearish signals: 0
Neutral signals: 2 (Currency, Commodities)

Signal Strength: BUY (4-5 bullish)
Position Size: 70%

Composite Score: 0.79 > 0.3
Macro Signal: BUY (Risk-on)
```

### **Trading Decision:**
```
Current Position: 50%
Target Position: 70%
Size Change: +20%

Action: BUY
Reason: "Macro environment is BUY (BUY). Increase exposure."
```

---

## 🎯 **Decision Tree**

```
                    Start
                      │
                      ▼
            Analyze 7 Signals
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
    Bullish       Neutral       Bearish
    Signals       Signals       Signals
        │             │             │
        ▼             ▼             ▼
    Count ≥ 6     Count 3-4     Count ≥ 6
        │             │             │
        ▼             ▼             ▼
   STRONG_BUY     NEUTRAL      STRONG_CASH
    (100%)         (30%)          (0%)
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
            Calculate Composite
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
    Score > 0.3   Score -0.3    Score < -0.3
                  to +0.3
        │             │             │
        ▼             ▼             ▼
       BUY         NEUTRAL         CASH
    (Risk-on)     (Mixed)      (Risk-off)
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
          Compare Target vs Current
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Target >      Target ≈      Target <
   Current       Current       Current
        │             │             │
        ▼             ▼             ▼
       BUY          HOLD          SELL
```

---

## 🔍 **Key Algorithm Features**

### **1. Multi-Signal Approach**
- 7 independent indicators reduce false signals
- Diversified across different market aspects
- No single signal dominates

### **2. Weighted Scoring**
- Important signals (central bank, yield curve) have higher weight
- Confidence adjusts for data quality
- Normalized score for consistent interpretation

### **3. Dynamic Position Sizing**
- Position size adapts to signal strength
- More conviction = larger position
- Risk management built-in

### **4. Threshold-Based Decisions**
- Clear rules for BUY/CASH/NEUTRAL
- Prevents overtrading on minor changes
- 0.1 buffer prevents whipsaws

### **5. Trend Following**
- Captures major macro shifts
- Reduces exposure in risk-off environments
- Increases exposure in risk-on environments

---

## 💡 **Algorithm Strengths**

✅ **Systematic** - No emotion, pure math  
✅ **Diversified** - 7 independent signals  
✅ **Weighted** - Important signals matter more  
✅ **Adaptive** - Position size adjusts to conditions  
✅ **Risk-Aware** - Reduces exposure in danger zones  
✅ **Transparent** - Every decision is explainable  

---

## ⚠️ **Algorithm Limitations**

⚠️ **Proxy Data** - Uses price as proxy for macro indicators  
⚠️ **Lagging** - Signals may lag major turning points  
⚠️ **Whipsaws** - Can get caught in choppy markets  
⚠️ **No Stock Selection** - Only determines position size  
⚠️ **Threshold Sensitivity** - Performance depends on thresholds  

---

## 🎓 **How to Interpret Results**

### **Composite Score:**
- **+1.0 to +0.5**: Strong risk-on (all systems go)
- **+0.5 to +0.3**: Moderate risk-on (favorable)
- **+0.3 to -0.3**: Neutral (mixed signals)
- **-0.3 to -0.5**: Moderate risk-off (caution)
- **-0.5 to -1.0**: Strong risk-off (danger zone)

### **Signal Count:**
- **6-7 bullish**: Rare, very strong signal
- **4-5 bullish**: Common, reliable signal
- **3-4 mixed**: Uncertain, reduce exposure
- **4-5 bearish**: Common, defensive signal
- **6-7 bearish**: Rare, very strong warning

---

**This is the complete algorithm powering the WorldMonitor strategy!** 🧠🚀
