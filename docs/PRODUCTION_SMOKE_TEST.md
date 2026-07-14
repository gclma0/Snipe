# Production Smoke Test

Use this after deploying frontend/backend changes and applying any Supabase migrations.

## Automated Checks

Run from the repository root:

```powershell
.\scripts\production-smoke.ps1 `
  -FrontendUrl https://your-frontend.vercel.app `
  -BackendUrl https://your-backend.onrender.com
```

If the deployment intentionally uses the local-template fallback or has not configured an external AI provider yet, the script should still pass. If the provider is external but incomplete, fix the environment variables or run with `-AllowUnconfiguredAI` only while diagnosing.

The script verifies:

- Frontend returns a successful app-shell response.
- Backend `GET /api/v1/health` returns `status: ok`.
- Backend `GET /api/v1/health/ai-provider` returns non-secret provider status.
- AI provider status does not expose raw API key fields.

## GitHub Actions

The same smoke check can be run manually from GitHub:

1. Open the repository in GitHub.
2. Go to `Actions`.
3. Select `Production Smoke`.
4. Click `Run workflow`.
5. Enter the deployed frontend URL.
6. Enter the deployed backend URL.
7. Leave `allow_unconfigured_ai` off unless you are diagnosing an intentionally incomplete external provider setup.
8. Click `Run workflow`.

## Manual Browser Checks

1. Open the deployed frontend.
2. Click `Check status` in the AI provider panel.
3. Confirm the provider panel shows either a ready local-template provider or the intended external provider.
4. Sign in with a test user.
5. Create or load a candidate profile.
6. Upload a PDF or DOCX resume.
7. Run `Resume quality`, `Readiness scores`, and `Readiness dashboard`.
8. Paste or upload a target job description.
9. Run `Skill gap analysis`.
10. Generate one AI output, such as `AI interpretation` or `Tailoring package`.
11. Click `Load history` and confirm the generated output appears.
12. Add one reference-library item and run a reference search.
13. Run a job match search if references are available.
14. Open `Data summary`, `Privacy events`, and `Export data`.

## Pass Criteria

- No page crashes or blank screens.
- Authenticated requests succeed for the signed-in user.
- Resume parsing creates profile evidence.
- Deterministic analyses return visible results.
- Generated outputs are saved and reload after refresh/history load.
- Privacy export works and does not include raw document bytes.
- AI-provider status shows booleans only for key presence, not secret values.
