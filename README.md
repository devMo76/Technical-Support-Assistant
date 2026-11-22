# Technical Support Assistant

Internal support application built with Next.js 16, FastAPI, Supabase, and a
shared low-effort Claude service.

## Run locally

Requirements: Python 3.13, Node.js 22, and a Supabase project.

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
cd frontend
npm ci
cd ..
```

Copy `backend/.env.example` to `backend/.env` and
`frontend/.env.example` to `frontend/.env.local`. Fill in the same Supabase
project URL and publishable key in both files. The publishable key is safe for
the browser; never put a secret key or service-role key in `NEXT_PUBLIC_*`.

The Claude variables remain server-only. Keep `ANTHROPIC_EFFORT=low`; the
shared service also enforces low effort and disables thinking.

Apply versioned migrations with the Supabase CLI against the intended project:

```powershell
supabase link --project-ref YOUR_PROJECT_REF
supabase db push
```

Review the linked project before running `db push`. The repository does not
run migrations automatically and no command here deletes production data.

Start the backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Start the frontend in another terminal:

```powershell
cd frontend
npm run dev
```

Open http://localhost:3000. The backend health check is at
http://127.0.0.1:8000/health.

## Staff accounts and the first administrator

Public registration is intentionally not implemented. In the Supabase
Dashboard, go to Authentication > Users and create staff test accounts with
email/password. The Stage 3 trigger creates a `profiles` row with the safe
default `staff` role for each new user.

Bootstrap the first administrator from the Supabase SQL editor while signed in
as a trusted project owner. Replace the placeholder email and run:

```sql
update public.profiles
set role = 'admin', updated_at = now()
where id = (
  select id from auth.users where email = 'first.admin@example.com'
);
```

Confirm exactly one intended row changed. After bootstrap, administrators can
use the `set_staff_role(target_user_id, new_role)` database function. It checks
the caller's verified identity, rejects staff callers, and prevents admins from
changing their own role. Do not distribute database owner or service-role
credentials to staff.

For repeatable tests, create at least two staff accounts and one admin account
in a non-production Supabase project. This allows owner isolation and admin
policy behavior to be checked without touching production data.

## Authentication and authorization

- Next.js refreshes Supabase sessions in `proxy.ts`, forwards refreshed
  cookies, and marks session-dependent responses private/no-store.
- `/login` supports email/password sign-in only; `/dashboard` is protected.
- Browser application requests should use `apiFetch`, which sends the current
  Supabase access token to FastAPI as a Bearer token.
- FastAPI verifies that token with Supabase Auth before trusting any identity,
  then loads the RLS-protected profile and applies staff/admin checks.
- PostgreSQL RLS restricts private support records to their owner or an admin.
  Column grants and a guarded function prevent self-promotion.

## Automated checks

Run all local checks without making Claude API calls:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests
.\.venv\Scripts\python.exe -m compileall -q backend
cd frontend
npm test
npm run lint
npm run build
```

GitHub Actions runs the same backend tests plus frontend tests, linting, and a
production build. Unit tests mock Supabase. RLS policies must additionally be
verified against an isolated local or test Supabase database before relying on
them in production.

## Paperless document chunking

Generate the searchable Paperless records from the five Markdown guides listed
in `data/paperless/sources.json`:

```powershell
.\.venv\Scripts\python.exe -m backend.ingestion.chunk_documents
```

The command verifies every source hash and atomically replaces
`data/paperless/processed/chunks.jsonl`. Each UTF-8 JSONL record contains the
chunk `id`, original `text`, source metadata, inclusive source line range, and
`heading_path` hierarchy. The 2,000-character target is a soft limit: a single
large paragraph, code block, or table remains intact and produces a warning
instead of being split or dropped.
