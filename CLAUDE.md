# TradeBotCascade — Project Conventions

Extends the global `~/.claude/CLAUDE.md`. Rules here take precedence for this repo.

## What this is
Full-stack trading research app: FastAPI backend serving technical analysis,
multi-strategy backtesting, ML signal models, and a macro "WorldMonitor" radar;
Next.js frontend for charts. Research/educational — not connected to a live broker.

## Stack & key libs
- Backend: Python 3.13, FastAPI + uvicorn, pydantic v2. Data via `yfinance` and
  Alpha Vantage (`alpha-vantage`). Analysis: pandas, numpy, `ta`, scipy,
  scikit-learn, statsmodels, optional torch. Auth: python-jose (JWT), passlib[bcrypt].
- Frontend: Next.js 14, React 18, TypeScript, TailwindCSS, Chart.js / react-chartjs-2, axios.

## Folder structure
- `backend/main.py` — FastAPI app, all routes (auth, /stock, /signals, /backtest,
  /portfolio, /ml, /worldmonitor). Entrypoint.
- `backend/algo_strategies.py` — RegimeDetector, ProbabilityCalculator, SegmentGauge,
  ShortSellingSignals (Bernut "Algorithmic Short Selling" methodology).
- `backend/backtesting.py` — BacktestEngine, StrategyLibrary (SMA/RSI/MACD/Bollinger/Turtle),
  MonteCarloSimulation.
- `backend/worldmonitor_strategy.py` — 7-signal macro radar (BUY/CASH) + position sizing.
- `backend/ml_models.py` — MLPredictor, EnsembleSignalGenerator.
- `backend/advanced_ml.py` — López de Prado techniques: TripleBarrierLabeling, PurgedKFold,
  FractionalDifferentiation, MetaLabeling, BetSizing, FeatureImportance.
- `backend/portfolio.py`, `backend/auth.py`.
- `frontend/src/` — Next.js app. Build artifacts (`node_modules`, `.venv`) are gitignored; ignore them.
- Vendored reference: `Algorithmic-Short-Selling-with-Python-Published-by-Packt/` (read-only notebooks).

## Run / backtest
- Backend: `cd backend && pip install -r ../requirements.txt && python main.py` → http://localhost:8000
  (use the repo `.venv`; see VENV_SETUP.md). Docs at `/docs`.
- Frontend: `cd frontend && npm install && npm run dev` → http://localhost:3000
- Backtest via API: `GET /backtest/{symbol}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`,
  or call `BacktestEngine.run_strategy(df, signals)` with `StrategyLibrary` signal series.

## Testing
- pytest suite lives in `backend/tests/` (config in `backend/pytest.ini`). Run with `cd backend && pytest`.
  Covers auth security (SECRET_KEY env handling, bcrypt hashing, JWT round-trips), TLS config, and the auth API.
  CI runs it on every push/PR via `.github/workflows/backend-tests.yml` (also a gitleaks secret scan).
  Add `pytest` tests under `backend/tests/` for new strategy/backtest logic. Lint frontend with `npm run lint`.
- Legacy ad-hoc scripts `backend/test_yfinance.py`, `backend/test_direct.py` make live network calls (not part
  of the pytest suite). `test_direct.py` still sets `verify=False` — a standalone manual script, not the app path.

## Data & secrets (env only)
- Config via `.env` (gitignored) loaded with `python-dotenv`; template is `.env.example`.
- Read keys with `os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')`. NEVER hardcode keys or commit `.env`.
  This workspace has had leaked keys before — treat any literal key/token as a defect.

## Gotchas
- `auth.py` loads `SECRET_KEY`/`ALGORITHM` from env (`load_dotenv()` at import). Unset + `ENVIRONMENT=production`
  raises at startup; dev gets an ephemeral fallback (logs a warning). Keep the key stable — don't reintroduce
  per-restart generation. Password hashing uses the `bcrypt` lib directly (passlib was removed — it broke on
  bcrypt ≥4.1); inputs are truncated to bcrypt's 72-byte limit.
- `main.py` talks to Alpha Vantage with TLS verification at its secure default (enabled). Do NOT reintroduce
  `verify=False` / `urllib3.disable_warnings` / `ssl._create_unverified_context`. For a TLS-intercepting proxy,
  set `REQUESTS_CA_BUNDLE` instead. `test_tls_config.py` guards against regressions.
- Strategy code uses `.shift(1)` to avoid look-ahead bias (e.g. Turtle); preserve this when editing.
  WorldMonitor proxies macro signals from a single price series — keep that caveat explicit.
- pandas: `fillna(method='ffill')` is deprecated (use `.ffill()`); numpy 2.x in use.

## Preferred specialists
trading-analysis (strategy/indicator/backtest), python-pro, ml-engineer, pandas-expert,
scikit-learn-expert, data-processing, code-reviewer — all from `~/.claude/agents`.
