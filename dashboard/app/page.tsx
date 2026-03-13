'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import type { TopHolder, HolderAlert } from '@/lib/supabase'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'

export default function DashboardPage() {
  const [topHolders, setTopHolders] = useState<TopHolder[]>([])
  const [alerts, setAlerts] = useState<HolderAlert[]>([])
  const [chartData, setChartData] = useState<{ time: string; 매수: number; 매도: number }[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [holdersRes, alertsRes] = await Promise.all([
          supabase
            .from('top_holders')
            .select('symbol, rank, wallet_address, balance_human, updated_at')
            .eq('symbol', 'PEPE')
            .order('rank'),
          supabase
            .from('holder_alerts')
            .select('id, symbol, alert_type, wallet_address, rank, balance_before, balance_after, created_at')
            .order('created_at', { ascending: false })
            .limit(200),
        ])

        if (holdersRes.error) throw holdersRes.error
        if (alertsRes.error) throw alertsRes.error

        setTopHolders((holdersRes.data as TopHolder[]) || [])
        setAlerts((alertsRes.data as HolderAlert[]) || [])

        const list = (alertsRes.data as HolderAlert[]) || []
        const byHour: Record<string, { 매수: number; 매도: number }> = {}
        list.forEach((a) => {
          const t = new Date(a.created_at)
          const key = t.toISOString().slice(0, 13)
          if (!byHour[key]) byHour[key] = { 매수: 0, 매도: 0 }
          if (a.alert_type === 'buy') byHour[key].매수 += 1
          else byHour[key].매도 += 1
        })
        setChartData(
          Object.entries(byHour)
            .map(([time, v]) => ({ time, ...v }))
            .sort((a, b) => a.time.localeCompare(b.time))
            .slice(-24)
        )
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <div className="section">로딩 중...</div>
  if (error) return <div className="section">에러: {error}</div>

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem', fontSize: '1.5rem' }}>PEPE 보유자 · 매수/매도 알럿</h1>

      <section className="section">
        <h2>PEPE 상위 100명 (현재)</h2>
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>순위</th>
                <th>지갑</th>
                <th>보유량(PEPE)</th>
                <th>갱신일시</th>
              </tr>
            </thead>
            <tbody>
              {topHolders.map((r) => (
                <tr key={`${r.symbol}-${r.rank}`}>
                  <td>{r.rank}</td>
                  <td>
                    <a
                      href={`https://etherscan.io/address/${r.wallet_address}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {r.wallet_address.slice(0, 10)}...
                    </a>
                  </td>
                  <td>{r.balance_human ?? '-'}</td>
                  <td>{r.updated_at ? new Date(r.updated_at).toLocaleString('ko-KR') : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>매수/매도 알럿 이력 (순위별 최신)</h2>
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>발생시각</th>
                <th>순위</th>
                <th>구분</th>
                <th>변동 수량</th>
              </tr>
            </thead>
            <tbody>
              {alerts.slice(0, 100).map((a) => {
                const before = Number(a.balance_before || 0) / 1e18
                const after = Number(a.balance_after || 0) / 1e18
                const diff = after - before
                const diffStr = diff >= 0 ? `+${diff.toLocaleString('ko-KR', { maximumFractionDigits: 2 })}` : diff.toLocaleString('ko-KR', { maximumFractionDigits: 2 })
                return (
                  <tr key={a.id} className={a.alert_type === 'buy' ? 'alert-buy' : 'alert-sell'}>
                    <td>{new Date(a.created_at).toLocaleString('ko-KR')}</td>
                    <td>{a.rank ?? '-'}</td>
                    <td>{a.alert_type === 'buy' ? '매수' : '매도'}</td>
                    <td>{diffStr}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>시간별 매수/매도 건수</h2>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="time" tick={{ fontSize: 11 }} stroke="#71717a" />
              <YAxis tick={{ fontSize: 11 }} stroke="#71717a" />
              <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a' }} />
              <Legend />
              <Bar dataKey="매수" fill="#22c55e" name="매수" />
              <Bar dataKey="매도" fill="#ef4444" name="매도" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  )
}
