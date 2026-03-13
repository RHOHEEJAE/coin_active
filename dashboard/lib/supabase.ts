import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type TopHolder = {
  symbol: string
  rank: number
  wallet_address: string
  balance_human: string | null
  updated_at: string
}

export type HolderAlert = {
  id: number
  symbol: string
  alert_type: string
  wallet_address: string
  rank: number | null
  balance_before: string | null
  balance_after: string | null
  created_at: string
}
