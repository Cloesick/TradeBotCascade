from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import ta
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

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
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        
        # Calculate technical indicators
        hist['SMA_20'] = ta.trend.sma_indicator(hist['Close'], window=20)
        hist['RSI'] = ta.momentum.rsi(hist['Close'], window=14)
        hist['MACD'] = ta.trend.macd_diff(hist['Close'])
        
        return {
            "status": "success",
            "data": hist.reset_index().to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
