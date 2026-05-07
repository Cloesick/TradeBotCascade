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
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import axios from 'axios'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

interface StockChartProps {
  symbol: string
}

export default function StockChart({ symbol }: StockChartProps) {
  const [chartData, setChartData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError('')
        const response = await axios.get(`http://localhost:8000/stock/${symbol}`)
        const data = response.data.data

        const dates = data.map((item: any) => new Date(item.Date).toLocaleDateString())
        const prices = data.map((item: any) => item.Close)
        const sma20 = data.map((item: any) => item.SMA_20)

        setChartData({
          labels: dates,
          datasets: [
            {
              label: 'Price',
              data: prices,
              borderColor: 'rgb(75, 192, 192)',
              tension: 0.1,
            },
            {
              label: 'SMA 20',
              data: sma20,
              borderColor: 'rgb(255, 99, 132)',
              tension: 0.1,
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

  if (loading) return <div className="text-center">Loading...</div>
  if (error) return <div className="text-red-500">{error}</div>
  if (!chartData) return null

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">{symbol} Stock Price</h2>
      <Line
        data={chartData}
        options={{
          responsive: true,
          plugins: {
            legend: {
              position: 'top' as const,
            },
            title: {
              display: true,
              text: 'Stock Price & SMA 20',
            },
          },
          scales: {
            y: {
              beginAtZero: false,
            },
          },
        }}
      />
    </div>
  )
}
