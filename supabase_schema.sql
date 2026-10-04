-- ==============================================================================
-- Wonde VIP Bot - Supabase (PostgreSQL) Schema
-- Run this in the Supabase SQL Editor (https://supabase.com/dashboard/project/_/sql)
-- ==============================================================================

-- 1. Users Table
CREATE TABLE IF NOT EXISTS public.users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    phone TEXT,
    start_date TIMESTAMPTZ,
    expiry_date TIMESTAMPTZ,
    is_vip INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for speedy lookups on VIP queries & expiry checks
CREATE INDEX IF NOT EXISTS idx_users_vip ON public.users(is_vip, expiry_date);
CREATE INDEX IF NOT EXISTS idx_users_phone ON public.users(phone);

-- 2. Payments Table
CREATE TABLE IF NOT EXISTS public.payments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES public.users(user_id) ON DELETE SET NULL,
    payer_name TEXT,
    phone TEXT,
    transaction_id TEXT UNIQUE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    bank TEXT,
    status TEXT DEFAULT 'approved', -- 'approved', 'pending', 'rejected'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payments_tid ON public.payments(transaction_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON public.payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON public.payments(status);

-- 3. Row Level Security (RLS) Configuration
-- Enable RLS for production security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;

-- Allow Service Role (Backend Bot) full access to all rows
DROP POLICY IF EXISTS "Service role full access on users" ON public.users;
CREATE POLICY "Service role full access on users" ON public.users
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role full access on payments" ON public.payments;
CREATE POLICY "Service role full access on payments" ON public.payments
    FOR ALL USING (true) WITH CHECK (true);

-- Enable Realtime for live updates in Next.js Admin Dashboard
ALTER PUBLICATION supabase_realtime ADD TABLE public.users;
ALTER PUBLICATION supabase_realtime ADD TABLE public.payments;
