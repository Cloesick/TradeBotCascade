import { useState } from 'react'

interface StockSearchProps {
  onSelect: (symbol: string) => void
}

export default function StockSearch({ onSelect }: StockSearchProps) {
  const [symbol, setSymbol] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (symbol) {
      onSelect(symbol.toUpperCase())
    }
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <form onSubmit={handleSubmit} className="flex gap-4">
        <input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Enter stock symbol (e.g., AAPL)"
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Search
        </button>
      </form>
    </div>
  )
}
