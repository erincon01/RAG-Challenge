import { useUISettings } from '../state/ui-settings'

export function ChatPage() {
  const { mode } = useUISettings()

  return (
    <section className="space-y-3 rounded-2xl border border-white/10 bg-panel/70 p-5">
      <h2 className="text-2xl font-semibold text-ink">Chat RAG</h2>
      <p className="text-mute">El flujo de chat se habilita en Fase 5 con restricciones dinámicas por source/capabilities.</p>
      <p className="text-sm text-ink">
        Modo actual: <span className="font-semibold capitalize">{mode}</span>
      </p>
    </section>
  )
}
