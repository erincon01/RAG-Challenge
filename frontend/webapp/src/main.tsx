import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'

import { App } from './App'
import { queryClient } from './lib/queryClient'
import { UISettingsProvider } from './state/ui-settings'
import './styles.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <UISettingsProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </UISettingsProvider>
    </QueryClientProvider>
  </StrictMode>,
)
