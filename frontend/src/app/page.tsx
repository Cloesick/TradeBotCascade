'use client'

import { useState } from 'react'
import StockChart from '../components/StockChart'
import StockSearch from '../components/StockSearch'
import { TrendingUp, BarChart3, Activity } from 'lucide-react'

export default function Home() {
  const [selectedStock, setSelectedStock] = useState('')

  return (
    <main className="relative min-h-screen">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-12 md:py-20">
        <div className="text-center mb-12 animate-fade-in">
          <div className="flex items-center justify-center gap-3 mb-6">
            <TrendingUp className="w-12 h-12 text-indigo-500" />
            <h1 className="text-5xl md:text-7xl font-bold gradient-text">
              TradeBotCascade
            </h1>
          </div>
          <p className="text-xl md:text-2xl text-slate-400 max-w-2xl mx-auto">
            Advanced algorithmic trading platform with real-time analytics and technical indicators
          </p>
          
          {/* Feature Pills */}
          <div className="flex flex-wrap justify-center gap-4 mt-8">
            <div className="glass px-4 py-2 rounded-full flex items-center gap-2 glow-hover">
              <BarChart3 className="w-4 h-4 text-indigo-400" />
              <span className="text-sm text-slate-300">Technical Analysis</span>
            </div>
            <div className="glass px-4 py-2 rounded-full flex items-center gap-2 glow-hover">
              <Activity className="w-4 h-4 text-purple-400" />
              <span className="text-sm text-slate-300">Real-time Data</span>
            </div>
            <div className="glass px-4 py-2 rounded-full flex items-center gap-2 glow-hover">
              <TrendingUp className="w-4 h-4 text-pink-400" />
              <span className="text-sm text-slate-300">Backtesting</span>
            </div>
          </div>
        </div>

        {/* Search Section */}
        <div className="max-w-4xl mx-auto mb-12 animate-slide-in">
          <StockSearch onSelect={setSelectedStock} />
        </div>

        {/* Chart Section */}
        {selectedStock && (
          <div className="max-w-7xl mx-auto animate-fade-in">
            <StockChart symbol={selectedStock} />
          </div>
        )}

        {/* Empty State */}
        {!selectedStock && (
          <div className="max-w-4xl mx-auto text-center py-20">
            <div className="glass p-12 rounded-2xl">
              <BarChart3 className="w-20 h-20 mx-auto mb-6 text-indigo-500 opacity-50" />
              <h3 className="text-2xl font-semibold mb-3 text-slate-300">
                Start Your Analysis
              </h3>
              <p className="text-slate-400">
                Enter a stock symbol above to view detailed charts and technical indicators
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 text-center text-slate-500 text-sm">
        <p>Built with Next.js, FastAPI, and ❤️</p>
      </footer>
    </main>
  )
}
