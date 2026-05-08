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
        
        # Calculate technical indicators
        hist['SMA_20'] = ta.trend.sma_indicator(hist['Close'], window=20)
        hist['RSI'] = ta.momentum.rsi(hist['Close'], window=14)
        hist['MACD'] = ta.trend.macd_diff(hist['Close'])
        
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
        
        # Calculate technical indicators
        hist['SMA_20'] = ta.trend.sma_indicator(hist['Close'], window=20)
        hist['RSI'] = ta.momentum.rsi(hist['Close'], window=14)
        hist['MACD'] = ta.trend.macd_diff(hist['Close'])
        
        # Replace NaN values with None for JSON compatibility
        hist = hist.fillna(value=np.nan).replace([np.nan], [None])
        
        return {
            "status": "success",
            "data": hist.reset_index().to_dict('records'),
            "source": "Mock Data (Demo)"
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
