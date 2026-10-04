# Next.js Admin Dashboard & Supabase Integration Guide

This guide walks you through connecting your **Next.js Admin UI** and your **Python VIP Telegram Bot** to **Supabase**.

---

## 1. Setup Supabase (5 Minutes)

1. Go to [https://supabase.com](https://supabase.com) and create a free account.
2. Click **New Project** and name it (e.g., `VIP-Bot`).
3. Once the database is ready, go to the **SQL Editor** tab on the left menu.
4. Open the file `supabase_schema.sql` located in this repository, copy everything, and click **Run**.
5. Go to **Project Settings** -> **API**:
   - Copy **Project URL**
   - Copy **anon public** key
   - Copy **service_role** secret key

---

## 2. Connect Your Python Bot to Supabase

In your bot folder, open `.env` (or create it from `.env.example`) and add:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

> **Note:** The bot uses the `service_role` key because it acts as the backend worker and needs to write/update all records.

Restart your bot:
```bash
python main.py
```
Your bot will print:
`Connected to Supabase PostgreSQL cloud database.`

---

## 3. Plug Admin Dashboard into Your Next.js App

In your Next.js project (such as `telegram-store`):

### Step A: Install Supabase Client
Run inside your Next.js project directory:
```bash
npm install @supabase/supabase-js
```

### Step B: Set Next.js Environment Variables
In your Next.js `.env.local` (and in Vercel project environment variables):
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_public_key_here
```

### Step C: Copy the Files
1. Copy `admin_nextjs/supabase.ts` into your Next.js app (e.g., `lib/supabase.ts`).
2. Copy `admin_nextjs/dashboard_page.tsx` into your Next.js app (e.g., `app/admin/page.tsx` or `pages/admin.tsx`).

---

## 4. Deploy Next.js to Vercel

1. Push your Next.js repository to GitHub.
2. Import the repository in [Vercel](https://vercel.com).
3. Add the two environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
4. Click **Deploy**.

Your live Admin Dashboard will deploy instantly with zero serverless timeout errors!
