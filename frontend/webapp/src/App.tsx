import { Route, Routes } from 'react-router-dom'

import { AppShell } from './components/layout/AppShell'
import { CatalogPage } from './pages/CatalogPage'
import { ChatPage } from './pages/ChatPage'
import { DashboardPage } from './pages/DashboardPage'
import { EmbeddingsPage } from './pages/EmbeddingsPage'
import { ExplorerPage } from './pages/ExplorerPage'
import { OperationsPage } from './pages/OperationsPage'
import { SourcesPage } from './pages/SourcesPage'

function NotFoundPage() {
  return <p className="text-mute">Ruta no encontrada.</p>
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="sources" element={<SourcesPage />} />
        <Route path="catalog" element={<CatalogPage />} />
        <Route path="operations" element={<OperationsPage />} />
        <Route path="explorer" element={<ExplorerPage />} />
        <Route path="embeddings" element={<EmbeddingsPage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
