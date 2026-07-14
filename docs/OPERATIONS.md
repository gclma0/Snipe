# Operations Runbook

## Purpose

This runbook covers production checks, common failure modes, rate-limit tuning, and user-support diagnostics for Snipe.

It must not contain secrets. Do not paste Supabase service-role keys, JWTs, AI provider API keys, raw resume text, raw job descriptions, generated AI outputs, or uploaded document contents into tickets, logs, screenshots, or support notes.

## Production Health Checks

### In-App Checks

Use the deployed frontend first.

1. Open the deployed frontend.
2. Open `System diagnostics`.
3. Click `Check status`.
4. Confirm backend health is ok.
5. Confirm a request ID is shown.
6. Confirm AI provider status is either ready or shows a clear configuration issue.
7. Click `Run smoke test`.
8. Confirm backend, AI provider, Supabase frontend config, and session checks render.
9. Sign in with a test user.
10. Click `Run smoke test` again.
11. Confirm authenticated backend connectivity passes.
12. Click `Load usage summary`.
13. Confirm only aggregate counts are shown.

### Automated Smoke Test

Run from the repository root:

```powershell
.\scripts\production-smoke.ps1 `
  -FrontendUrl https://your-frontend.vercel.app `
  -BackendUrl https://your-backend.onrender.com
```

The smoke test checks frontend app shell availability, backend health, AI provider readiness, and secret-safe provider reporting.

### Direct Backend Checks

Use these only when browser diagnostics are not enough:

```powershell
Invoke-RestMethod https://your-backend.onrender.com/api/v1/health
Invoke-RestMethod https://your-backend.onrender.com/api/v1/health/ai-provider
Invoke-RestMethod https://your-backend.onrender.com/api/v1/usage/summary
```

For `429` responses, inspect `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

## Request IDs

Every backend response includes:

- `X-Request-ID`.
- `X-Process-Time-ms`.

When a user reports an error:

1. Ask for the visible `Request ID` from the UI error or diagnostics panel.
2. Search backend logs for that request ID.
3. Check the HTTP status code and endpoint.
4. Inspect the first useful traceback or error message.
5. Do not ask the user for raw resumes, job text, JWTs, or API keys.

Request IDs are diagnostic metadata only. They must never include secrets or user content.

## Common Failure Modes

### Frontend Cannot Reach Backend

Symptoms:

- Browser shows `Failed to fetch`.
- Diagnostics cannot load backend health.

Check:

- `VITE_API_BASE_URL` points to the deployed backend `/api/v1` base path.
- Backend CORS includes the deployed frontend origin.
- Render service is awake and has not failed startup.
- Browser devtools network tab shows the expected backend URL.

### Auth Works But Backend Rejects User

Symptoms:

- Supabase sign-in succeeds.
- Authenticated app requests return `401`.

Check:

- Backend `SUPABASE_JWT_SECRET` matches the Supabase project JWT secret.
- Frontend `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` belong to the same Supabase project.
- User is signed in again after changing Supabase/Auth settings.
- Backend logs include JWT validation details without logging token values.

### Supabase Operation Failed

Symptoms:

- Backend returns `Supabase <operation> failed.`

Check:

- Supabase service role key is configured only in backend environment variables.
- Required migrations have been applied.
- RLS policies and storage bucket exist.
- The failing operation name in the API response matches the backend log.
- The user owns the target profile.

### AI Provider Not Ready

Symptoms:

- Diagnostics show provider configuration needs attention.
- AI generation falls back or fails.

Check:

- `AI_PROVIDER` is supported.
- `AI_MODEL` is set for external providers.
- `AI_API_KEY` is not a placeholder.
- `AI_BASE_URL` is set and valid for `openai_compatible`.
- The provider health endpoint does not make a paid model call.

### Usage Summary Empty

Symptoms:

- `Load usage summary` shows zero events.

Check:

- Migration `005_usage_events.sql` has been applied.
- Public usage event endpoint is not blocked by CORS or rate limits.
- Browser requests to `/usage/events` return `202`.
- The app has been used after the migration was applied.

### Rate Limit Exceeded

Symptoms:

- Public endpoints return `429`.
- Diagnostics or smoke tests briefly fail after repeated clicks.

Check:

- Wait for `Retry-After`.
- Confirm this is not a repeated browser auto-refresh or script loop.
- Tune the public rate-limit environment variables only if normal usage is blocked.

## Rate-Limit Tuning

Environment variables:

- `PUBLIC_RATE_LIMIT_ENABLED`: default `true`.
- `PUBLIC_RATE_LIMIT_REQUESTS`: default `60`.
- `PUBLIC_RATE_LIMIT_WINDOW_SECONDS`: default `60`.

Guidance:

- Keep rate limiting enabled in production.
- Raise `PUBLIC_RATE_LIMIT_REQUESTS` if normal smoke testing or diagnostics are blocked.
- Lower it only if anonymous endpoints are being spammed.
- Remember the limiter is in-memory and per backend process. It is a free-tier guard, not a distributed edge firewall.

## Deployment Checklist

Before marking a deployment healthy:

1. Confirm frontend deploy succeeded.
2. Confirm backend deploy succeeded.
3. Apply any new Supabase migrations.
4. Run the automated production smoke test.
5. Run the in-app smoke test while signed out.
6. Sign in with a test user.
7. Run the in-app smoke test while signed in.
8. Upload a small PDF or DOCX resume.
9. Run at least one deterministic analysis.
10. Generate one cached AI output.
11. Load saved outputs after refresh.
12. Check privacy data summary and export.
13. Load usage summary.

## Logging Rules

Log:

- Request ID.
- Endpoint.
- Status code.
- Operation names.
- Timing.
- Non-secret configuration status.

Do not log:

- JWTs.
- API keys.
- Supabase service role keys.
- Resume text.
- Job-description text.
- Generated AI output.
- Uploaded document bytes.
- Full user emails unless explicitly needed for account support.

## Escalation Notes

Escalate when:

- Data deletion does not complete.
- A user can access another user's profile data.
- Raw document content appears in logs or diagnostics.
- A service-role key, JWT secret, or AI key was committed or exposed.
- RLS policies or storage privacy are suspected to be broken.

Immediate action for exposed secrets:

1. Rotate the affected key in the provider dashboard.
2. Update backend or frontend environment variables as appropriate.
3. Redeploy affected services.
4. Remove the secret from repository history if it was committed.
5. Record the incident and fix in `docs/DECISIONS.md` if it changes architecture or policy.
