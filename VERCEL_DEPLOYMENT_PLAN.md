# Vercel Deployment Plan (Refactored Full Vercel)

## Architecture Implemented

- Frontend: `index.html` (browser camera + `face-api.js`)
- Backend: Vercel serverless functions under `api/`
- Storage: Vercel Blob (file-based, no database)
  - `students/master.json`
  - `students/images/<id>.jpg`
  - `attendance/attendance_YYYY-MM-DD.csv`
- Retention: 15-day cleanup in runtime + Vercel cron

## Required Vercel Environment Variables

1. `BLOB_READ_WRITE_TOKEN` (required)
2. `LOG_RETENTION_DAYS` (optional, default `15`)
3. `APP_TIMEZONE` (optional, default `Asia/Colombo`)
4. `FACE_MATCH_THRESHOLD` (optional, default `0.5`)
5. `CRON_SECRET` (recommended, protects `/api/cron/cleanup`)

## Deployment Steps

1. Connect this repo to Vercel.
2. Add environment variables above in Project Settings.
3. Deploy with Node 18+ runtime.
4. Confirm cron exists from `vercel.json`:
   - Path: `/api/cron/cleanup`
   - Schedule: `0 1 * * *` (daily)

## Production Validation Checklist

1. Open deployed URL and allow camera permissions.
2. Register a student and confirm image + descriptor persistence.
3. Check-in and check-out for the student.
4. Download CSV from the dashboard by date.
5. Call `/api/health` and `/api/attendance/files` to verify API health.
6. Trigger `/api/cron/cleanup` manually (with `CRON_SECRET`) and verify old files are removed.

## Notes

- This is fully Vercel-compatible and database-free.
- The old Python Flask implementation is still in the repo for local legacy use but is not required for Vercel deployment.
