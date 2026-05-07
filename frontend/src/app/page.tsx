'use client'

import { useState } from 'react'
import StockChart from '../components/StockChart'
import StockSearch from '../components/StockSearch'

export default function Home() {
  const [selectedStock, setSelectedStock] = useState('')

  return (
    <main className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8 text-center">TradeBotCascade</h1>
      <div className="grid grid-cols-1 gap-8">
        <StockSearch onSelect={setSelectedStock} />
        {selectedStock && <StockChart symbol={selectedStock} />}
      </div>
    </main>
  )
}
