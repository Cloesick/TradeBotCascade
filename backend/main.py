from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from datetime import datetime, timedelta
import ta
import numpy as np
import os
from dotenv import load_dotenv
from alpha_vantage.timeseries import TimeSeries
import requests

load_dotenv()

# Disable SSL warnings and verification for development
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a custom session with SSL verification disabled
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Initialize Alpha Vantage
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')

# Create custom session for Alpha Vantage
av_session = requests.Session()
av_session.verify = False

ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')

# Cache for API responses (symbol -> {data, timestamp})
from datetime import timedelta
cache = {}
CACHE_TTL = timedelta(hours=1)  # Cache data for 1 hour

app = FastAPI(
    title="TradeBotCascade API",
    description="Trading bot API with backtesting and technical analysis",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate comprehensive technical indicators"""
    # Trend Indicators
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
    df['EMA_12'] = ta.trend.ema_indicator(df['Close'], window=12)
    df['EMA_26'] = ta.trend.ema_indicator(df['Close'], window=26)
    
    # MACD
    df['MACD'] = ta.trend.macd(df['Close'])
    df['MACD_signal'] = ta.trend.macd_signal(df['Close'])
    df['MACD_diff'] = ta.trend.macd_diff(df['Close'])
    
    # Bollinger Bands
    df['BB_high'] = ta.volatility.bollinger_hband(df['Close'])
    df['BB_mid'] = ta.volatility.bollinger_mavg(df['Close'])
    df['BB_low'] = ta.volatility.bollinger_lband(df['Close'])
    df['BB_width'] = ta.volatility.bollinger_wband(df['Close'])
    
    # Momentum Indicators
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    df['Stoch'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'])
    df['Stoch_signal'] = ta.momentum.stoch_signal(df['High'], df['Low'], df['Close'])
    
    # Volume Indicators
    df['OBV'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])
    df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
    
    # Volatility
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
    
    return df

def generate_trading_signals(df: pd.DataFrame) -> dict:
    """Generate trading signals based on technical indicators"""
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    signals = {
        'overall': 'NEUTRAL',
        'strength': 0,
        'indicators': {}
    }
    
    score = 0
    
    # RSI Signal
    if latest['RSI'] < 30:
        signals['indicators']['RSI'] = {'signal': 'BUY', 'value': latest['RSI'], 'reason': 'Oversold'}
        score += 2
    elif latest['RSI'] > 70:
        signals['indicators']['RSI'] = {'signal': 'SELL', 'value': latest['RSI'], 'reason': 'Overbought'}
        score -= 2
    else:
        signals['indicators']['RSI'] = {'signal': 'NEUTRAL', 'value': latest['RSI'], 'reason': 'Normal range'}
    
    # MACD Signal
    if latest['MACD_diff'] > 0 and prev['MACD_diff'] <= 0:
        signals['indicators']['MACD'] = {'signal': 'BUY', 'value': latest['MACD_diff'], 'reason': 'Bullish crossover'}
        score += 2
    elif latest['MACD_diff'] < 0 and prev['MACD_diff'] >= 0:
        signals['indicators']['MACD'] = {'signal': 'SELL', 'value': latest['MACD_diff'], 'reason': 'Bearish crossover'}
        score -= 2
    else:
        signals['indicators']['MACD'] = {'signal': 'NEUTRAL', 'value': latest['MACD_diff'], 'reason': 'No crossover'}
    
    # Moving Average Signal
    if latest['Close'] > latest['SMA_20'] > latest['SMA_50']:
        signals['indicators']['MA'] = {'signal': 'BUY', 'reason': 'Price above moving averages'}
        score += 1
    elif latest['Close'] < latest['SMA_20'] < latest['SMA_50']:
        signals['indicators']['MA'] = {'signal': 'SELL', 'reason': 'Price below moving averages'}
        score -= 1
    else:
        signals['indicators']['MA'] = {'signal': 'NEUTRAL', 'reason': 'Mixed signals'}
    
    # Bollinger Bands Signal
    if latest['Close'] < latest['BB_low']:
        signals['indicators']['BB'] = {'signal': 'BUY', 'reason': 'Price below lower band'}
        score += 1
    elif latest['Close'] > latest['BB_high']:
        signals['indicators']['BB'] = {'signal': 'SELL', 'reason': 'Price above upper band'}
        score -= 1
    else:
        signals['indicators']['BB'] = {'signal': 'NEUTRAL', 'reason': 'Within bands'}
    
    # Stochastic Signal
    if latest['Stoch'] < 20:
        signals['indicators']['Stochastic'] = {'signal': 'BUY', 'value': latest['Stoch'], 'reason': 'Oversold'}
        score += 1
    elif latest['Stoch'] > 80:
        signals['indicators']['Stochastic'] = {'signal': 'SELL', 'value': latest['Stoch'], 'reason': 'Overbought'}
        score -= 1
    else:
        signals['indicators']['Stochastic'] = {'signal': 'NEUTRAL', 'value': latest['Stoch'], 'reason': 'Normal range'}
    
    # Overall signal
    signals['strength'] = score
    if score >= 3:
        signals['overall'] = 'STRONG BUY'
    elif score >= 1:
        signals['overall'] = 'BUY'
    elif score <= -3:
        signals['overall'] = 'STRONG SELL'
    elif score <= -1:
        signals['overall'] = 'SELL'
    else:
        signals['overall'] = 'NEUTRAL'
    
    return signals

@app.get("/")
async def root():
    return {"message": "Welcome to TradeBotCascade API"}

@app.get("/stock/{symbol}")
async def get_stock_data(symbol: str, period: str = "1y"):
    # Check cache first
    cache_key = f"{symbol}_{period}"
    if cache_key in cache:
        cached_entry = cache[cache_key]
        if datetime.now() - cached_entry['timestamp'] < CACHE_TTL:
            print(f"✓ Returning cached data for {symbol}")
            return {
                "status": "success",
                "data": cached_entry['data'],
                "source": "Alpha Vantage (Cached)"
            }
    
    try:
        # Fetch data from Alpha Vantage using requests directly
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'
        print(f"Fetching data for {symbol} from Alpha Vantage...")
        response = av_session.get(url, verify=False, timeout=10)
        print(f"Response status: {response.status_code}")
        data_json = response.json()
        print(f"Response keys: {list(data_json.keys())}")
        
        if 'Time Series (Daily)' not in data_json:
            error_msg = data_json.get('Note', data_json.get('Error Message', data_json.get('Information', 'Unknown error')))
            raise Exception(f"No data returned: {error_msg}")
        
        # Convert to DataFrame
        time_series = data_json['Time Series (Daily)']
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # Convert to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        # Filter by period (last 252 days for 1 year)
        period_days = 252 if period == "1y" else 30
        hist = df.tail(period_days)
        
        # Calculate comprehensive technical indicators
        hist = calculate_technical_indicators(hist)
        
        # Replace NaN values with None for JSON compatibility
        hist = hist.fillna(value=np.nan).replace([np.nan], [None])
        
        # Prepare response data
        response_data = hist.reset_index().to_dict('records')
        
        # Store in cache
        cache[cache_key] = {
            'data': response_data,
            'timestamp': datetime.now()
        }
        print(f"✓ Cached data for {symbol}")
        
        return {
            "status": "success",
            "data": response_data,
            "source": "Alpha Vantage (Real Data)"
        }
    except Exception as e:
        # Fallback to mock data if API fails
        print(f"Alpha Vantage error for {symbol}: {e}")
        print("Using mock data as fallback")
        
        # Generate mock data
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        np.random.seed(hash(symbol) % 2**32)
        base_price = 150 + np.random.rand() * 100
        returns = np.random.randn(252) * 0.02
        prices = base_price * (1 + returns).cumprod()
        
        hist = pd.DataFrame({
            'Open': prices * (1 + np.random.randn(252) * 0.01),
            'High': prices * (1 + abs(np.random.randn(252)) * 0.02),
            'Low': prices * (1 - abs(np.random.randn(252)) * 0.02),
            'Close': prices,
            'Volume': (np.random.rand(252) * 1000000 + 500000).astype(int)
        }, index=dates)
        
        # Calculate comprehensive technical indicators
        hist = calculate_technical_indicators(hist)
        
        # Replace NaN values with None for JSON compatibility
        hist = hist.fillna(value=np.nan).replace([np.nan], [None])
        
        return {
            "status": "success",
            "data": hist.reset_index().to_dict('records'),
            "source": "Mock Data (Demo)"
        }

@app.get("/signals/{symbol}")
async def get_trading_signals(symbol: str):
    """Get trading signals for a symbol"""
    try:
        # Fetch recent data
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={ALPHA_VANTAGE_API_KEY}'
        response = av_session.get(url, verify=False, timeout=10)
        data_json = response.json()
        
        if 'Time Series (Daily)' not in data_json:
            raise Exception("No data available")
        
        # Convert to DataFrame
        time_series = data_json['Time Series (Daily)']
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        # Calculate indicators
        df = calculate_technical_indicators(df)
        
        # Generate signals
        signals = generate_trading_signals(df)
        
        # Get latest values
        latest = df.iloc[-1]
        
        return {
            "status": "success",
            "symbol": symbol,
            "signals": signals,
            "current_price": float(latest['Close']),
            "indicators": {
                "RSI": float(latest['RSI']) if not pd.isna(latest['RSI']) else None,
                "MACD": float(latest['MACD']) if not pd.isna(latest['MACD']) else None,
                "MACD_signal": float(latest['MACD_signal']) if not pd.isna(latest['MACD_signal']) else None,
                "BB_high": float(latest['BB_high']) if not pd.isna(latest['BB_high']) else None,
                "BB_low": float(latest['BB_low']) if not pd.isna(latest['BB_low']) else None,
                "ATR": float(latest['ATR']) if not pd.isna(latest['ATR']) else None,
                "Volume_vs_avg": float(latest['Volume'] / latest['Volume_SMA']) if not pd.isna(latest['Volume_SMA']) else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/compare")
async def compare_stocks(symbols: str):
    """Compare multiple stocks (comma-separated symbols)"""
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    
    if len(symbol_list) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 stocks allowed")
    
    results = []
    
    for symbol in symbol_list:
        try:
            url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}'
            response = av_session.get(url, verify=False, timeout=10)
            data = response.json()
            
            if 'Symbol' in data:
                results.append({
                    "symbol": symbol,
                    "name": data.get('Name', 'N/A'),
                    "sector": data.get('Sector', 'N/A'),
                    "industry": data.get('Industry', 'N/A'),
                    "market_cap": data.get('MarketCapitalization', 'N/A'),
                    "pe_ratio": data.get('PERatio', 'N/A'),
                    "eps": data.get('EPS', 'N/A'),
                    "dividend_yield": data.get('DividendYield', 'N/A'),
                    "52_week_high": data.get('52WeekHigh', 'N/A'),
                    "52_week_low": data.get('52WeekLow', 'N/A')
                })
        except:
            results.append({"symbol": symbol, "error": "Data unavailable"})
    
    return {
        "status": "success",
        "comparison": results
    }

@app.get("/industry/{sector}")
async def get_industry_leaders(sector: str):
    """Get top stocks in a sector/industry"""
    # Predefined industry leaders by sector
    industry_data = {
        "technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "TSLA", "AMD", "INTC", "CRM", "ORCL"],
        "finance": ["JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "USB"],
        "healthcare": ["JNJ", "UNH", "PFE", "ABBV", "TMO", "MRK", "ABT", "DHR", "LLY", "BMY"],
        "energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL"],
        "consumer": ["AMZN", "WMT", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW", "TJX", "DG"],
        "industrial": ["BA", "CAT", "GE", "HON", "UNP", "UPS", "LMT", "MMM", "DE", "RTX"],
        "materials": ["LIN", "APD", "ECL", "SHW", "FCX", "NEM", "DOW", "DD", "NUE", "VMC"],
        "utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "PEG", "XEL", "ED"],
        "real_estate": ["AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "WELL", "DLR", "O", "AVB"],
        "communication": ["GOOGL", "META", "DIS", "NFLX", "CMCSA", "T", "VZ", "TMUS", "CHTR", "EA"]
    }
    
    sector_lower = sector.lower()
    if sector_lower not in industry_data:
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found. Available: {', '.join(industry_data.keys())}")
    
    symbols = industry_data[sector_lower]
    
    return {
        "status": "success",
        "sector": sector,
        "top_stocks": symbols,
        "count": len(symbols)
    }

@app.get("/backtest/{symbol}")
async def backtest_strategy(symbol: str, start_date: str, end_date: str):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(start=start_date, end=end_date)
        
        # Simple strategy example
        hist['SMA_20'] = ta.trend.sma_indicator(hist['Close'], window=20)
        hist['SMA_50'] = ta.trend.sma_indicator(hist['Close'], window=50)
        
        # Generate signals
        hist['Signal'] = np.where(hist['SMA_20'] > hist['SMA_50'], 1, -1)
        
        # Calculate returns
        hist['Returns'] = hist['Close'].pct_change()
        hist['Strategy_Returns'] = hist['Signal'].shift(1) * hist['Returns']
        
        return {
            "status": "success",
            "cumulative_returns": hist['Strategy_Returns'].cumsum().iloc[-1],
            "data": hist.reset_index().to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
