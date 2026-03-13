import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PEPE 보유자 · 매수/매도 알럿',
  description: 'PEPE 상위 보유자 & 변동 알럿 대시보드',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}
