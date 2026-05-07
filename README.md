# TradeBotCascade

A full-stack trading bot application with backtesting capabilities, technical analysis, and real-time stock data visualization.

## Tech Stack

**Backend:**
- FastAPI (Python 3.13)
- yfinance for market data
- pandas/numpy for data processing
- ta for technical indicators

**Frontend:**
- Next.js 14 (React 18)
- TypeScript
- TailwindCSS
- Chart.js for visualization

## Setup

### Prerequisites
- Python 3.13+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
pip install -r ../requirements.txt
python main.py
```

Backend runs on `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`

## Features

- **Stock Search**: Search and select stocks by symbol
- **Technical Indicators**: SMA, RSI, MACD calculations
- **Backtesting**: Test trading strategies on historical data
- **Real-time Charts**: Interactive price and indicator visualization

## API Endpoints

- `GET /` - Health check
- `GET /stock/{symbol}?period=1y` - Get stock data with indicators
- `GET /backtest/{symbol}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Backtest strategy

## Environment Variables

Copy `.env.example` to `.env` and configure:
- `BACKEND_PORT` - Backend server port (default: 8000)
- `NEXT_PUBLIC_API_URL` - API URL for frontend

## Development

- Backend auto-reloads on file changes
- Frontend has hot module replacement
- CORS configured for local development