import { useEffect, useState } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import axios from 'axios'
import { TrendingUp, TrendingDown, Activity, Loader2 } from 'lucide-react'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface StockChartProps {
  symbol: string
}

export default function StockChart({ symbol }: StockChartProps) {
  const [chartData, setChartData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError('')
        const response = await axios.get(`http://localhost:8000/stock/${symbol}`)
        const data = response.data.data

        const dates = data.map((item: any) => {
          const date = new Date(item.index || item.Date)
          return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        })
        const prices = data.map((item: any) => item.Close)
        const sma20 = data.map((item: any) => item.SMA_20)
        const rsi = data.map((item: any) => item.RSI)

        // Calculate stats
        const currentPrice = prices[prices.length - 1]
        const previousPrice = prices[prices.length - 2]
        const priceChange = currentPrice - previousPrice
        const priceChangePercent = ((priceChange / previousPrice) * 100).toFixed(2)
        const high = Math.max(...prices)
        const low = Math.min(...prices)
        const avgVolume = data.reduce((sum: number, item: any) => sum + (item.Volume || 0), 0) / data.length

        setStats({
          currentPrice: currentPrice.toFixed(2),
          priceChange: priceChange.toFixed(2),
          priceChangePercent,
          high: high.toFixed(2),
          low: low.toFixed(2),
          avgVolume: (avgVolume / 1000000).toFixed(2),
          isPositive: priceChange >= 0,
        })

        setChartData({
          labels: dates,
          datasets: [
            {
              label: 'Price',
              data: prices,
              borderColor: 'rgb(99, 102, 241)',
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              borderWidth: 2,
              fill: true,
              tension: 0.4,
              pointRadius: 0,
              pointHoverRadius: 6,
              pointHoverBackgroundColor: 'rgb(99, 102, 241)',
              pointHoverBorderColor: '#fff',
              pointHoverBorderWidth: 2,
            },
            {
              label: 'SMA 20',
              data: sma20,
              borderColor: 'rgb(236, 72, 153)',
              borderWidth: 2,
              borderDash: [5, 5],
              fill: false,
              tension: 0.4,
              pointRadius: 0,
              pointHoverRadius: 6,
              pointHoverBackgroundColor: 'rgb(236, 72, 153)',
              pointHoverBorderColor: '#fff',
              pointHoverBorderWidth: 2,
            },
          ],
        })
      } catch (err) {
        setError('Failed to fetch stock data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [symbol])

  if (loading) {
    return (
      <div className="glass p-12 rounded-2xl glow">
        <div className="flex flex-col items-center justify-center space-y-4">
          <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
          <p className="text-slate-400">Loading {symbol} data...</p>
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="glass p-8 rounded-2xl border border-red-500/30">
        <p className="text-red-400 text-center">{error}</p>
      </div>
    )
  }
  
  if (!chartData) return null

  return (
    <div className="glass p-8 rounded-2xl glow space-y-6">
      {/* Header with Stats */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div>
          <h2 className="text-3xl font-bold text-slate-100 mb-2">{symbol}</h2>
          {stats && (
            <div className="flex items-center gap-4">
              <div className="text-4xl font-bold text-slate-100">
                ${stats.currentPrice}
              </div>
              <div className={`flex items-center gap-1 px-3 py-1 rounded-lg ${
                stats.isPositive ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
              }`}>
                {stats.isPositive ? (
                  <TrendingUp className="w-4 h-4" />
                ) : (
                  <TrendingDown className="w-4 h-4" />
                )}
                <span className="font-semibold">
                  {stats.priceChange} ({stats.priceChangePercent}%)
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-3 gap-4">
            <div className="glass p-3 rounded-lg">
              <div className="text-xs text-slate-400 mb-1">High</div>
              <div className="text-lg font-semibold text-green-400">${stats.high}</div>
            </div>
            <div className="glass p-3 rounded-lg">
              <div className="text-xs text-slate-400 mb-1">Low</div>
              <div className="text-lg font-semibold text-red-400">${stats.low}</div>
            </div>
            <div className="glass p-3 rounded-lg">
              <div className="text-xs text-slate-400 mb-1">Avg Vol</div>
              <div className="text-lg font-semibold text-indigo-400">{stats.avgVolume}M</div>
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="glass p-6 rounded-xl">
        <Line
          data={chartData}
          options={{
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
              mode: 'index',
              intersect: false,
            },
            plugins: {
              legend: {
                display: true,
                position: 'top' as const,
                labels: {
                  color: '#cbd5e1',
                  padding: 15,
                  font: {
                    size: 12,
                    weight: 500,
                  },
                  usePointStyle: true,
                  pointStyle: 'circle',
                },
              },
              tooltip: {
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                titleColor: '#f1f5f9',
                bodyColor: '#cbd5e1',
                borderColor: '#334155',
                borderWidth: 1,
                padding: 12,
                displayColors: true,
                callbacks: {
                  label: function(context: any) {
                    let label = context.dataset.label || ''
                    if (label) {
                      label += ': '
                    }
                    if (context.parsed.y !== null) {
                      label += '$' + context.parsed.y.toFixed(2)
                    }
                    return label
                  },
                },
              },
            },
            scales: {
              x: {
                grid: {
                  color: 'rgba(51, 65, 85, 0.3)',
                },
                ticks: {
                  color: '#94a3b8',
                  maxRotation: 0,
                  autoSkipPadding: 20,
                },
              },
              y: {
                beginAtZero: false,
                grid: {
                  color: 'rgba(51, 65, 85, 0.3)',
                },
                ticks: {
                  color: '#94a3b8',
                  callback: function(value: any) {
                    return '$' + value.toFixed(0)
                  },
                },
              },
            },
          }}
        />
      </div>

      {/* Indicators */}
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Activity className="w-4 h-4" />
        <span>Technical Indicators: SMA(20), RSI(14), MACD</span>
      </div>
    </div>
  )
}
