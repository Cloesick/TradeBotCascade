import './globals.css'

export const metadata = {
  title: 'TradeBotCascade',
  description: 'Algorithmic Trading Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-100">
        <div className="min-h-screen">
          {children}
        </div>
      </body>
    </html>
  )
}
