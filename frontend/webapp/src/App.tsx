import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'

import { AppShell } from './components/layout/AppShell'

const HomePage = lazy(() => import('./pages/HomePage').then(m => ({ default: m.HomePage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })))
const CatalogPage = lazy(() => import('./pages/CatalogPage').then(m => ({ default: m.CatalogPage })))
const OperationsPage = lazy(() => import('./pages/OperationsPage').then(m => ({ default: m.OperationsPage })))
const ExplorerPage = lazy(() => import('./pages/ExplorerPage').then(m => ({ default: m.ExplorerPage })))
const EmbeddingsPage = lazy(() => import('./pages/EmbeddingsPage').then(m => ({ default: m.EmbeddingsPage })))
const ChatPage = lazy(() => import('./pages/ChatPage').then(m => ({ default: m.ChatPage })))
const TutorialsPage = lazy(() => import('./pages/TutorialsPage').then(m => ({ default: m.TutorialsPage })))

function PageLoader() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
    </div>
  )
}

function NotFoundPage() {
  return <p className="text-mute">Ruta no encontrada.</p>
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<Suspense fallback={<PageLoader />}><HomePage /></Suspense>} />
        <Route path="dashboard" element={<Suspense fallback={<PageLoader />}><DashboardPage /></Suspense>} />
        <Route path="catalog" element={<Suspense fallback={<PageLoader />}><CatalogPage /></Suspense>} />
        <Route path="operations" element={<Suspense fallback={<PageLoader />}><OperationsPage /></Suspense>} />
        <Route path="explorer" element={<Suspense fallback={<PageLoader />}><ExplorerPage /></Suspense>} />
        <Route path="embeddings" element={<Suspense fallback={<PageLoader />}><EmbeddingsPage /></Suspense>} />
        <Route path="chat" element={<Suspense fallback={<PageLoader />}><ChatPage /></Suspense>} />
        <Route path="tutorials" element={<Suspense fallback={<PageLoader />}><TutorialsPage /></Suspense>} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
