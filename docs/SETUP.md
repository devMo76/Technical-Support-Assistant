# Local setup and authentication

[← Project overview](../README.md)

## Requirements

- Python 3.13 and Node.js 22.
- A Supabase project and the Supabase CLI for applying database migrations.
- Anthropic and Gemini API access for live questions.

Follow the dependency installation commands in the [root README](../README.md#run-it-locally).

## Environment files

Copy the examples without overwriting an existing configured file:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env.local
```

Fill in:

| File | Setting | Purpose |
| :--- | :--- | :--- |
| `backend/.env` | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | Answer generation; select a model available to your account |
| `backend/.env` | `ANTHROPIC_EFFORT=low` | Required by the shared Claude service |
| `backend/.env` | `GEMINI_API_KEY`, `GEMINI_EMBEDDING_MODEL=gemini-embedding-2` | Question embeddings; keep compatible with stored document embeddings |
| `backend/.env` | `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` | Verify identity and load the user's profile |
| `backend/.env` | `FRONTEND_ORIGIN=http://localhost:3000` | Allowed browser origin |
| `frontend/.env.local` | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Browser/server authentication with the same Supabase project |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` | Backend URL |

The publishable key is intended for client use; never put secret/service-role keys in `NEXT_PUBLIC_*`. Keep real environment files out of Git. Restart each service after changing its environment file.

## Database setup

Apply migrations to the intended project:

```powershell
supabase link --project-ref YOUR_PROJECT_REF
supabase db push
```

Review the linked project before `db push`. These commands apply schema changes; they are not required on every startup.

The migration creates profiles with a default `staff` role and automatically adds a profile when an Auth user is created. Normal users can update their display name, not their role. Private support records are owner-scoped with admin access through RLS.

`staff` is the current implementation's ordinary application role, including for self-registered users. It does not establish employment or membership in an organization. Self-registration therefore changes the original invite-only access model deliberately.

## Basic development signup

In your hosted Supabase project's Authentication settings:

1. Enable new-user signups and the Email provider.
2. For the current basic development flow, disable **Confirm email** and leave custom SMTP disabled.
3. Set Site URL to `http://localhost:3000`.
4. Save, open `/signup` and register a fresh test email/password. The form requires at least 12 password characters.
5. Confirm that a profile was created with role `staff`, then ask a question.

Disabling confirmation means an email address is not proof of ownership. Use verified identities and appropriate abuse/cost controls before making registration publicly accessible.

Hosted settings are not changed by editing `supabase/config.toml`. The checked-in local configuration currently has `[auth] enable_signup = false`; change it to `true` when running local Supabase with self-registration.

## Optional email confirmation

The application includes `/auth/confirm` and `/auth/confirmation-error`. To use them:

1. Enable Confirm email in hosted Supabase.
2. Configure custom SMTP for delivery to real users; the default Supabase mail service has recipient restrictions.
3. Set the Confirm signup template's link to:

```html
<a href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&amp;type=email">
  Confirm email
</a>
```

Use the deployed HTTPS site URL instead of localhost when deploying. A localhost URL is appropriate only for development on the machine running the frontend. The callback uses Supabase's `verifyOtp` and redirects to the dashboard on success.

See the official [password authentication guide](https://supabase.com/docs/guides/auth/passwords) and [SMTP guide](https://supabase.com/docs/guides/auth/auth-smtp).

## First administrator

Use the Supabase SQL editor as a trusted project owner. Replace the placeholder with the intended existing Auth user's email:

```sql
update public.profiles
set role = 'admin', updated_at = now()
where id = (
  select id from auth.users where email = 'first.admin@example.com'
);
```

Confirm exactly one intended row changed. After bootstrap, the guarded `set_staff_role(target_user_id, new_role)` function checks admin privileges and rejects attempts to change the caller's own role. Do not expose project-owner or service-role credentials to application users.

For role/isolation checks, use two staff accounts and an admin account in an isolated test project.

## Start the services

Backend, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Frontend, in a second terminal:

```powershell
cd frontend
npm run dev
```

Open [localhost:3000](http://localhost:3000).

## Common development problems

| Symptom | Check |
| :--- | :--- |
| `No module named fastapi` | Use `.\.venv\Scripts\python.exe`, not the unrelated Conda/system interpreter. |
| `503` with `Authentication service is not configured` | Set both backend Supabase variables, then restart the backend. Frontend variables alone are insufficient. |
| Other authentication `503` | Check Supabase connectivity and the exact response detail. |
| `401` | Sign in again; the token may be missing or expired. |
| `403` | Check the matching profile and allowed role. Do not bypass the backend authorization check. |
| Signup asks for confirmation unexpectedly | Check hosted Confirm email settings; an existing account and a fresh registration can follow different paths. |
| No confirmation email arrives | Check provider delivery, SMTP configuration and spam folders. |
| Chunk/embedding mismatch | Regenerate chunks and matching embeddings together before querying. |
| `502` during a question | Check server-side provider configuration, quotas, network availability and generation failure logs. |

Current queries use JSONL files and calculate rankings in Python. The app does not yet persist conversations or send earlier visible exchanges back to the model.
