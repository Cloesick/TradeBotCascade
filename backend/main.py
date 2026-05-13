from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import pandas as pd
from datetime import datetime, timedelta
import ta
import numpy as np
import os
from dotenv import load_dotenv
from alpha_vantage.timeseries import TimeSeries
import requests
from algo_strategies import (
    RegimeDetector, ProbabilityCalculator, 
    SegmentGauge, ShortSellingSignals
)
from backtesting import BacktestEngine, StrategyLibrary, MonteCarloSimulation
from portfolio import PortfolioManager, Position
from ml_models import MLPredictor, EnsembleSignalGenerator
from advanced_ml import (
    TripleBarrierLabeling, PurgedKFold, FeatureImportance,
    FractionalDifferentiation, MetaLabeling, BetSizing
)
from auth import (
    User, UserCreate, UserLogin, Token, UserInDB, UserRole,
    user_db, TokenManager, get_current_user, get_current_active_user,
    get_current_user_optional, require_admin, require_trader, require_viewer
)

# Try to import deep learning
try:
    from ml_models import DeepLearningPredictor
    DL_AVAILABLE = True
except ImportError:
    DL_AVAILABLE = False

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

# Global portfolio manager (in production, use database)
portfolio_manager = PortfolioManager(initial_capital=100000.0)

# Global ML predictor
ml_predictor = MLPredictor()

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


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/auth/register", response_model=User, tags=["Authentication"])
async def register(user_create: UserCreate):
    """
    Register a new user
    
    Password requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    try:
        user = user_db.create_user(user_create, role=UserRole.VIEWER)
        return User(**user.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login(user_login: UserLogin):
    """
    Login with username and password
    
    Returns JWT access token and refresh token
    """
    user = user_db.authenticate_user(user_login.username, user_login.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = TokenManager.create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    refresh_token = TokenManager.create_refresh_token(
        data={"sub": user.username, "role": user.role.value}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800  # 30 minutes
    )


@app.post("/auth/refresh", response_model=Token, tags=["Authentication"])
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token
    """
    token_data = TokenManager.verify_token(refresh_token, token_type="refresh")
    
    if not token_data or not token_data.username:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )
    
    user = user_db.get_user(token_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Create new tokens
    access_token = TokenManager.create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    new_refresh_token = TokenManager.create_refresh_token(
        data={"sub": user.username, "role": user.role.value}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=1800
    )


@app.get("/auth/me", response_model=User, tags=["Authentication"])
async def get_current_user_info(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get current user information
    
    Requires: Valid JWT token
    """
    return User(**current_user.dict())


@app.post("/auth/api-key", tags=["Authentication"])
async def create_api_key(
    key_name: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Create API key for programmatic access
    
    Requires: Valid JWT token
    
    Note: API key is shown only once. Store it securely!
    """
    try:
        api_key = user_db.create_api_key(current_user.username, key_name)
        return {
            "success": True,
            "api_key": api_key,
            "message": "API key created successfully. Store it securely - it won't be shown again!"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/users", tags=["Authentication", "Admin"])
async def list_users(current_user: UserInDB = Depends(require_admin)):
    """
    List all users (Admin only)
    
    Requires: Admin role
    """
    users = [User(**user.dict()) for user in user_db.users.values()]
    return {"users": users, "count": len(users)}


@app.put("/auth/users/{username}/role", tags=["Authentication", "Admin"])
async def update_user_role(
    username: str,
    new_role: UserRole,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Update user role (Admin only)
    
    Requires: Admin role
    """
    user = user_db.get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = new_role
    return {"success": True, "message": f"User {username} role updated to {new_role.value}"}


@app.put("/auth/users/{username}/disable", tags=["Authentication", "Admin"])
async def disable_user(
    username: str,
    disabled: bool,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Enable/disable user account (Admin only)
    
    Requires: Admin role
    """
    user = user_db.get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.username == current_user.username:
        raise HTTPException(status_code=400, detail="Cannot disable your own account")
    
    user.disabled = disabled
    status_text = "disabled" if disabled else "enabled"
    return {"success": True, "message": f"User {username} {status_text}"}


# ============================================================================
# PUBLIC ENDPOINTS (No authentication required)
# ============================================================================

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

@app.get("/advanced-analysis/{symbol}")
async def get_advanced_analysis(symbol: str):
    """
    Get comprehensive algorithmic analysis including:
    - Regime detection (Floor/Ceiling, Breakout, MA crossover)
    - Probability calculations
    - Segment gauges
    - Short-selling signals
    """
    try:
        # Fetch data
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'
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
        
        # Take last 252 days (1 year)
        df = df.tail(252)
        
        # Regime Detection
        regime_sma_50_200 = RegimeDetector.regime_sma(df, 'Close', 50, 200).iloc[-1]
        regime_ema_50_200 = RegimeDetector.regime_ema(df, 'Close', 50, 200).iloc[-1]
        regime_turtle = RegimeDetector.turtle_trader(df, 'High', 'Low', 50, 20).iloc[-1]
        regime_breakout_252 = RegimeDetector.regime_breakout(df, 'High', 'Low', 252).iloc[-1]
        
        # Probability Analysis
        prob_5pct = ProbabilityCalculator.calculate_movement_probability(df, 'Close', target_move=0.05)
        prob_10pct = ProbabilityCalculator.calculate_movement_probability(df, 'Close', target_move=0.10)
        monte_carlo_30d = ProbabilityCalculator.monte_carlo_simulation(df, 'Close', days_ahead=30)
        
        # Segment Gauges
        trend_gauge = SegmentGauge.calculate_trend_strength(df, 'Close')
        momentum_gauge = SegmentGauge.calculate_momentum_gauge(df, 'Close')
        volatility_gauge = SegmentGauge.calculate_volatility_gauge(df, 'Close', 'High', 'Low')
        
        # Short Selling Signal
        short_signal = ShortSellingSignals.generate_short_signal(df, 'Close', 'High', 'Low')
        
        # Current price info
        current_price = float(df['Close'].iloc[-1])
        price_change_1d = float((df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1) * 100)
        price_change_5d = float((df['Close'].iloc[-1] / df['Close'].iloc[-6] - 1) * 100) if len(df) >= 6 else 0
        price_change_20d = float((df['Close'].iloc[-1] / df['Close'].iloc[-21] - 1) * 100) if len(df) >= 21 else 0
        
        return {
            "status": "success",
            "symbol": symbol,
            "current_price": current_price,
            "price_changes": {
                "1_day": round(price_change_1d, 2),
                "5_day": round(price_change_5d, 2),
                "20_day": round(price_change_20d, 2)
            },
            "regime_detection": {
                "sma_50_200": int(regime_sma_50_200),
                "ema_50_200": int(regime_ema_50_200),
                "turtle_trader": int(regime_turtle),
                "breakout_252d": int(regime_breakout_252),
                "interpretation": {
                    "sma": "Bullish" if regime_sma_50_200 > 0 else "Bearish",
                    "ema": "Bullish" if regime_ema_50_200 > 0 else "Bearish",
                    "turtle": "Long" if regime_turtle > 0 else "Short" if regime_turtle < 0 else "Neutral",
                    "breakout": "Bullish" if regime_breakout_252 > 0 else "Bearish"
                }
            },
            "probability_analysis": {
                "5_percent_move": prob_5pct,
                "10_percent_move": prob_10pct,
                "monte_carlo_30_days": monte_carlo_30d
            },
            "segment_gauges": {
                "trend": trend_gauge,
                "momentum": momentum_gauge,
                "volatility": volatility_gauge
            },
            "short_selling_signal": short_signal,
            "trading_recommendation": {
                "action": short_signal['signal'],
                "confidence": short_signal['confidence'],
                "score": short_signal['score'],
                "reasoning": f"Regime: {short_signal['trend_direction']}, Momentum: {short_signal['momentum_direction']}, Volatility: {short_signal['volatility_regime']}"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/probability/{symbol}")
async def get_probability_analysis(symbol: str, target_move: float = 0.05, days_ahead: int = 30):
    """
    Get detailed probability analysis for stock movements
    """
    try:
        # Fetch data
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'
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
        
        df = df.tail(252)
        
        # Calculate probabilities
        prob_analysis = ProbabilityCalculator.calculate_movement_probability(
            df, 'Close', target_move=target_move
        )
        
        # Monte Carlo simulation
        monte_carlo = ProbabilityCalculator.monte_carlo_simulation(
            df, 'Close', days_ahead=days_ahead
        )
        
        return {
            "status": "success",
            "symbol": symbol,
            "target_move_percent": target_move * 100,
            "days_ahead": days_ahead,
            "probability_analysis": prob_analysis,
            "monte_carlo_simulation": monte_carlo,
            "interpretation": {
                "upside_probability": f"{prob_analysis['prob_up'] * 100:.1f}%",
                "downside_probability": f"{prob_analysis['prob_down'] * 100:.1f}%",
                "target_upside_probability": f"{prob_analysis['prob_target_up'] * 100:.1f}%",
                "target_downside_probability": f"{prob_analysis['prob_target_down'] * 100:.1f}%",
                "expected_price_range": f"${monte_carlo['percentile_25']:.2f} - ${monte_carlo['percentile_75']:.2f}",
                "profit_probability": f"{monte_carlo['prob_profit'] * 100:.1f}%"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/regime/{symbol}")
async def get_regime_analysis(symbol: str):
    """
    Get detailed regime analysis using multiple methodologies
    """
    try:
        # Fetch data
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'
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
        
        df = df.tail(252)
        
        # Multiple regime methodologies
        regimes = {
            "sma_20_50": int(RegimeDetector.regime_sma(df, 'Close', 20, 50).iloc[-1]),
            "sma_50_200": int(RegimeDetector.regime_sma(df, 'Close', 50, 200).iloc[-1]),
            "ema_12_26": int(RegimeDetector.regime_ema(df, 'Close', 12, 26).iloc[-1]),
            "ema_50_200": int(RegimeDetector.regime_ema(df, 'Close', 50, 200).iloc[-1]),
            "turtle_50_20": int(RegimeDetector.turtle_trader(df, 'High', 'Low', 50, 20).iloc[-1]),
            "breakout_50d": int(RegimeDetector.regime_breakout(df, 'High', 'Low', 50).iloc[-1]),
            "breakout_200d": int(RegimeDetector.regime_breakout(df, 'High', 'Low', 200).iloc[-1]),
            "breakout_252d": int(RegimeDetector.regime_breakout(df, 'High', 'Low', 252).iloc[-1])
        }
        
        # Consensus regime
        regime_values = list(regimes.values())
        consensus_score = sum(regime_values)
        total_indicators = len(regime_values)
        
        if consensus_score >= total_indicators * 0.6:
            consensus = "STRONG BULL"
        elif consensus_score >= total_indicators * 0.3:
            consensus = "BULL"
        elif consensus_score <= -total_indicators * 0.6:
            consensus = "STRONG BEAR"
        elif consensus_score <= -total_indicators * 0.3:
            consensus = "BEAR"
        else:
            consensus = "NEUTRAL/MIXED"
        
        return {
            "status": "success",
            "symbol": symbol,
            "regimes": regimes,
            "consensus": {
                "regime": consensus,
                "score": consensus_score,
                "total_indicators": total_indicators,
                "bullish_count": sum(1 for v in regime_values if v > 0),
                "bearish_count": sum(1 for v in regime_values if v < 0),
                "neutral_count": sum(1 for v in regime_values if v == 0)
            },
            "interpretation": {
                "short_term": "Bullish" if regimes["sma_20_50"] > 0 else "Bearish",
                "medium_term": "Bullish" if regimes["sma_50_200"] > 0 else "Bearish",
                "long_term": "Bullish" if regimes["breakout_252d"] > 0 else "Bearish",
                "turtle_signal": "Long" if regimes["turtle_50_20"] > 0 else "Short" if regimes["turtle_50_20"] < 0 else "Neutral"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/backtest/{symbol}")
async def backtest_strategy(symbol: str, strategy: str = "sma_crossover", initial_capital: float = 100000):
    """
    Enhanced backtesting with multiple strategies and comprehensive metrics
    
    Strategies: sma_crossover, rsi, macd, bollinger_bands, turtle_trader
    """
    try:
        # Fetch data
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'
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
        
        # Take last 2 years
        df = df.tail(504)
        
        # Select strategy
        strategy_map = {
            'sma_crossover': StrategyLibrary.sma_crossover,
            'rsi': StrategyLibrary.rsi_strategy,
            'macd': StrategyLibrary.macd_strategy,
            'bollinger_bands': StrategyLibrary.bollinger_bands_strategy,
            'turtle_trader': StrategyLibrary.turtle_trader_strategy
        }
        
        if strategy not in strategy_map:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}")
        
        # Generate signals
        signals = strategy_map[strategy](df)
        
        # Run backtest
        engine = BacktestEngine(initial_capital=initial_capital)
        metrics = engine.run_strategy(df, signals)
        
        # Run Monte Carlo simulation if enough trades
        monte_carlo_results = None
        if metrics.get('total_trades', 0) >= 10:
            monte_carlo_results = MonteCarloSimulation.run_monte_carlo(
                metrics.get('trades', []),
                num_simulations=1000,
                initial_capital=initial_capital
            )
        
        return {
            "status": "success",
            "symbol": symbol,
            "strategy": strategy,
            "metrics": metrics,
            "monte_carlo": monte_carlo_results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# PORTFOLIO MANAGEMENT ENDPOINTS (Requires TRADER role)
# ============================================================================

@app.post("/portfolio/position", tags=["Portfolio"])
async def add_portfolio_position(
    symbol: str, 
    shares: float, 
    price: float, 
    stop_loss: float = None, 
    take_profit: float = None,
    current_user: UserInDB = Depends(require_trader)
):
    """
    Add a position to the portfolio
    
    Requires: TRADER role or higher
    """
    result = portfolio_manager.add_position(symbol, shares, price, stop_loss, take_profit)
    return result

@app.delete("/portfolio/position/{symbol}", tags=["Portfolio"])
async def close_portfolio_position(
    symbol: str, 
    price: float, 
    shares: float = None,
    current_user: UserInDB = Depends(require_trader)
):
    """
    Close a position (full or partial)
    
    Requires: TRADER role or higher
    """
    result = portfolio_manager.close_position(symbol, price, shares)
    return result

@app.get("/portfolio/summary", tags=["Portfolio"])
async def get_portfolio_summary(current_user: UserInDB = Depends(require_viewer)):
    """
    Get portfolio summary
    
    Requires: VIEWER role or higher
    """
    summary = portfolio_manager.get_summary()
    return {"status": "success", "portfolio": summary}

@app.get("/portfolio/positions", tags=["Portfolio"])
async def get_all_positions(current_user: UserInDB = Depends(require_viewer)):
    """
    Get all open positions
    
    Requires: VIEWER role or higher
    """
    positions = portfolio_manager.get_all_positions()
    return {"status": "success", "positions": positions, "count": len(positions)}

@app.post("/portfolio/optimize", tags=["Portfolio"])
async def optimize_portfolio(
    symbols: List[str], 
    risk_tolerance: str = "moderate",
    current_user: UserInDB = Depends(require_trader)
):
    """
    Optimize portfolio allocation
    
    Requires: TRADER role or higher
    """
    # For demo, use mock expected returns and volatilities
    # In production, calculate from historical data
    expected_returns = {symbol: 0.10 for symbol in symbols}  # 10% annual return
    volatilities = {symbol: 0.20 for symbol in symbols}  # 20% volatility
    
    recommendations = portfolio_manager.optimize_allocation(
        symbols, expected_returns, volatilities, risk_tolerance
    )
    
    return {
        "status": "success",
        "optimization": recommendations
    }

# ============================================================================
# MACHINE LEARNING ENDPOINTS (Requires TRADER role)
# ============================================================================

@app.post("/ml/train/{symbol}", tags=["Machine Learning"])
async def train_ml_model(
    symbol: str, 
    model_type: str = "classifier",
    current_user: UserInDB = Depends(require_trader)
):
    """
    Train ML model for price prediction
    
    Requires: TRADER role or higher
    
    model_type: classifier (direction) or regressor (price)
    """
    try:
        # Fetch data
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'
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
        
        # Train model
        if model_type == "classifier":
            result = ml_predictor.train_direction_classifier(df, lookahead=5)
        elif model_type == "regressor":
            result = ml_predictor.train_price_regressor(df, lookahead=5)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown model type: {model_type}")
        
        return {
            "status": "success",
            "symbol": symbol,
            "model_type": model_type,
            "training_results": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/ml/predict/{symbol}", tags=["Machine Learning"])
async def ml_predict(
    symbol: str, 
    prediction_type: str = "direction",
    current_user: UserInDB = Depends(require_viewer)
):
    """
    Get ML prediction for stock
    
    Requires: VIEWER role or higher
    
    prediction_type: direction or price
    """
    try:
        # Fetch data
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'
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
        
        # Predict
        if prediction_type == "direction":
            result = ml_predictor.predict_direction(df)
        elif prediction_type == "price":
            result = ml_predictor.predict_price(df)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown prediction type: {prediction_type}")
        
        return {
            "status": "success",
            "symbol": symbol,
            "prediction_type": prediction_type,
            "prediction": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
