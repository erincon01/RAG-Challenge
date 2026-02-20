interface StatusBadgeProps {
  ok: boolean
  okLabel?: string
  failLabel?: string
}

export function StatusBadge({ ok, okLabel = 'Online', failLabel = 'Offline' }: StatusBadgeProps) {
  return (
    <span
      className={[
        'rounded-full px-3 py-1 text-xs font-semibold tracking-wide',
        ok ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300',
      ].join(' ')}
    >
      {ok ? okLabel : failLabel}
    </span>
  )
}
