'use client'

import { useEffect, useState } from 'react'
import Image from 'next/image'
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
import pepeHero from '../../assets/c__Users_Owner_Desktop_docker-compose_pipe_line_coin_active_pepe.jpg'

export default function DashboardPage() {
  const [topHolders, setTopHolders] = useState<TopHolder[]>([])
  const [alerts, setAlerts] = useState<HolderAlert[]>([])
  const [chartData, setChartData] = useState<{ time: string; 매수: number; 매도: number }[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [now, setNow] = useState<Date | null>(null)

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
        setNow(new Date())
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

  const totalTracked = topHolders.length
  const totalBuy = alerts.filter((a) => a.alert_type === 'buy').length
  const totalSell = alerts.filter((a) => a.alert_type === 'sell').length

  return (
    <div className="container">
      <div className="header-row">
        <div>
          <div className="title">PEPE 상위 100 보유자 모니터링</div>
          <div className="subtitle">
            상위 보유자 지갑의 실시간 보유량 변화와 매수·매도 알럿을 한눈에 확인합니다.
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div className="pill">
            {now ? `업데이트: ${now.toLocaleString('ko-KR')}` : '업데이트 준비 중'}
          </div>
          <div className="hero-pepe">
            <Image
              src={pepeHero}
              alt="Make Memecoins Great Again"
              fill
              sizes="120px"
              priority
            />
          </div>
        </div>
      </div>

      <div className="stats-row">
        <div className="stat-tile">
          <div className="stat-label">모니터링 지갑 수</div>
          <div className="stat-value">{totalTracked.toLocaleString('ko-KR')}</div>
          <div className="stat-tag">상위 100명 중</div>
        </div>
        <div className="stat-tile">
          <div className="stat-label">누적 매수 알럿</div>
          <div className="stat-value" style={{ color: '#4ade80' }}>
            {totalBuy.toLocaleString('ko-KR')}
          </div>
          <div className="stat-tag">알럿 이력 기준</div>
        </div>
        <div className="stat-tile">
          <div className="stat-label">누적 매도 알럿</div>
          <div className="stat-value" style={{ color: '#f97373' }}>
            {totalSell.toLocaleString('ko-KR')}
          </div>
          <div className="stat-tag">알럿 이력 기준</div>
        </div>
      </div>

      <div className="grid">
        <section className="section">
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">PEPE 상위 100명 보유자</div>
                <div className="card-caption">현재 기준 상위 지갑과 보유량</div>
              </div>
            </div>
            <div style={{ overflowX: 'auto', maxHeight: 420 }}>
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
                          {r.wallet_address.slice(0, 8)}...
                        </a>
                      </td>
                      <td>{r.balance_human ?? '-'}</td>
                      <td>{r.updated_at ? new Date(r.updated_at).toLocaleString('ko-KR') : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">최근 매수/매도 알럿</div>
                <div className="card-caption">상위 100명 지갑의 변동 이력</div>
              </div>
            </div>
            <div style={{ overflowX: 'auto', maxHeight: 220 }}>
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
                  {alerts.slice(0, 60).map((a) => {
                    const before = Number(a.balance_before || 0) / 1e18
                    const after = Number(a.balance_after || 0) / 1e18
                    const diff = after - before
                    const diffStr =
                      diff >= 0
                        ? `+${diff.toLocaleString('ko-KR', { maximumFractionDigits: 2 })}`
                        : diff.toLocaleString('ko-KR', { maximumFractionDigits: 2 })
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
          </div>

          <div className="card" style={{ marginTop: '1rem' }}>
            <div className="card-header">
              <div>
                <div className="card-title">시간별 매수/매도 건수</div>
                <div className="card-caption">최근 시간 구간별 알럿 빈도</div>
              </div>
            </div>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="time" tick={{ fontSize: 10 }} stroke="#9ca3af" />
                  <YAxis tick={{ fontSize: 10 }} stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{
                      background: '#020617',
                      border: '1px solid #1f2937',
                      borderRadius: 8,
                    }}
                  />
                  <Legend />
                  <Bar dataKey="매수" fill="#22c55e" name="매수" />
                  <Bar dataKey="매도" fill="#ef4444" name="매도" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
