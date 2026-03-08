const palette: Record<string, string> = {
  created: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  paid: 'bg-sky-50 text-sky-700 ring-sky-600/20',
  shipped: 'bg-violet-50 text-violet-700 ring-violet-600/20',
  delivered: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  cancelled: 'bg-stone-100 text-stone-500 ring-stone-500/20',
}

export default function StatusBadge({ status }: { status: string }) {
  const cls = palette[status] ?? 'bg-stone-100 text-stone-600 ring-stone-500/20'
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${cls}`}
    >
      {status}
    </span>
  )
}
