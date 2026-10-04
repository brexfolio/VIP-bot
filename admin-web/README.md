# Wonde VIP - Next.js Admin Web Dashboard

This is a standalone **Next.js 14** web application for managing your Telegram VIP bot, viewing live revenue, monitoring active VIP subscriptions, approving bank payments, and auto-banning expired members.

---

## Quick Start (Run Locally)

1. Open your terminal in this directory:
   ```bash
   cd admin-web
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create your `.env.local` file:
   ```bash
   cp .env.example .env.local
   ```
   Fill in your Supabase project keys:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_public_key_here
   ```

4. Start development server:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) to view your live admin dashboard.

---

## Deploy to Vercel (Production)

### Method A: Deploy from Existing Monorepo
When importing your GitHub repository to Vercel:
1. In the Vercel project configuration, set **Root Directory** to `admin-web`.
2. Add your environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. Click **Deploy**.

### Method B: Deploy as a Separate GitHub Repository
1. Initialize this folder as its own repo:
   ```bash
   cd admin-web
   git init
   git add .
   git commit -m "Initial commit of VIP Admin Web"
   ```
2. Create a new GitHub repository (e.g. `VIP-bot-admin`) and push to it.
3. Import into Vercel and deploy.
