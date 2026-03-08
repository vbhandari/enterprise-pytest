import { api } from '../api'
import { useFetch } from '../hooks'

export default function Coupons() {
  const { data: coupons, loading } = useFetch(() => api.listCoupons(), [])

  if (loading) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-stone-400">
        Loading…
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-lg font-semibold text-stone-800">Coupons</h1>
      <p className="mt-1 text-sm text-stone-500">Discount codes and promotions.</p>

      <div className="mt-6 overflow-hidden rounded-lg border border-stone-200 bg-white">
        <table className="w-full text-left text-sm" data-testid="coupons-table">
          <thead>
            <tr className="border-b border-stone-100 bg-stone-50/60">
              <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Code</th>
              <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Discount</th>
              <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Valid From</th>
              <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Valid To</th>
              <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Uses</th>
              <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Status</th>
            </tr>
          </thead>
          <tbody>
            {(coupons ?? []).map((c) => {
              const now = new Date()
              const from = new Date(c.valid_from)
              const to = new Date(c.valid_to)
              const isExpired = now > to
              const isUpcoming = now < from

              return (
                <tr key={c.id} className="border-b border-stone-100 last:border-0">
                  <td className="px-4 py-2.5">
                    <code className="rounded bg-stone-100 px-1.5 py-0.5 text-xs font-medium text-stone-700">
                      {c.code}
                    </code>
                  </td>
                  <td className="px-4 py-2.5 font-medium text-stone-700">
                    {c.discount_percent}%
                  </td>
                  <td className="px-4 py-2.5 text-stone-500">
                    {from.toLocaleDateString()}
                  </td>
                  <td className="px-4 py-2.5 text-stone-500">
                    {to.toLocaleDateString()}
                  </td>
                  <td className="px-4 py-2.5 text-stone-500">
                    {c.current_uses} / {c.max_uses}
                  </td>
                  <td className="px-4 py-2.5">
                    {isExpired ? (
                      <span className="inline-flex items-center rounded-md bg-stone-100 px-2 py-0.5 text-xs font-medium text-stone-500 ring-1 ring-inset ring-stone-500/20">
                        expired
                      </span>
                    ) : isUpcoming ? (
                      <span className="inline-flex items-center rounded-md bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20">
                        upcoming
                      </span>
                    ) : c.is_active ? (
                      <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
                        active
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-md bg-stone-100 px-2 py-0.5 text-xs font-medium text-stone-500 ring-1 ring-inset ring-stone-500/20">
                        inactive
                      </span>
                    )}
                  </td>
                </tr>
              )
            })}
            {(coupons ?? []).length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-stone-400">
                  No coupons found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
