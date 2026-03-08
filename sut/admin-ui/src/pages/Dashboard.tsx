import { api } from '../api'
import { useFetch } from '../hooks'
import StatusBadge from '../components/StatusBadge'
import { Activity, Package, ShoppingCart, Tag } from 'lucide-react'

export default function Dashboard() {
  const { data: orders, loading: lo } = useFetch(() => api.listOrders(), [])
  const { data: products, loading: lp } = useFetch(() => api.listProducts(), [])
  const { data: coupons, loading: lc } = useFetch(() => api.listCoupons(), [])

  const orderCount = orders?.length ?? 0
  const revenue = orders?.reduce((s, o) => s + o.total, 0) ?? 0
  const productCount = products?.length ?? 0
  const couponCount = coupons?.length ?? 0
  const recentOrders = (orders ?? []).slice(0, 8)

  const loading = lo || lp || lc

  const stats = [
    { label: 'Total Orders', value: orderCount, icon: ShoppingCart, color: 'text-sky-600' },
    { label: 'Revenue', value: `$${revenue.toFixed(2)}`, icon: Activity, color: 'text-emerald-600' },
    { label: 'Products', value: productCount, icon: Package, color: 'text-violet-600' },
    { label: 'Coupons', value: couponCount, icon: Tag, color: 'text-amber-600' },
  ]

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-stone-400">
        Loading…
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-lg font-semibold text-stone-800" data-testid="dashboard-heading">
        Dashboard
      </h1>
      <p className="mt-1 text-sm text-stone-500">
        Overview of your store activity.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div
            key={label}
            className="rounded-lg border border-stone-200 bg-white px-5 py-4"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-stone-500">{label}</span>
              <Icon size={16} className={color} strokeWidth={1.8} />
            </div>
            <p className="mt-2 text-2xl font-semibold text-stone-800">{value}</p>
          </div>
        ))}
      </div>

      <div className="mt-8">
        <h2 className="text-sm font-medium text-stone-700">Recent Orders</h2>
        <div className="mt-3 overflow-hidden rounded-lg border border-stone-200 bg-white">
          <table className="w-full text-left text-sm" data-testid="orders-table">
            <thead>
              <tr className="border-b border-stone-100 bg-stone-50/60">
                <th className="px-4 py-2.5 text-xs font-medium text-stone-500">ID</th>
                <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Customer</th>
                <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Status</th>
                <th className="px-4 py-2.5 text-right text-xs font-medium text-stone-500">Total</th>
                <th className="px-4 py-2.5 text-xs font-medium text-stone-500">Date</th>
              </tr>
            </thead>
            <tbody>
              {recentOrders.map((o) => (
                <tr key={o.id} className="border-b border-stone-100 last:border-0">
                  <td className="px-4 py-2.5 font-medium text-stone-700">#{o.id}</td>
                  <td className="px-4 py-2.5 text-stone-500">Customer #{o.customer_id}</td>
                  <td className="px-4 py-2.5">
                    <StatusBadge status={o.status} />
                  </td>
                  <td className="px-4 py-2.5 text-right font-medium text-stone-700">
                    ${o.total.toFixed(2)}
                  </td>
                  <td className="px-4 py-2.5 text-stone-400">
                    {new Date(o.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
              {recentOrders.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-stone-400">
                    No orders yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
