import { useState } from 'react'
import { Search, TrendingUp } from 'lucide-react'

interface StockSearchProps {
  onSelect: (symbol: string) => void
}

const popularStocks = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']

export default function StockSearch({ onSelect }: StockSearchProps) {
  const [symbol, setSymbol] = useState('')
  const [isFocused, setIsFocused] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (symbol.trim()) {
      onSelect(symbol.toUpperCase().trim())
      setSymbol('')
    }
  }

  const handleQuickSelect = (stock: string) => {
    onSelect(stock)
  }

  return (
    <div className="glass p-8 rounded-2xl glow">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="relative">
          <div className={`flex items-center gap-3 glass rounded-xl p-4 transition-all duration-300 ${
            isFocused ? 'ring-2 ring-indigo-500 glow' : ''
          }`}>
            <Search className="w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Enter stock symbol (e.g., AAPL, TSLA)"
              className="flex-1 bg-transparent text-slate-100 placeholder-slate-500 focus:outline-none text-lg"
            />
            <button
              type="submit"
              className="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-500 hover:to-purple-500 transition-all duration-300 font-semibold shadow-lg hover:shadow-indigo-500/50 transform hover:scale-105"
            >
              Analyze
            </button>
          </div>
        </div>

        {/* Quick Select */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <TrendingUp className="w-4 h-4" />
            <span>Popular Stocks</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {popularStocks.map((stock) => (
              <button
                key={stock}
                type="button"
                onClick={() => handleQuickSelect(stock)}
                className="px-4 py-2 glass rounded-lg text-sm text-slate-300 hover:text-white hover:bg-indigo-600/20 transition-all duration-200 border border-transparent hover:border-indigo-500/50"
              >
                {stock}
              </button>
            ))}
          </div>
        </div>
      </form>
    </div>
  )
}
