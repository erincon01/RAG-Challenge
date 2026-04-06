# RAG Challenge - Web Frontend

> Modern React TypeScript application for football analytics with AI-powered semantic search.

## 🎯 Overview

Full-featured web application built with React 19, TypeScript, and TailwindCSS. Provides a complete UI for managing StatsBomb data ingestion, exploring football match data, and performing RAG-powered semantic searches.

### Tech Stack

- **React 19** - Modern UI library with latest features
- **TypeScript 5** - Type safety throughout
- **Vite 6** - Fast build tool and dev server
- **TailwindCSS 3** - Utility-first CSS framework
- **TanStack Query** - Powerful data fetching and state management
- **React Router 7** - Client-side routing
- **Zod** - Runtime type validation

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Backend API running (see [backend/README.md](../../backend/README.md))

### Local Development

```bash
# Install dependencies
cd frontend/webapp
npm install

# Start dev server
npm run dev

# App runs at http://localhost:5173
```

### Docker

```bash
# From project root
docker compose up frontend

# Or build manually
docker build -f frontend/webapp/Dockerfile -t rag-frontend .
docker run -p 5173:5173 rag-frontend
```

---

## 📐 Architecture

### Project Structure

```
src/
├── pages/                    # Page components
│   ├── HomePage.tsx         # Landing page
│   ├── DashboardPage.tsx    # System overview
│   ├── CatalogPage.tsx      # StatsBomb catalog browser
│   ├── OperationsPage.tsx   # Data ingestion & jobs
│   ├── ExplorerPage.tsx     # Data explorer
│   ├── EmbeddingsPage.tsx   # Embeddings management
│   └── ChatPage.tsx         # RAG chat interface
│
├── components/              # Reusable components
│   ├── layout/             # Layout components
│   │   └── AppShell.tsx    # Main app layout with nav
│   └── ui/                 # UI components
│       └── StatusBadge.tsx # Status indicator
│
├── lib/                     # Utilities and helpers
│   ├── api/                # Backend API client
│   │   ├── client.ts       # HTTP client (151 lines)
│   │   └── types.ts        # TypeScript types (208 types)
│   ├── storage/            # Local storage utilities
│   │   └── catalogSelection.ts
│   └── queryClient.ts      # TanStack Query config
│
├── state/                   # Global state management
│   └── ui-settings.tsx     # UI preferences
│
├── App.tsx                  # Root component with routing
├── main.tsx                # Application entry point
└── styles.css              # Global styles + Tailwind
```

### Key Patterns

#### Type-Safe API Client

All backend communication goes through a centralized, type-safe client:

```typescript
import { apiClient } from '@/lib/api/client';
import type { Competition, Match } from '@/lib/api/types';

// Fully typed requests and responses
const competitions = await apiClient.getCompetitions('postgres');
const match = await apiClient.getMatch('postgres', 12345);
```

#### TanStack Query for State

Uses React Query for caching, refetching, and state management:

```typescript
const { data: competitions, isLoading, error } = useQuery({
  queryKey: ['competitions', source],
  queryFn: () => apiClient.getCompetitions(source),
  refetchInterval: 30000, // Auto-refresh every 30s
});
```

#### Local State Persistence

UI preferences stored in localStorage:

```typescript
import { useUiSettings } from '@/state/ui-settings';

const { isDeveloperMode, setDeveloperMode } = useUiSettings();
```

---

## 🎨 Features & Pages

### 1. Dashboard (`/`)

**Purpose:** System health and quick overview

**Features:**
- Backend API health status
- Database connectivity checks
- Recent job activity
- Quick links to main sections

**Key Components:**
- Health status cards
- Job summary table

---

### 2. StatsBomb Catalog (`/catalog`)

**Purpose:** Browse and select competitions/matches from StatsBomb open data

**Features:**
- Competition browser with search
- Season selection
- Match listing by competition
- Bulk selection for import
- Local storage persistence

**API Endpoints:**
- `GET /api/v1/statsbomb/competitions`
- `GET /api/v1/statsbomb/matches?competition_id=...`

**State Management:**
- Selected items stored in localStorage
- Persists across page refreshes

---

### 3. Operations (`/operations`)

**Purpose:** Data ingestion and job management

**Features:**
- Download StatsBomb data
- Load into PostgreSQL or SQL Server
- Create aggregations
- Rebuild embeddings
- Real-time job tracking
- Job filtering and cleanup
- Execution terminal

**API Endpoints:**
- `POST /api/v1/ingestion/download`
- `POST /api/v1/ingestion/load`
- `GET /api/v1/ingestion/jobs`
- `POST /api/v1/ingestion/jobs/{id}/cancel`
- `DELETE /api/v1/ingestion/jobs`

**Job States:**
- `pending` - Queued
- `running` - In progress
- `success` - Completed successfully
- `error` - Failed
- `canceled` - User canceled

**Polling:**
- Auto-refreshes job list every 2 seconds when jobs are running

---

### 4. Data Explorer (`/explorer`)

**Purpose:** Browse loaded data

**Features:**
- Competitions view
- Matches view (with filters)
- Teams view
- Players view
- Events view (by match)
- Tables info (metadata)

**API Endpoints:**
- `GET /api/v1/competitions?source=...`
- `GET /api/v1/matches?source=...`
- `GET /api/v1/explorer/teams?source=...`
- `GET /api/v1/explorer/players?source=...`
- `GET /api/v1/events?source=...&match_id=...`

**Filtering:**
- Source selection (PostgreSQL vs SQL Server)
- Match-specific filters
- Search functionality

---

### 5. Embeddings (`/embeddings`)

**Purpose:** Manage vector embeddings

**Features:**
- Coverage status by model
- Match-specific embedding status
- Rebuild embeddings manually
- Model selection

**API Endpoints:**
- `GET /api/v1/embeddings/status?source=...`
- `POST /api/v1/embeddings/rebuild`

**Supported Models:**
- `text-embedding-ada-002`
- `text-embedding-3-small`
- `text-embedding-3-large`
- `e5-large-v2`

---

### 6. Chat (`/chat`)

**Purpose:** RAG-powered semantic search

**Features:**
- Natural language queries
- Multi-language support
- Model/algorithm selection
- Capability-aware UI (adapts to available features)
- Source selection (PostgreSQL or SQL Server)

**API Endpoints:**
- `POST /api/v1/chat/search`
- `GET /api/v1/capabilities`

**Search Algorithms:**
- Cosine similarity
- Inner product
- L2 distance

**Example Queries:**
- "Who scored the most goals in this match?"
- "Show me all fouls in the second half"
- "What were the key moments of the game?"

---

## ⚙️ Configuration

### Environment Variables

Create a `.env.local` file (gitignored):

```bash
# Backend API URL
VITE_BACKEND_ORIGIN=http://localhost:8000

# API base path (default: /api/v1)
VITE_API_BASE_URL=/api/v1
```

### Vite Proxy

Development server proxies `/api/*` requests to backend:

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: env.VITE_BACKEND_ORIGIN || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

---

## 🛠️ Development

### Scripts

```bash
# Development server (hot reload)
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format

# Production build
npm run build

# Preview production build
npm run preview
```

### Code Style

- **TypeScript:** Strict mode enabled
- **ESLint:** React + TypeScript rules
- **Prettier:** Not configured (can be added)
- **Tailwind:** Utility-first, no custom CSS preferred

### Best Practices

1. **Type Everything:** All API responses typed via `types.ts`
2. **Use React Query:** For all async state and server data
3. **Component Composition:** Small, focused components
4. **Error Handling:** Always handle loading/error states
5. **Accessibility:** Semantic HTML, ARIA labels where needed

---

## 🧪 Testing

**Status:** Not yet implemented

**Planned:**
- Unit tests with Vitest
- Component tests with React Testing Library
- E2E tests with Playwright

---

## 📦 Build & Deployment

### Production Build

```bash
npm run build

# Output in dist/
# - Minified JS/CSS
# - Tree-shaken dependencies
# - Source maps (optional)
```

### Docker Build

```dockerfile
# Multi-stage build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Environment-Specific Builds

```bash
# Development
npm run dev

# Staging
VITE_BACKEND_ORIGIN=https://api-staging.example.com npm run build

# Production
VITE_BACKEND_ORIGIN=https://api.example.com npm run build
```

---

## 🔧 Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Change port in vite.config.ts or use env var
PORT=5174 npm run dev
```

#### API Connection Failed

```bash
# Check backend is running
curl http://localhost:8000/api/v1/health

# Check proxy configuration in vite.config.ts
# Verify VITE_BACKEND_ORIGIN in .env.local
```

#### Type Errors

```bash
# Regenerate types if backend API changed
# (Manual process - update src/lib/api/types.ts)

# Run type checker
npm run type-check
```

#### Build Fails

```bash
# Clear cache and rebuild
rm -rf node_modules dist
npm install
npm run build
```

---

## 🚀 Performance Optimization

### Current Optimizations

- ✅ Code splitting by route
- ✅ Lazy loading of pages
- ✅ TanStack Query caching (30s default)
- ✅ Vite tree-shaking
- ✅ Production builds minified

### Future Improvements

- [ ] Image optimization
- [ ] Service worker for offline support
- [ ] Virtual scrolling for large lists
- [ ] Debounced search inputs
- [ ] Optimistic UI updates

---

## 📚 Dependencies

### Core

- `react` ^19.0.0
- `react-dom` ^19.0.0
- `react-router` ^7.1.3
- `@tanstack/react-query` ^5.64.2

### UI

- `tailwindcss` ^3.4.17
- `@headlessui/react` (if needed)
- `lucide-react` (icons, if added)

### Build Tools

- `vite` ^6.0.7
- `typescript` ^5.7.3
- `@vitejs/plugin-react` ^4.3.4

### Validation

- `zod` ^3.24.1 (if added for forms)

---

## 🤝 Contributing

### Adding a New Page

1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation link in `src/components/layout/AppShell.tsx`
4. Update this README

### Adding a New API Endpoint

1. Add type definitions to `src/lib/api/types.ts`
2. Add method to `src/lib/api/client.ts`
3. Use in component with `useQuery` or `useMutation`

### Code Review Checklist

- [ ] TypeScript types added
- [ ] Error states handled
- [ ] Loading states shown
- [ ] Responsive design tested
- [ ] Accessibility considered
- [ ] No console errors/warnings

---

## 📄 License

MIT - See [LICENSE](../../LICENSE)

---

## 🔗 Related Documentation

- [Backend API](../../backend/README.md)
- [Architecture Decision Records](../../docs/adr/)
- [Project Status](../../PROJECT_STATUS.md)
- [Main README](../../README.md)

---

**Last Updated:** 2026-02-20
