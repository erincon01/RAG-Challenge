# Web Frontend (React + TypeScript + Tailwind)

## Run locally

```bash
cd frontend/webapp
npm install
npm run dev
```

By default the app expects backend API under `/api/v1` and proxies `/api/*` to `VITE_BACKEND_ORIGIN` (default `http://localhost:8000`).

## Environment variables

- `VITE_BACKEND_ORIGIN` (default: `http://localhost:8000`)
- `VITE_API_BASE_URL` (default: `/api/v1`)

## Build

```bash
npm run build
npm run preview
```
