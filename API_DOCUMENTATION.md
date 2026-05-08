# TradeBotCascade API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### 1. Get Stock Data with Technical Indicators
**GET** `/stock/{symbol}`

Fetch historical stock data with comprehensive technical analysis indicators.

**Parameters:**
- `symbol` (path) - Stock ticker symbol (e.g., AAPL, TSLA)
- `period` (query, optional) - Time period: "1y" (default) or "1mo"

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "index": "2024-01-01",
      "Open": 150.0,
      "High": 155.0,
      "Low": 149.0,
      "Close": 153.0,
      "Volume": 1000000,
      "SMA_20": 151.5,
      "SMA_50": 150.0,
      "SMA_200": 148.0,
      "EMA_12": 152.0,
      "EMA_26": 151.0,
      "MACD": 1.2,
      "MACD_signal": 0.8,
      "MACD_diff": 0.4,
      "BB_high": 156.0,
      "BB_mid": 153.0,
      "BB_low": 150.0,
      "BB_width": 0.04,
      "RSI": 65.5,
      "Stoch": 75.0,
      "Stoch_signal": 70.0,
      "OBV": 50000000,
      "Volume_SMA": 950000,
      "ATR": 2.5
    }
  ],
  "source": "Alpha Vantage (Real Data)"
}
```

**Technical Indicators Included:**
- **Trend**: SMA (20, 50, 200), EMA (12, 26), MACD
- **Momentum**: RSI, Stochastic Oscillator
- **Volatility**: Bollinger Bands, ATR
- **Volume**: OBV, Volume SMA

---

### 2. Get Trading Signals
**GET** `/signals/{symbol}`

Get AI-generated trading signals based on technical analysis.

**Parameters:**
- `symbol` (path) - Stock ticker symbol

**Response:**
```json
{
  "status": "success",
  "symbol": "AAPL",
  "signals": {
    "overall": "BUY",
    "strength": 4,
    "indicators": {
      "RSI": {
        "signal": "NEUTRAL",
        "value": 55.5,
        "reason": "Normal range"
      },
      "MACD": {
        "signal": "BUY",
        "value": 0.5,
        "reason": "Bullish crossover"
      },
      "MA": {
        "signal": "BUY",
        "reason": "Price above moving averages"
      },
      "BB": {
        "signal": "NEUTRAL",
        "reason": "Within bands"
      },
      "Stochastic": {
        "signal": "BUY",
        "value": 25.0,
        "reason": "Oversold"
      }
    }
  },
  "current_price": 175.50,
  "indicators": {
    "RSI": 55.5,
    "MACD": 1.2,
    "MACD_signal": 0.7,
    "BB_high": 180.0,
    "BB_low": 170.0,
    "ATR": 3.5,
    "Volume_vs_avg": 1.15
  }
}
```

**Signal Types:**
- `STRONG BUY` - Score >= 3
- `BUY` - Score >= 1
- `NEUTRAL` - Score between -1 and 1
- `SELL` - Score <= -1
- `STRONG SELL` - Score <= -3

---

### 3. Compare Multiple Stocks
**GET** `/compare?symbols={comma_separated_symbols}`

Compare fundamental data for multiple stocks.

**Parameters:**
- `symbols` (query) - Comma-separated stock symbols (max 10)

**Example:**
```
GET /compare?symbols=AAPL,MSFT,GOOGL
```

**Response:**
```json
{
  "status": "success",
  "comparison": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "market_cap": "2800000000000",
      "pe_ratio": "28.5",
      "eps": "6.15",
      "dividend_yield": "0.0052",
      "52_week_high": "199.62",
      "52_week_low": "164.08"
    },
    {
      "symbol": "MSFT",
      "name": "Microsoft Corporation",
      "sector": "Technology",
      "industry": "Software",
      "market_cap": "2750000000000",
      "pe_ratio": "35.2",
      "eps": "11.23",
      "dividend_yield": "0.0078",
      "52_week_high": "420.82",
      "52_week_low": "309.45"
    }
  ]
}
```

---

### 4. Get Industry Leaders
**GET** `/industry/{sector}`

Get top 10 stocks in a specific sector.

**Parameters:**
- `sector` (path) - Industry sector name

**Available Sectors:**
- `technology`
- `finance`
- `healthcare`
- `energy`
- `consumer`
- `industrial`
- `materials`
- `utilities`
- `real_estate`
- `communication`

**Example:**
```
GET /industry/technology
```

**Response:**
```json
{
  "status": "success",
  "sector": "technology",
  "top_stocks": [
    "AAPL", "MSFT", "GOOGL", "NVDA", "META", 
    "TSLA", "AMD", "INTC", "CRM", "ORCL"
  ],
  "count": 10
}
```

---

### 5. Backtest Trading Strategy
**GET** `/backtest/{symbol}?start_date={date}&end_date={date}`

Backtest a simple moving average crossover strategy.

**Parameters:**
- `symbol` (path) - Stock ticker symbol
- `start_date` (query) - Start date (YYYY-MM-DD)
- `end_date` (query) - End date (YYYY-MM-DD)

**Example:**
```
GET /backtest/AAPL?start_date=2023-01-01&end_date=2024-01-01
```

**Response:**
```json
{
  "status": "success",
  "cumulative_returns": 0.15,
  "data": [...]
}
```

---

## Technical Indicators Explained

### Trend Indicators
- **SMA (Simple Moving Average)**: Average price over N periods
  - SMA_20: Short-term trend
  - SMA_50: Medium-term trend
  - SMA_200: Long-term trend

- **EMA (Exponential Moving Average)**: Weighted average giving more importance to recent prices
  - EMA_12: Fast EMA
  - EMA_26: Slow EMA

- **MACD (Moving Average Convergence Divergence)**: Trend-following momentum indicator
  - MACD: Difference between 12 and 26 EMA
  - MACD_signal: 9-period EMA of MACD
  - MACD_diff: Histogram (MACD - Signal)

### Momentum Indicators
- **RSI (Relative Strength Index)**: Measures speed and magnitude of price changes
  - < 30: Oversold (potential buy)
  - > 70: Overbought (potential sell)
  - 30-70: Normal range

- **Stochastic Oscillator**: Compares closing price to price range
  - < 20: Oversold
  - > 80: Overbought

### Volatility Indicators
- **Bollinger Bands**: Volatility bands around moving average
  - BB_high: Upper band (resistance)
  - BB_mid: Middle band (SMA)
  - BB_low: Lower band (support)
  - BB_width: Band width (volatility measure)

- **ATR (Average True Range)**: Measures market volatility

### Volume Indicators
- **OBV (On-Balance Volume)**: Cumulative volume indicator
- **Volume_SMA**: Average volume over 20 periods

---

## Trading Signal Logic

The `/signals` endpoint uses a scoring system:

| Indicator | Buy Signal | Sell Signal | Score |
|-----------|-----------|-------------|-------|
| RSI | < 30 | > 70 | ±2 |
| MACD | Bullish crossover | Bearish crossover | ±2 |
| MA | Price > SMA_20 > SMA_50 | Price < SMA_20 < SMA_50 | ±1 |
| Bollinger | Price < BB_low | Price > BB_high | ±1 |
| Stochastic | < 20 | > 80 | ±1 |

**Total Score → Overall Signal:**
- Score ≥ 3: STRONG BUY
- Score ≥ 1: BUY
- Score -1 to 1: NEUTRAL
- Score ≤ -1: SELL
- Score ≤ -3: STRONG SELL

---

## Rate Limits & Caching

- **Alpha Vantage Free Tier**: 5 API calls per minute
- **Cache Duration**: 1 hour per symbol
- **Fallback**: Mock data when API limit reached

---

## Error Handling

All endpoints return standard error responses:

```json
{
  "detail": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (invalid endpoint or sector)
- `500`: Internal Server Error

---

## Example Usage

### Python
```python
import requests

# Get stock data
response = requests.get('http://localhost:8000/stock/AAPL')
data = response.json()

# Get trading signals
signals = requests.get('http://localhost:8000/signals/AAPL').json()
print(f"Signal: {signals['signals']['overall']}")

# Compare stocks
compare = requests.get('http://localhost:8000/compare?symbols=AAPL,MSFT,GOOGL').json()

# Get tech leaders
tech_stocks = requests.get('http://localhost:8000/industry/technology').json()
```

### JavaScript
```javascript
// Get stock data
const stockData = await fetch('http://localhost:8000/stock/AAPL')
  .then(res => res.json());

// Get trading signals
const signals = await fetch('http://localhost:8000/signals/AAPL')
  .then(res => res.json());

console.log(`Signal: ${signals.signals.overall}`);
```

### cURL
```bash
# Get stock data
curl http://localhost:8000/stock/AAPL

# Get trading signals
curl http://localhost:8000/signals/AAPL

# Compare stocks
curl "http://localhost:8000/compare?symbols=AAPL,MSFT,GOOGL"

# Get industry leaders
curl http://localhost:8000/industry/technology
```

---

## Notes

- All prices are in USD
- Timestamps are in ISO 8601 format
- Data source: Alpha Vantage API
- Technical indicators calculated using `ta` library
- Cache implemented to avoid rate limits
