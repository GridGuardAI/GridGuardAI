# GridGuard AI — Frontend (Phase 1 Spec-Compliant)

Next.js dashboard matching the rewritten backend (bill upload + manual entry,
deterministic engineering facts, per-anomaly AI diagnosis with confidence
language and evidence citations, prioritized recommendations).

## Setup
```bash
npm install
cp .env.local.example .env.local
```
Edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Run
```bash
npm run dev
```
Open http://localhost:3000. Make sure the backend (`gridguard-backend-v2`) is
running on port 8000 at the same time.

## Two input modes
- **Upload Bill**: upload a photo/PDF of an electricity bill. Optionally add
  voltage/current/PF/tariff if you have a meter reading (bills alone don't
  have these).
- **Manual Entry**: type in current/previous consumption, billing days, plus
  the same optional electrical readings/tariff.

## What the dashboard shows
1. **Agent Pipeline** — Orchestrator → Engineering Engine → Consumption/Fault
   Analysis Agent → Recommendation Agent (animated as the request resolves).
2. **Engineering Facts** — the deterministic numbers (consumption change %,
   power factor, voltage, real/apparent power, cost) plus any data
   limitations (e.g. "tariff not provided").
3. **Diagnosis** — one card per detected anomaly (EE-01 to EE-07), each with
   severity, the engine's triggering condition, the AI's plain-language
   explanation, a confidence label, and cited evidence.
4. **Recommendations** — prioritized action list from the Recommendation Agent.

## Push to GitHub / Deploy (Vercel)
Same as before — see the previous README section if needed, or:
```bash
git init && git add . && git commit -m "GridGuard AI frontend v2"
git remote add origin <your-repo-url>
git push -u origin main
```
Then import the repo on vercel.com and set `NEXT_PUBLIC_API_URL` to your
deployed backend URL in the project's environment variables.
