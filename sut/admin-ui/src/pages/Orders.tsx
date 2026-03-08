import { useState } from 'react'
import { api } from '../api'
import { useFetch } from '../hooks'
import StatusBadge from '../components/StatusBadge'
import type { OrderStatus } from '../types'

const STATUSES: Array<{ label: string; value: string | undefined }> = [
  { label: 'All', value: undefined },
  { label: 'Created', value: 'created' },
  { label: 'Paid', value: 'paid' },
  { label: 'Shipped', value: 'shipped' },
  { label: 'Delivered', value: 'delivered' },
  { label: 'Cancelled', value: 'cancelled' },
]

const NEXT_STATUS: Record<string, OrderStatus | null> = {
  created: 'paid',
  paid: 'shipped',
  shipped: 'delivered',
  delivered: null,
  cancelled: null,
}

export default function Orders() {
  const [filter, setFilter] = useState<string | undefined>(undefined)
  const { data: orders, loading, refetch } = useFetch(
    () => api.listOrders(filter),
    [filter],
  )

  async function advanceStatus(orderId: number, currentStatus: string) {
    const next = NEXT_STATUS[currentStatus]
    if (!next) return
    await api.updateOrderStatus(orderId, next)
    refetch()
  }

  return (
    <div>
      <h1 className="text-lg font-semibold text-stone-800">Orders</h1>
      <p className="mt-1 text-sm text-stone-500">Manage and track all customer orders.</p>

      <div className="mt-5 flex gap-1.5" data-testid="status-filters">
        {STATUSES.map(({ label, value }) => (
          <button
            key={label}
            onClick={() => setFilter(value)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              filter === value
                ? 'bg-stone-900 text-white'
                : 'bg-white text-stone-500 ring-1 ring-stone-200 hover:bg-stone-50'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex h-40 items-center justify-center text-sm text-stone-400">
          Loading…
        </div>
      ) : (
        <div className="mt-4 overflow-hidden rounded-lg border border-stone-200 bg-white">
          <table className="w-full text-left text-sm" data-testid="orders-table">
            <thead>
              <tr className="border-b border-stone-100 bg-stone-50/60">
                <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Order</th>
                <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Customer</th>
                <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Status</th>
                <th className="px-4 py-2.5 text-right text-xs font-medium text-stone-500">Total</th>
                <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Date</th>
                <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Action</th>
              </tr>
            </thead>
            <tbody>
              {(orders ?? []).map((o) => (
                <tr key={o.id} className="border-b border-stone-100 last:border-0">
                  <td className="px-4 py-2.5 font-medium text-stone-700">#{o.id}</td>
                  <td className="px-4 py-2.5 text-stone-500">#{o.customer_id}</td>
                  <td className="px-4 py-2.5">
                    <StatusBadge status={o.status} />
                  </td>
                  <td className="px-4 py-2.5 text-right font-medium text-stone-700">
                    ${o.total.toFixed(2)}
                  </td>
                  <td className="px-4 py-2.5 text-stone-400">
                    {new Date(o.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-2.5">
                    {NEXT_STATUS[o.status] && (
                      <button
                        onClick={() => advanceStatus(o.id, o.status)}
                        className="rounded-md bg-stone-100 px-2.5 py-1 text-xs font-medium text-stone-600 transition-colors hover:bg-stone-200"
                      >
                        → {NEXT_STATUS[o.status]}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {(orders ?? []).length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-stone-400">
                    No orders found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
